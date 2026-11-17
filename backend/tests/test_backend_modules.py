"""
Comprehensive Backend Integration Tests.
Validates Centers, Users/Staff, Transfers, Attendance, Competencies, Activities,
Learning Sessions, Progress, Analytics, Reports, and Audit Logging.
"""
import uuid
from datetime import date, datetime, timedelta
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    ActivityCompetency,
    ActivityTemplate,
    AttendanceAuditLog,
    AttendanceRecord,
    AuditLog,
    Center,
    Competency,
    EnrollmentRecord,
    LearningSession,
    SessionStudent,
    SessionStudentEvaluation,
    Student,
    StudentSkillProgress,
    TransferRequest,
    User,
    UserCenter,
    AttendanceStatus,
    EnrollmentStatus,
    MasteryLevel,
    SessionParticipationStatus,
    StudentStatus,
    TransferStatus,
    UserRole,
    UserStatus,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest.fixture(scope="module")
def full_test_engine():
    """Module-scoped in-memory SQLite engine with all 16 tables created."""
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
    TransferRequest.__table__.create(bind=engine)
    AttendanceRecord.__table__.create(bind=engine)
    AttendanceAuditLog.__table__.create(bind=engine)
    Competency.__table__.create(bind=engine)
    ActivityTemplate.__table__.create(bind=engine)
    ActivityCompetency.__table__.create(bind=engine)
    LearningSession.__table__.create(bind=engine)
    SessionStudent.__table__.create(bind=engine)
    SessionStudentEvaluation.__table__.create(bind=engine)
    StudentSkillProgress.__table__.create(bind=engine)
    AuditLog.__table__.create(bind=engine)

    yield engine

    AuditLog.__table__.drop(bind=engine)
    StudentSkillProgress.__table__.drop(bind=engine)
    SessionStudentEvaluation.__table__.drop(bind=engine)
    SessionStudent.__table__.drop(bind=engine)
    LearningSession.__table__.drop(bind=engine)
    ActivityCompetency.__table__.drop(bind=engine)
    ActivityTemplate.__table__.drop(bind=engine)
    Competency.__table__.drop(bind=engine)
    AttendanceAuditLog.__table__.drop(bind=engine)
    AttendanceRecord.__table__.drop(bind=engine)
    TransferRequest.__table__.drop(bind=engine)
    EnrollmentRecord.__table__.drop(bind=engine)
    Student.__table__.drop(bind=engine)
    UserCenter.__table__.drop(bind=engine)
    User.__table__.drop(bind=engine)
    Center.__table__.drop(bind=engine)


@pytest.fixture(scope="module")
def full_session_factory(full_test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=full_test_engine)


