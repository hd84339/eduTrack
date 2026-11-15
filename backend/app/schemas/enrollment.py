"""
Student Enrollment Records Pydantic schemas.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.models.enums import EnrollmentStatus
from app.schemas.common import BaseSchema


class EnrollmentCreate(BaseModel):
    """Payload for creating a new student enrollment record."""
    student_id: UUID = Field(..., description="ID of student being enrolled")
    center_id: UUID = Field(..., description="ID of learning center")
    start_date: date = Field(..., description="Enrollment effective start date")
    end_date: Optional[date] = Field(None, description="Enrollment end date (null if active)")
    status: EnrollmentStatus = Field(default=EnrollmentStatus.ACTIVE, description="Enrollment status")
    notes: Optional[str] = Field(None, description="Administrative remarks")

    @model_validator(mode="after")
    def validate_date_range(self) -> "EnrollmentCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class EnrollmentUpdate(BaseModel):
    """Payload for updating an enrollment record (e.g. terminating enrollment)."""
    end_date: Optional[date] = Field(None, description="Updated end date")
    status: Optional[EnrollmentStatus] = Field(None, description="Updated enrollment status")
    notes: Optional[str] = Field(None, description="Administrative remarks")


class EnrollmentResponse(BaseSchema):
    """Full enrollment record response representation."""
    id: UUID
    student_id: UUID
    center_id: UUID
    start_date: date
    end_date: Optional[date] = None
    status: EnrollmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    center_name: Optional[str] = None

