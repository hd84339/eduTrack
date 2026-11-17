"""
Student Management Integration Tests.
Validates student creation, listing, retrieval, OCC version updates,
center-tenant boundary isolation, RBAC role restrictions, and immutable audit trails.
"""
import uuid
from datetime import date, datetime
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.center import Center
from app.models.enums import EnrollmentStatus, StudentStatus, UserRole, UserStatus
from app.models.student import EnrollmentRecord, Student
from app.models.user import User, UserCenter


# Compile PostgreSQL JSONB type to SQLite JSON for in-memory testing
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


# ==============================================================================
# Isolated SQLite Test Database Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def student_test_engine():
    """Module-scoped in-memory SQLite engine with StaticPool for student tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Center.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    UserCenter.__table__.create(bind=engine)
    Student.__table__.create(bind=engine)
    EnrollmentRecord.__table__.create(bind=engine)
    AuditLog.__table__.create(bind=engine)

    yield engine

    AuditLog.__table__.drop(bind=engine)
    EnrollmentRecord.__table__.drop(bind=engine)
    Student.__table__.drop(bind=engine)
    UserCenter.__table__.drop(bind=engine)
    User.__table__.drop(bind=engine)
    Center.__table__.drop(bind=engine)


@pytest.fixture(scope="module")
def student_session_factory(student_test_engine):
    """Sessionmaker bound to the test database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=student_test_engine)


@pytest.fixture
def student_db(student_session_factory) -> Generator[Session, None, None]:
    """Provides a clean session per test."""
    session = student_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def student_client(student_session_factory) -> Generator[TestClient, None, None]:
    """TestClient configured with get_db dependency override."""
    def override_get_db():
        session = student_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# Domain Seed Fixtures
# ==============================================================================

@pytest.fixture
def test_centers(student_db: Session):
    """Creates two distinct learning centers for multi-tenant boundary testing."""
    center_a = student_db.query(Center).filter(Center.code == "CEN-STU-A").first()
    if not center_a:
        center_a = Center(
            id=uuid.uuid4(),
            code="CEN-STU-A",
            name="Alpha Learning Center",
            address="100 Alpha Blvd",
            timezone="America/New_York",
            contact_phone="+1-555-0101",
            contact_email="alpha@edutrack.org",
            capacity=100,
            is_active=True,
        )
        student_db.add(center_a)

    center_b = student_db.query(Center).filter(Center.code == "CEN-STU-B").first()
    if not center_b:
        center_b = Center(
            id=uuid.uuid4(),
            code="CEN-STU-B",
            name="Beta Learning Center",
            address="200 Beta Blvd",
            timezone="America/New_York",
            contact_phone="+1-555-0202",
            contact_email="beta@edutrack.org",
            capacity=100,
            is_active=True,
        )
        student_db.add(center_b)

    student_db.commit()
    student_db.refresh(center_a)
    student_db.refresh(center_b)
    return {"center_a": center_a, "center_b": center_b}


@pytest.fixture
def test_users(student_db: Session, test_centers):
    """Provisions Super Admin, Center Manager (Center A), and Teacher (Center A)."""
    center_a = test_centers["center_a"]

    # Super Admin
    super_admin = student_db.query(User).filter(User.email == "admin@edutrack.org").first()
    if not super_admin:
        super_admin = User(
            id=uuid.uuid4(),
            email="admin@edutrack.org",
            password_hash=hash_password("SuperSecret123!"),
            full_name="Super Administrator",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
        )
        student_db.add(super_admin)
        student_db.flush()

    # Center Manager assigned to Center A
    manager = student_db.query(User).filter(User.email == "manager.alpha@edutrack.org").first()
    if not manager:
        manager = User(
            id=uuid.uuid4(),
            email="manager.alpha@edutrack.org",
            password_hash=hash_password("ManagerSecret123!"),
            full_name="Alpha Center Manager",
            role=UserRole.CENTER_MANAGER,
            status=UserStatus.ACTIVE,
        )
        student_db.add(manager)
        student_db.flush()
        student_db.add(UserCenter(user_id=manager.id, center_id=center_a.id))

    # Teacher assigned to Center A
    teacher = student_db.query(User).filter(User.email == "teacher.alpha@edutrack.org").first()
    if not teacher:
        teacher = User(
            id=uuid.uuid4(),
            email="teacher.alpha@edutrack.org",
            password_hash=hash_password("TeacherSecret123!"),
            full_name="Alpha Teacher",
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE,
        )
        student_db.add(teacher)
        student_db.flush()
        student_db.add(UserCenter(user_id=teacher.id, center_id=center_a.id))

    student_db.commit()
    student_db.refresh(super_admin)
    student_db.refresh(manager)
    student_db.refresh(teacher)

    return {
        "super_admin": super_admin,
        "super_admin_token": create_access_token(super_admin.id),
        "manager": manager,
        "manager_token": create_access_token(manager.id),
        "teacher": teacher,
        "teacher_token": create_access_token(teacher.id),
    }


