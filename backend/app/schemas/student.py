"""
Student Profile Pydantic schemas.
Features Optimistic Concurrency Control (OCC) version tracking on updates.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import StudentStatus
from app.schemas.common import BaseSchema, EmailStr
from app.schemas.enrollment import EnrollmentResponse


class StudentBase(BaseModel):
    """Shared core attributes for student profiles."""
    student_id_number: str = Field(..., max_length=50, description="Organization student ID")
    first_name: str = Field(..., min_length=1, max_length=100, description="Student first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Student last name")
    date_of_birth: date = Field(..., description="Student birth date")
    gender: str = Field(..., min_length=1, max_length=20, description="Gender identity")
    guardian_name: str = Field(..., min_length=1, max_length=150, description="Primary guardian name")
    guardian_phone: str = Field(..., min_length=1, max_length=30, description="Guardian phone number")
    guardian_email: Optional[EmailStr] = Field(None, max_length=255, description="Guardian contact email")
    guardian_relationship: str = Field(default="Parent", max_length=50, description="Relationship to student")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact details")
    notes: Optional[str] = Field(None, description="Administrative notes")
    status: StudentStatus = Field(default=StudentStatus.ACTIVE, description="Student enrollment status")


class StudentCreate(BaseModel):
    """Payload for registering a new student."""
    student_id_number: str = Field(..., max_length=50, description="Unique organization student ID")
    center_id: UUID = Field(..., description="Initial learning center assignment")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., min_length=1, max_length=20)
    guardian_name: str = Field(..., min_length=1, max_length=150)
    guardian_phone: str = Field(..., min_length=1, max_length=30)
    guardian_email: Optional[EmailStr] = Field(None, max_length=255)
    guardian_relationship: str = Field(default="Parent", max_length=50)
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None


class StudentUpdate(BaseModel):
    """
    Payload for updating a student profile.
    Requires submitting the current version for Optimistic Concurrency Control (OCC).
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    guardian_name: Optional[str] = Field(None, min_length=1, max_length=150)
    guardian_phone: Optional[str] = Field(None, max_length=30)
    guardian_email: Optional[EmailStr] = Field(None, max_length=255)
    guardian_relationship: Optional[str] = Field(None, max_length=50)
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[StudentStatus] = None
    version: int = Field(..., description="Current version tag to prevent concurrent overwrite collisions")


class StudentResponse(BaseSchema):
    """Full student record response representation."""
    id: UUID
    student_id_number: str
    current_center_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    guardian_name: str
    guardian_phone: str
    guardian_email: Optional[str] = None
    guardian_relationship: str
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    status: StudentStatus
    version: int
    created_at: datetime
    updated_at: datetime


class StudentListItemResponse(BaseSchema):
    """Summary representation for paginated student listings."""
    id: UUID
    student_id_number: str
    first_name: str
    last_name: str
    current_center_id: UUID
    center_name: Optional[str] = None
    date_of_birth: date
    gender: str
    status: StudentStatus
    guardian_name: str
    guardian_phone: str
    version: int


class StudentDetailResponse(StudentResponse):
    """Detailed student profile with resolved center and active enrollment."""
    center_name: Optional[str] = None
    active_enrollment: Optional[EnrollmentResponse] = None
