"""
Student Center Transfer Pydantic schemas.
"""
from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.models.enums import TransferStatus
from app.schemas.common import BaseSchema


class TransferRequestCreate(BaseModel):
    """Payload for submitting an inter-center student transfer request."""
    student_id: UUID = Field(..., description="ID of student to transfer")
    to_center_id: UUID = Field(..., description="Target destination center ID")
    effective_date: date = Field(..., description="Planned effective transfer date")
    request_reason: str = Field(..., min_length=1, description="Justification for transfer request")


class TransferReviewRequest(BaseModel):
    """Payload for approving or rejecting a pending transfer request."""
    action: Literal["APPROVE", "REJECT"] = Field(..., description="Review action decision")
    review_notes: Optional[str] = Field(None, description="Reviewer feedback or notes")
    capacity_override: bool = Field(default=False, description="Flag indicating Super Admin capacity override")
    capacity_override_reason: Optional[str] = Field(
        None, description="Mandatory justification if capacity_override is enabled"
    )

    @model_validator(mode="after")
    def validate_capacity_override(self) -> "TransferReviewRequest":
        if self.capacity_override and not (self.capacity_override_reason and self.capacity_override_reason.strip()):
            raise ValueError("capacity_override_reason is required when capacity_override is True")
        return self


class TransferResponse(BaseSchema):
    """Full transfer request response representation."""
    id: UUID
    student_id: UUID
    from_center_id: UUID
    to_center_id: UUID
    requested_by_user_id: UUID
    reviewed_by_user_id: Optional[UUID] = None
    status: TransferStatus
    request_reason: str
    review_notes: Optional[str] = None
    capacity_override: bool
    capacity_override_reason: Optional[str] = None
    effective_date: date
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    student_name: Optional[str] = None
    from_center_name: Optional[str] = None
    to_center_name: Optional[str] = None


class TransferReviewResponse(BaseSchema):
    """Result summary of a reviewed transfer request."""
    transfer_id: UUID
    status: TransferStatus
    student_id: UUID
    new_center_id: Optional[UUID] = None
    closed_enrollment_id: Optional[UUID] = None
    new_enrollment_id: Optional[UUID] = None
    capacity_override: bool = False

