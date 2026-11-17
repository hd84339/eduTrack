"""
System Audit Logging Business Service Layer.
Enforces immutable query views of security and domain events (FR-AUD-01 to 03).
"""
import math
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse


def list_audit_logs(
    db: Session,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    size: int = 50,
) -> Tuple[List[AuditLog], int]:
    """Queries system-wide audit records (Super Admin only)."""
    query = db.query(AuditLog).options(joinedload(AuditLog.user))

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type.strip())
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    total_items = query.count()
    offset = (page - 1) * size
    records = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(size).all()
    return records, total_items


def serialize_audit_response(a: AuditLog) -> AuditLogResponse:
    """Serializes AuditLog with resolved actor name."""
    user_name = a.user.full_name if a.user else None
    return AuditLogResponse(
        id=a.id,
        user_id=a.user_id,
        action=a.action,
        resource_type=a.resource_type,
        resource_id=a.resource_id,
        client_ip=a.client_ip,
        old_values=a.old_values,
        new_values=a.new_values,
        created_at=a.created_at,
        user_name=user_name,
    )