# ==============================================================================
# Student Creation Tests (POST /students)
# ==============================================================================

def test_student_creation_successful(student_client, test_centers, test_users, student_db):
    """
    Manager successfully registers a student.
    Verifies: 201 Created, version: 1, initial EnrollmentRecord created, AuditLog created.
    """
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]
    student_id_num = f"STU-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "student_id_number": student_id_num,
        "center_id": str(center_a.id),
        "first_name": "Oliver",
        "last_name": "Queen",
        "date_of_birth": "2017-04-12",
        "gender": "Male",
        "guardian_name": "Moira Queen",
        "guardian_phone": "+1-555-0199",
        "guardian_email": "moira@queen.org",
        "guardian_relationship": "Mother",
        "emergency_contact": "Thea: +1-555-0198",
        "notes": "Prefers archery club",
    }

    response = student_client.post(
        "/api/v1/students",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Center-ID": str(center_a.id),
        },
        json=payload,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["student_id_number"] == student_id_num
    assert data["first_name"] == "Oliver"
    assert data["last_name"] == "Queen"
    assert data["current_center_id"] == str(center_a.id)
    assert data["status"] == "ACTIVE"
    assert data["version"] == 1
    assert "id" in data

    # Verify initial EnrollmentRecord was created atomically
    created_student_id = uuid.UUID(data["id"])
    enrollment = (
        student_db.query(EnrollmentRecord)
        .filter(EnrollmentRecord.student_id == created_student_id)
        .first()
    )
    assert enrollment is not None
    assert enrollment.center_id == center_a.id
    assert enrollment.status == EnrollmentStatus.ACTIVE
    assert enrollment.end_date is None

    # Verify immutable AuditLog record was captured
    audit = (
        student_db.query(AuditLog)
        .filter(
            AuditLog.resource_id == created_student_id,
            AuditLog.action == "STUDENT_CREATE",
        )
        .first()
    )
    assert audit is not None
    assert audit.user_id == test_users["manager"].id
    assert audit.resource_type == "STUDENT"


def test_student_creation_invalid_input(student_client, test_centers, test_users):
    """Validates that malformed or incomplete payload returns 422 Unprocessable Entity."""
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]

    # Missing required first_name and date_of_birth
    payload = {
        "student_id_number": "STU-INVALID",
        "center_id": str(center_a.id),
        "last_name": "Doe",
        "gender": "Male",
        "guardian_name": "Jane Doe",
        "guardian_phone": "555-1234",
    }

    response = student_client.post(
        "/api/v1/students",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Center-ID": str(center_a.id),
        },
        json=payload,
    )
    assert response.status_code == 422


def test_student_creation_duplicate_identifier(student_client, test_centers, test_users):
    """Attempting to create another student with an existing student_id_number returns 409 Conflict."""
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]
    duplicate_num = f"STU-DUP-{uuid.uuid4().hex[:6].upper()}"

    payload = {
        "student_id_number": duplicate_num,
        "center_id": str(center_a.id),
        "first_name": "Barry",
        "last_name": "Allen",
        "date_of_birth": "2016-03-14",
        "gender": "Male",
        "guardian_name": "Henry Allen",
        "guardian_phone": "+1-555-0314",
    }

    # First creation succeeds
    res1 = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json=payload,
    )
    assert res1.status_code == 201

    # Second creation with identical student_id_number fails with 409 Conflict
    res2 = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json=payload,
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_student_creation_with_unauthorized_center(student_client, test_centers, test_users):
    """Manager of Center A attempts to register a student for Center B; returns 403 Forbidden."""
    center_b = test_centers["center_b"]
    token = test_users["manager_token"]  # Manager is only assigned to Center A

    payload = {
        "student_id_number": f"STU-UNAUTH-{uuid.uuid4().hex[:6]}",
        "center_id": str(center_b.id),
        "first_name": "Bruce",
        "last_name": "Wayne",
        "date_of_birth": "2015-05-20",
        "gender": "Male",
        "guardian_name": "Alfred Pennyworth",
        "guardian_phone": "+1-555-0999",
    }

    response = student_client.post(
        "/api/v1/students",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Center-ID": str(center_b.id),
        },
        json=payload,
    )
    assert response.status_code == 403


