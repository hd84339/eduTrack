"""
Attendance and Attendance Correction Audit Log Pydantic schemas.
Features Optimistic Concurrency Control (OCC) version tracking on corrections.
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import AttendanceStatus
from app.schemas.common import BaseSchema


class AttendanceItem(BaseModel):
    """Single student attendance entry for bulk logging."""
    student_id: UUID = Field(..., description="Student identifier")
    status: AttendanceStatus = Field(..., description="Recorded attendance state")
    remarks: Optional[str] = Field(None, max_length=255, description="Optional note or explanation")


class BulkAttendanceCreate(BaseModel):
    """Payload for submitting atomic multi-student daily attendance."""
    center_id: UUID = Field(..., description="Target center where attendance is conducted")
    attendance_date: date = Field(..., description="Calendar date of attendance")
    records: List[AttendanceItem] = Field(..., min_length=1, description="List of student attendance records")


class BulkAttendanceResponse(BaseModel):
    """Confirmation payload returned on successful bulk attendance persistence."""
    message: str = Field(default="Bulk attendance recorded successfully")
    processed_count: int = Field(..., description="Number of attendance entries processed")
    attendance_date: date = Field(..., description="Calendar date for which attendance was recorded")


class AttendanceCorrectionRequest(BaseModel):
    """
    Payload for correcting an existing attendance record.
    Requires submitting the current version for Optimistic Concurrency Control (OCC)
    and a mandatory justification reason for the audit trail.
    """
    status: AttendanceStatus = Field(..., description="Corrected attendance state")
    reason: str = Field(..., min_length=1, description="Mandatory audit justification for correction")
    remarks: Optional[str] = Field(None, max_length=255, description="Updated remarks")
    version: int = Field(..., description="Current version tag to prevent concurrent collision")


class AttendanceRecordResponse(BaseSchema):
    """Full attendance record response representation."""
    id: UUID
    student_id: UUID
    center_id: UUID
    recorded_by_user_id: UUID
    attendance_date: date
    status: AttendanceStatus
    remarks: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    student_id_number: Optional[str] = None


class AttendanceAuditLogResponse(BaseSchema):
    """Immutable attendance correction audit entry response."""
    id: UUID
    attendance_record_id: UUID
    changed_by_user_id: UUID
    previous_status: AttendanceStatus
    new_status: AttendanceStatus
    reason: str
    changed_at: datetime
    changed_by_name: Optional[str] = None

