"""
User and Staff Management Business Service Layer.
Enforces email uniqueness, secure password hashing, center assignments, and role boundaries.
"""
import math
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.center import Center
from app.models.enums import UserRole, UserStatus
from app.models.user import User, UserCenter
from app.schemas.user import (
    UserCenterAssign,
    UserCenterSummary,
    UserCreate,
    UserResponse,
    UserUpdate,
)


class UserServiceError(Exception):
    """Base exception for user service operations."""
    pass


class UserNotFoundError(UserServiceError):
    """Raised when user is not found."""
    pass


class UserAlreadyExistsError(UserServiceError):
    """Raised when creating user with existing email."""
    pass


class UnauthorizedRoleAssignmentError(UserServiceError):
    """Raised when an actor attempts to provision an unauthorized role."""
    pass


def serialize_user_response(user: User) -> UserResponse:
    """Safely converts User ORM instance into UserResponse, resolving assigned center summaries."""
    assigned_centers_list = []
    if hasattr(user, "assigned_centers") and user.assigned_centers:
        for uc in user.assigned_centers:
            if hasattr(uc, "center") and uc.center:
                assigned_centers_list.append(
                    UserCenterSummary(
                        id=uc.center.id,
                        code=uc.center.code,
                        name=uc.center.name,
                    )
                )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        assigned_centers=assigned_centers_list,
    )


def create_user(
    db: Session,
    payload: UserCreate,
    actor_user: User,
    client_ip: Optional[str] = None,
) -> User:
    """
    Provisions a new staff user.
    - Super Admin can create any role and assign any centers.
    - Center Manager can only create TEACHER accounts for their assigned center.
    """
    if actor_user.role == UserRole.CENTER_MANAGER:
        if payload.role != UserRole.TEACHER:
            raise UnauthorizedRoleAssignmentError(
                "Center Managers are only authorized to provision TEACHER accounts."
            )
        # Ensure center_ids are within the manager's assigned centers
        manager_center_ids = {
            uc.center_id
            for uc in db.query(UserCenter).filter(UserCenter.user_id == actor_user.id).all()
        }
        if payload.center_ids:
            for cid in payload.center_ids:
                if cid not in manager_center_ids:
                    raise UnauthorizedRoleAssignmentError(
                        "Cannot assign teacher to a center you do not manage."
                    )
        else:
            raise UnauthorizedRoleAssignmentError(
                "Must assign teacher to at least one managed center."
            )

    # Check unique email
    existing = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if existing:
        raise UserAlreadyExistsError(f"User with email '{payload.email}' already exists.")

    user = User(
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone_number=payload.phone_number.strip() if payload.phone_number else None,
        role=payload.role,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()

    # Assign centers
    if payload.center_ids:
        for cid in payload.center_ids:
            center = db.get(Center, cid)
            if center:
                db.add(UserCenter(user_id=user.id, center_id=cid))

    audit = AuditLog(
        user_id=actor_user.id,
        action="USER_CREATE",
        resource_type="USER",
        resource_id=user.id,
        client_ip=client_ip,
        old_values=None,
        new_values={
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "status": user.status.value,
            "center_ids": [str(cid) for cid in payload.center_ids] if payload.center_ids else [],
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(user)
    return user


def list_users(
    db: Session,
    current_user: User,
    role: Optional[UserRole] = None,
    center_id: Optional[UUID] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[User], int]:
    """
    Lists staff users.
    - Super Admins can see all users.
    - Center Managers can only see TEACHERs in their assigned centers.
    """
    query = db.query(User).options(
        joinedload(User.assigned_centers).joinedload(UserCenter.center)
    )

    if current_user.role == UserRole.CENTER_MANAGER:
        manager_center_ids = [
            uc.center_id
            for uc in db.query(UserCenter).filter(UserCenter.user_id == current_user.id).all()
        ]
        query = (
            query.filter(User.role == UserRole.TEACHER)
            .join(UserCenter, UserCenter.user_id == User.id)
            .filter(UserCenter.center_id.in_(manager_center_ids))
        )
    elif role is not None:
        query = query.filter(User.role == role)

    if center_id is not None and current_user.role == UserRole.SUPER_ADMIN:
        query = query.join(UserCenter, UserCenter.user_id == User.id).filter(
            UserCenter.center_id == center_id
        )

    total_items = query.distinct().count()
    offset = (page - 1) * size
    users = query.distinct().order_by(User.full_name.asc()).offset(offset).limit(size).all()
    return users, total_items


def update_user_centers(
    db: Session,
    user_id: UUID,
    payload: UserCenterAssign,
    actor_user_id: UUID,
    client_ip: Optional[str] = None,
) -> User:
    """Updates center assignments for a staff member (Super Admin only)."""
    user = db.get(User, user_id)
    if not user:
        raise UserNotFoundError("User not found.")

    # Remove existing assignments
    db.query(UserCenter).filter(UserCenter.user_id == user.id).delete()

    # Insert new assignments
    for cid in payload.center_ids:
        center = db.get(Center, cid)
        if center:
            db.add(UserCenter(user_id=user.id, center_id=cid))

    audit = AuditLog(
        user_id=actor_user_id,
        action="USER_CENTERS_UPDATE",
        resource_type="USER",
        resource_id=user.id,
        client_ip=client_ip,
        old_values=None,
        new_values={"assigned_center_ids": [str(c) for c in payload.center_ids]},
    )
    db.add(audit)

    db.commit()
    db.refresh(user)
    return user

