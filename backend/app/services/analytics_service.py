"""
Dashboard and Operational Analytics Business Service Layer.
Computes indexed aggregations without in-memory bottlenecks (FR-DSH-01, FR-DSH-02, FR-DSH-03).
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.session import LearningSession
from app.models.attendance import AttendanceRecord
from app.models.center import Center
from app.models.enums import AttendanceStatus, EnrollmentStatus, StudentStatus, TransferStatus
from app.models.student import EnrollmentRecord, Student, TransferRequest
from app.services.center_service import get_center_occupancy


def get_overview_analytics(db: Session) -> Dict[str, Any]:
    """Generates organization-wide benchmarks for Super Admins (FR-DSH-02)."""
    total_centers = db.query(func.count(Center.id)).filter(Center.is_active.is_(True)).scalar() or 0
    total_active_students = (
        db.query(func.count(Student.id)).filter(Student.status == StudentStatus.ACTIVE).scalar() or 0
    )

    # Attendance rate today
    today = date.today()
    total_att_today = (
        db.query(func.count(AttendanceRecord.id))
        .filter(AttendanceRecord.attendance_date == today)
        .scalar()
        or 0
    )
    present_att_today = (
        db.query(func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.attendance_date == today,
            AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
        )
        .scalar()
        or 0
    )
    system_attendance_rate = (
        round((present_att_today / total_att_today) * 100, 1) if total_att_today > 0 else 0.0
    )

    # Completed sessions this month
    start_of_month = today.replace(day=1)
    monthly_sessions = (
        db.query(func.count(LearningSession.id))
        .filter(LearningSession.session_date >= start_of_month)
        .scalar()
        or 0
    )

    pending_transfers = (
        db.query(func.count(TransferRequest.id))
        .filter(TransferRequest.status == TransferStatus.PENDING)
        .scalar()
        or 0
    )

    return {
        "total_centers": total_centers,
        "total_active_students": total_active_students,
        "system_wide_attendance_rate_today": system_attendance_rate,
        "monthly_sessions_count": monthly_sessions,
        "pending_transfers_count": pending_transfers,
    }


def get_center_analytics(db: Session, center_id: UUID) -> Dict[str, Any]:
    """Generates center operational metrics for Center Managers and Admins (FR-DSH-01)."""
    center = db.get(Center, center_id)
    if not center:
        return {}

    occupancy = get_center_occupancy(db, center.id)
    capacity_pct = round((occupancy / center.capacity) * 100, 1) if center.capacity > 0 else 0.0

    today = date.today()
    total_att_today = (
        db.query(func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.center_id == center.id,
            AttendanceRecord.attendance_date == today,
        )
        .scalar()
        or 0
    )
    present_att_today = (
        db.query(func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.center_id == center.id,
            AttendanceRecord.attendance_date == today,
            AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
        )
        .scalar()
        or 0
    )
    attendance_rate = (
        round((present_att_today / total_att_today) * 100, 1) if total_att_today > 0 else 0.0
    )

    # 30-day attendance rate
    thirty_days_ago = today - timedelta(days=30)
    total_30d = (
        db.query(func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.center_id == center.id,
            AttendanceRecord.attendance_date >= thirty_days_ago,
        )
        .scalar()
        or 0
    )
    present_30d = (
        db.query(func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.center_id == center.id,
            AttendanceRecord.attendance_date >= thirty_days_ago,
            AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
        )
        .scalar()
        or 0
    )
    thirty_day_rate = round((present_30d / total_30d) * 100, 1) if total_30d > 0 else 0.0

    # Weekly sessions
    seven_days_ago = today - timedelta(days=7)
    weekly_sessions = (
        db.query(func.count(LearningSession.id))
        .filter(
            LearningSession.center_id == center.id,
            LearningSession.session_date >= seven_days_ago,
        )
        .scalar()
        or 0
    )

    pending_incoming_transfers = (
        db.query(func.count(TransferRequest.id))
        .filter(
            TransferRequest.to_center_id == center.id,
            TransferRequest.status == TransferStatus.PENDING,
        )
        .scalar()
        or 0
    )

    pending_outgoing_transfers = (
        db.query(func.count(TransferRequest.id))
        .filter(
            TransferRequest.from_center_id == center.id,
            TransferRequest.status == TransferStatus.PENDING,
        )
        .scalar()
        or 0
    )

    return {
        "center_id": str(center.id),
        "center_name": center.name,
        "capacity": center.capacity,
        "active_student_count": occupancy,
        "capacity_occupancy_percentage": capacity_pct,
        "attendance_rate_today": attendance_rate,
        "attendance_rate_30_days": thirty_day_rate,
        "weekly_completed_sessions_count": weekly_sessions,
        "pending_incoming_transfers": pending_incoming_transfers,
        "pending_outgoing_transfers": pending_outgoing_transfers,
    }