@pytest.fixture
def full_db(full_session_factory) -> Generator[Session, None, None]:
    session = full_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def full_client(full_session_factory) -> Generator[TestClient, None, None]:
    def override_get_db():
        session = full_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def seed_data(full_db: Session):
    """Provisions sample centers, users, competencies, and students."""
    # Centers
    c1 = full_db.query(Center).filter(Center.code == "MOD-CEN-01").first()
    if not c1:
        c1 = Center(
            id=uuid.uuid4(),
            code="MOD-CEN-01",
            name="Main Downtown Center",
            address="100 Main St",
            timezone="UTC",
            contact_phone="555-0100",
            contact_email="main@edutrack.org",
            capacity=10,
            is_active=True,
        )
        full_db.add(c1)

    c2 = full_db.query(Center).filter(Center.code == "MOD-CEN-02").first()
    if not c2:
        c2 = Center(
            id=uuid.uuid4(),
            code="MOD-CEN-02",
            name="Uptown Branch",
            address="200 Uptown Ave",
            timezone="UTC",
            contact_phone="555-0200",
            contact_email="uptown@edutrack.org",
            capacity=2,  # Low capacity for capacity testing
            is_active=True,
        )
        full_db.add(c2)

    full_db.flush()

    # Users
    admin = full_db.query(User).filter(User.email == "admin.mod@edutrack.org").first()
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            email="admin.mod@edutrack.org",
            password_hash=hash_password("Admin123!"),
            full_name="Admin Module User",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
        )
        full_db.add(admin)

    manager = full_db.query(User).filter(User.email == "manager.mod1@edutrack.org").first()
    if not manager:
        manager = User(
            id=uuid.uuid4(),
            email="manager.mod1@edutrack.org",
            password_hash=hash_password("Manager123!"),
            full_name="Manager Center 1",
            role=UserRole.CENTER_MANAGER,
            status=UserStatus.ACTIVE,
        )
        full_db.add(manager)
        full_db.flush()
        full_db.add(UserCenter(user_id=manager.id, center_id=c1.id))

    manager2 = full_db.query(User).filter(User.email == "manager.mod2@edutrack.org").first()
    if not manager2:
        manager2 = User(
            id=uuid.uuid4(),
            email="manager.mod2@edutrack.org",
            password_hash=hash_password("Manager123!"),
            full_name="Manager Center 2",
            role=UserRole.CENTER_MANAGER,
            status=UserStatus.ACTIVE,
        )
        full_db.add(manager2)
        full_db.flush()
        full_db.add(UserCenter(user_id=manager2.id, center_id=c2.id))

    teacher = full_db.query(User).filter(User.email == "teacher.mod1@edutrack.org").first()
    if not teacher:
        teacher = User(
            id=uuid.uuid4(),
            email="teacher.mod1@edutrack.org",
            password_hash=hash_password("Teacher123!"),
            full_name="Teacher Center 1",
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE,
        )
        full_db.add(teacher)
        full_db.flush()
        full_db.add(UserCenter(user_id=teacher.id, center_id=c1.id))

    # Competency
    comp = full_db.query(Competency).filter(Competency.code == "MOD-MATH-01").first()
    if not comp:
        comp = Competency(
            id=uuid.uuid4(),
            code="MOD-MATH-01",
            name="Single Digit Addition",
            domain="Mathematics",
            description="Adds numbers up to 10",
        )
        full_db.add(comp)

    # Activity Template
    tmpl = full_db.query(ActivityTemplate).filter(ActivityTemplate.title == "Math Tiles Workshop").first()
    if not tmpl:
        tmpl = ActivityTemplate(
            id=uuid.uuid4(),
            center_id=c1.id,
            created_by_user_id=admin.id,
            title="Math Tiles Workshop",
            subject_area="Mathematics",
            description="Hands on addition with colored tiles",
            target_age_min=5,
            target_age_max=8,
            duration_minutes=45,
            is_global=True,
            is_active=True,
        )
        full_db.add(tmpl)
        full_db.flush()
        full_db.add(ActivityCompetency(activity_template_id=tmpl.id, competency_id=comp.id, is_primary=True))

    full_db.commit()
    full_db.refresh(c1)
    full_db.refresh(c2)
    full_db.refresh(admin)
    full_db.refresh(manager)
    full_db.refresh(manager2)
    full_db.refresh(teacher)
    full_db.refresh(comp)
    full_db.refresh(tmpl)

    return {
        "center_1": c1,
        "center_2": c2,
        "admin": admin,
        "admin_token": create_access_token(admin.id),
        "manager_1": manager,
        "manager_1_token": create_access_token(manager.id),
        "manager_2": manager2,
        "manager_2_token": create_access_token(manager2.id),
        "teacher_1": teacher,
        "teacher_1_token": create_access_token(teacher.id),
        "competency": comp,
        "template": tmpl,
    }


# ==============================================================================
# Center API Tests
# ==============================================================================

def test_center_crud(full_client, seed_data):
    admin_token = seed_data["admin_token"]
    c_code = f"NEW-CEN-{uuid.uuid4().hex[:4].upper()}"

    # 1. Create center
    res = full_client.post(
        "/api/v1/centers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": c_code,
            "name": "Eastside Hub",
            "address": "500 East Rd",
            "timezone": "America/New_York",
            "capacity": 50,
        },
    )
    assert res.status_code == 201
    cid = res.json()["id"]

    # 2. Duplicate code -> 409
    res_dup = full_client.post(
        "/api/v1/centers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": c_code,
            "name": "Duplicate Eastside",
            "address": "500 East Rd",
            "capacity": 50,
        },
    )
    assert res_dup.status_code == 409

    # 3. Get center details with occupancy
    res_get = full_client.get(
        f"/api/v1/centers/{cid}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["current_occupancy"] == 0

    # 4. Update center
    res_upd = full_client.put(
        f"/api/v1/centers/{cid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Eastside Innovation Hub", "capacity": 60},
    )
    assert res_upd.status_code == 200
    assert res_upd.json()["name"] == "Eastside Innovation Hub"
    assert res_upd.json()["capacity"] == 60


