"""
Learning Activity Templates and Competency Linkage Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.schemas.common import BaseSchema


class ActivityCompetencyItem(BaseModel):
    """Specification of a curriculum competency linked to an activity template."""
    competency_id: UUID = Field(..., description="Targeted competency catalog ID")
    is_primary: bool = Field(default=False, description="Flag indicating if this is the primary focus competency")


class ActivityCompetencyResponse(BaseSchema):
    """Junction representation of an activity-competency linkage."""
    id: UUID
    activity_template_id: UUID
    competency_id: UUID
    is_primary: bool
    competency_code: Optional[str] = None
    competency_name: Optional[str] = None


class ActivityTemplateCreate(BaseModel):
    """Payload for authoring a new reusable activity template."""
    center_id: Optional[UUID] = Field(None, description="Center ID if center-scoped, None if organization-wide")
    is_global: bool = Field(default=False, description="Whether this template is available across all centers")
    title: str = Field(..., min_length=1, max_length=150, description="Activity title")
    subject_area: str = Field(..., min_length=1, max_length=100, description="Subject area (e.g. Mathematics, Literacy)")
    description: str = Field(..., min_length=1, description="Instructions and learning objectives")
    target_age_min: int = Field(default=3, ge=0, description="Minimum recommended age in years")
    target_age_max: int = Field(default=18, ge=0, description="Maximum recommended age in years")
    duration_minutes: int = Field(default=45, ge=5, description="Standard duration in minutes (>= 5)")
    competencies: Optional[List[ActivityCompetencyItem]] = Field(
        default=None, description="Curriculum competencies mapped to this activity"
    )

    @model_validator(mode="after")
    def validate_age_boundaries(self) -> "ActivityTemplateCreate":
        if self.target_age_max < self.target_age_min:
            raise ValueError("target_age_max must be greater than or equal to target_age_min")
        return self


class ActivityTemplateUpdate(BaseModel):
    """Payload for modifying an existing activity template."""
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    subject_area: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    target_age_min: Optional[int] = Field(None, ge=0)
    target_age_max: Optional[int] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=5)
    is_active: Optional[bool] = None
    competencies: Optional[List[ActivityCompetencyItem]] = None

    @model_validator(mode="after")
    def validate_age_boundaries(self) -> "ActivityTemplateUpdate":
        if (
            self.target_age_min is not None
            and self.target_age_max is not None
            and self.target_age_max < self.target_age_min
        ):
            raise ValueError("target_age_max must be greater than or equal to target_age_min")
        return self


class ActivityTemplateResponse(BaseSchema):
    """Full activity template response representation."""
    id: UUID
    center_id: Optional[UUID] = None
    created_by_user_id: UUID
    title: str
    subject_area: str
    description: str
    target_age_min: int
    target_age_max: int
    duration_minutes: int
    is_global: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    competencies: Optional[List[ActivityCompetencyResponse]] = None
    center_name: Optional[str] = None
    creator_name: Optional[str] = None

