"""
User and Staff Management API Router.
Implements user provisioning, listing with role/center filters, and center assignment
per API_DESIGN.md Module 12.
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_center_manager, require_super_admin
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.schemas.user import UserCenterAssign, UserCreate, UserResponse
from app.services import user_service
from app.services.user_service import (
    UnauthorizedRoleAssignmentError,
    UserAlreadyExistsError,
    UserNotFoundError,
    serialize_user_response,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List staff members",
)
def list_users(
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    center_id: Optional[UUID] = Query(None, description="Filter by assigned center ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[UserResponse]:
    """
    Lists staff users.
    - Super Admins can list all users.
    - Center Managers can only view Teachers assigned to their centers.
    """
    users, total_items = user_service.list_users(
        db=db,
        current_user=current_user,
        role=role,
        center_id=center_id,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[serialize_user_response(u) for u in users],
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
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a new staff user",
)
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Provisions a new staff account.
    - Super Admins can provision any role.
    - Center Managers can only provision TEACHERs for their assigned center.
    """
    client_ip = request.client.host if request.client else None
    try:
        user = user_service.create_user(
            db=db,
            payload=payload,
            actor_user=current_user,
            client_ip=client_ip,
        )
        return serialize_user_response(user)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except UnauthorizedRoleAssignmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.put(
    "/{user_id}/centers",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update center assignments for staff",
)
def update_user_centers(
    user_id: UUID,
    payload: UserCenterAssign,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Super Admin updates assigned learning centers for a staff user."""
    client_ip = request.client.host if request.client else None
    try:
        user = user_service.update_user_centers(
            db=db,
            user_id=user_id,
            payload=payload,
            actor_user_id=current_user.id,
            client_ip=client_ip,
        )
        return serialize_user_response(user)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

