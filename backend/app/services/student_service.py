"""
Student Management Business Service Layer.
Enforces multi-center scoping, unique identifier checks, atomic enrollment creation,
Optimistic Concurrency Control (OCC) versioning, and immutable audit logging.
"""
import math
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditLog
from app.models.center import Center
from app.models.enums import EnrollmentStatus, StudentStatus
from app.models.student import EnrollmentRecord, Student
from app.schemas.student import StudentCreate, StudentUpdate


class StudentServiceError(Exception):
    """Base exception for student service operations."""
    pass


class StudentNotFoundError(StudentServiceError):
    """Raised when a student cannot be found within the active center scope."""
    pass


class StudentAlreadyExistsError(StudentServiceError):
    """Raised when attempting to create a student with a duplicate unique identifier."""
    pass


class CenterMismatchError(StudentServiceError):
    """Raised when payload center ID does not match active center context."""
    pass


class ConcurrencyConflictError(StudentServiceError):
    """Raised when an update is submitted with a stale OCC version number."""
    pass


def get_student_by_id(
    db: Session,
    student_id: UUID,
    center_id: Optional[UUID] = None,
) -> Optional[Student]:
    """
    Retrieve a student by primary key, optionally scoped to a specific center.
    Eagerly loads the current center and enrollment records.
    """
    query = db.query(Student).filter(Student.id == student_id)
    if center_id is not None:
        query = query.filter(Student.current_center_id == center_id)
    return query.options(
        joinedload(Student.current_center),
        joinedload(Student.enrollment_records),
    ).first()


def get_student_by_id_number(
    db: Session,
    student_id_number: str,
) -> Optional[Student]:
    """Retrieve a student by unique organization student ID number."""
    return (
        db.query(Student)
        .filter(Student.student_id_number == student_id_number.strip())
        .first()
    )


def get_active_enrollment(
    db: Session,
    student_id: UUID,
) -> Optional[EnrollmentRecord]:
    """
    Retrieve the current active enrollment record for a student.
    Guaranteed to be at most one by partial unique constraint.
    """
    return (
        db.query(EnrollmentRecord)
        .filter(
            EnrollmentRecord.student_id == student_id,
            EnrollmentRecord.status == EnrollmentStatus.ACTIVE,
            EnrollmentRecord.end_date.is_(None),
        )
        .options(joinedload(EnrollmentRecord.center))
        .first()
    )


