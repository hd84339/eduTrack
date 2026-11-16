"""
Authorization Unit and Integration Tests for EduTrack RBAC and Center-Level ABAC.
Validates role hierarchy, multi-role requirements, center-scoping via X-Center-ID,
Super Admin global bypass, multi-center teacher switching, and tampering prevention.
"""
import uuid
from typing import Optional
import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.api.permissions import (
    get_center_context,
    get_optional_center_context,
    require_center_manager,
    require_roles,
    require_super_admin,
    require_teacher,
    verify_user_center_access,
)
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.models.center import Center
from app.models.enums import UserRole, UserStatus
from app.models.user import User, UserCenter


# ==============================================================================
# Isolated In-Memory SQLite Test Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def authz_db_engine():
    """Isolated in-memory SQLite engine with StaticPool for authorization tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Center.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    UserCenter.__table__.create(bind=engine)
    yield engine
    UserCenter.__table__.drop(bind=engine)
    User.__table__.drop(bind=engine)
    Center.__table__.drop(bind=engine)


@pytest.fixture(scope="module")
def authz_session_factory(authz_db_engine):
    """Sessionmaker bound to the test database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=authz_db_engine)


@pytest.fixture
def authz_db(authz_session_factory):
    """Provides a transactional database session for each test."""
    session = authz_session_factory()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# Test Application and Test Routes
# ==============================================================================

authz_router = APIRouter()

@authz_router.get("/test/super-admin-only")
def super_admin_only_endpoint(user: User = Depends(require_super_admin)):
    return {"status": "ok", "user_id": str(user.id), "role": user.role.value}


@authz_router.get("/test/manager-or-admin")
def manager_or_admin_endpoint(user: User = Depends(require_center_manager)):
    return {"status": "ok", "user_id": str(user.id), "role": user.role.value}


@authz_router.get("/test/teacher-only")
def teacher_only_endpoint(user: User = Depends(require_roles(UserRole.TEACHER))):
    return {"status": "ok", "user_id": str(user.id), "role": user.role.value}


@authz_router.get("/test/multi-roles")
def multi_roles_endpoint(
    user: User = Depends(require_roles(UserRole.TEACHER, UserRole.CENTER_MANAGER))
):
    return {"status": "ok", "user_id": str(user.id), "role": user.role.value}


@authz_router.get("/test/center-context")
def center_context_endpoint(
    center: Center = Depends(get_center_context),
    user: User = Depends(get_current_user),
):
    return {
        "status": "ok",
        "center_id": str(center.id),
        "center_code": center.code,
        "center_name": center.name,
        "user_id": str(user.id),
    }


@authz_router.get("/test/optional-center-context")
def optional_center_context_endpoint(
    center: Optional[Center] = Depends(get_optional_center_context),
    user: User = Depends(get_current_user),
):
    return {
        "status": "ok",
        "center_id": str(center.id) if center else None,
        "user_id": str(user.id),
    }


@pytest.fixture(scope="module")
def authz_client(authz_session_factory):
    """TestClient configured with test routes and get_db dependency override."""
    test_app = FastAPI()
    test_app.include_router(authz_router)

    def override_get_db():
        session = authz_session_factory()
        try:
            yield session
        finally:
            session.close()

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as client:
        yield client


# ==============================================================================
# Seed Data Fixtures
# ==============================================================================

@pytest.fixture
def seed_centers(authz_db):
    """Creates three centers: Center A, Center B, and Center C (unassigned)."""
    center_a = Center(
        id=uuid.uuid4(),
        code=f"CEN-A-{uuid.uuid4().hex[:6]}",
        name="Alpha Learning Center",
        address="100 Alpha St",
        capacity=100,
    )
    center_b = Center(
        id=uuid.uuid4(),
        code=f"CEN-B-{uuid.uuid4().hex[:6]}",
        name="Beta Learning Center",
        address="200 Beta St",
        capacity=120,
    )
    center_c = Center(
        id=uuid.uuid4(),
        code=f"CEN-C-{uuid.uuid4().hex[:6]}",
        name="Gamma Learning Center",
        address="300 Gamma St",
        capacity=80,
    )
    authz_db.add_all([center_a, center_b, center_c])
    authz_db.commit()
    return {"center_a": center_a, "center_b": center_b, "center_c": center_c}


