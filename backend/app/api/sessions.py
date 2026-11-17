"""
Learning Sessions API Router.
Implements session logging with granular student observations and evaluations
per API_DESIGN.md Module 8.
"""
from datetime import date
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import get_center_context, require_teacher, verify_user_center_access
from app.db.session import get_db
from app.models.center import Center
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.schemas.session import SessionCreate, SessionResponse
from app.services import session_service
from app.services.session_service import SessionValidationError, serialize_session_response

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get(
    "",
    response_model=PaginatedResponse[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List learning sessions",
)
def list_sessions(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
    center_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SessionResponse]:
    """Lists conducted learning sessions filterable by date and center."""
    sessions, total_items = session_service.list_sessions(
        db=db,
        current_user=current_user,
        center_id=center_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[serialize_session_response(s) for s in sessions],
        pagination=PaginationMetadata(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1 and total_pages > 0,
        ),
    )


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a conducted learning session",
)
def create_session(
    payload: SessionCreate,
    request: Request,
    center: Center = Depends(get_center_context),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    Logs a conducted teaching session.
    Validates enrollment dates, records student ratings, and increments cumulative progress.
    """
    if payload.center_id != center.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload center_id does not match the active center context (X-Center-ID header).",
        )

    client_ip = request.client.host if request.client else None
    try:
        session_obj = session_service.create_session(
            db=db,
            payload=payload,
            current_user=current_user,
            client_ip=client_ip,
        )
        return serialize_session_response(session_obj)
    except SessionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve session details",
)
def get_session(
    session_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Retrieves full session with student observations and competency ratings."""
    s = session_service.get_session(db, session_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    verify_user_center_access(center_id=s.center_id, current_user=current_user, db=db)
    return serialize_session_response(s)