# ==============================================================================
# Users & Staff API Tests
# ==============================================================================

def test_user_management(full_client, seed_data):
    admin_token = seed_data["admin_token"]
    c1 = seed_data["center_1"]
    u_email = f"staff_{uuid.uuid4().hex[:6]}@edutrack.org"

    # 1. Create staff user
    res = full_client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": u_email,
            "password": "InitialPassword123!",
            "full_name": "New Teacher Roberts",
            "role": "TEACHER",
            "center_ids": [str(c1.id)],
        },
    )
    assert res.status_code == 201
    uid = res.json()["id"]
    assert res.json()["role"] == "TEACHER"
    assert "password_hash" not in res.json()

    # 2. List users
    res_list = full_client.get(
        "/api/v1/users?role=TEACHER",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_list.status_code == 200
    assert any(u["id"] == uid for u in res_list.json()["items"])

    # 3. Manager cannot create another Admin
    mgr_token = seed_data["manager_1_token"]
    res_hacker = full_client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={
            "email": f"hacker_{uuid.uuid4().hex[:6]}@edutrack.org",
            "password": "Password123!",
            "full_name": "Privilege Escalation",
            "role": "SUPER_ADMIN",
            "center_ids": [str(c1.id)],
        },
    )
    assert res_hacker.status_code == 403


# ==============================================================================
# Enrollment & Student Transfers API Tests
# ==============================================================================

def test_student_transfers_workflow(full_client, seed_data):
    admin_token = seed_data["admin_token"]
    mgr1_token = seed_data["manager_1_token"]
    mgr2_token = seed_data["manager_2_token"]
    c1 = seed_data["center_1"]
    c2 = seed_data["center_2"]

    # Register student in Center 1
    res_st = full_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {mgr1_token}", "X-Center-ID": str(c1.id)},
        json={
            "student_id_number": f"TR-STU-{uuid.uuid4().hex[:6]}",
            "center_id": str(c1.id),
            "first_name": "Miles",
            "last_name": "Morales",
            "date_of_birth": "2017-05-15",
            "gender": "Male",
            "guardian_name": "Rio Morales",
            "guardian_phone": "555-0911",
        },
    )
    assert res_st.status_code == 201
    student_id = res_st.json()["id"]

    # 1. Initiate transfer to Center 2
    res_tr = full_client.post(
        "/api/v1/transfers",
        headers={"Authorization": f"Bearer {mgr1_token}"},
        json={
            "student_id": student_id,
            "to_center_id": str(c2.id),
            "effective_date": date.today().isoformat(),
            "request_reason": "Relocated to uptown district",
        },
    )
    assert res_tr.status_code == 201
    transfer_id = res_tr.json()["id"]
    assert res_tr.json()["status"] == "PENDING"

    # 2. Cannot transfer to same center
    res_same = full_client.post(
        "/api/v1/transfers",
        headers={"Authorization": f"Bearer {mgr1_token}"},
        json={
            "student_id": student_id,
            "to_center_id": str(c1.id),
            "effective_date": date.today().isoformat(),
            "request_reason": "Same center error",
        },
    )
    assert res_same.status_code == 400

    # 3. List transfers
    res_list = full_client.get(
        "/api/v1/transfers?status=PENDING",
        headers={"Authorization": f"Bearer {mgr2_token}"},
    )
    assert res_list.status_code == 200
    assert any(t["id"] == transfer_id for t in res_list.json()["items"])

    # 4. Review transfer (Approve) by Destination Manager
    res_review = full_client.post(
        f"/api/v1/transfers/{transfer_id}/review",
        headers={"Authorization": f"Bearer {mgr2_token}"},
        json={
            "action": "APPROVE",
            "review_notes": "Welcome to Uptown branch!",
            "capacity_override": False,
        },
    )
    assert res_review.status_code == 200
    review_data = res_review.json()
    assert review_data["status"] == "APPROVED"
    assert review_data["closed_enrollment_id"] is not None
    assert review_data["new_enrollment_id"] is not None

    # Verify student current_center_id is now Center 2
    res_student = full_client.get(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}", "X-Center-ID": str(c2.id)},
    )
    assert res_student.status_code == 200
    assert res_student.json()["current_center_id"] == str(c2.id)


