"""
Learning Activity Templates Business Service Layer.
Enforces age boundary validation, normalized competency linkage, and center scope.
"""
import math
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.activity import ActivityCompetency, ActivityTemplate
from app.models.competency import Competency
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.user import User, UserCenter
from app.schemas.activity import (
    ActivityCompetencyResponse,
    ActivityTemplateCreate,
    ActivityTemplateResponse,
    ActivityTemplateUpdate,
)


class ActivityServiceError(Exception):
    """Base exception for activity service operations."""
    pass


class ActivityTemplateNotFoundError(ActivityServiceError):
    """Raised when activity template is not found."""
    pass


class ActivityTemplateValidationError(ActivityServiceError):
    """Raised for validation violations."""
    pass


def serialize_activity_template(tmpl: ActivityTemplate) -> ActivityTemplateResponse:
    """Serializes ActivityTemplate with resolved competencies and creator name."""
    comp_items = []
    if hasattr(tmpl, "competencies") and tmpl.competencies:
        for ac in tmpl.competencies:
            comp_code = ac.competency.code if ac.competency else None
            comp_name = ac.competency.name if ac.competency else None
            comp_items.append(
                ActivityCompetencyResponse(
                    id=ac.id,
                    activity_template_id=ac.activity_template_id,
                    competency_id=ac.competency_id,
                    is_primary=ac.is_primary,
                    competency_code=comp_code,
                    competency_name=comp_name,
                )
            )

    creator_name = tmpl.created_by.full_name if tmpl.created_by else None
    center_name = tmpl.center.name if tmpl.center else None

    return ActivityTemplateResponse(
        id=tmpl.id,
        center_id=tmpl.center_id,
        created_by_user_id=tmpl.created_by_user_id,
        title=tmpl.title,
        subject_area=tmpl.subject_area,
        description=tmpl.description,
        target_age_min=tmpl.target_age_min,
        target_age_max=tmpl.target_age_max,
        duration_minutes=tmpl.duration_minutes,
        is_global=tmpl.is_global,
        is_active=tmpl.is_active,
        created_at=tmpl.created_at,
        updated_at=tmpl.updated_at,
        competencies=comp_items,
        center_name=center_name,
        creator_name=creator_name,
    )


def create_activity_template(
    db: Session,
    payload: ActivityTemplateCreate,
    current_user: User,
    client_ip: Optional[str] = None,
) -> ActivityTemplate:
    """Creates a new learning activity template."""
    if payload.is_global and current_user.role != UserRole.SUPER_ADMIN:
        raise ActivityTemplateValidationError("Only Super Admins can author global activity templates.")

    if not payload.is_global and not payload.center_id:
        raise ActivityTemplateValidationError("center_id is required for center-specific activity templates.")

    tmpl = ActivityTemplate(
        center_id=payload.center_id if not payload.is_global else None,
        created_by_user_id=current_user.id,
        title=payload.title.strip(),
        subject_area=payload.subject_area.strip(),
        description=payload.description.strip(),
        target_age_min=payload.target_age_min,
        target_age_max=payload.target_age_max,
        duration_minutes=payload.duration_minutes,
        is_global=payload.is_global,
        is_active=True,
    )
    db.add(tmpl)
    db.flush()

    if payload.competencies:
        for c in payload.competencies:
            comp_exists = db.get(Competency, c.competency_id)
            if comp_exists:
                db.add(
                    ActivityCompetency(
                        activity_template_id=tmpl.id,
                        competency_id=c.competency_id,
                        is_primary=c.is_primary,
                    )
                )

    audit = AuditLog(
        user_id=current_user.id,
        action="ACTIVITY_TEMPLATE_CREATE",
        resource_type="ACTIVITY_TEMPLATE",
        resource_id=tmpl.id,
        client_ip=client_ip,
        old_values=None,
        new_values={"title": tmpl.title, "subject_area": tmpl.subject_area, "is_global": tmpl.is_global},
    )
    db.add(audit)

    db.commit()
    db.refresh(tmpl)
    return tmpl


def list_activity_templates(
    db: Session,
    current_user: User,
    center_id: Optional[UUID] = None,
    subject_area: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[ActivityTemplate], int]:
    """Lists templates accessible to user: all global templates + assigned center templates."""
    query = db.query(ActivityTemplate).options(
        joinedload(ActivityTemplate.competencies).joinedload(ActivityCompetency.competency),
        joinedload(ActivityTemplate.created_by),
        joinedload(ActivityTemplate.center),
    )

    if current_user.role != UserRole.SUPER_ADMIN:
        assigned_cids = [
            uc.center_id
            for uc in db.query(UserCenter).filter(UserCenter.user_id == current_user.id).all()
        ]
        query = query.filter(
            (ActivityTemplate.is_global.is_(True))
            | (ActivityTemplate.center_id.in_(assigned_cids))
        )
    elif center_id is not None:
        query = query.filter(
            (ActivityTemplate.is_global.is_(True))
            | (ActivityTemplate.center_id == center_id)
        )

    if subject_area:
        query = query.filter(ActivityTemplate.subject_area.ilike(f"%{subject_area.strip()}%"))

    if is_active is not None:
        query = query.filter(ActivityTemplate.is_active == is_active)

    total_items = query.distinct().count()
    offset = (page - 1) * size
    templates = (
        query.distinct()
        .order_by(ActivityTemplate.title.asc())
        .offset(offset)
        .limit(size)
        .all()
    )
    return templates, total_items


def get_activity_template(db: Session, template_id: UUID) -> Optional[ActivityTemplate]:
    """Retrieves an activity template by primary key."""
    return (
        db.query(ActivityTemplate)
        .options(
            joinedload(ActivityTemplate.competencies).joinedload(ActivityCompetency.competency),
            joinedload(ActivityTemplate.created_by),
            joinedload(ActivityTemplate.center),
        )
        .filter(ActivityTemplate.id == template_id)
        .first()
    )


def update_activity_template(
    db: Session,
    template_id: UUID,
    payload: ActivityTemplateUpdate,
    current_user: User,
    client_ip: Optional[str] = None,
) -> ActivityTemplate:
    """Updates an existing activity template."""
    tmpl = get_activity_template(db, template_id)
    if not tmpl:
        raise ActivityTemplateNotFoundError("Activity template not found.")

    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("competencies", None)

    for k, v in update_data.items():
        if hasattr(tmpl, k):
            setattr(tmpl, k, v)

    tmpl.updated_at = datetime.utcnow()

    if payload.competencies is not None:
        db.query(ActivityCompetency).filter(
            ActivityCompetency.activity_template_id == tmpl.id
        ).delete()
        for c in payload.competencies:
            db.add(
                ActivityCompetency(
                    activity_template_id=tmpl.id,
                    competency_id=c.competency_id,
                    is_primary=c.is_primary,
                )
            )

    audit = AuditLog(
        user_id=current_user.id,
        action="ACTIVITY_TEMPLATE_UPDATE",
        resource_type="ACTIVITY_TEMPLATE",
        resource_id=tmpl.id,
        client_ip=client_ip,
        old_values=None,
        new_values={"title": tmpl.title, "is_active": tmpl.is_active},
    )
    db.add(audit)

    db.commit()
    db.refresh(tmpl)
    return tmpl
