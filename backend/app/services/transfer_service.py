"""
Student Center Transfer and Enrollment Lifecycle Business Service Layer.
Enforces atomic cross-center transitions, single active enrollment guarantee,
and Super Admin capacity override controls within ACID transactions.
"""
import math
from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditLog
from app.models.center import Center
from app.models.enums import EnrollmentStatus, TransferStatus, UserRole
from app.models.student import EnrollmentRecord, Student, TransferRequest
from app.models.user import User, UserCenter
from app.schemas.transfer import (
    TransferRequestCreate,
    TransferResponse,
    TransferReviewRequest,
    TransferReviewResponse,
)
from app.services.center_service import get_center_occupancy


class TransferServiceError(Exception):
    """Base exception for transfer service operations."""
    pass


class TransferNotFoundError(TransferServiceError):
    """Raised when transfer request is not found."""
    pass


class TransferValidationError(TransferServiceError):
    """Raised for business rule violations."""
    pass


class DestinationCapacityExceededError(TransferServiceError):
    """Raised when destination center is full without authorized override."""
    pass


def serialize_transfer_response(tr: TransferRequest) -> TransferResponse:
    """Safely converts TransferRequest ORM instance into TransferResponse."""
    student_name = None
    if tr.student:
        student_name = f"{tr.student.first_name} {tr.student.last_name}"

    from_center_name = tr.from_center.name if tr.from_center else None
    to_center_name = tr.to_center.name if tr.to_center else None

    return TransferResponse(
        id=tr.id,
        student_id=tr.student_id,
        from_center_id=tr.from_center_id,
        to_center_id=tr.to_center_id,
        requested_by_user_id=tr.requested_by_user_id,
        reviewed_by_user_id=tr.reviewed_by_user_id,
        status=tr.status,
        request_reason=tr.request_reason,
        review_notes=tr.review_notes,
        capacity_override=tr.capacity_override,
        capacity_override_reason=tr.capacity_override_reason,
        effective_date=tr.effective_date,
        requested_at=tr.requested_at,
        reviewed_at=tr.reviewed_at,
        student_name=student_name,
        from_center_name=from_center_name,
        to_center_name=to_center_name,
    )