@pytest.fixture
def seed_users(authz_db, seed_centers):
    """Creates staff users with various role and center assignments."""
    ca = seed_centers["center_a"]
    cb = seed_centers["center_b"]

    # 1. Super Admin (no user_centers records needed)
    admin = User(
        id=uuid.uuid4(),
        email=f"admin_{uuid.uuid4().hex[:6]}@edutrack.org",
        password_hash=hash_password("Pass123!"),
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )

    # 2. Center Manager assigned to Center A
    manager_a = User(
        id=uuid.uuid4(),
        email=f"manager_a_{uuid.uuid4().hex[:6]}@edutrack.org",
        password_hash=hash_password("Pass123!"),
        full_name="Manager Alpha",
        role=UserRole.CENTER_MANAGER,
        status=UserStatus.ACTIVE,
    )

    # 3. Teacher assigned to Center A only
    teacher_a = User(
        id=uuid.uuid4(),
        email=f"teacher_a_{uuid.uuid4().hex[:6]}@edutrack.org",
        password_hash=hash_password("Pass123!"),
        full_name="Teacher Alpha",
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE,
    )

    # 4. Multi-center Teacher assigned to Center A and Center B
    teacher_multi = User(
        id=uuid.uuid4(),
        email=f"teacher_multi_{uuid.uuid4().hex[:6]}@edutrack.org",
        password_hash=hash_password("Pass123!"),
        full_name="Teacher Multi",
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE,
    )

    # 5. Locked User
    locked_user = User(
        id=uuid.uuid4(),
        email=f"locked_{uuid.uuid4().hex[:6]}@edutrack.org",
        password_hash=hash_password("Pass123!"),
        full_name="Locked Staff",
        role=UserRole.TEACHER,
        status=UserStatus.LOCKED,
    )

    # 6. Inactive User
    inactive_user = User(
        id=uuid.uuid4(),
        email=f"inactive_{uuid.uuid4().hex[:6]}@edutrack.org",
        password_hash=hash_password("Pass123!"),
        full_name="Inactive Staff",
        role=UserRole.TEACHER,
        status=UserStatus.INACTIVE,
    )

    authz_db.add_all([admin, manager_a, teacher_a, teacher_multi, locked_user, inactive_user])
    authz_db.commit()

    # Assign centers
    uc1 = UserCenter(id=uuid.uuid4(), user_id=manager_a.id, center_id=ca.id)
    uc2 = UserCenter(id=uuid.uuid4(), user_id=teacher_a.id, center_id=ca.id)
    uc3 = UserCenter(id=uuid.uuid4(), user_id=teacher_multi.id, center_id=ca.id)
    uc4 = UserCenter(id=uuid.uuid4(), user_id=teacher_multi.id, center_id=cb.id)
    authz_db.add_all([uc1, uc2, uc3, uc4])
    authz_db.commit()

    return {
        "admin": admin,
        "manager_a": manager_a,
        "teacher_a": teacher_a,
        "teacher_multi": teacher_multi,
        "locked_user": locked_user,
        "inactive_user": inactive_user,
    }


def auth_headers(user: User) -> dict:
    """Helper creating Bearer Authorization header for a user."""
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. RBAC Tests
# ==============================================================================

