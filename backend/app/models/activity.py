import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ActivityTemplate(Base):
    """
    Standard curriculum activity template.
    Links to normalized competencies via the activity_competencies junction table.
    """
    __tablename__ = "activity_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("centers.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    subject_area: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    target_age_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default=text("3"),
    )
    target_age_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=18,
        server_default=text("18"),
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=45,
        server_default=text("45"),
    )
    is_global: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    center: Mapped[Optional["Center"]] = relationship("Center")
    created_by: Mapped["User"] = relationship("User")
    competencies: Mapped[List["ActivityCompetency"]] = relationship(
        "ActivityCompetency",
        back_populates="activity_template",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[List["LearningSession"]] = relationship(
        "LearningSession",
        back_populates="activity_template",
    )

    __table_args__ = (
        CheckConstraint("target_age_min >= 0", name="ck_activity_templates_age_min"),
        CheckConstraint("target_age_max >= target_age_min", name="ck_activity_templates_age_max"),
        CheckConstraint("duration_minutes >= 5", name="ck_activity_templates_duration"),
        Index("idx_act_templates_subject", "subject_area"),
        Index("idx_act_templates_center_global", "center_id", "is_global"),
    )


class ActivityCompetency(Base):
    """
    Normalized junction associating activity templates with curriculum competencies.
    """
    __tablename__ = "activity_competencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    activity_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    # Relationships
    activity_template: Mapped["ActivityTemplate"] = relationship(
        "ActivityTemplate",
        back_populates="competencies",
    )
    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="activities",
    )

    __table_args__ = (
        UniqueConstraint("activity_template_id", "competency_id", name="uq_activity_competencies"),
        Index("idx_act_comp_competency", "competency_id"),
    )

