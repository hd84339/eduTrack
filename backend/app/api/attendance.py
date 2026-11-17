"""
Attendance Management API Router.
Implements daily roster queries, atomic bulk attendance logging, and 24-hour OCC corrections
per API_DESIGN.md Module 5.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import get_center_context, require_teacher
from app.db.session import get_db
from app.models.center import Center
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCorrectionRequest,
    AttendanceRecordResponse,
    BulkAttendanceCreate,
    BulkAttendanceResponse,
)
from app.services import attendance_service
from app.services.attendance_service import (
    AttendanceConflictError,
    AttendanceCorrectionWindowExpiredError,
    AttendanceNotFoundError,
    AttendanceValidationError,
    serialize_attendance_response,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get(
    "",
    response_model=List[AttendanceRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Query daily attendance roster for a center and date",
)
def get_daily_attendance(
    attendance_date: date = Query(..., alias="date", description="Target calendar date"),
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> List[AttendanceRecordResponse]:
    """Retrieves all student attendance records for the active center on the given date."""
    records = attendance_service.list_daily_attendance(
        db=db,
        center_id=center.id,
        attendance_date=attendance_date,
    )
    return [serialize_attendance_response(r) for r in records]


@router.post(
    "/bulk",
    response_model=BulkAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record bulk daily attendance atomically",
)
def record_bulk_attendance(
    payload: BulkAttendanceCreate,
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> BulkAttendanceResponse:
    """
    Records attendance for an entire classroom in a single atomic payload.
    Validates enrollment dates, future date constraints, and uniqueness.
    """
    if payload.center_id != center.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload center_id does not match the active center context (X-Center-ID header).",
        )

    try:
        return attendance_service.record_bulk_attendance(
            db=db,
            payload=payload,
            active_center=center,
            current_user=current_user,
        )
    except AttendanceValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except AttendanceConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.put(
    "/{attendance_id}",
    response_model=AttendanceRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Correct an existing attendance record",
)
def correct_attendance(
    attendance_id: UUID,
    payload: AttendanceCorrectionRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> AttendanceRecordResponse:
    """
    Corrects an attendance record. Enforces 24-hour window for Teachers,
    OCC version tag, and mandatory audit justification.
    """
    try:
        updated = attendance_service.correct_attendance_record(
            db=db,
            attendance_id=attendance_id,
            payload=payload,
            current_user=current_user,
        )
        return serialize_attendance_response(updated)
    except AttendanceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except AttendanceCorrectionWindowExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except AttendanceConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

