"""
User and Authentication Pydantic schemas.
Ensures password hashes and credential secrets are strictly excluded from response payloads.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import UserRole, UserStatus
from app.schemas.common import BaseSchema, EmailStr


class UserCenterSummary(BaseSchema):
    """Minimal representation of an assigned learning center for staff profile responses."""
    id: UUID
    code: str
    name: str


class UserBase(BaseModel):
    """Shared core attributes for staff user profiles."""
    email: EmailStr = Field(..., max_length=255, description="Staff login email address")
    full_name: str = Field(..., min_length=1, max_length=150, description="Full name of staff member")
    phone_number: Optional[str] = Field(None, max_length=30, description="Contact phone number")
    role: UserRole = Field(..., description="System role for RBAC")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Staff account status")


class UserCreate(BaseModel):
    """Payload for provisioning a new staff user."""
    email: EmailStr = Field(..., max_length=255, description="Staff login email address")
    password: str = Field(..., min_length=8, max_length=128, description="Initial plaintext password")
    full_name: str = Field(..., min_length=1, max_length=150, description="Full name of staff member")
    phone_number: Optional[str] = Field(None, max_length=30, description="Contact phone number")
    role: UserRole = Field(..., description="System role for RBAC")
    center_ids: Optional[List[UUID]] = Field(default=None, description="Initial center assignments")


class UserUpdate(BaseModel):
    """Payload for updating staff profile attributes."""
    email: Optional[EmailStr] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=30)
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None


class UserCenterAssign(BaseModel):
    """Payload for updating center assignments for a staff member."""
    center_ids: List[UUID] = Field(..., description="Center IDs to assign")


class UserResponse(BaseSchema):
    """
    Staff profile response.
    Explicitly excludes password_hash to ensure credentials cannot be leaked.
    """
    id: UUID
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    assigned_centers: Optional[List[UserCenterSummary]] = None


class LoginRequest(BaseModel):
    """Payload for staff login authentication."""
    email: EmailStr = Field(..., description="Staff email address")
    password: str = Field(..., min_length=1, description="Staff plaintext password")


class TokenResponse(BaseModel):
    """JWT bearer token pair response on successful authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=1800, description="Access token expiration in seconds")
    user: Optional[UserResponse] = None


class RefreshTokenRequest(BaseModel):
    """Payload for requesting access token renewal."""
    refresh_token: str = Field(..., min_length=1, description="Active refresh token")


class TokenRefreshResponse(BaseModel):
    """Renewed access token response."""
    access_token: str
    expires_in: int = Field(default=1800, description="Access token expiration in seconds")
