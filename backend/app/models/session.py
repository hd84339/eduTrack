import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import SessionParticipationStatus, MasteryLevel


class LearningSession(Base):
    """
    Conducted teaching session instance.
    Anchored to the center where conducted and associated activity template.
    """
    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("centers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    activity_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    conducted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    session_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    topic_summary: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    general_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
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
    center: Mapped["Center"] = relationship("Center")
    activity_template: Mapped["ActivityTemplate"] = relationship(
        "ActivityTemplate",
        back_populates="sessions",
    )
    conducted_by: Mapped["User"] = relationship("User")
    student_roster: Mapped[List["SessionStudent"]] = relationship(
        "SessionStudent",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("end_time >= start_time", name="ck_learning_sessions_time"),
        Index("idx_sessions_center_date", "center_id", "session_date"),
        Index("idx_sessions_teacher", "conducted_by_user_id"),
    )


class SessionStudent(Base):
    """
    Student participation and qualitative scorecard for a conducted learning session.
    """
    __tablename__ = "session_students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    participation_status: Mapped[SessionParticipationStatus] = mapped_column(
        ENUM(
            SessionParticipationStatus,
            name="session_participation_status",
            create_type=False,
            native_enum=True,
        ),
        nullable=False,
        default=SessionParticipationStatus.COMPLETED,
        server_default=text("'COMPLETED'"),
    )
    qualitative_feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(
        "LearningSession",
        back_populates="student_roster",
    )
    student: Mapped["Student"] = relationship("Student")
    evaluations: Mapped[List["SessionStudentEvaluation"]] = relationship(
        "SessionStudentEvaluation",
        back_populates="session_student",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_students"),
        CheckConstraint(
            "score IS NULL OR (score >= 0.0 AND score <= 100.0)",
            name="ck_session_students_score",
        ),
        CheckConstraint(
            "participation_status <> 'ABSENT' OR score IS NULL",
            name="ck_session_students_absent_score",
        ),
        Index("idx_session_students_student", "student_id"),
    )


class SessionStudentEvaluation(Base):
    """
    Granular mastery assessment per competency for each student participating in a session.
    """
    __tablename__ = "session_student_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    session_student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    mastery_level: Mapped[MasteryLevel] = mapped_column(
        ENUM(MasteryLevel, name="mastery_level", create_type=False, native_enum=True),
        nullable=False,
    )
    teacher_notes: Mapped[Optional[str]] = mapped_column(
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
    session_student: Mapped["SessionStudent"] = relationship(
        "SessionStudent",
        back_populates="evaluations",
    )
    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="evaluations",
    )

    __table_args__ = (
        UniqueConstraint("session_student_id", "competency_id", name="uq_session_student_evaluations"),
        Index("idx_evaluations_competency", "competency_id"),
    )

