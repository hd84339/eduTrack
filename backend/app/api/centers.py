"""
Center Management API Router.
Implements center creation, listing, detail retrieval with occupancy, and updates
per API_DESIGN.md Module 2.
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import (
    require_roles,
    require_super_admin,
    verify_user_center_access,
)
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.center import (
    CenterCreate,
    CenterDetailResponse,
    CenterResponse,
    CenterUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.services import center_service
from app.services.center_service import (
    CenterAlreadyExistsError,
    CenterNotFoundError,
)

router = APIRouter(prefix="/centers", tags=["Centers"])


@router.get(
    "",
    response_model=PaginatedResponse[CenterResponse],
    status_code=status.HTTP_200_OK,
    summary="List learning centers",
)
def list_centers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name, code, or address"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[CenterResponse]:
    """
    Lists learning centers.
    - Super Admins see all centers.
    - Managers and Teachers see their assigned centers.
    """
    centers, total_items = center_service.list_centers(
        db=db,
        current_user=current_user,
        is_active=is_active,
        search=search,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[CenterResponse.model_validate(c) for c in centers],
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
    response_model=CenterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new learning center",
)
def create_center(
    payload: CenterCreate,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> CenterResponse:
    """Super Admin provisions a new learning center."""
    client_ip = request.client.host if request.client else None
    try:
        center = center_service.create_center(
            db=db,
            payload=payload,
            user_id=current_user.id,
            client_ip=client_ip,
        )
        return CenterResponse.model_validate(center)
    except CenterAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{center_id}",
    response_model=CenterDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch center details and current occupancy count",
)
def get_center(
    center_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CenterDetailResponse:
    """Fetches center details including live current occupancy count."""
    center = verify_user_center_access(center_id=center_id, current_user=current_user, db=db)
    occupancy = center_service.get_center_occupancy(db, center.id)

    response_data = CenterDetailResponse(
        id=center.id,
        code=center.code,
        name=center.name,
        address=center.address,
        timezone=center.timezone,
        contact_phone=center.contact_phone,
        contact_email=center.contact_email,
        capacity=center.capacity,
        is_active=center.is_active,
        created_at=center.created_at,
        updated_at=center.updated_at,
        current_occupancy=occupancy,
    )
    return response_data


@router.put(
    "/{center_id}",
    response_model=CenterResponse,
    status_code=status.HTTP_200_OK,
    summary="Update learning center information",
)
def update_center(
    center_id: UUID,
    payload: CenterUpdate,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> CenterResponse:
    """Super Admin updates learning center attributes."""
    client_ip = request.client.host if request.client else None
    try:
        center = center_service.update_center(
            db=db,
            center_id=center_id,
            payload=payload,
            user_id=current_user.id,
            client_ip=client_ip,
        )
        return CenterResponse.model_validate(center)
    except CenterNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

