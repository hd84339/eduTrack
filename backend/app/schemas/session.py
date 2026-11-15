"""
Conducted Learning Session and Granular Competency Evaluation Pydantic schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.models.enums import MasteryLevel, SessionParticipationStatus
from app.schemas.common import BaseSchema


class SessionStudentEvaluationItem(BaseModel):
    """Granular observation rating for a specific competency in a session."""
    competency_id: UUID = Field(..., description="Target curriculum competency catalog ID")
    mastery_level: MasteryLevel = Field(..., description="Observed competency mastery level")
    teacher_notes: Optional[str] = Field(None, description="Competency-specific observation notes")


class SessionStudentItem(BaseModel):
    """Participating student record with qualitative notes and optional competency evaluations."""
    student_id: UUID = Field(..., description="Participating student ID")
    participation_status: SessionParticipationStatus = Field(
        default=SessionParticipationStatus.COMPLETED, description="Participation state"
    )
    qualitative_feedback: Optional[str] = Field(None, description="Overall qualitative teacher feedback")
    score: Optional[Decimal] = Field(
        None, ge=Decimal("0.0"), le=Decimal("100.0"), description="Optional numerical score (0-100)"
    )
    evaluations: Optional[List[SessionStudentEvaluationItem]] = Field(
        default=None, description="Granular per-competency ratings"
    )

    @model_validator(mode="after")
    def validate_absent_score(self) -> "SessionStudentItem":
        if self.participation_status == SessionParticipationStatus.ABSENT and self.score is not None:
            raise ValueError("score must be null when student participation status is ABSENT")
        return self


class SessionCreate(BaseModel):
    """Payload for logging a conducted teaching session and student evaluations."""
    center_id: UUID = Field(..., description="Center where session was held")
    activity_template_id: UUID = Field(..., description="Applied activity template ID")
    session_date: date = Field(..., description="Calendar date of session")
    start_time: datetime = Field(..., description="Session start timestamp")
    end_time: datetime = Field(..., description="Session end timestamp")
    topic_summary: str = Field(..., min_length=1, max_length=255, description="Focus topic summary")
    general_notes: Optional[str] = Field(None, description="Overall teacher notes")
    students: Optional[List[SessionStudentItem]] = Field(
        default=None, description="Participating students roster"
    )

    @model_validator(mode="after")
    def validate_session_time_interval(self) -> "SessionCreate":
        if self.end_time < self.start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        return self


class SessionStudentEvaluationResponse(BaseSchema):
    """Evaluation response representation for a single competency."""
    id: UUID
    session_student_id: UUID
    competency_id: UUID
    mastery_level: MasteryLevel
    teacher_notes: Optional[str] = None
    created_at: datetime
    competency_code: Optional[str] = None
    competency_name: Optional[str] = None


class SessionStudentResponse(BaseSchema):
    """Student participation response with nested evaluations."""
    id: UUID
    session_id: UUID
    student_id: UUID
    participation_status: SessionParticipationStatus
    qualitative_feedback: Optional[str] = None
    score: Optional[Decimal] = None
    created_at: datetime
    student_name: Optional[str] = None
    evaluations: Optional[List[SessionStudentEvaluationResponse]] = None


class SessionResponse(BaseSchema):
    """Full learning session response representation."""
    id: UUID
    center_id: UUID
    activity_template_id: UUID
    conducted_by_user_id: UUID
    session_date: date
    start_time: datetime
    end_time: datetime
    topic_summary: str
    general_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    center_name: Optional[str] = None
    activity_title: Optional[str] = None
    teacher_name: Optional[str] = None
    student_roster: Optional[List[SessionStudentResponse]] = None

