import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Date,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    CheckConstraint,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import StudentStatus, EnrollmentStatus, TransferStatus


class Student(Base):
    """
    Student demographic profile and current operational status.
    Features integer version column for Optimistic Concurrency Control (OCC).
    """
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    student_id_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    current_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("centers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    guardian_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    guardian_phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    guardian_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    guardian_relationship: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Parent",
        server_default=text("'Parent'"),
    )
    emergency_contact: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[StudentStatus] = mapped_column(
        ENUM(StudentStatus, name="student_status", create_type=False, native_enum=True),
        nullable=False,
        default=StudentStatus.ACTIVE,
        server_default=text("'ACTIVE'"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
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
    current_center: Mapped["Center"] = relationship(
        "Center",
        back_populates="students",
    )
    enrollment_records: Mapped[List["EnrollmentRecord"]] = relationship(
        "EnrollmentRecord",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    transfer_requests: Mapped[List["TransferRequest"]] = relationship(
        "TransferRequest",
        back_populates="student",
    )
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="student",
    )
    skill_progress: Mapped[List["StudentSkillProgress"]] = relationship(
        "StudentSkillProgress",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_students_center_status", "current_center_id", "status"),
        Index("idx_students_name", "last_name", "first_name"),
    )


class EnrollmentRecord(Base):
    """
    Historical enrollment registry for longitudinal tracking.
    Enforces exactly one active enrollment per student via a partial unique index.
    """
    __tablename__ = "enrollment_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("centers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        ENUM(EnrollmentStatus, name="enrollment_status", create_type=False, native_enum=True),
        nullable=False,
        default=EnrollmentStatus.ACTIVE,
        server_default=text("'ACTIVE'"),
    )
    notes: Mapped[Optional[str]] = mapped_column(
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
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="enrollment_records",
    )
    center: Mapped["Center"] = relationship(
        "Center",
        back_populates="enrollments",
    )

    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_enrollment_dates"),
        Index(
            "uq_student_active_enrollment",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE' AND end_date IS NULL"),
            sqlite_where=text("status = 'ACTIVE' AND end_date IS NULL"),
        ),
        Index("idx_enrollment_student", "student_id"),
        Index("idx_enrollment_center_status", "center_id", "status"),
    )


class TransferRequest(Base):
    """
    Inter-center student transfer workflow.
    Supports Super Admin capacity overrides with mandatory audit reason.
    """
    __tablename__ = "transfer_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("centers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("centers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[TransferStatus] = mapped_column(
        ENUM(TransferStatus, name="transfer_status", create_type=False, native_enum=True),
        nullable=False,
        default=TransferStatus.PENDING,
        server_default=text("'PENDING'"),
    )
    request_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    capacity_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    capacity_override_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="transfer_requests",
    )
    from_center: Mapped["Center"] = relationship(
        "Center",
        foreign_keys=[from_center_id],
    )
    to_center: Mapped["Center"] = relationship(
        "Center",
        foreign_keys=[to_center_id],
    )
    requested_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by_user_id],
    )
    reviewed_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by_user_id],
    )

    __table_args__ = (
        CheckConstraint("from_center_id <> to_center_id", name="ck_transfers_different_centers"),
        CheckConstraint(
            "capacity_override = FALSE OR capacity_override_reason IS NOT NULL",
            name="ck_transfers_capacity_override_reason",
        ),
        Index("idx_transfers_student", "student_id"),
        Index("idx_transfers_status", "status"),
        Index("idx_transfers_from_center", "from_center_id"),
        Index("idx_transfers_to_center", "to_center_id"),
    )