def test_student_creation_with_mismatched_center_id(student_client, test_centers, test_users):
    """Payload center_id does not match the active X-Center-ID context header; returns 400 Bad Request."""
    center_a = test_centers["center_a"]
    center_b = test_centers["center_b"]
    token = test_users["manager_token"]

    payload = {
        "student_id_number": f"STU-MISMATCH-{uuid.uuid4().hex[:6]}",
        "center_id": str(center_b.id),  # Mismatched from header
        "first_name": "Clark",
        "last_name": "Kent",
        "date_of_birth": "2016-06-18",
        "gender": "Male",
        "guardian_name": "Martha Kent",
        "guardian_phone": "+1-555-0888",
    }

    response = student_client.post(
        "/api/v1/students",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Center-ID": str(center_a.id),
        },
        json=payload,
    )
    assert response.status_code == 400
    assert "Payload center_id does not match" in response.json()["detail"]


def test_student_creation_unauthorized_role_teacher(student_client, test_centers, test_users):
    """Teachers do not have student registration privileges; returns 403 Forbidden."""
    center_a = test_centers["center_a"]
    teacher_token = test_users["teacher_token"]

    payload = {
        "student_id_number": f"STU-TEACH-{uuid.uuid4().hex[:6]}",
        "center_id": str(center_a.id),
        "first_name": "Diana",
        "last_name": "Prince",
        "date_of_birth": "2017-02-15",
        "gender": "Female",
        "guardian_name": "Hippolyta",
        "guardian_phone": "+1-555-0777",
    }

    response = student_client.post(
        "/api/v1/students",
        headers={
            "Authorization": f"Bearer {teacher_token}",
            "X-Center-ID": str(center_a.id),
        },
        json=payload,
    )
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]


def test_student_creation_missing_authentication(student_client, test_centers):
    """Request without Authorization header returns 401 Unauthorized."""
    center_a = test_centers["center_a"]
    payload = {
        "student_id_number": "STU-NOAUTH",
        "center_id": str(center_a.id),
        "first_name": "No",
        "last_name": "Auth",
        "date_of_birth": "2018-01-01",
        "gender": "Other",
        "guardian_name": "Guardian",
        "guardian_phone": "555-0000",
    }
    response = student_client.post(
        "/api/v1/students",
        headers={"X-Center-ID": str(center_a.id)},
        json=payload,
    )
    assert response.status_code == 401


# ==============================================================================
# Student Listing Tests (GET /students)
# ==============================================================================

def test_student_listing_center_scoped(student_client, test_centers, test_users):
    """Teachers and Managers can list students strictly scoped to their center."""
    center_a = test_centers["center_a"]
    token = test_users["teacher_token"]

    response = student_client.get(
        "/api/v1/students",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Center-ID": str(center_a.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["size"] == 20
    assert data["pagination"]["total_items"] >= 1

    # Verify every returned student belongs to center A
    for item in data["items"]:
        assert item["current_center_id"] == str(center_a.id)
        assert item["center_name"] == center_a.name


def test_student_listing_filtering_and_search(student_client, test_centers, test_users):
    """Validates multi-attribute status filtering and case-insensitive search."""
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]

    # Register a student with distinct search term
    unique_search_name = f"Zackery{uuid.uuid4().hex[:4]}"
    student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": f"STU-SRCH-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_a.id),
            "first_name": unique_search_name,
            "last_name": "Taylor",
            "date_of_birth": "2016-09-01",
            "gender": "Male",
            "guardian_name": "Mr Taylor",
            "guardian_phone": "+1-555-0999",
        },
    )

    # Search by partial first name (case-insensitive)
    search_query = unique_search_name[:5].lower()
    response = student_client.get(
        f"/api/v1/students?search={search_query}&status=ACTIVE",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["first_name"] == unique_search_name


def test_student_listing_sorting(student_client, test_centers, test_users):
    """Validates sorting by last_name asc and desc."""
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]

    res_asc = student_client.get(
        "/api/v1/students?sort_by=last_name&sort_dir=asc",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
    )
    assert res_asc.status_code == 200
    asc_names = [item["last_name"] for item in res_asc.json()["items"]]
    assert asc_names == sorted(asc_names)

    res_desc = student_client.get(
        "/api/v1/students?sort_by=last_name&sort_dir=desc",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
    )
    assert res_desc.status_code == 200
    desc_names = [item["last_name"] for item in res_desc.json()["items"]]
    assert desc_names == sorted(desc_names, reverse=True)


