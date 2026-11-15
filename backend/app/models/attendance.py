import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Date,
    DateTime,
    Integer,
    ForeignKey,
    UniqueConstraint,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import AttendanceStatus


class AttendanceRecord(Base):
    """
    Daily student attendance ledger.
    Enforces exactly one attendance record per student per calendar day via a unique constraint.
    Date validation (preventing future dates) is enforced in backend application logic.
    """
    __tablename__ = "attendance_records"

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
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        ENUM(AttendanceStatus, name="attendance_status", create_type=False, native_enum=True),
        nullable=False,
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
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
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="attendance_records",
    )
    center: Mapped["Center"] = relationship("Center")
    recorded_by: Mapped["User"] = relationship("User")
    audit_logs: Mapped[List["AttendanceAuditLog"]] = relationship(
        "AttendanceAuditLog",
        back_populates="attendance_record",
    )

    __table_args__ = (
        UniqueConstraint("student_id", "attendance_date", name="uq_attendance_student_date"),
        Index("idx_attendance_center_date", "center_id", "attendance_date"),
    )


class AttendanceAuditLog(Base):
    """
    Fine-grained change log for attendance corrections.
    Foreign keys enforce ON DELETE RESTRICT to guarantee audit trail preservation.
    """
    __tablename__ = "attendance_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    attendance_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attendance_records.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_status: Mapped[AttendanceStatus] = mapped_column(
        ENUM(AttendanceStatus, name="attendance_status", create_type=False, native_enum=True),
        nullable=False,
    )
    new_status: Mapped[AttendanceStatus] = mapped_column(
        ENUM(AttendanceStatus, name="attendance_status", create_type=False, native_enum=True),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    attendance_record: Mapped["AttendanceRecord"] = relationship(
        "AttendanceRecord",
        back_populates="audit_logs",
    )
    changed_by: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_att_audit_record", "attendance_record_id"),
        Index("idx_att_audit_changed_at", "changed_at"),
    )