def test_super_admin_passes_super_admin_only_check(authz_client, seed_users):
    headers = auth_headers(seed_users["admin"])
    resp = authz_client.get("/test/super-admin-only", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "SUPER_ADMIN"


def test_center_manager_denied_super_admin_only_permission(authz_client, seed_users):
    headers = auth_headers(seed_users["manager_a"])
    resp = authz_client.get("/test/super-admin-only", headers=headers)
    assert resp.status_code == 403
    assert "Operation not permitted" in resp.json()["detail"]


def test_teacher_denied_super_admin_only_permission(authz_client, seed_users):
    headers = auth_headers(seed_users["teacher_a"])
    resp = authz_client.get("/test/super-admin-only", headers=headers)
    assert resp.status_code == 403
    assert "Operation not permitted" in resp.json()["detail"]


def test_teacher_denied_manager_only_permission(authz_client, seed_users):
    headers = auth_headers(seed_users["teacher_a"])
    resp = authz_client.get("/test/manager-or-admin", headers=headers)
    assert resp.status_code == 403
    assert "Operation not permitted" in resp.json()["detail"]


def test_center_manager_allowed_manager_route(authz_client, seed_users):
    headers = auth_headers(seed_users["manager_a"])
    resp = authz_client.get("/test/manager-or-admin", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "CENTER_MANAGER"


def test_super_admin_allowed_manager_route(authz_client, seed_users):
    headers = auth_headers(seed_users["admin"])
    resp = authz_client.get("/test/manager-or-admin", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "SUPER_ADMIN"


def test_multiple_allowed_roles_teacher_and_manager(authz_client, seed_users):
    # Teacher allowed
    resp_t = authz_client.get(
        "/test/multi-roles", headers=auth_headers(seed_users["teacher_a"])
    )
    assert resp_t.status_code == 200

    # Manager allowed
    resp_m = authz_client.get(
        "/test/multi-roles", headers=auth_headers(seed_users["manager_a"])
    )
    assert resp_m.status_code == 200

    # Admin denied on route strictly allowing only Teacher and Manager
    resp_a = authz_client.get(
        "/test/multi-roles", headers=auth_headers(seed_users["admin"])
    )
    assert resp_a.status_code == 403


def test_missing_auth_header_on_rbac_returns_401(authz_client):
    resp = authz_client.get("/test/super-admin-only")
    assert resp.status_code == 401
    assert "Authentication credentials were not provided" in resp.json()["detail"]
    assert "WWW-Authenticate" in resp.headers


def test_invalid_token_on_rbac_returns_401(authz_client):
    resp = authz_client.get(
        "/test/super-admin-only",
        headers={"Authorization": "Bearer bad-token-signature"},
    )
    assert resp.status_code == 401
    assert "Invalid or malformed authentication token" in resp.json()["detail"]


# ==============================================================================
# 2. Center-Level ABAC Tests
# ==============================================================================

def test_assigned_teacher_can_select_assigned_center(
    authz_client, seed_users, seed_centers
):
    headers = auth_headers(seed_users["teacher_a"])
    headers["X-Center-ID"] = str(seed_centers["center_a"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["center_id"] == str(seed_centers["center_a"].id)
    assert resp.json()["center_name"] == "Alpha Learning Center"


def test_teacher_cannot_select_unassigned_center(
    authz_client, seed_users, seed_centers
):
    # Teacher A is only assigned to Center A; tries selecting Center B
    headers = auth_headers(seed_users["teacher_a"])
    headers["X-Center-ID"] = str(seed_centers["center_b"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 403
    assert "Access denied: staff member is not assigned" in resp.json()["detail"]


def test_manager_cannot_access_unassigned_center(
    authz_client, seed_users, seed_centers
):
    # Manager A is assigned to Center A; tries selecting Center B
    headers = auth_headers(seed_users["manager_a"])
    headers["X-Center-ID"] = str(seed_centers["center_b"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 403
    assert "Access denied: staff member is not assigned" in resp.json()["detail"]


def test_manager_accesses_assigned_center(authz_client, seed_users, seed_centers):
    headers = auth_headers(seed_users["manager_a"])
    headers["X-Center-ID"] = str(seed_centers["center_a"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["center_id"] == str(seed_centers["center_a"].id)


def test_multi_center_teacher_can_select_either_assigned_center(
    authz_client, seed_users, seed_centers
):
    headers = auth_headers(seed_users["teacher_multi"])

    # 1. Select Center A -> Approved
    headers["X-Center-ID"] = str(seed_centers["center_a"].id)
    resp_a = authz_client.get("/test/center-context", headers=headers)
    assert resp_a.status_code == 200
    assert resp_a.json()["center_id"] == str(seed_centers["center_a"].id)

    # 2. Select Center B -> Approved
    headers["X-Center-ID"] = str(seed_centers["center_b"].id)
    resp_b = authz_client.get("/test/center-context", headers=headers)
    assert resp_b.status_code == 200
    assert resp_b.json()["center_id"] == str(seed_centers["center_b"].id)

    # 3. Select Center C (unassigned) -> Denied
    headers["X-Center-ID"] = str(seed_centers["center_c"].id)
    resp_c = authz_client.get("/test/center-context", headers=headers)
    assert resp_c.status_code == 403
    assert "Access denied: staff member is not assigned" in resp_c.json()["detail"]


def test_super_admin_global_access_rule(authz_client, seed_users, seed_centers):
    """Super Admin can select any existing center without user_centers assignment."""
    headers = auth_headers(seed_users["admin"])

    for center_key in ["center_a", "center_b", "center_c"]:
        target_center = seed_centers[center_key]
        headers["X-Center-ID"] = str(target_center.id)
        resp = authz_client.get("/test/center-context", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["center_id"] == str(target_center.id)


def test_missing_x_center_id_header_rejected_400(authz_client, seed_users):
    headers = auth_headers(seed_users["teacher_a"])
    # X-Center-ID header completely omitted
    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 400
    assert "X-Center-ID header is required" in resp.json()["detail"]


def test_invalid_uuid_header_rejected_400(authz_client, seed_users):
    headers = auth_headers(seed_users["teacher_a"])
    headers["X-Center-ID"] = "not-a-valid-uuid"

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 400
    assert "Invalid X-Center-ID header format" in resp.json()["detail"]


def test_nonexistent_center_id_rejected_404(authz_client, seed_users):
    random_id = str(uuid.uuid4())

    # For Teacher -> 404 Not Found
    headers_t = auth_headers(seed_users["teacher_a"])
    headers_t["X-Center-ID"] = random_id
    resp_t = authz_client.get("/test/center-context", headers=headers_t)
    assert resp_t.status_code == 404
    assert "Learning center not found" in resp_t.json()["detail"]

    # For Super Admin -> also 404 Not Found (center must exist)
    headers_a = auth_headers(seed_users["admin"])
    headers_a["X-Center-ID"] = random_id
    resp_a = authz_client.get("/test/center-context", headers=headers_a)
    assert resp_a.status_code == 404
    assert "Learning center not found" in resp_a.json()["detail"]


def test_changing_header_cannot_bypass_membership(
    authz_client, seed_users, seed_centers
):
    """Verifies that an attacker tampering with X-Center-ID cannot access unassigned centers."""
    headers = auth_headers(seed_users["teacher_a"])
    headers["X-Center-ID"] = str(seed_centers["center_c"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 403


def test_locked_user_denied_access(authz_client, seed_users, seed_centers):
    headers = auth_headers(seed_users["locked_user"])
    headers["X-Center-ID"] = str(seed_centers["center_a"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 403
    assert "Account is locked" in resp.json()["detail"]


def test_inactive_user_denied_access(authz_client, seed_users, seed_centers):
    headers = auth_headers(seed_users["inactive_user"])
    headers["X-Center-ID"] = str(seed_centers["center_a"].id)

    resp = authz_client.get("/test/center-context", headers=headers)
    assert resp.status_code == 403
    assert "Account is inactive" in resp.json()["detail"]


# ==============================================================================
# 3. Optional Center Context Tests
# ==============================================================================

def test_optional_center_context_when_omitted(authz_client, seed_users):
    headers = auth_headers(seed_users["teacher_a"])
    resp = authz_client.get("/test/optional-center-context", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["center_id"] is None


def test_optional_center_context_when_provided_valid(
    authz_client, seed_users, seed_centers
):
    headers = auth_headers(seed_users["teacher_a"])
    headers["X-Center-ID"] = str(seed_centers["center_a"].id)

    resp = authz_client.get("/test/optional-center-context", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["center_id"] == str(seed_centers["center_a"].id)


def test_optional_center_context_when_provided_unassigned(
    authz_client, seed_users, seed_centers
):
    headers = auth_headers(seed_users["teacher_a"])
    headers["X-Center-ID"] = str(seed_centers["center_b"].id)

    resp = authz_client.get("/test/optional-center-context", headers=headers)
    assert resp.status_code == 403


# ==============================================================================
# 4. Direct Helper Unit Test
# ==============================================================================

def test_verify_user_center_access_direct(authz_db, seed_users, seed_centers):
    ca = seed_centers["center_a"]
    cb = seed_centers["center_b"]

    # Teacher A with Center A -> Success
    res = verify_user_center_access(ca.id, seed_users["teacher_a"], authz_db)
    assert res.id == ca.id

    # Teacher A with Center B -> 403
    with pytest.raises(Exception) as exc:
        verify_user_center_access(cb.id, seed_users["teacher_a"], authz_db)
    assert "Access denied" in str(exc.value)

    # Super Admin with Center B -> Success (global access)
    res_admin = verify_user_center_access(cb.id, seed_users["admin"], authz_db)
    assert res_admin.id == cb.id
