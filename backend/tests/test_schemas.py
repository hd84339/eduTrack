"""
Comprehensive Unit Tests for EduTrack Pydantic v2 Schemas and Data Validation.
Tests structural validation, required/optional fields, UUIDs, enums, constraints,
update schemas, ORM model serialization, and password hash exclusion.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.models.enums import (
    UserRole,
    UserStatus,
    StudentStatus,
    EnrollmentStatus,
    TransferStatus,
    AttendanceStatus,
    SessionParticipationStatus,
    MasteryLevel,
)
from app.models.user import User
from app.models.center import Center
from app.models.student import Student
from app.models.attendance import AttendanceRecord
from app.models.competency import Competency
from app.models.audit import AuditLog
from app.schemas import (
    PaginationMetadata,
    PaginatedResponse,
    ErrorDetail,
    ErrorBody,
    ErrorResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    CenterCreate,
    CenterUpdate,
    CenterResponse,
    CenterDetailResponse,
    CenterSummary,
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListItemResponse,
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    TransferRequestCreate,
    TransferReviewRequest,
    TransferResponse,
    TransferReviewResponse,
    BulkAttendanceCreate,
    AttendanceItem,
    AttendanceCorrectionRequest,
    AttendanceRecordResponse,
    AttendanceAuditLogResponse,
    CompetencyCreate,
    CompetencyUpdate,
    CompetencyResponse,
    StudentSkillProgressResponse,
    ActivityTemplateCreate,
    ActivityTemplateUpdate,
    ActivityTemplateResponse,
    SessionCreate,
    SessionStudentItem,
    SessionStudentEvaluationItem,
    SessionResponse,
    AuditLogCreate,
    AuditLogResponse,
)


# ==============================================================================
# 1. Common & Pagination Schemas Tests
# ==============================================================================

def test_pagination_metadata_valid():
    meta = PaginationMetadata(
        page=1, size=20, total_items=100, total_pages=5, has_next=True, has_prev=False
    )
    assert meta.page == 1
    assert meta.size == 20
    assert meta.total_items == 100
    assert meta.total_pages == 5


def test_pagination_metadata_invalid():
    with pytest.raises(ValidationError):
        PaginationMetadata(
            page=0, size=20, total_items=10, total_pages=1, has_next=False, has_prev=False
        )
    with pytest.raises(ValidationError):
        PaginationMetadata(
            page=1, size=101, total_items=10, total_pages=1, has_next=False, has_prev=False
        )


def test_paginated_response_generic():
    meta = PaginationMetadata(
        page=1, size=10, total_items=2, total_pages=1, has_next=False, has_prev=False
    )
    resp = PaginatedResponse[str](items=["apple", "banana"], pagination=meta)
    assert len(resp.items) == 2
    assert resp.pagination.total_items == 2


def test_error_envelope():
    err_body = ErrorBody(
        code="VALIDATION_ERROR",
        message="Invalid payload",
        details=[ErrorDetail(field="email", issue="Invalid email syntax")],
        timestamp=datetime.now(timezone.utc),
        request_id="req-1234",
    )
    err_resp = ErrorResponse(error=err_body)
    assert err_resp.error.code == "VALIDATION_ERROR"
    assert err_resp.error.details[0].field == "email"


# ==============================================================================
# 2. User & Auth Schemas Tests
# ==============================================================================

def test_user_create_valid():
    center_id = uuid.uuid4()
    payload = {
        "email": "teacher.jane@edutrack.org",
        "password": "SecurePassword123!",
        "full_name": "Jane Smith",
        "phone_number": "+1-555-0100",
        "role": UserRole.TEACHER,
        "center_ids": [center_id],
    }
    user_in = UserCreate(**payload)
    assert user_in.email == "teacher.jane@edutrack.org"
    assert user_in.full_name == "Jane Smith"
    assert user_in.role == UserRole.TEACHER
    assert user_in.center_ids == [center_id]


def test_user_create_email_normalization():
    payload = {
        "email": "  TEACHER.DOE@EDUTRACK.ORG  ",
        "password": "Password123!",
        "full_name": "John Doe",
        "role": UserRole.TEACHER,
    }
    user_in = UserCreate(**payload)
    assert user_in.email == "teacher.doe@edutrack.org"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="invalid-not-an-email",
            password="Password123!",
            full_name="John Doe",
            role=UserRole.TEACHER,
        )


def test_user_create_short_password():
    with pytest.raises(ValidationError):
        UserCreate(
            email="valid@edutrack.org",
            password="short",
            full_name="John Doe",
            role=UserRole.TEACHER,
        )


def test_user_update_partial():
    update = UserUpdate(full_name="New Name")
    dump = update.model_dump(exclude_unset=True)
    assert dump == {"full_name": "New Name"}
    assert "email" not in dump


def test_user_response_from_orm_excludes_password_hash():
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    user_orm = User(
        id=user_id,
        email="admin@edutrack.org",
        password_hash="$2b$12$securehashthatmustneverbeexposedintheapiresponse",
        full_name="Super Admin",
        phone_number=None,
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    user_resp = UserResponse.model_validate(user_orm)
    assert user_resp.id == user_id
    assert user_resp.email == "admin@edutrack.org"
    assert user_resp.full_name == "Super Admin"
    assert not hasattr(user_resp, "password_hash")
    dump = user_resp.model_dump()
    assert "password_hash" not in dump


# ==============================================================================
# 3. Center Schemas Tests
# ==============================================================================

def test_center_create_valid():
    center_in = CenterCreate(
        code="CEN-WEST-01",
        name="West District Center",
        address="100 West Blvd",
        timezone="America/Los_Angeles",
        contact_phone="+1-555-0200",
        capacity=150,
    )
    assert center_in.code == "CEN-WEST-01"
    assert center_in.capacity == 150


def test_center_create_invalid_capacity():
    with pytest.raises(ValidationError):
        CenterCreate(
            code="CEN-01",
            name="Center",
            address="Address",
            capacity=0,  # must be gt=0
        )
    with pytest.raises(ValidationError):
        CenterCreate(
            code="CEN-01",
            name="Center",
            address="Address",
            capacity=-10,  # must be gt=0
        )


def test_center_response_from_orm():
    c_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    center_orm = Center(
        id=c_id,
        code="CEN-01",
        name="Main Center",
        address="1 Main St",
        timezone="UTC",
        capacity=100,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    resp = CenterResponse.model_validate(center_orm)
    assert resp.id == c_id
    assert resp.code == "CEN-01"


# ==============================================================================
# 4. Student Schemas Tests
# ==============================================================================

def test_student_create_valid():
    center_id = uuid.uuid4()
    student_in = StudentCreate(
        student_id_number="STU-2026-0001",
        center_id=center_id,
        first_name="Alice",
        last_name="Wonderland",
        date_of_birth=date(2018, 4, 15),
        gender="Female",
        guardian_name="Queen Wonderland",
        guardian_phone="+1-555-0300",
        guardian_email="queen@example.com",
    )
    assert student_in.student_id_number == "STU-2026-0001"
    assert student_in.center_id == center_id
    assert student_in.first_name == "Alice"


def test_student_update_requires_version():
    with pytest.raises(ValidationError):
        StudentUpdate(first_name="Alice Updated")  # missing required version tag


def test_student_update_valid_with_version():
    up = StudentUpdate(first_name="Alice Updated", version=1)
    assert up.first_name == "Alice Updated"
    assert up.version == 1


def test_student_response_from_orm():
    s_id = uuid.uuid4()
    c_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    student_orm = Student(
        id=s_id,
        student_id_number="STU-001",
        current_center_id=c_id,
        first_name="Bob",
        last_name="Builder",
        date_of_birth=date(2017, 1, 1),
        gender="Male",
        guardian_name="Parent Builder",
        guardian_phone="+1-555-0301",
        guardian_relationship="Parent",
        status=StudentStatus.ACTIVE,
        version=1,
        created_at=now,
        updated_at=now,
    )
    resp = StudentResponse.model_validate(student_orm)
    assert resp.id == s_id
    assert resp.student_id_number == "STU-001"
    assert resp.version == 1


# ==============================================================================
# 5. Enrollment Schemas Tests
# ==============================================================================

def test_enrollment_create_date_validation():
    s_id = uuid.uuid4()
    c_id = uuid.uuid4()
    # Invalid: end_date < start_date
    with pytest.raises(ValidationError):
        EnrollmentCreate(
            student_id=s_id,
            center_id=c_id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 5, 1),
        )

    # Valid: end_date >= start_date
    valid = EnrollmentCreate(
        student_id=s_id,
        center_id=c_id,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 1),
    )
    assert valid.start_date == valid.end_date


# ==============================================================================
# 6. Transfer Schemas Tests
# ==============================================================================

def test_transfer_review_capacity_override_validation():
    # Invalid: capacity_override=True but capacity_override_reason is None
    with pytest.raises(ValidationError):
        TransferReviewRequest(
            action="APPROVE",
            capacity_override=True,
            capacity_override_reason=None,
        )

    # Valid: capacity_override=True with mandatory reason provided
    req = TransferReviewRequest(
        action="APPROVE",
        capacity_override=True,
        capacity_override_reason="Super Admin special enrollment permission granted",
    )
    assert req.capacity_override is True
    assert req.capacity_override_reason is not None


# ==============================================================================
# 7. Attendance Schemas Tests
# ==============================================================================

def test_bulk_attendance_create_valid():
    c_id = uuid.uuid4()
    s_id = uuid.uuid4()
    payload = BulkAttendanceCreate(
        center_id=c_id,
        attendance_date=date(2026, 11, 15),
        records=[
            AttendanceItem(student_id=s_id, status=AttendanceStatus.PRESENT)
        ],
    )
    assert len(payload.records) == 1
    assert payload.records[0].status == AttendanceStatus.PRESENT


def test_bulk_attendance_empty_records_fails():
    with pytest.raises(ValidationError):
        BulkAttendanceCreate(
            center_id=uuid.uuid4(),
            attendance_date=date(2026, 11, 15),
            records=[],  # min_length=1
        )


def test_attendance_correction_requires_version_and_reason():
    with pytest.raises(ValidationError):
        # Missing reason
        AttendanceCorrectionRequest(status=AttendanceStatus.PRESENT, version=1)

    with pytest.raises(ValidationError):
        # Missing version
        AttendanceCorrectionRequest(
            status=AttendanceStatus.PRESENT, reason="Was present"
        )


def test_attendance_record_response_from_orm():
    a_id = uuid.uuid4()
    s_id = uuid.uuid4()
    c_id = uuid.uuid4()
    u_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    att_orm = AttendanceRecord(
        id=a_id,
        student_id=s_id,
        center_id=c_id,
        recorded_by_user_id=u_id,
        attendance_date=date(2026, 11, 15),
        status=AttendanceStatus.PRESENT,
        remarks="On time",
        version=1,
        created_at=now,
        updated_at=now,
    )
    resp = AttendanceRecordResponse.model_validate(att_orm)
    assert resp.id == a_id
    assert resp.status == AttendanceStatus.PRESENT
    assert resp.version == 1


# ==============================================================================
# 8. Competency & Activity Schemas Tests
# ==============================================================================

def test_competency_create_valid():
    comp = CompetencyCreate(
        code="MATH-FRAC-01",
        name="Identifies Unit Fractions",
        domain="Mathematics",
        description="Explores 1/2, 1/4, 1/8",
    )
    assert comp.code == "MATH-FRAC-01"


def test_activity_template_age_validation():
    # Invalid: target_age_max < target_age_min
    with pytest.raises(ValidationError):
        ActivityTemplateCreate(
            title="Activity",
            subject_area="Math",
            description="Desc",
            target_age_min=10,
            target_age_max=5,
        )

    # Invalid: duration < 5
    with pytest.raises(ValidationError):
        ActivityTemplateCreate(
            title="Activity",
            subject_area="Math",
            description="Desc",
            target_age_min=5,
            target_age_max=10,
            duration_minutes=2,
        )


# ==============================================================================
# 9. Learning Session Schemas Tests
# ==============================================================================

def test_session_time_interval_validation():
    now = datetime.now(timezone.utc)
    earlier = datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc)
    later = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)

    # Invalid: end_time < start_time
    with pytest.raises(ValidationError):
        SessionCreate(
            center_id=uuid.uuid4(),
            activity_template_id=uuid.uuid4(),
            session_date=date(2026, 11, 15),
            start_time=later,
            end_time=earlier,
            topic_summary="Introduction",
        )


def test_session_student_absent_score_validation():
    # Invalid: status=ABSENT but score is provided
    with pytest.raises(ValidationError):
        SessionStudentItem(
            student_id=uuid.uuid4(),
            participation_status=SessionParticipationStatus.ABSENT,
            score=Decimal("85.0"),
        )

    # Valid: status=ABSENT and score is None
    item = SessionStudentItem(
        student_id=uuid.uuid4(),
        participation_status=SessionParticipationStatus.ABSENT,
        score=None,
    )
    assert item.participation_status == SessionParticipationStatus.ABSENT
    assert item.score is None


def test_session_student_score_bounds():
    # Invalid: score > 100
    with pytest.raises(ValidationError):
        SessionStudentItem(
            student_id=uuid.uuid4(),
            participation_status=SessionParticipationStatus.COMPLETED,
            score=Decimal("105.0"),
        )

    # Invalid: score < 0
    with pytest.raises(ValidationError):
        SessionStudentItem(
            student_id=uuid.uuid4(),
            participation_status=SessionParticipationStatus.COMPLETED,
            score=Decimal("-5.0"),
        )


# ==============================================================================
# 10. Audit Log Schemas Tests
# ==============================================================================

def test_audit_log_create_valid():
    audit_in = AuditLogCreate(
        user_id=uuid.uuid4(),
        action="UPDATE",
        resource_type="STUDENT",
        resource_id=uuid.uuid4(),
        client_ip="192.168.1.1",
        old_values={"status": "ACTIVE"},
        new_values={"status": "TRANSFERRED"},
    )
    assert audit_in.action == "UPDATE"
    assert audit_in.old_values["status"] == "ACTIVE"


def test_audit_log_response_from_orm():
    a_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    audit_orm = AuditLog(
        id=a_id,
        user_id=u_id,
        action="CREATE",
        resource_type="ATTENDANCE",
        resource_id=r_id,
        client_ip="127.0.0.1",
        old_values=None,
        new_values={"status": "PRESENT"},
        created_at=now,
    )
    resp = AuditLogResponse.model_validate(audit_orm)
    assert resp.id == a_id
    assert resp.action == "CREATE"
    assert resp.resource_type == "ATTENDANCE"
    assert resp.new_values == {"status": "PRESENT"}