def test_student_listing_pagination_and_empty_results(student_client, test_centers, test_users):
    """Validates empty results when no students match criteria."""
    center_b = test_centers["center_b"]
    token = test_users["super_admin_token"]  # Super admin can inspect Center B

    response = student_client.get(
        "/api/v1/students?search=NONEXISTENT_STUDENT_STRING_XYZ",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_b.id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["pagination"]["total_items"] == 0
    assert data["pagination"]["total_pages"] == 0
    assert data["pagination"]["has_next"] is False
    assert data["pagination"]["has_prev"] is False


def test_student_listing_cannot_expose_another_centers_records(
    student_client, test_centers, test_users
):
    """Ensures students in Center A are never visible when querying Center B."""
    center_a = test_centers["center_a"]
    center_b = test_centers["center_b"]
    admin_token = test_users["super_admin_token"]

    # Register student in Center B
    student_b_num = f"STU-CENB-{uuid.uuid4().hex[:6]}"
    student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(center_b.id)},
        json={
            "student_id_number": student_b_num,
            "center_id": str(center_b.id),
            "first_name": "Arthur",
            "last_name": "Curry",
            "date_of_birth": "2015-11-20",
            "gender": "Male",
            "guardian_name": "Thomas Curry",
            "guardian_phone": "+1-555-0333",
        },
    )

    # Query Center A with Teacher A credentials
    teacher_token = test_users["teacher_token"]
    response = student_client.get(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {teacher_token}", "X-Center-ID": str(center_a.id)},
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item["student_id_number"] != student_b_num
        assert item["current_center_id"] == str(center_a.id)


def test_student_listing_mismatched_center_query_param(student_client, test_centers, test_users):
    """Query parameter center_id mismatching X-Center-ID header returns 400 Bad Request."""
    center_a = test_centers["center_a"]
    center_b = test_centers["center_b"]
    token = test_users["teacher_token"]

    response = student_client.get(
        f"/api/v1/students?center_id={center_b.id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
    )
    assert response.status_code == 400
    assert "Query parameter center_id does not match" in response.json()["detail"]


# ==============================================================================
# Student Detail Retrieval Tests (GET /students/{id})
# ==============================================================================

def test_student_retrieval_successful(student_client, test_centers, test_users):
    """Retrieves student details including resolved center_name and active_enrollment."""
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]

    # Create student
    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": f"STU-DET-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_a.id),
            "first_name": "Victor",
            "last_name": "Stone",
            "date_of_birth": "2016-08-10",
            "gender": "Male",
            "guardian_name": "Silas Stone",
            "guardian_phone": "+1-555-0444",
        },
    )
    student_id = res_create.json()["id"]

    # Retrieve student detail
    res_get = student_client.get(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
    )
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["id"] == student_id
    assert data["first_name"] == "Victor"
    assert data["center_name"] == center_a.name
    assert data["active_enrollment"] is not None
    assert data["active_enrollment"]["status"] == "ACTIVE"
    assert data["active_enrollment"]["center_id"] == str(center_a.id)


def test_student_retrieval_nonexistent(student_client, test_centers, test_users):
    """Retrieving a nonexistent student UUID returns 404 Not Found."""
    center_a = test_centers["center_a"]
    token = test_users["teacher_token"]
    random_id = uuid.uuid4()

    response = student_client.get(
        f"/api/v1/students/{random_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
    )
    assert response.status_code == 404
    assert "Student not found" in response.json()["detail"]


