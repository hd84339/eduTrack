"""
Audit Logging API Router.
Implements system-wide audit record queries per API_DESIGN.md Module 13.
"""
from datetime import datetime
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.services import audit_service
from app.services.audit_service import serialize_audit_response

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Query system-wide audit records (Super Admin only)",
)
def list_audit_logs(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[AuditLogResponse]:
    """Queries immutable audit logs."""
    logs, total_items = audit_service.list_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[serialize_audit_response(l) for l in logs],
        pagination=PaginationMetadata(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1 and total_pages > 0,
        ),
    )

