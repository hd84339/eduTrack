"""
Curriculum Competency Catalog API Router.
Implements catalog creation and listing per API_DESIGN.md Module 6.
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.schemas.competency import CompetencyCreate, CompetencyResponse
from app.services import competency_service
from app.services.competency_service import CompetencyAlreadyExistsError

router = APIRouter(prefix="/competencies", tags=["Competencies"])


@router.get(
    "",
    response_model=PaginatedResponse[CompetencyResponse],
    status_code=status.HTTP_200_OK,
    summary="List standardized competencies",
)
def list_competencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    domain: Optional[str] = Query(None, description="Filter by subject domain"),
    search: Optional[str] = Query(None, description="Search by name, code, or description"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[CompetencyResponse]:
    """Lists standardized competencies across the curriculum catalog."""
    competencies, total_items = competency_service.list_competencies(
        db=db,
        domain=domain,
        search=search,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[CompetencyResponse.model_validate(c) for c in competencies],
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
    response_model=CompetencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new competency to catalog",
)
def create_competency(
    payload: CompetencyCreate,
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> CompetencyResponse:
    """Super Admin provisions a new standardized competency."""
    client_ip = request.client.host if request.client else None
    try:
        comp = competency_service.create_competency(
            db=db,
            payload=payload,
            user_id=current_user.id,
            client_ip=client_ip,
        )
        return CompetencyResponse.model_validate(comp)
    except CompetencyAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