def test_student_retrieval_student_from_another_center(student_client, test_centers, test_users):
    """
    Attempting to retrieve a student from another center returns 404 Not Found,
    preventing data leakage across tenant boundaries.
    """
    center_a = test_centers["center_a"]
    center_b = test_centers["center_b"]
    admin_token = test_users["super_admin_token"]
    teacher_token = test_users["teacher_token"]

    # Create student in Center B
    res_b = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(center_b.id)},
        json={
            "student_id_number": f"STU-OTHER-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_b.id),
            "first_name": "Hal",
            "last_name": "Jordan",
            "date_of_birth": "2015-02-20",
            "gender": "Male",
            "guardian_name": "Martin Jordan",
            "guardian_phone": "+1-555-0555",
        },
    )
    student_b_id = res_b.json()["id"]

    # Teacher A queries student B using Center A's context header -> 404 Not Found
    response = student_client.get(
        f"/api/v1/students/{student_b_id}",
        headers={"Authorization": f"Bearer {teacher_token}", "X-Center-ID": str(center_a.id)},
    )
    assert response.status_code == 404
    assert "Student not found" in response.json()["detail"]


# ==============================================================================
# Student Profile Update & OCC Tests (PUT /students/{id})
# ==============================================================================

def test_student_update_successful(student_client, test_centers, test_users, student_db):
    """
    Manager updates student profile submitting valid version 1.
    Verifies: 200 OK, version becomes 2, updated_at updated, AuditLog recorded.
    """
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]

    # Register student (starts at version 1)
    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": f"STU-UPD-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_a.id),
            "first_name": "Wally",
            "last_name": "West",
            "date_of_birth": "2017-01-16",
            "gender": "Male",
            "guardian_name": "Rudolph West",
            "guardian_phone": "+1-555-0666",
        },
    )
    student_id = res_create.json()["id"]
    current_version = res_create.json()["version"]
    assert current_version == 1

    # Update with version 1
    update_payload = {
        "first_name": "Wallace",
        "last_name": "West-Allen",
        "notes": "Fast learner in physics",
        "version": current_version,
    }
    res_update = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json=update_payload,
    )
    assert res_update.status_code == 200
    data = res_update.json()
    assert data["first_name"] == "Wallace"
    assert data["last_name"] == "West-Allen"
    assert data["notes"] == "Fast learner in physics"
    assert data["version"] == 2

    # Verify audit log was recorded for update
    audit = (
        student_db.query(AuditLog)
        .filter(
            AuditLog.resource_id == uuid.UUID(student_id),
            AuditLog.action == "STUDENT_UPDATE",
        )
        .first()
    )
    assert audit is not None
    assert audit.old_values["first_name"] == "Wally"
    assert audit.new_values["first_name"] == "Wallace"


def test_student_update_stale_or_missing_occ_version(student_client, test_centers, test_users):
    """
    Submitting an update with a stale version returns 409 Conflict.
    Submitting an update without version returns 422 Unprocessable Entity.
    """
    center_a = test_centers["center_a"]
    token = test_users["manager_token"]

    # Register student
    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": f"STU-STALE-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_a.id),
            "first_name": "Roy",
            "last_name": "Harper",
            "date_of_birth": "2016-04-10",
            "gender": "Male",
            "guardian_name": "Jim Harper",
            "guardian_phone": "+1-555-0777",
        },
    )
    student_id = res_create.json()["id"]

    # Perform valid update 1: version 1 -> 2
    student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={"notes": "Updated note", "version": 1},
    )

    # Attempt second update using stale version 1 -> 409 Conflict
    res_stale = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={"notes": "Stale update attempt", "version": 1},
    )
    assert res_stale.status_code == 409
    assert "Concurrency conflict" in res_stale.json()["detail"]

    # Attempt update without version field -> 422 Unprocessable Entity
    res_no_ver = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={"notes": "No version field"},
    )
    assert res_no_ver.status_code == 422


