"""
Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) authorization guards.
Enforces role hierarchies and center-level tenant scoping based on user_centers assignments.
"""
from typing import Optional, Sequence, Set
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.center import Center
from app.models.enums import UserRole
from app.models.user import User, UserCenter


# ==============================================================================
# Role-Based Access Control (RBAC)
# ==============================================================================

class RoleChecker:
    """
    FastAPI dependency callable enforcing that the authenticated staff member
    holds at least one of the permitted system roles.
    """
    def __init__(self, allowed_roles: Sequence[UserRole]) -> None:
        self.allowed_roles: Set[UserRole] = set(allowed_roles)

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            allowed_names = ", ".join(sorted(r.value for r in self.allowed_roles))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {allowed_names}",
            )
        return current_user


def require_roles(*roles: UserRole) -> RoleChecker:
    """
    Dependency factory to require one or more specific UserRole permissions.

    Example:
        @router.post("/centers")
        def create_center(user: User = Depends(require_roles(UserRole.SUPER_ADMIN))):
            ...

        @router.get("/students")
        def list_students(user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.CENTER_MANAGER))):
            ...
    """
    return RoleChecker(roles)


# Convenient pre-configured role dependencies matching the documentation matrix
require_super_admin = require_roles(UserRole.SUPER_ADMIN)
require_center_manager = require_roles(UserRole.SUPER_ADMIN, UserRole.CENTER_MANAGER)
require_teacher = require_roles(UserRole.SUPER_ADMIN, UserRole.CENTER_MANAGER, UserRole.TEACHER)


# ==============================================================================
# Center-Level Attribute-Based Access Control (ABAC)
# ==============================================================================

def verify_user_center_access(
    center_id: UUID,
    current_user: User,
    db: Session,
) -> Center:
    """
    Verifies that the target center exists and that the authenticated staff member
    has authorized access to it.

    Authorization Rules:
    1. Center must exist in the database; otherwise HTTP 404 Not Found is raised.
    2. SUPER_ADMIN has organization-wide global access; bypasses user_centers check.
    3. CENTER_MANAGER and TEACHER must have an explicit assignment in user_centers;
       otherwise HTTP 403 Forbidden is raised.
    """
    center = db.get(Center, center_id)
    if center is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning center not found",
        )

    # Super Admin has unrestricted global organization access
    if current_user.role == UserRole.SUPER_ADMIN:
        return center

    # Center Manager and Teacher must be assigned to the center via user_centers
    is_assigned = (
        db.query(UserCenter)
        .filter(
            UserCenter.user_id == current_user.id,
            UserCenter.center_id == center.id,
        )
        .first()
        is not None
    )

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: staff member is not assigned to this learning center",
        )

    return center


def get_center_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Center:
    """
    Extracts, validates, and scopes active center context from the request header:
        X-Center-ID: <uuid>

    Requirements:
    1. Header X-Center-ID must be present for center-scoped operations.
    2. Header value must be a syntactically valid UUID.
    3. Center must exist in database (404 Not Found).
    4. Authenticated user must have permissions for that center (403 Forbidden).
    5. Returns validated Center model instance for downstream service logic.
    """
    raw_header = request.headers.get("X-Center-ID")
    if not raw_header or not raw_header.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Center-ID header is required for this operation",
        )

    try:
        center_id = UUID(raw_header.strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Center-ID header format. Must be a valid UUID.",
        )

    return verify_user_center_access(
        center_id=center_id,
        current_user=current_user,
        db=db,
    )


def get_optional_center_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[Center]:
    """
    Optionally extracts and validates center context if X-Center-ID is provided.
    If header is omitted, returns None. If provided, strictly validates membership.
    """
    raw_header = request.headers.get("X-Center-ID")
    if not raw_header or not raw_header.strip():
        return None

    try:
        center_id = UUID(raw_header.strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Center-ID header format. Must be a valid UUID.",
        )

    return verify_user_center_access(
        center_id=center_id,
        current_user=current_user,
        db=db,
    )

