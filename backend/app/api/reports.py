"""
Reporting and Student Dossier API Router.
Implements attendance exports and longitudinal student dossiers per API_DESIGN.md Module 11.
"""
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_center_manager, require_teacher, verify_user_center_access
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/attendance",
    summary="Generate attendance report (CSV or JSON)",
)
def get_attendance_report(
    center_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> Any:
    """Generates attendance data rows as JSON or downloadable CSV."""
    verify_user_center_access(center_id=center_id, current_user=current_user, db=db)
    rows = report_service.generate_attendance_report(
        db=db,
        center_id=center_id,
        start_date=start_date,
        end_date=end_date,
    )

    if format == "csv":
        csv_content = report_service.generate_attendance_csv(rows)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=attendance_report_{center_id}_{start_date}_{end_date}.csv"
            },
        )
    return {"rows": rows, "total_records": len(rows)}


@router.get(
    "/students/{student_id}/dossier",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Comprehensive longitudinal student dossier",
)
def get_student_dossier(
    student_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves full student dossier (bio, enrollments, attendance, mastery timeline)."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    verify_user_center_access(center_id=student.current_center_id, current_user=current_user, db=db)
    dossier = report_service.get_student_dossier(db, student.id)
    return dossier
