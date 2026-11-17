"""
Student Management API Router.
Implements student registration, listing, retrieval, and OCC-protected updates
scoped to authorized learning centers per API_DESIGN.md Module 3.
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.permissions import (
    get_center_context,
    require_center_manager,
    require_teacher,
)
from app.db.session import get_db
from app.models.center import Center
from app.models.enums import StudentStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.schemas.enrollment import EnrollmentResponse
from app.schemas.student import (
    StudentCreate,
    StudentDetailResponse,
    StudentListItemResponse,
    StudentResponse,
    StudentUpdate,
)
from app.services import student_service
from app.services.student_service import (
    CenterMismatchError,
    ConcurrencyConflictError,
    StudentAlreadyExistsError,
    StudentNotFoundError,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student and initialize enrollment",
    description="Registers a student profile and atomically initializes their first EnrollmentRecord.",
)
def create_student(
    payload: StudentCreate,
    request: Request,
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> StudentResponse:
    """
    Registers a new student profile within the active center context.
    - Requires SUPER_ADMIN or CENTER_MANAGER role.
    - Validates that payload center_id matches authorized X-Center-ID header context.
    - Atomically creates initial active EnrollmentRecord.
    - Captures an immutable audit log entry.
    """
    client_ip = request.client.host if request.client else None
    try:
        student = student_service.create_student(
            db=db,
            payload=payload,
            active_center_id=center.id,
            user_id=current_user.id,
            client_ip=client_ip,
        )
        return StudentResponse.model_validate(student)
    except CenterMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except StudentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=PaginatedResponse[StudentListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List students scoped to authorized center",
    description="Lists student summaries with multi-attribute filtering, search, and pagination.",
)
def list_students(
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
    center_id: Optional[UUID] = Query(
        None,
        description="Optional center ID filter (must match active X-Center-ID context if provided)",
    ),
    status_filter: Optional[StudentStatus] = Query(
        None,
        alias="status",
        description="Filter by student enrollment status (e.g. ACTIVE, INACTIVE)",
    ),
    search: Optional[str] = Query(
        None,
        min_length=1,
        description="Case-insensitive search matching first name, last name, or student ID number",
    ),
    page: int = Query(1, ge=1, description="1-based page index (default: 1)"),
    size: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    sort_by: str = Query("created_at", description="Field identifier to sort by"),
    sort_dir: str = Query("desc", description="Sort direction ('asc' or 'desc')"),
) -> PaginatedResponse[StudentListItemResponse]:
    """
    Returns a paginated collection of student summaries strictly scoped to the active center.
    - Accessible to SUPER_ADMIN, CENTER_MANAGER, and TEACHER for their authorized center.
    - Executes SQL-level filtering and pagination.
    """
    if center_id is not None and center_id != center.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter center_id does not match the active center context (X-Center-ID header)",
        )

    students, total_items = student_service.list_students(
        db=db,
        center_id=center.id,
        status=status_filter,
        search=search,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1 and total_pages > 0

    items = [
        StudentListItemResponse(
            id=s.id,
            student_id_number=s.student_id_number,
            first_name=s.first_name,
            last_name=s.last_name,
            current_center_id=s.current_center_id,
            center_name=s.current_center.name if s.current_center else center.name,
            date_of_birth=s.date_of_birth,
            gender=s.gender,
            status=s.status,
            guardian_name=s.guardian_name,
            guardian_phone=s.guardian_phone,
            version=s.version,
        )
        for s in students
    ]

    return PaginatedResponse(
        items=items,
        pagination=PaginationMetadata(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        ),
    )


@router.get(
    "/{student_id}",
    response_model=StudentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve individual student profile and active enrollment",
    description="Returns detailed student record and resolved active enrollment.",
)
def get_student(
    student_id: UUID,
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> StudentDetailResponse:
    """
    Retrieves full student profile and active enrollment for an individual student.
    - Requires SUPER_ADMIN, CENTER_MANAGER, or TEACHER assigned to the center.
    - Scoped strictly to the active center context. Returns 404 for nonexistent or out-of-scope students.
    """
    student = student_service.get_student_by_id(
        db=db,
        student_id=student_id,
        center_id=center.id,
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Resolve active enrollment if present
    active_enrollment = student_service.get_active_enrollment(db, student_id=student.id)
    enrollment_response = None
    if active_enrollment is not None:
        enrollment_response = EnrollmentResponse(
            id=active_enrollment.id,
            student_id=active_enrollment.student_id,
            center_id=active_enrollment.center_id,
            start_date=active_enrollment.start_date,
            end_date=active_enrollment.end_date,
            status=active_enrollment.status,
            notes=active_enrollment.notes,
            created_at=active_enrollment.created_at,
            updated_at=active_enrollment.updated_at,
            center_name=active_enrollment.center.name if active_enrollment.center else center.name,
        )

    return StudentDetailResponse(
        id=student.id,
        student_id_number=student.student_id_number,
        current_center_id=student.current_center_id,
        first_name=student.first_name,
        last_name=student.last_name,
        date_of_birth=student.date_of_birth,
        gender=student.gender,
        guardian_name=student.guardian_name,
        guardian_phone=student.guardian_phone,
        guardian_email=student.guardian_email,
        guardian_relationship=student.guardian_relationship,
        emergency_contact=student.emergency_contact,
        notes=student.notes,
        status=student.status,
        version=student.version,
        created_at=student.created_at,
        updated_at=student.updated_at,
        center_name=center.name,
        active_enrollment=enrollment_response,
    )


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student profile protected by OCC",
    description="Updates student profile attributes. Requires valid OCC version to prevent concurrent collisions.",
)
def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    request: Request,
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> StudentResponse:
    """
    Updates a student profile within the active center.
    - Requires SUPER_ADMIN or CENTER_MANAGER role.
    - Enforces Optimistic Concurrency Control (OCC): rejects stale version with HTTP 409 Conflict.
    - Atomically captures changes in the immutable audit log.
    """
    student = student_service.get_student_by_id(
        db=db,
        student_id=student_id,
        center_id=center.id,
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    client_ip = request.client.host if request.client else None
    try:
        updated_student = student_service.update_student(
            db=db,
            student=student,
            payload=payload,
            user_id=current_user.id,
            client_ip=client_ip,
        )
        return StudentResponse.model_validate(updated_student)
    except ConcurrencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

