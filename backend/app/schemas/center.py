"""
Learning Center Pydantic schemas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.common import BaseSchema, EmailStr


class CenterBase(BaseModel):
    """Shared core attributes for learning centers."""
    code: str = Field(..., min_length=1, max_length=30, description="Organization center code (e.g. CEN-01)")
    name: str = Field(..., min_length=1, max_length=150, description="Display name of center")
    address: str = Field(..., min_length=1, description="Physical center address")
    timezone: str = Field(default="UTC", max_length=50, description="IANA timezone name")
    contact_phone: Optional[str] = Field(None, max_length=30, description="Official center phone")
    contact_email: Optional[EmailStr] = Field(None, max_length=255, description="Official center contact email")
    capacity: int = Field(default=100, gt=0, description="Maximum student capacity, must be strictly positive")
    is_active: bool = Field(default=True, description="Active status flag")


class CenterCreate(BaseModel):
    """Payload for creating a new learning center."""
    code: str = Field(..., min_length=1, max_length=30, description="Unique center code (e.g. CEN-SOUTH-02)")
    name: str = Field(..., min_length=1, max_length=150, description="Display name of center")
    address: str = Field(..., min_length=1, description="Physical center address")
    timezone: str = Field(default="UTC", max_length=50, description="IANA timezone (e.g. America/Los_Angeles)")
    contact_phone: Optional[str] = Field(None, max_length=30, description="Official center phone")
    contact_email: Optional[EmailStr] = Field(None, max_length=255, description="Official center contact email")
    capacity: int = Field(default=100, gt=0, description="Max student capacity, must be strictly positive")


class CenterUpdate(BaseModel):
    """Payload for modifying learning center attributes."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    address: Optional[str] = Field(None, min_length=1)
    timezone: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[EmailStr] = Field(None, max_length=255)
    capacity: Optional[int] = Field(None, gt=0, description="Capacity must be strictly positive if provided")
    is_active: Optional[bool] = None


class CenterResponse(BaseSchema):
    """Full learning center response representation."""
    id: UUID
    code: str
    name: str
    address: str
    timezone: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    capacity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CenterDetailResponse(CenterResponse):
    """Detailed center response with live calculated occupancy count."""
    current_occupancy: Optional[int] = Field(None, description="Current count of actively enrolled students")


class CenterSummary(BaseSchema):
    """Minimal center summary representation for dropdowns and nested views."""
    id: UUID
    code: str
    name: str