def create_student(
    db: Session,
    payload: StudentCreate,
    active_center_id: UUID,
    user_id: UUID,
    client_ip: Optional[str] = None,
) -> Student:
    """
    Registers a new student, atomically initializes their first EnrollmentRecord,
    and captures an immutable audit entry within an ACID database transaction.
    """
    # Verify that payload center matches selected active center context
    if payload.center_id != active_center_id:
        raise CenterMismatchError(
            "Payload center_id does not match the active center context (X-Center-ID header)"
        )

    # Check for duplicate student identifier
    existing = get_student_by_id_number(db, payload.student_id_number)
    if existing:
        raise StudentAlreadyExistsError(
            f"Student with ID number '{payload.student_id_number}' already exists"
        )

    # Create Student demographic profile
    student = Student(
        student_id_number=payload.student_id_number.strip(),
        current_center_id=active_center_id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        date_of_birth=payload.date_of_birth,
        gender=payload.gender.strip(),
        guardian_name=payload.guardian_name.strip(),
        guardian_phone=payload.guardian_phone.strip(),
        guardian_email=payload.guardian_email,
        guardian_relationship=payload.guardian_relationship.strip(),
        emergency_contact=payload.emergency_contact,
        notes=payload.notes,
        status=StudentStatus.ACTIVE,
        version=1,
    )
    db.add(student)
    db.flush()  # Generate student.id before foreign key insertion

    # Determine center local date for initial enrollment
    center_obj = db.get(Center, active_center_id)
    try:
        from zoneinfo import ZoneInfo
        center_today = datetime.now(ZoneInfo(center_obj.timezone)).date() if center_obj and center_obj.timezone else date.today()
    except Exception:
        center_today = date.today()

    # Atomically initialize first EnrollmentRecord (FR-ENR-01)
    enrollment = EnrollmentRecord(
        student_id=student.id,
        center_id=active_center_id,
        start_date=center_today,
        end_date=None,
        status=EnrollmentStatus.ACTIVE,
        notes="Initial center enrollment on registration",
    )
    db.add(enrollment)

    # Write immutable audit entry (FR-AUD-02)
    audit_entry = AuditLog(
        user_id=user_id,
        action="STUDENT_CREATE",
        resource_type="STUDENT",
        resource_id=student.id,
        client_ip=client_ip,
        old_values=None,
        new_values={
            "student_id_number": student.student_id_number,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "current_center_id": str(student.current_center_id),
            "status": student.status.value,
            "version": student.version,
        },
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(student)
    return student


def list_students(
    db: Session,
    center_id: UUID,
    status: Optional[StudentStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Tuple[List[Student], int]:
    """
    Retrieves a paginated list of students scoped to the authorized center.
    Supports multi-attribute filtering, search, sorting, and pagination via SQL queries.
    Avoids N+1 query overhead by eager-loading the current center.
    """
    query = db.query(Student).filter(Student.current_center_id == center_id)

    # Status filter
    if status is not None:
        query = query.filter(Student.status == status)

    # Search filter (first_name, last_name, or student_id_number)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.first_name.ilike(term),
                Student.last_name.ilike(term),
                Student.student_id_number.ilike(term),
            )
        )

    # Total matching records count at database level
    total_items = query.count()

    # Dynamic sorting
    sort_columns: Dict[str, Any] = {
        "created_at": Student.created_at,
        "updated_at": Student.updated_at,
        "last_name": Student.last_name,
        "first_name": Student.first_name,
        "student_id_number": Student.student_id_number,
        "date_of_birth": Student.date_of_birth,
        "status": Student.status,
        "version": Student.version,
    }
    sort_col = sort_columns.get(sort_by, Student.created_at)
    if sort_dir.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    offset = (page - 1) * size
    students = (
        query.options(joinedload(Student.current_center))
        .offset(offset)
        .limit(size)
        .all()
    )

    return students, total_items


def update_student(
    db: Session,
    student: Student,
    payload: StudentUpdate,
    user_id: UUID,
    client_ip: Optional[str] = None,
) -> Student:
    """
    Updates an existing student profile protected by Optimistic Concurrency Control (OCC).
    Validates version match, increments version, applies changes, and records audit history.
    """
    # Enforce Optimistic Concurrency Control (BR-06, NFR-INT-02)
    if payload.version != student.version:
        raise ConcurrencyConflictError(
            f"Concurrency conflict: submitted version {payload.version} does not match current record version {student.version}. "
            "The record has been updated by another user. Reload and re-apply changes."
        )

    # Capture pre-mutation snapshot for audit log
    old_values = {
        "first_name": student.first_name,
        "last_name": student.last_name,
        "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
        "gender": student.gender,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "guardian_email": student.guardian_email,
        "guardian_relationship": student.guardian_relationship,
        "emergency_contact": student.emergency_contact,
        "notes": student.notes,
        "status": student.status.value,
        "version": student.version,
    }

    # Apply only provided mutable fields (do not allow ID, center, or created_at mutation)
    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("version", None)

    for field_name, value in update_data.items():
        if hasattr(student, field_name):
            if isinstance(value, str):
                setattr(student, field_name, value.strip())
            else:
                setattr(student, field_name, value)

    # Increment version tag and update timestamp
    student.version += 1
    student.updated_at = datetime.utcnow()

    # Capture post-mutation snapshot for audit log
    new_values = {
        "first_name": student.first_name,
        "last_name": student.last_name,
        "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
        "gender": student.gender,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "guardian_email": student.guardian_email,
        "guardian_relationship": student.guardian_relationship,
        "emergency_contact": student.emergency_contact,
        "notes": student.notes,
        "status": student.status.value,
        "version": student.version,
    }

    # Record immutable audit entry
    audit_entry = AuditLog(
        user_id=user_id,
        action="STUDENT_UPDATE",
        resource_type="STUDENT",
        resource_id=student.id,
        client_ip=client_ip,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(student)
    return student

