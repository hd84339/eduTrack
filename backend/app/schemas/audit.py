"""
System-wide Immutable Security and Operational Audit Log Pydantic schemas.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.common import BaseSchema


class AuditLogCreate(BaseModel):
    """Payload for capturing an immutable audit event."""
    user_id: Optional[UUID] = Field(None, description="Actor staff ID (None for background/system action)")
    action: str = Field(..., min_length=1, max_length=50, description="Action identifier (e.g. CREATE, TRANSFER_APPROVE)")
    resource_type: str = Field(..., min_length=1, max_length=50, description="Target entity type (e.g. STUDENT, ATTENDANCE)")
    resource_id: UUID = Field(..., description="Target entity primary key")
    client_ip: Optional[str] = Field(None, max_length=45, description="Originating client IP address")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Prior snapshot values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="Updated snapshot values")


class AuditLogResponse(BaseSchema):
    """Immutable audit trail record response representation."""
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: UUID
    client_ip: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime
    user_name: Optional[str] = None

