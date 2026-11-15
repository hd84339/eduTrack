import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    CheckConstraint,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Center(Base):
    """
    Centers table storing learning center branches, capacity, and operational metadata.
    """
    __tablename__ = "centers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        server_default=text("'UTC'"),
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default=text("100"),
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
    staff_assignments: Mapped[List["UserCenter"]] = relationship(
        "UserCenter",
        back_populates="center",
        cascade="all, delete-orphan",
    )
    students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="current_center",
    )
    enrollments: Mapped[List["EnrollmentRecord"]] = relationship(
        "EnrollmentRecord",
        back_populates="center",
    )

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_centers_capacity"),
        Index("idx_centers_is_active", "is_active"),
    )

