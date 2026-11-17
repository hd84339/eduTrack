"""
Reports and Student Dossier Business Service Layer.
Generates attendance reporting and longitudinal student dossiers (FR-REP-01, FR-REP-02).
"""
import csv
import io
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.competency import Competency, StudentSkillProgress
from app.models.attendance import AttendanceRecord
from app.models.center import Center
from app.models.enums import AttendanceStatus
from app.models.student import EnrollmentRecord, Student


def generate_attendance_report(
    db: Session,
    center_id: UUID,
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """Generates attendance data rows for reporting."""
    records = (
        db.query(AttendanceRecord)
        .options(joinedload(AttendanceRecord.student), joinedload(AttendanceRecord.center))
        .filter(
            AttendanceRecord.center_id == center_id,
            AttendanceRecord.attendance_date >= start_date,
            AttendanceRecord.attendance_date <= end_date,
        )
        .order_by(AttendanceRecord.attendance_date.asc())
        .all()
    )

    rows = []
    for r in records:
        rows.append(
            {
                "attendance_date": r.attendance_date.isoformat(),
                "center_name": r.center.name if r.center else "",
                "student_id_number": r.student.student_id_number if r.student else "",
                "student_name": f"{r.student.first_name} {r.student.last_name}" if r.student else "",
                "status": r.status.value,
                "remarks": r.remarks or "",
            }
        )
    return rows


def generate_attendance_csv(rows: List[Dict[str, Any]]) -> str:
    """Renders attendance report rows to CSV format."""
    output = io.StringIO()
    fieldnames = ["attendance_date", "center_name", "student_id_number", "student_name", "status", "remarks"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def get_student_dossier(db: Session, student_id: UUID) -> Dict[str, Any]:
    """
    Produces comprehensive student longitudinal dossier containing student bio,
    historical center enrollments, attendance summary, and competency mastery history.
    """
    student = db.get(Student, student_id)
    if not student:
        return {}

    center = db.get(Center, student.current_center_id)

    # Historical enrollments
    enrollments = (
        db.query(EnrollmentRecord)
        .options(joinedload(EnrollmentRecord.center))
        .filter(EnrollmentRecord.student_id == student.id)
        .order_by(EnrollmentRecord.start_date.asc())
        .all()
    )
    enrollment_history = [
        {
            "id": str(e.id),
            "center_name": e.center.name if e.center else "",
            "start_date": e.start_date.isoformat(),
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "status": e.status.value,
            "notes": e.notes,
        }
        for e in enrollments
    ]

    # Attendance statistics
    total_att = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).count()
    present_att = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
        )
        .count()
    )
    attendance_rate = round((present_att / total_att) * 100, 1) if total_att > 0 else 0.0

    # Competency progression
    skills = (
        db.query(StudentSkillProgress)
        .options(joinedload(StudentSkillProgress.competency))
        .filter(StudentSkillProgress.student_id == student.id)
        .all()
    )
    competencies_summary = [
        {
            "code": s.competency.code if s.competency else "",
            "name": s.competency.name if s.competency else "",
            "domain": s.competency.domain if s.competency else "",
            "current_level": s.current_level.value,
            "total_sessions_count": s.total_sessions_count,
            "last_evaluated_at": s.last_evaluated_at.isoformat(),
        }
        for s in skills
    ]

    return {
        "student": {
            "id": str(student.id),
            "student_id_number": student.student_id_number,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "date_of_birth": student.date_of_birth.isoformat(),
            "gender": student.gender,
            "status": student.status.value,
            "current_center_name": center.name if center else "",
            "guardian_name": student.guardian_name,
            "guardian_phone": student.guardian_phone,
            "guardian_email": student.guardian_email,
            "guardian_relationship": student.guardian_relationship,
            "emergency_contact": student.emergency_contact,
            "notes": student.notes,
        },
        "enrollment_history": enrollment_history,
        "attendance_metrics": {
            "total_records": total_att,
            "present_count": present_att,
            "attendance_rate_percentage": attendance_rate,
        },
        "competencies_mastery": competencies_summary,
    }
