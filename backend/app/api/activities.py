"""
Learning Activity Templates API Router.
Implements template creation, listing, retrieval, and updates per API_DESIGN.md Module 7.
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_center_manager, require_teacher
from app.db.session import get_db
from app.models.user import User
from app.schemas.activity import (
    ActivityTemplateCreate,
    ActivityTemplateResponse,
    ActivityTemplateUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.services import activity_service
from app.services.activity_service import (
    ActivityTemplateNotFoundError,
    ActivityTemplateValidationError,
    serialize_activity_template,
)

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get(
    "",
    response_model=PaginatedResponse[ActivityTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="List learning activity templates",
)
def list_activity_templates(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
    center_id: Optional[UUID] = Query(None),
    subject_area: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ActivityTemplateResponse]:
    """Lists templates available to the authenticated staff member."""
    templates, total_items = activity_service.list_activity_templates(
        db=db,
        current_user=current_user,
        center_id=center_id,
        subject_area=subject_area,
        is_active=is_active,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[serialize_activity_template(t) for t in templates],
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
    response_model=ActivityTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Author a new learning activity template",
)
def create_activity_template(
    payload: ActivityTemplateCreate,
    request: Request,
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> ActivityTemplateResponse:
    """Super Admin or Center Manager authors a new activity template."""
    client_ip = request.client.host if request.client else None
    try:
        tmpl = activity_service.create_activity_template(
            db=db,
            payload=payload,
            current_user=current_user,
            client_ip=client_ip,
        )
        return serialize_activity_template(tmpl)
    except ActivityTemplateValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/{template_id}",
    response_model=ActivityTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve activity template details",
)
def get_activity_template(
    template_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> ActivityTemplateResponse:
    """Retrieves full activity template with mapped competencies."""
    tmpl = activity_service.get_activity_template(db, template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity template not found",
        )
    return serialize_activity_template(tmpl)


@router.put(
    "/{template_id}",
    response_model=ActivityTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update activity template",
)
def update_activity_template(
    template_id: UUID,
    payload: ActivityTemplateUpdate,
    request: Request,
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> ActivityTemplateResponse:
    """Updates activity template metadata and linked competencies."""
    client_ip = request.client.host if request.client else None
    try:
        tmpl = activity_service.update_activity_template(
            db=db,
            template_id=template_id,
            payload=payload,
            current_user=current_user,
            client_ip=client_ip,
        )
        return serialize_activity_template(tmpl)
    except ActivityTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

