"""
Authentication and Authorization unit and integration tests.
Tests password hashing, verification, JWT token lifecycle, login endpoint,
token refresh, user status enforcement, and protected route access control.
"""
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeMismatchError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.main import app
from app.models.center import Center
from app.models.enums import UserRole, UserStatus
from app.models.user import User, UserCenter


# ==============================================================================
# Isolated In-Memory SQLite Test Fixtures for Auth API Tests
# ==============================================================================

@pytest.fixture(scope="module")
def auth_db_engine():
    """Isolated SQLite in-memory engine with StaticPool for auth tests."""
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
def auth_session_factory(auth_db_engine):
    """Sessionmaker bound to the isolated in-memory test database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=auth_db_engine)


@pytest.fixture
def auth_db(auth_session_factory):
    """Provides a transactional database session for each test."""
    session = auth_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_client(auth_session_factory):
    """TestClient configured with dependency override for get_db."""
    def override_get_db():
        session = auth_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# 1. Password Hashing & Verification Unit Tests
# ==============================================================================

def test_password_hashing():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    assert hashed is not None
    assert hashed != raw_password
    assert hashed.startswith("$2b$12$"), "Hash must use bcrypt cost factor >= 12"

    # Verifies unique salts: same password produces different hashes
    hashed_2 = hash_password(raw_password)
    assert hashed != hashed_2


def test_password_verification():
    raw_password = "MySecurePassword2026!"
    hashed = hash_password(raw_password)

    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_password_verification_malformed_hash_fails_safely():
    assert verify_password("Password123!", "not-a-valid-bcrypt-hash") is False
    assert verify_password("Password123!", "") is False


# ==============================================================================
# 2. JWT Creation, Decoding & Validation Unit Tests
# ==============================================================================

def test_jwt_creation_and_decoding():
    user_id = uuid.uuid4()
    access_token = create_access_token(subject=user_id)

    payload = decode_token(access_token, expected_type="access")
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload
    assert payload["exp"] > payload["iat"]


def test_jwt_refresh_token_creation_and_decoding():
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(subject=user_id)

    payload = decode_token(refresh_token, expected_type="refresh")
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_jwt_expired_token_rejection():
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        subject=user_id, expires_delta=timedelta(seconds=-10)
    )

    with pytest.raises(TokenExpiredError, match="Token has expired"):
        decode_token(expired_token)


def test_jwt_invalid_token_rejection():
    with pytest.raises(TokenInvalidError):
        decode_token("completely-invalid.token.payload")


def test_jwt_token_type_mismatch_rejection():
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(subject=user_id)

    with pytest.raises(TokenTypeMismatchError, match="Invalid token type"):
        decode_token(refresh_token, expected_type="access")


# ==============================================================================
# 3. Authentication API Endpoint Tests (/auth/login)
# ==============================================================================

def test_login_successful(auth_client, auth_db):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="teacher.valid@edutrack.org",
        password_hash=hash_password("ValidPassword123!"),
        full_name="Valid Teacher",
        phone_number="+1-555-0100",
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE,
    )
    auth_db.add(user)
    auth_db.commit()

    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "teacher.valid@edutrack.org", "password": "ValidPassword123!"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800
    assert data["user"]["email"] == "teacher.valid@edutrack.org"
    assert data["user"]["full_name"] == "Valid Teacher"
    assert "password_hash" not in data["user"]


def test_login_incorrect_password(auth_client, auth_db):
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "teacher.valid@edutrack.org", "password": "WrongPassword!"},
    )

    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]
    assert "WWW-Authenticate" in resp.headers


def test_login_nonexistent_user(auth_client):
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@edutrack.org", "password": "AnyPassword123!"},
    )

    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_login_locked_user_rejected(auth_client, auth_db):
    user = User(
        id=uuid.uuid4(),
        email="locked.user@edutrack.org",
        password_hash=hash_password("Password123!"),
        full_name="Locked Staff",
        role=UserRole.TEACHER,
        status=UserStatus.LOCKED,
    )
    auth_db.add(user)
    auth_db.commit()

    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "locked.user@edutrack.org", "password": "Password123!"},
    )

    assert resp.status_code == 403
    assert "Account is locked" in resp.json()["detail"]


def test_login_inactive_user_rejected(auth_client, auth_db):
    user = User(
        id=uuid.uuid4(),
        email="inactive.user@edutrack.org",
        password_hash=hash_password("Password123!"),
        full_name="Inactive Staff",
        role=UserRole.TEACHER,
        status=UserStatus.INACTIVE,
    )
    auth_db.add(user)
    auth_db.commit()

    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "inactive.user@edutrack.org", "password": "Password123!"},
    )

    assert resp.status_code == 403
    assert "Account is inactive" in resp.json()["detail"]


# ==============================================================================
# 4. Token Refresh API Endpoint Tests (/auth/refresh)
# ==============================================================================

def test_refresh_token_endpoint_success(auth_client, auth_db):
    user = User(
        id=uuid.uuid4(),
        email="refresh.user@edutrack.org",
        password_hash=hash_password("Password123!"),
        full_name="Refresh Staff",
        role=UserRole.CENTER_MANAGER,
        status=UserStatus.ACTIVE,
    )
    auth_db.add(user)
    auth_db.commit()

    valid_refresh = create_refresh_token(subject=user.id)
    resp = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": valid_refresh},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["expires_in"] == 1800


def test_refresh_token_endpoint_expired_rejected(auth_client):
    expired_refresh = create_refresh_token(
        subject=uuid.uuid4(), expires_delta=timedelta(seconds=-1)
    )
    resp = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh},
    )

    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_refresh_token_endpoint_with_access_token_rejected(auth_client):
    access_token = create_access_token(subject=uuid.uuid4())
    resp = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert resp.status_code == 401
    assert "Invalid refresh token" in resp.json()["detail"]


# ==============================================================================
# 5. Protected Endpoint Tests (/auth/me & get_current_user dependency)
# ==============================================================================

def test_me_endpoint_missing_auth_header(auth_client):
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "Authentication credentials were not provided" in resp.json()["detail"]
    assert "WWW-Authenticate" in resp.headers


def test_me_endpoint_invalid_token(auth_client):
    resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-tampered-token"},
    )
    assert resp.status_code == 401
    assert "Invalid or malformed authentication token" in resp.json()["detail"]


def test_me_endpoint_invalid_auth_scheme(auth_client):
    resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert resp.status_code == 401
    assert "Invalid authentication scheme" in resp.json()["detail"]


def test_me_endpoint_successful(auth_client, auth_db):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="me.user@edutrack.org",
        password_hash=hash_password("Password123!"),
        full_name="Me User",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    auth_db.add(user)
    auth_db.commit()

    token = create_access_token(subject=user_id)
    resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(user_id)
    assert data["email"] == "me.user@edutrack.org"
    assert data["role"] == "SUPER_ADMIN"
    assert "password_hash" not in data


def test_me_endpoint_locked_user_denied(auth_client, auth_db):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="locked.me@edutrack.org",
        password_hash=hash_password("Password123!"),
        full_name="Locked Me",
        role=UserRole.TEACHER,
        status=UserStatus.LOCKED,
    )
    auth_db.add(user)
    auth_db.commit()

    token = create_access_token(subject=user_id)
    resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403
    assert "Account is locked" in resp.json()["detail"]

