"""
Learning Sessions and Student Competency Evaluation Business Service Layer.
Enforces date boundaries, enrollment alignment, atomic session observations,
and cumulative student skill progress updates.
"""
import math
from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.activity import ActivityTemplate
from app.models.competency import Competency, StudentSkillProgress
from app.models.session import (
    LearningSession,
    SessionStudent,
    SessionStudentEvaluation,
)
from app.models.audit import AuditLog
from app.models.center import Center
from app.models.enums import EnrollmentStatus, UserRole
from app.models.student import EnrollmentRecord, Student
from app.models.user import User, UserCenter
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionStudentEvaluationResponse,
    SessionStudentResponse,
)


class SessionServiceError(Exception):
    """Base exception for session service operations."""
    pass


class SessionNotFoundError(SessionServiceError):
    """Raised when session is not found."""
    pass


class SessionValidationError(SessionServiceError):
    """Raised for validation errors."""
    pass


def serialize_session_response(s: LearningSession) -> SessionResponse:
    """Serializes LearningSession with nested student roster and evaluations."""
    students_list = []
    if hasattr(s, "student_roster") and s.student_roster:
        for ss in s.student_roster:
            evals_list = []
            if hasattr(ss, "evaluations") and ss.evaluations:
                for ev in ss.evaluations:
                    evals_list.append(
                        SessionStudentEvaluationResponse(
                            id=ev.id,
                            session_student_id=ev.session_student_id,
                            competency_id=ev.competency_id,
                            mastery_level=ev.mastery_level,
                            teacher_notes=ev.teacher_notes,
                            created_at=ev.created_at,
                            competency_code=ev.competency.code if ev.competency else None,
                            competency_name=ev.competency.name if ev.competency else None,
                        )
                    )

            student_name = f"{ss.student.first_name} {ss.student.last_name}" if ss.student else None
            students_list.append(
                SessionStudentResponse(
                    id=ss.id,
                    session_id=ss.session_id,
                    student_id=ss.student_id,
                    participation_status=ss.participation_status,
                    qualitative_feedback=ss.qualitative_feedback,
                    score=ss.score,
                    created_at=ss.created_at,
                    student_name=student_name,
                    evaluations=evals_list,
                )
            )

    return SessionResponse(
        id=s.id,
        center_id=s.center_id,
        activity_template_id=s.activity_template_id,
        conducted_by_user_id=s.conducted_by_user_id,
        session_date=s.session_date,
        start_time=s.start_time,
        end_time=s.end_time,
        topic_summary=s.topic_summary,
        general_notes=s.general_notes,
        created_at=s.created_at,
        updated_at=s.updated_at,
        center_name=s.center.name if s.center else None,
        activity_title=s.activity_template.title if s.activity_template else None,
        teacher_name=s.conducted_by.full_name if s.conducted_by else None,
        student_roster=students_list,
    )


