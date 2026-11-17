"""
Center Management Business Service Layer.
Enforces code uniqueness, calculates live occupancy counts, and handles center lifecycle.
"""
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.center import Center
from app.models.enums import EnrollmentStatus, UserRole
from app.models.student import EnrollmentRecord
from app.models.user import User, UserCenter
from app.schemas.center import CenterCreate, CenterUpdate


class CenterServiceError(Exception):
    """Base exception for center service operations."""
    pass


class CenterNotFoundError(CenterServiceError):
    """Raised when a center is not found."""
    pass


class CenterAlreadyExistsError(CenterServiceError):
    """Raised when creating a center with a duplicate code."""
    pass


def get_center_by_id(db: Session, center_id: UUID) -> Optional[Center]:
    """Retrieves a center by primary key."""
    return db.get(Center, center_id)


def get_center_occupancy(db: Session, center_id: UUID) -> int:
    """Calculates the current live count of actively enrolled students."""
    return (
        db.query(func.count(EnrollmentRecord.id))
        .filter(
            EnrollmentRecord.center_id == center_id,
            EnrollmentRecord.status == EnrollmentStatus.ACTIVE,
            EnrollmentRecord.end_date.is_(None),
        )
        .scalar()
        or 0
    )


def create_center(
    db: Session,
    payload: CenterCreate,
    user_id: UUID,
    client_ip: Optional[str] = None,
) -> Center:
    """Creates a new learning center and logs the audit event."""
    existing = db.query(Center).filter(Center.code == payload.code.strip()).first()
    if existing:
        raise CenterAlreadyExistsError(f"Center with code '{payload.code}' already exists")

    center = Center(
        code=payload.code.strip(),
        name=payload.name.strip(),
        address=payload.address.strip(),
        timezone=payload.timezone.strip(),
        contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
        contact_email=payload.contact_email,
        capacity=payload.capacity,
        is_active=True,
    )
    db.add(center)
    db.flush()

    audit_entry = AuditLog(
        user_id=user_id,
        action="CENTER_CREATE",
        resource_type="CENTER",
        resource_id=center.id,
        client_ip=client_ip,
        old_values=None,
        new_values={
            "code": center.code,
            "name": center.name,
            "capacity": center.capacity,
            "timezone": center.timezone,
        },
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(center)
    return center


def list_centers(
    db: Session,
    current_user: User,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[Center], int]:
    """
    Lists centers.
    - Super Admins see all centers.
    - Center Managers and Teachers see only assigned centers.
    """
    query = db.query(Center)

    if current_user.role != UserRole.SUPER_ADMIN:
        assigned_subquery = (
            db.query(UserCenter.center_id)
            .filter(UserCenter.user_id == current_user.id)
            .subquery()
        )
        query = query.filter(Center.id.in_(assigned_subquery))

    if is_active is not None:
        query = query.filter(Center.is_active == is_active)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Center.name.ilike(term),
                Center.code.ilike(term),
                Center.address.ilike(term),
            )
        )

    total_items = query.count()
    offset = (page - 1) * size
    centers = query.order_by(Center.code.asc()).offset(offset).limit(size).all()
    return centers, total_items


def update_center(
    db: Session,
    center_id: UUID,
    payload: CenterUpdate,
    user_id: UUID,
    client_ip: Optional[str] = None,
) -> Center:
    """Updates center metadata and records an audit log entry."""
    center = get_center_by_id(db, center_id)
    if not center:
        raise CenterNotFoundError("Learning center not found")

    old_values = {
        "name": center.name,
        "address": center.address,
        "timezone": center.timezone,
        "contact_phone": center.contact_phone,
        "contact_email": center.contact_email,
        "capacity": center.capacity,
        "is_active": center.is_active,
    }

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if hasattr(center, k):
            setattr(center, k, v)

    center.updated_at = datetime.utcnow()

    new_values = {
        "name": center.name,
        "address": center.address,
        "timezone": center.timezone,
        "contact_phone": center.contact_phone,
        "contact_email": center.contact_email,
        "capacity": center.capacity,
        "is_active": center.is_active,
    }

    audit = AuditLog(
        user_id=user_id,
        action="CENTER_UPDATE",
        resource_type="CENTER",
        resource_id=center.id,
        client_ip=client_ip,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(audit)

    db.commit()
    db.refresh(center)
    return center