def test_student_update_concurrent_protection(student_client, test_centers, test_users):
    """Simulates two concurrent users editing the same student profile at the same time."""
    center_a = test_centers["center_a"]
    admin_token = test_users["super_admin_token"]
    manager_token = test_users["manager_token"]

    # Create student (version = 1)
    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {manager_token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": f"STU-CONCUR-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_a.id),
            "first_name": "Dick",
            "last_name": "Grayson",
            "date_of_birth": "2016-10-24",
            "gender": "Male",
            "guardian_name": "Bruce Wayne",
            "guardian_phone": "+1-555-0888",
        },
    )
    student_id = res_create.json()["id"]

    # User 1 (Admin) updates first with version 1 -> succeeds, version becomes 2
    res_admin = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(center_a.id)},
        json={"guardian_phone": "+1-555-1111", "version": 1},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["version"] == 2

    # User 2 (Manager) attempts update with stale version 1 -> fails with 409 Conflict
    res_manager = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {manager_token}", "X-Center-ID": str(center_a.id)},
        json={"guardian_phone": "+1-555-2222", "version": 1},
    )
    assert res_manager.status_code == 409


def test_student_update_unauthorized_role_teacher(student_client, test_centers, test_users):
    """Teachers cannot update student profiles; returns 403 Forbidden."""
    center_a = test_centers["center_a"]
    manager_token = test_users["manager_token"]
    teacher_token = test_users["teacher_token"]

    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {manager_token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": f"STU-TEACHUPD-{uuid.uuid4().hex[:6]}",
            "center_id": str(center_a.id),
            "first_name": "Donna",
            "last_name": "Troy",
            "date_of_birth": "2017-07-07",
            "gender": "Female",
            "guardian_name": "Rhea",
            "guardian_phone": "+1-555-0999",
        },
    )
    student_id = res_create.json()["id"]

    res_teacher = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {teacher_token}", "X-Center-ID": str(center_a.id)},
        json={"notes": "Teacher note", "version": 1},
    )
    assert res_teacher.status_code == 403


def test_student_update_cannot_overwrite_server_managed_fields(
    student_client, test_centers, test_users
):
    """Verifies that client cannot alter student_id_number, current_center_id, or id via PUT."""
    center_a = test_centers["center_a"]
    center_b = test_centers["center_b"]
    token = test_users["manager_token"]
    orig_number = f"STU-IMMUT-{uuid.uuid4().hex[:6]}"

    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": orig_number,
            "center_id": str(center_a.id),
            "first_name": "Garth",
            "last_name": "Lagoon",
            "date_of_birth": "2016-12-12",
            "gender": "Male",
            "guardian_name": "Atlan",
            "guardian_phone": "+1-555-0123",
        },
    )
    student_id = res_create.json()["id"]

    # Submit PUT with attempted overwrites of immutable fields
    res_update = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {token}", "X-Center-ID": str(center_a.id)},
        json={
            "student_id_number": "STU-HACKED",
            "current_center_id": str(center_b.id),
            "first_name": "Garth Updated",
            "version": 1,
        },
    )
    assert res_update.status_code == 200
    data = res_update.json()
    assert data["student_id_number"] == orig_number  # Remains unchanged
    assert data["current_center_id"] == str(center_a.id)  # Remains Center A
    assert data["first_name"] == "Garth Updated"


def test_super_admin_global_student_access(student_client, test_centers, test_users):
    """Super Admin can manage students across any valid center without user_centers assignment."""
    center_b = test_centers["center_b"]
    admin_token = test_users["super_admin_token"]

    # Super Admin registers student in Center B
    student_b_num = f"STU-GLOB-{uuid.uuid4().hex[:6]}"
    res_create = student_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(center_b.id)},
        json={
            "student_id_number": student_b_num,
            "center_id": str(center_b.id),
            "first_name": "Kara",
            "last_name": "Zor-El",
            "date_of_birth": "2016-09-22",
            "gender": "Female",
            "guardian_name": "Alura Zor-El",
            "guardian_phone": "+1-555-9988",
        },
    )
    assert res_create.status_code == 201
    student_id = res_create.json()["id"]

    # Super Admin retrieves student
    res_get = student_client.get(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(center_b.id)},
    )
    assert res_get.status_code == 200
    assert res_get.json()["first_name"] == "Kara"

    # Super Admin updates student
    res_upd = student_client.put(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(center_b.id)},
        json={"notes": "Supergirl enrolled", "version": 1},
    )
    assert res_upd.status_code == 200
    assert res_upd.json()["version"] == 2

