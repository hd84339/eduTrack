"""
Curriculum Competency Catalog and Student Skill Mastery Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import MasteryLevel
from app.schemas.common import BaseSchema


class CompetencyCreate(BaseModel):
    """Payload for adding a new standardized competency to the central catalog."""
    code: str = Field(..., min_length=1, max_length=50, description="Official competency code (e.g. MATH-FRAC-01)")
    name: str = Field(..., min_length=1, max_length=150, description="Display name of competency")
    domain: str = Field(..., min_length=1, max_length=100, description="Curriculum domain (e.g. Mathematics, Literacy)")
    description: Optional[str] = Field(None, description="Detailed rubric and mastery description")


class CompetencyUpdate(BaseModel):
    """Payload for updating catalog competency metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    domain: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class CompetencyResponse(BaseSchema):
    """Full curriculum competency catalog item representation."""
    id: UUID
    code: str
    name: str
    domain: str
    description: Optional[str] = None
    created_at: datetime


class StudentSkillProgressResponse(BaseSchema):
    """Aggregated competency mastery level for a student."""
    id: UUID
    student_id: UUID
    competency_id: UUID
    code: Optional[str] = Field(None, description="Competency code")
    name: Optional[str] = Field(None, description="Competency name")
    domain: Optional[str] = Field(None, description="Competency domain")
    current_level: MasteryLevel
    total_sessions_count: int
    last_evaluated_at: datetime
    updated_at: Optional[datetime] = None


class StudentProgressOverviewResponse(BaseModel):
    """Comprehensive mastery progress summary for a student."""
    student_id: UUID
    competencies: List[StudentSkillProgressResponse]

