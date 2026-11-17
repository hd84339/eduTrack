"""
Attendance Management Business Service Layer.
Enforces center-timezone future date checks, active enrollment coverage,
duplicate prevention, atomic bulk writes, OCC versioning, and 24-hour correction window.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, joinedload

from app.models.attendance import AttendanceAuditLog, AttendanceRecord
from app.models.center import Center
from app.models.enums import AttendanceStatus, EnrollmentStatus, UserRole
from app.models.student import EnrollmentRecord, Student
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCorrectionRequest,
    AttendanceRecordResponse,
    BulkAttendanceCreate,
    BulkAttendanceResponse,
)


class AttendanceServiceError(Exception):
    """Base exception for attendance service operations."""
    pass


class AttendanceNotFoundError(AttendanceServiceError):
    """Raised when attendance record is not found."""
    pass


class AttendanceValidationError(AttendanceServiceError):
    """Raised for validation errors like future dates or un-enrolled students."""
    pass


class AttendanceConflictError(AttendanceServiceError):
    """Raised when record has OCC version conflict or duplicate daily attendance."""
    pass


class AttendanceCorrectionWindowExpiredError(AttendanceServiceError):
    """Raised when teacher attempts correction past the 24-hour window."""
    pass


def serialize_attendance_response(rec: AttendanceRecord) -> AttendanceRecordResponse:
    """Serializes AttendanceRecord with resolved student name and ID number."""
    student_name = None
    student_id_num = None
    if rec.student:
        student_name = f"{rec.student.first_name} {rec.student.last_name}"
        student_id_num = rec.student.student_id_number

    return AttendanceRecordResponse(
        id=rec.id,
        student_id=rec.student_id,
        center_id=rec.center_id,
        recorded_by_user_id=rec.recorded_by_user_id,
        attendance_date=rec.attendance_date,
        status=rec.status,
        remarks=rec.remarks,
        version=rec.version,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        student_name=student_name,
        student_id_number=student_id_num,
    )


def record_bulk_attendance(
    db: Session,
    payload: BulkAttendanceCreate,
    active_center: Center,
    current_user: User,
) -> BulkAttendanceResponse:
    """
    Atomically records daily attendance for multiple students.
    Validates:
    - Attendance date is not in the future according to the center's timezone.
    - Each student has an active enrollment at the center covering the date.
    - No duplicate attendance for any student on the same date.
    """
    # 1. Timezone-aware date validation (FR-ATT-02)
    try:
        tz = ZoneInfo(active_center.timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    local_today = datetime.now(tz).date()
    if payload.attendance_date > local_today:
        raise AttendanceValidationError(
            f"Cannot record attendance for future date {payload.attendance_date} "
            f"(Center local date is {local_today})."
        )

    # 2. Validate and insert records
    created_count = 0
    for item in payload.records:
        student = db.get(Student, item.student_id)
        if not student:
            raise AttendanceValidationError(f"Student with ID '{item.student_id}' not found.")

        # Verify active enrollment on attendance date (FR-ATT-03, BR-02)
        valid_enrollment = (
            db.query(EnrollmentRecord)
            .filter(
                EnrollmentRecord.student_id == student.id,
                EnrollmentRecord.center_id == active_center.id,
                EnrollmentRecord.start_date <= payload.attendance_date,
                (
                    EnrollmentRecord.end_date.is_(None)
                    | (EnrollmentRecord.end_date >= payload.attendance_date)
                ),
            )
            .first()
        )
        if not valid_enrollment:
            raise AttendanceValidationError(
                f"Student '{student.first_name} {student.last_name}' ({student.student_id_number}) "
                f"was not actively enrolled at {active_center.name} on {payload.attendance_date}."
            )

        # Check for existing attendance on date (BR-01)
        existing = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.attendance_date == payload.attendance_date,
            )
            .first()
        )
        if existing:
            raise AttendanceConflictError(
                f"Attendance for student '{student.first_name} {student.last_name}' "
                f"has already been recorded for date {payload.attendance_date}."
            )

        record = AttendanceRecord(
            student_id=student.id,
            center_id=active_center.id,
            recorded_by_user_id=current_user.id,
            attendance_date=payload.attendance_date,
            status=item.status,
            remarks=item.remarks.strip() if item.remarks else None,
            version=1,
        )
        db.add(record)
        created_count += 1

    db.commit()

    return BulkAttendanceResponse(
        message=f"Successfully recorded attendance for {created_count} students.",
        processed_count=created_count,
        attendance_date=payload.attendance_date,
    )


def list_daily_attendance(
    db: Session,
    center_id: UUID,
    attendance_date: date,
) -> List[AttendanceRecord]:
    """Retrieves all attendance records for a center on a specific date."""
    return (
        db.query(AttendanceRecord)
        .options(joinedload(AttendanceRecord.student))
        .filter(
            AttendanceRecord.center_id == center_id,
            AttendanceRecord.attendance_date == attendance_date,
        )
        .order_by(AttendanceRecord.created_at.asc())
        .all()
    )


def correct_attendance_record(
    db: Session,
    attendance_id: UUID,
    payload: AttendanceCorrectionRequest,
    current_user: User,
) -> AttendanceRecord:
    """
    Corrects an existing attendance record protected by OCC and 24-hour window.
    Records an immutable entry in attendance_audit_logs.
    """
    record = db.get(AttendanceRecord, attendance_id)
    if not record:
        raise AttendanceNotFoundError("Attendance record not found.")

    # 24-hour edit window for Teachers (BR-04, FR-ATT-05)
    if current_user.role == UserRole.TEACHER:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        record_created = record.created_at if record.created_at.tzinfo else record.created_at.replace(tzinfo=timezone.utc)
        cutoff = record_created + timedelta(hours=24)
        if now_utc > cutoff:
            raise AttendanceCorrectionWindowExpiredError(
                "Teachers may only correct attendance within 24 hours of creation. "
                "Contact your Center Manager or Super Admin for retroactive modifications."
            )

    # OCC check (BR-06)
    if payload.version != record.version:
        raise AttendanceConflictError(
            f"Concurrency conflict: submitted version {payload.version} does not match current record version {record.version}."
        )

    previous_status = record.status

    # Apply changes and increment version
    record.status = payload.status
    record.remarks = payload.remarks
    record.version += 1
    record.updated_at = datetime.utcnow()

    # Immutable attendance audit log entry (FR-ATT-05, BR-05)
    audit = AttendanceAuditLog(
        attendance_record_id=record.id,
        changed_by_user_id=current_user.id,
        previous_status=previous_status,
        new_status=payload.status,
        reason=payload.reason.strip(),
    )
    db.add(audit)

    db.commit()
    db.refresh(record)
    return record

