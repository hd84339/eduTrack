"""
Analytics and Operational Dashboards API Router.
Implements Super Admin and Center Manager aggregations per API_DESIGN.md Module 10.
"""
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_center_manager, require_super_admin, verify_user_center_access
from app.db.session import get_db
from app.models.user import User
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Organization-wide summary overview for Super Admins",
)
def get_overview_analytics(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves organization-wide metrics benchmarks."""
    return analytics_service.get_overview_analytics(db)


@router.get(
    "/centers/{center_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Operational metrics for a specific center",
)
def get_center_analytics(
    center_id: UUID,
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves operational metrics for a specific center."""
    center = verify_user_center_access(center_id=center_id, current_user=current_user, db=db)
    metrics = analytics_service.get_center_analytics(db, center.id)
    if not metrics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center metrics not found")
    return metrics

