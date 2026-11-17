"""
Curriculum Competency Catalog and Student Skill Mastery Business Service Layer.
Enforces competency uniqueness and aggregates longitudinal student mastery progression.
"""
import math
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.competency import Competency, StudentSkillProgress
from app.models.audit import AuditLog
from app.models.student import Student
from app.models.user import User
from app.schemas.competency import (
    CompetencyCreate,
    CompetencyResponse,
    StudentProgressOverviewResponse,
    StudentSkillProgressResponse,
)


class CompetencyServiceError(Exception):
    """Base exception for competency service operations."""
    pass


class CompetencyAlreadyExistsError(CompetencyServiceError):
    """Raised when competency code already exists."""
    pass


class StudentNotFoundError(CompetencyServiceError):
    """Raised when target student is not found."""
    pass


def create_competency(
    db: Session,
    payload: CompetencyCreate,
    user_id: UUID,
    client_ip: Optional[str] = None,
) -> Competency:
    """Super Admin adds a new competency to the central catalog."""
    existing = db.query(Competency).filter(Competency.code == payload.code.strip()).first()
    if existing:
        raise CompetencyAlreadyExistsError(f"Competency with code '{payload.code}' already exists.")

    comp = Competency(
        code=payload.code.strip(),
        name=payload.name.strip(),
        domain=payload.domain.strip(),
        description=payload.description.strip() if payload.description else None,
    )
    db.add(comp)
    db.flush()

    audit = AuditLog(
        user_id=user_id,
        action="COMPETENCY_CREATE",
        resource_type="COMPETENCY",
        resource_id=comp.id,
        client_ip=client_ip,
        old_values=None,
        new_values={"code": comp.code, "name": comp.name, "domain": comp.domain},
    )
    db.add(audit)

    db.commit()
    db.refresh(comp)
    return comp


def list_competencies(
    db: Session,
    domain: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> Tuple[List[Competency], int]:
    """Lists curriculum competencies filterable by domain and search term."""
    query = db.query(Competency)

    if domain and domain.strip():
        query = query.filter(Competency.domain.ilike(f"%{domain.strip()}%"))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Competency.name.ilike(term),
                Competency.code.ilike(term),
                Competency.description.ilike(term),
            )
        )

    total_items = query.count()
    offset = (page - 1) * size
    items = query.order_by(Competency.domain.asc(), Competency.code.asc()).offset(offset).limit(size).all()
    return items, total_items


def get_student_progress(
    db: Session,
    student_id: UUID,
) -> StudentProgressOverviewResponse:
    """Aggregates all recorded competency mastery levels for a student."""
    student = db.get(Student, student_id)
    if not student:
        raise StudentNotFoundError("Student not found.")

    progress_records = (
        db.query(StudentSkillProgress)
        .options(joinedload(StudentSkillProgress.competency))
        .filter(StudentSkillProgress.student_id == student.id)
        .order_by(StudentSkillProgress.last_evaluated_at.desc())
        .all()
    )

    items = [
        StudentSkillProgressResponse(
            id=p.id,
            student_id=p.student_id,
            competency_id=p.competency_id,
            code=p.competency.code if p.competency else None,
            name=p.competency.name if p.competency else None,
            domain=p.competency.domain if p.competency else None,
            current_level=p.current_level,
            total_sessions_count=p.total_sessions_count,
            last_evaluated_at=p.last_evaluated_at,
            updated_at=p.updated_at,
        )
        for p in progress_records
    ]

    return StudentProgressOverviewResponse(
        student_id=student.id,
        competencies=items,
    )
