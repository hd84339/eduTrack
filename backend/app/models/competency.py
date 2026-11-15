import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import MasteryLevel


class Competency(Base):
    """
    Standardized curriculum competency catalog.
    Enables normalized multi-competency mappings for activities and student sessions.
    """
    __tablename__ = "competencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    activities: Mapped[List["ActivityCompetency"]] = relationship(
        "ActivityCompetency",
        back_populates="competency",
    )
    evaluations: Mapped[List["SessionStudentEvaluation"]] = relationship(
        "SessionStudentEvaluation",
        back_populates="competency",
    )
    skill_progress: Mapped[List["StudentSkillProgress"]] = relationship(
        "StudentSkillProgress",
        back_populates="competency",
    )

    __table_args__ = (
        Index("idx_competencies_domain", "domain"),
    )


class StudentSkillProgress(Base):
    """
    Aggregated longitudinal competency mastery index per student.
    Tracks cumulative sessions attended and latest evaluated mastery rating.
    """
    __tablename__ = "student_skill_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_level: Mapped[MasteryLevel] = mapped_column(
        ENUM(MasteryLevel, name="mastery_level", create_type=False, native_enum=True),
        nullable=False,
    )
    total_sessions_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="skill_progress",
    )
    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="skill_progress",
    )

    __table_args__ = (
        UniqueConstraint("student_id", "competency_id", name="uq_student_skill_progress"),
        CheckConstraint("total_sessions_count > 0", name="ck_skill_progress_total_sessions"),
        Index("idx_skill_progress_competency", "competency_id"),
    )