def create_session(
    db: Session,
    payload: SessionCreate,
    current_user: User,
    client_ip: Optional[str] = None,
) -> LearningSession:
    """
    Creates a learning session, logs student participation, and updates skill progress.
    """
    center = db.get(Center, payload.center_id)
    if not center or not center.is_active:
        raise SessionValidationError("Learning center not found or is inactive.")

    # Timezone-aware date validation (FR-SES-02)
    try:
        tz = ZoneInfo(center.timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    local_today = datetime.now(tz).date()
    if payload.session_date > local_today:
        raise SessionValidationError(
            f"Cannot conduct sessions in the future (Center local date is {local_today})."
        )

    # Duration check (>= 5 mins)
    duration_secs = (payload.end_time - payload.start_time).total_seconds()
    if duration_secs < 300:
        raise SessionValidationError("Session duration must be at least 5 minutes.")

    # Activity template check
    template = db.get(ActivityTemplate, payload.activity_template_id)
    if not template or not template.is_active:
        raise SessionValidationError("Activity template not found or is inactive.")

    session_obj = LearningSession(
        center_id=center.id,
        activity_template_id=template.id,
        conducted_by_user_id=current_user.id,
        session_date=payload.session_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        topic_summary=payload.topic_summary.strip(),
        general_notes=payload.general_notes.strip() if payload.general_notes else None,
    )
    db.add(session_obj)
    db.flush()

    if payload.students:
        for st in payload.students:
            # Check student active enrollment on session date (FR-SES-04)
            valid_enr = (
                db.query(EnrollmentRecord)
                .filter(
                    EnrollmentRecord.student_id == st.student_id,
                    EnrollmentRecord.center_id == center.id,
                    EnrollmentRecord.start_date <= payload.session_date,
                    (
                        EnrollmentRecord.end_date.is_(None)
                        | (EnrollmentRecord.end_date >= payload.session_date)
                    ),
                )
                .first()
            )
            if not valid_enr:
                student = db.get(Student, st.student_id)
                s_name = f"{student.first_name} {student.last_name}" if student else str(st.student_id)
                raise SessionValidationError(
                    f"Student '{s_name}' was not actively enrolled at {center.name} on {payload.session_date}."
                )

            session_student = SessionStudent(
                session_id=session_obj.id,
                student_id=st.student_id,
                participation_status=st.participation_status,
                qualitative_feedback=st.qualitative_feedback,
                score=st.score,
            )
            db.add(session_student)
            db.flush()

            if st.evaluations:
                for ev in st.evaluations:
                    eval_obj = SessionStudentEvaluation(
                        session_student_id=session_student.id,
                        competency_id=ev.competency_id,
                        mastery_level=ev.mastery_level,
                        teacher_notes=ev.teacher_notes,
                    )
                    db.add(eval_obj)

                    # Update cumulative student skill progress (FR-PRG-01, FR-PRG-02)
                    progress = (
                        db.query(StudentSkillProgress)
                        .filter(
                            StudentSkillProgress.student_id == st.student_id,
                            StudentSkillProgress.competency_id == ev.competency_id,
                        )
                        .first()
                    )
                    if progress:
                        progress.total_sessions_count += 1
                        progress.current_level = ev.mastery_level
                        progress.last_evaluated_at = payload.start_time
                        progress.updated_at = datetime.utcnow()
                    else:
                        progress = StudentSkillProgress(
                            student_id=st.student_id,
                            competency_id=ev.competency_id,
                            current_level=ev.mastery_level,
                            total_sessions_count=1,
                            last_evaluated_at=payload.start_time,
                        )
                        db.add(progress)

    audit = AuditLog(
        user_id=current_user.id,
        action="SESSION_CREATE",
        resource_type="LEARNING_SESSION",
        resource_id=session_obj.id,
        client_ip=client_ip,
        old_values=None,
        new_values={
            "center_id": str(center.id),
            "session_date": payload.session_date.isoformat(),
            "topic_summary": session_obj.topic_summary,
            "students_count": len(payload.students) if payload.students else 0,
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(session_obj)
    return session_obj


def list_sessions(
    db: Session,
    current_user: User,
    center_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[LearningSession], int]:
    """Lists learning sessions scoped to user role and center assignments."""
    query = db.query(LearningSession).options(
        joinedload(LearningSession.center),
        joinedload(LearningSession.activity_template),
        joinedload(LearningSession.conducted_by),
        joinedload(LearningSession.student_roster).joinedload(SessionStudent.student),
        joinedload(LearningSession.student_roster)
        .joinedload(SessionStudent.evaluations)
        .joinedload(SessionStudentEvaluation.competency),
    )

    if current_user.role != UserRole.SUPER_ADMIN:
        assigned_cids = [
            uc.center_id
            for uc in db.query(UserCenter).filter(UserCenter.user_id == current_user.id).all()
        ]
        query = query.filter(LearningSession.center_id.in_(assigned_cids))
    elif center_id is not None:
        query = query.filter(LearningSession.center_id == center_id)

    if date_from:
        query = query.filter(LearningSession.session_date >= date_from)
    if date_to:
        query = query.filter(LearningSession.session_date <= date_to)

    total_items = query.distinct().count()
    offset = (page - 1) * size
    sessions = (
        query.distinct()
        .order_by(LearningSession.session_date.desc(), LearningSession.start_time.desc())
        .offset(offset)
        .limit(size)
        .all()
    )
    return sessions, total_items


def get_session(db: Session, session_id: UUID) -> Optional[LearningSession]:
    """Retrieves session by ID with complete student and evaluation details."""
    return (
        db.query(LearningSession)
        .options(
            joinedload(LearningSession.center),
            joinedload(LearningSession.activity_template),
            joinedload(LearningSession.conducted_by),
            joinedload(LearningSession.student_roster).joinedload(SessionStudent.student),
            joinedload(LearningSession.student_roster)
            .joinedload(SessionStudent.evaluations)
            .joinedload(SessionStudentEvaluation.competency),
        )
        .filter(LearningSession.id == session_id)
        .first()
    )