# ==============================================================================
# Attendance API Tests
# ==============================================================================

def test_attendance_operations(full_client, seed_data):
    mgr_token = seed_data["manager_1_token"]
    c1 = seed_data["center_1"]
    today = date.today()

    # Create student
    res_st = full_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
        json={
            "student_id_number": f"ATT-STU-{uuid.uuid4().hex[:6]}",
            "center_id": str(c1.id),
            "first_name": "Kamala",
            "last_name": "Khan",
            "date_of_birth": "2016-08-20",
            "gender": "Female",
            "guardian_name": "Muneeba Khan",
            "guardian_phone": "555-0811",
        },
    )
    assert res_st.status_code == 201
    student_id = res_st.json()["id"]

    # 1. Record bulk daily attendance
    res_att = full_client.post(
        "/api/v1/attendance/bulk",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
        json={
            "center_id": str(c1.id),
            "attendance_date": today.isoformat(),
            "records": [
                {
                    "student_id": student_id,
                    "status": "PRESENT",
                    "remarks": "On time and engaged",
                }
            ],
        },
    )
    assert res_att.status_code == 201
    assert res_att.json()["processed_count"] == 1

    # 2. Reject duplicate daily attendance
    res_dup = full_client.post(
        "/api/v1/attendance/bulk",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
        json={
            "center_id": str(c1.id),
            "attendance_date": today.isoformat(),
            "records": [{"student_id": student_id, "status": "LATE"}],
        },
    )
    assert res_dup.status_code == 409

    # 3. Reject future date attendance
    future_date = today + timedelta(days=2)
    res_fut = full_client.post(
        "/api/v1/attendance/bulk",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
        json={
            "center_id": str(c1.id),
            "attendance_date": future_date.isoformat(),
            "records": [{"student_id": student_id, "status": "PRESENT"}],
        },
    )
    assert res_fut.status_code == 422

    # 4. Query daily attendance roster
    res_roster = full_client.get(
        f"/api/v1/attendance?date={today.isoformat()}",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
    )
    assert res_roster.status_code == 200
    roster = res_roster.json()
    assert len(roster) >= 1
    target_rec = next(r for r in roster if r["student_id"] == student_id)
    att_id = target_rec["id"]

    # 5. Correct attendance record (OCC version: 1 -> 2)
    res_corr = full_client.put(
        f"/api/v1/attendance/{att_id}",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
        json={
            "status": "LATE",
            "reason": "Correcting: Student arrived 15 minutes late due to traffic",
            "remarks": "Traffic delay",
            "version": 1,
        },
    )
    assert res_corr.status_code == 200
    assert res_corr.json()["status"] == "LATE"
    assert res_corr.json()["version"] == 2


# ==============================================================================
# Competency Catalog & Progress API Tests
# ==============================================================================