def create_transfer_request(
    db: Session,
    payload: TransferRequestCreate,
    current_user: User,
    client_ip: Optional[str] = None,
) -> TransferRequest:
    """Initiates an inter-center transfer request from source center."""
    student = db.get(Student, payload.student_id)
    if not student:
        raise TransferValidationError("Target student not found.")

    from_center_id = student.current_center_id
    if from_center_id == payload.to_center_id:
        raise TransferValidationError("Destination center must be different from the student's current center.")

    to_center = db.get(Center, payload.to_center_id)
    if not to_center or not to_center.is_active:
        raise TransferValidationError("Destination center not found or is inactive.")

    # Authorization: User must have access to source center
    if current_user.role != UserRole.SUPER_ADMIN:
        is_assigned = (
            db.query(UserCenter)
            .filter(UserCenter.user_id == current_user.id, UserCenter.center_id == from_center_id)
            .first()
            is not None
        )
        if not is_assigned:
            raise TransferValidationError("You can only initiate transfers for students at your assigned center.")

    # Check if a pending transfer already exists for this student
    pending_existing = (
        db.query(TransferRequest)
        .filter(
            TransferRequest.student_id == student.id,
            TransferRequest.status == TransferStatus.PENDING,
        )
        .first()
    )
    if pending_existing:
        raise TransferValidationError("A pending transfer request already exists for this student.")

    transfer = TransferRequest(
        student_id=student.id,
        from_center_id=from_center_id,
        to_center_id=payload.to_center_id,
        requested_by_user_id=current_user.id,
        status=TransferStatus.PENDING,
        request_reason=payload.request_reason.strip(),
        effective_date=payload.effective_date,
    )
    db.add(transfer)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="TRANSFER_INITIATE",
        resource_type="TRANSFER_REQUEST",
        resource_id=transfer.id,
        client_ip=client_ip,
        old_values=None,
        new_values={
            "student_id": str(student.id),
            "from_center_id": str(from_center_id),
            "to_center_id": str(payload.to_center_id),
            "effective_date": payload.effective_date.isoformat(),
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(transfer)
    return transfer


def list_transfers(
    db: Session,
    current_user: User,
    status: Optional[TransferStatus] = None,
    direction: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[TransferRequest], int]:
    """Lists transfer requests scoped to user role and center assignments."""
    query = db.query(TransferRequest).options(
        joinedload(TransferRequest.student),
        joinedload(TransferRequest.from_center),
        joinedload(TransferRequest.to_center),
    )

    if current_user.role != UserRole.SUPER_ADMIN:
        assigned_cids = [
            uc.center_id
            for uc in db.query(UserCenter).filter(UserCenter.user_id == current_user.id).all()
        ]
        if direction == "incoming":
            query = query.filter(TransferRequest.to_center_id.in_(assigned_cids))
        elif direction == "outgoing":
            query = query.filter(TransferRequest.from_center_id.in_(assigned_cids))
        else:
            query = query.filter(
                (TransferRequest.from_center_id.in_(assigned_cids))
                | (TransferRequest.to_center_id.in_(assigned_cids))
            )

    if status is not None:
        query = query.filter(TransferRequest.status == status)

    total_items = query.count()
    offset = (page - 1) * size
    transfers = query.order_by(TransferRequest.requested_at.desc()).offset(offset).limit(size).all()
    return transfers, total_items


def review_transfer_request(
    db: Session,
    transfer_id: UUID,
    payload: TransferReviewRequest,
    current_user: User,
    client_ip: Optional[str] = None,
) -> TransferReviewResponse:
    """
    Reviews, approves, or rejects a pending transfer within an atomic ACID transaction.
    If approved:
    - Verifies destination capacity (allows Super Admin override with required note).
    - Closes previous active enrollment with TRANSFERRED status.
    - Creates new active enrollment for destination center.
    - Updates student's current_center_id and increments OCC version.
    - Records immutable audit log.
    """
    transfer = (
        db.query(TransferRequest)
        .options(
            joinedload(TransferRequest.student),
            joinedload(TransferRequest.from_center),
            joinedload(TransferRequest.to_center),
        )
        .filter(TransferRequest.id == transfer_id)
        .first()
    )
    if not transfer:
        raise TransferNotFoundError("Transfer request not found.")

    if transfer.status != TransferStatus.PENDING:
        raise TransferValidationError(
            f"Cannot review transfer request that is already '{transfer.status.value}'."
        )

    # Authorization: Destination Center Manager or Super Admin
    if current_user.role != UserRole.SUPER_ADMIN:
        is_assigned_to = (
            db.query(UserCenter)
            .filter(
                UserCenter.user_id == current_user.id,
                UserCenter.center_id == transfer.to_center_id,
            )
            .first()
            is not None
        )
        if not is_assigned_to:
            raise TransferValidationError(
                "Only the destination center manager or a Super Admin can review this transfer."
            )

    # Decision: REJECT
    if payload.action == "REJECT":
        transfer.status = TransferStatus.REJECTED
        transfer.reviewed_by_user_id = current_user.id
        transfer.reviewed_at = datetime.utcnow()
        transfer.review_notes = payload.review_notes

        audit = AuditLog(
            user_id=current_user.id,
            action="TRANSFER_REJECT",
            resource_type="TRANSFER_REQUEST",
            resource_id=transfer.id,
            client_ip=client_ip,
            old_values={"status": "PENDING"},
            new_values={"status": "REJECTED", "notes": payload.review_notes},
        )
        db.add(audit)
        db.commit()

        return TransferReviewResponse(
            transfer_id=transfer.id,
            status=transfer.status,
            student_id=transfer.student_id,
            new_center_id=None,
            closed_enrollment_id=None,
            new_enrollment_id=None,
            capacity_override=False,
        )

    # Decision: APPROVE
    to_center = db.get(Center, transfer.to_center_id)
    current_occupancy = get_center_occupancy(db, transfer.to_center_id)

    if current_occupancy >= to_center.capacity:
        if payload.capacity_override:
            if current_user.role != UserRole.SUPER_ADMIN:
                raise DestinationCapacityExceededError(
                    "Only Super Admins are authorized to execute a capacity override."
                )
            if not (payload.capacity_override_reason and payload.capacity_override_reason.strip()):
                raise DestinationCapacityExceededError(
                    "A mandatory capacity_override_reason must be provided when capacity override is enabled."
                )
        else:
            raise DestinationCapacityExceededError(
                f"Destination center '{to_center.name}' is at capacity ({to_center.capacity} students). "
                "Transfer blocked unless Super Admin executes a capacity override."
            )

    student = db.get(Student, transfer.student_id)

    # 1. Close previous active enrollment record
    closed_enrollment = (
        db.query(EnrollmentRecord)
        .filter(
            EnrollmentRecord.student_id == student.id,
            EnrollmentRecord.status == EnrollmentStatus.ACTIVE,
            EnrollmentRecord.end_date.is_(None),
        )
        .first()
    )
    closed_id = None
    if closed_enrollment:
        closed_enrollment.status = EnrollmentStatus.TRANSFERRED
        closed_enrollment.end_date = transfer.effective_date
        closed_enrollment.updated_at = datetime.utcnow()
        closed_id = closed_enrollment.id

    # 2. Insert new enrollment record for destination center (FR-ENR-03)
    new_enrollment = EnrollmentRecord(
        student_id=student.id,
        center_id=transfer.to_center_id,
        start_date=transfer.effective_date,
        end_date=None,
        status=EnrollmentStatus.ACTIVE,
        notes=f"Transferred from {transfer.from_center.name}",
    )
    db.add(new_enrollment)
    db.flush()

    # 3. Update student current center and bump version
    student.current_center_id = transfer.to_center_id
    student.version += 1
    student.updated_at = datetime.utcnow()

    # 4. Update transfer request
    transfer.status = TransferStatus.APPROVED
    transfer.reviewed_by_user_id = current_user.id
    transfer.reviewed_at = datetime.utcnow()
    transfer.review_notes = payload.review_notes
    transfer.capacity_override = payload.capacity_override
    transfer.capacity_override_reason = payload.capacity_override_reason

    # 5. Insert audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="TRANSFER_APPROVE",
        resource_type="TRANSFER_REQUEST",
        resource_id=transfer.id,
        client_ip=client_ip,
        old_values={"status": "PENDING"},
        new_values={
            "status": "APPROVED",
            "new_center_id": str(transfer.to_center_id),
            "closed_enrollment_id": str(closed_id) if closed_id else None,
            "new_enrollment_id": str(new_enrollment.id),
            "capacity_override": payload.capacity_override,
            "capacity_override_reason": payload.capacity_override_reason,
        },
    )
    db.add(audit)

    db.commit()

    return TransferReviewResponse(
        transfer_id=transfer.id,
        status=transfer.status,
        student_id=student.id,
        new_center_id=transfer.to_center_id,
        closed_enrollment_id=closed_id,
        new_enrollment_id=new_enrollment.id,
        capacity_override=payload.capacity_override,
    )

