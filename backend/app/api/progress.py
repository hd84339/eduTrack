"""
Student Progress Tracking API Router.
Implements student longitudinal competency mastery queries per API_DESIGN.md Module 9.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import verify_user_center_access
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.competency import StudentProgressOverviewResponse
from app.services import competency_service
from app.services.competency_service import StudentNotFoundError

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get(
    "/students/{student_id}",
    response_model=StudentProgressOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve student competency mastery progression",
)
def get_student_progress(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProgressOverviewResponse:
    """
    Returns aggregated competency mastery levels for a student.
    Validates that authenticated staff has access to student's center.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Center authorization verification
    verify_user_center_access(
        center_id=student.current_center_id,
        current_user=current_user,
        db=db,
    )

    try:
        return competency_service.get_student_progress(db=db, student_id=student.id)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