def test_competency_and_progress(full_client, seed_data):
    admin_token = seed_data["admin_token"]
    comp_code = f"COMP-{uuid.uuid4().hex[:6].upper()}"

    # 1. Create competency
    res_comp = full_client.post(
        "/api/v1/competencies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": comp_code,
            "name": "Fraction Identification",
            "domain": "Mathematics",
            "description": "Identifies 1/2, 1/4 and 3/4 fractions visually",
        },
    )
    assert res_comp.status_code == 201

    # 2. List competencies
    res_list = full_client.get(
        "/api/v1/competencies?domain=Mathematics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_list.status_code == 200
    assert any(c["code"] == comp_code for c in res_list.json()["items"])


# ==============================================================================
# Learning Sessions API Tests
# ==============================================================================

def test_learning_session_lifecycle(full_client, seed_data):
    mgr_token = seed_data["manager_1_token"]
    teacher_token = seed_data["teacher_1_token"]
    c1 = seed_data["center_1"]
    tmpl = seed_data["template"]
    comp = seed_data["competency"]
    today = date.today()

    # Create student
    res_st = full_client.post(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {mgr_token}", "X-Center-ID": str(c1.id)},
        json={
            "student_id_number": f"SES-STU-{uuid.uuid4().hex[:6]}",
            "center_id": str(c1.id),
            "first_name": "Peter",
            "last_name": "Parker",
            "date_of_birth": "2016-08-10",
            "gender": "Male",
            "guardian_name": "May Parker",
            "guardian_phone": "555-0919",
        },
    )
    student_id = res_st.json()["id"]

    start_time = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=45)

    # Log session with student competency evaluation
    res_ses = full_client.post(
        "/api/v1/sessions",
        headers={"Authorization": f"Bearer {teacher_token}", "X-Center-ID": str(c1.id)},
        json={
            "center_id": str(c1.id),
            "activity_template_id": str(tmpl.id),
            "session_date": today.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "topic_summary": "Introduction to Unit Fractions",
            "general_notes": "Student actively built all models.",
            "students": [
                {
                    "student_id": student_id,
                    "participation_status": "COMPLETED",
                    "qualitative_feedback": "Demonstrated quick grasp of fraction tiles",
                    "score": 95.0,
                    "evaluations": [
                        {
                            "competency_id": str(comp.id),
                            "mastery_level": "PROFICIENT",
                            "teacher_notes": "Mastered unit fractions independently",
                        }
                    ],
                }
            ],
        },
    )
    assert res_ses.status_code == 201
    ses_id = res_ses.json()["id"]

    # Retrieve session details
    res_get = full_client.get(
        f"/api/v1/sessions/{ses_id}",
        headers={"Authorization": f"Bearer {teacher_token}", "X-Center-ID": str(c1.id)},
    )
    assert res_get.status_code == 200
    assert len(res_get.json()["student_roster"]) == 1

    # Verify student skill progress was updated
    res_prog = full_client.get(
        f"/api/v1/progress/students/{student_id}",
        headers={"Authorization": f"Bearer {teacher_token}", "X-Center-ID": str(c1.id)},
    )
    assert res_prog.status_code == 200
    prog_data = res_prog.json()
    assert len(prog_data["competencies"]) == 1
    assert prog_data["competencies"][0]["current_level"] == "PROFICIENT"
    assert prog_data["competencies"][0]["total_sessions_count"] == 1


# ==============================================================================
# Analytics, Reports & Audit API Tests
# ==============================================================================

def test_analytics_reports_and_audit(full_client, seed_data):
    admin_token = seed_data["admin_token"]
    mgr_token = seed_data["manager_1_token"]
    c1 = seed_data["center_1"]

    # 1. Super Admin Overview Analytics
    res_ov = full_client.get(
        "/api/v1/analytics/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_ov.status_code == 200
    assert "total_centers" in res_ov.json()
    assert "total_active_students" in res_ov.json()

    # 2. Center Analytics
    res_ca = full_client.get(
        f"/api/v1/analytics/centers/{c1.id}",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert res_ca.status_code == 200
    assert res_ca.json()["center_id"] == str(c1.id)
    assert "capacity_occupancy_percentage" in res_ca.json()

    # 3. Attendance Report JSON & CSV
    today = date.today()
    res_rep = full_client.get(
        f"/api/v1/reports/attendance?center_id={c1.id}&start_date={today.isoformat()}&end_date={today.isoformat()}&format=json",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert res_rep.status_code == 200
    assert "rows" in res_rep.json()

    res_csv = full_client.get(
        f"/api/v1/reports/attendance?center_id={c1.id}&start_date={today.isoformat()}&end_date={today.isoformat()}&format=csv",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert res_csv.status_code == 200
    assert "attendance_date,center_name" in res_csv.text

    # 4. System Audit Logs
    res_audit = full_client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_audit.status_code == 200
    assert "items" in res_audit.json()
    assert len(res_audit.json()["items"]) >= 1
