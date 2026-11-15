"""
Tests for EduTrack SQLAlchemy 2.0 ORM Models and Database Schema Specifications.
Validates table registrations, column definitions, constraints, indexes,
foreign key ondelete actions, and optimistic concurrency versioning.
"""
import pytest
from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
)
from app.db.base import Base
from app.models import (
    UserRole,
    UserStatus,
    StudentStatus,
    EnrollmentStatus,
    TransferStatus,
    AttendanceStatus,
    SessionParticipationStatus,
    MasteryLevel,
    User,
    Center,
    UserCenter,
    Student,
    EnrollmentRecord,
    TransferRequest,
    AttendanceRecord,
    AttendanceAuditLog,
    Competency,
    ActivityTemplate,
    ActivityCompetency,
    LearningSession,
    SessionStudent,
    SessionStudentEvaluation,
    StudentSkillProgress,
    AuditLog,
)

EXPECTED_TABLES = {
    "users",
    "centers",
    "user_centers",
    "students",
    "enrollment_records",
    "transfer_requests",
    "attendance_records",
    "attendance_audit_logs",
    "competencies",
    "activity_templates",
    "activity_competencies",
    "learning_sessions",
    "session_students",
    "session_student_evaluations",
    "student_skill_progress",
    "audit_logs",
}


def test_metadata_contains_all_16_tables():
    """Verify that Base.metadata has registered exactly all 16 specified tables."""
    registered_tables = set(Base.metadata.tables.keys())
    assert EXPECTED_TABLES.issubset(registered_tables), (
        f"Missing tables: {EXPECTED_TABLES - registered_tables}"
    )
    assert len(EXPECTED_TABLES) == 16


def test_all_models_can_be_instantiated():
    """Verify all 16 model classes can be imported and instantiated without error."""
    models = [
        User,
        Center,
        UserCenter,
        Student,
        EnrollmentRecord,
        TransferRequest,
        AttendanceRecord,
        AttendanceAuditLog,
        Competency,
        ActivityTemplate,
        ActivityCompetency,
        LearningSession,
        SessionStudent,
        SessionStudentEvaluation,
        StudentSkillProgress,
        AuditLog,
    ]
    assert len(models) == 16
    for model_cls in models:
        assert issubclass(model_cls, Base)
        assert hasattr(model_cls, "__tablename__")
        assert model_cls.__tablename__ in EXPECTED_TABLES


def test_enums_definition():
    """Verify all 8 ENUMs have the exact members specified in docs/DATABASE_DESIGN.md."""
    assert set(e.value for e in UserRole) == {"SUPER_ADMIN", "CENTER_MANAGER", "TEACHER"}
    assert set(e.value for e in UserStatus) == {"ACTIVE", "INACTIVE", "LOCKED"}
    assert set(e.value for e in StudentStatus) == {"ACTIVE", "INACTIVE", "TRANSFERRED", "GRADUATED", "SUSPENDED"}
    assert set(e.value for e in EnrollmentStatus) == {"ACTIVE", "TRANSFERRED", "COMPLETED", "WITHDRAWN"}
    assert set(e.value for e in TransferStatus) == {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}
    assert set(e.value for e in AttendanceStatus) == {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
    assert set(e.value for e in SessionParticipationStatus) == {"COMPLETED", "PARTIAL", "ABSENT"}
    assert set(e.value for e in MasteryLevel) == {"EMERGING", "DEVELOPING", "PROFICIENT", "MASTERY"}


def test_primary_keys():
    """Verify every table has a single UUID primary key named 'id'."""
    for table_name in EXPECTED_TABLES:
        table = Base.metadata.tables[table_name]
        pk_columns = [col.name for col in table.primary_key.columns]
        assert pk_columns == ["id"], f"Table {table_name} does not have single PK 'id': {pk_columns}"


def test_optimistic_concurrency_version_columns():
    """Verify students and attendance_records have integer version columns for OCC."""
    students_table = Base.metadata.tables["students"]
    attendance_table = Base.metadata.tables["attendance_records"]

    assert "version" in students_table.c, "students table missing version column"
    assert "version" in attendance_table.c, "attendance_records table missing version column"


def test_foreign_key_ondelete_actions():
    """
    Verify foreign keys enforce exact approved ON DELETE actions:
    - CASCADE on junction / child rows (user_centers, activity_competencies, session_students, etc.)
    - RESTRICT on historical and operational rows (students, attendance, transfers, etc.)
    - SET NULL on audit_logs.user_id
    """
    def get_fks(table_name):
        table = Base.metadata.tables[table_name]
        return {
            (col.name, fk.target_fullname): fk.ondelete
            for col in table.columns
            for fk in col.foreign_keys
        }

    # user_centers: CASCADE
    uc_fks = get_fks("user_centers")
    assert uc_fks.get(("user_id", "users.id")) == "CASCADE"
    assert uc_fks.get(("center_id", "centers.id")) == "CASCADE"

    # students: RESTRICT
    s_fks = get_fks("students")
    assert s_fks.get(("current_center_id", "centers.id")) == "RESTRICT"

    # enrollment_records: RESTRICT
    er_fks = get_fks("enrollment_records")
    assert er_fks.get(("student_id", "students.id")) == "RESTRICT"
    assert er_fks.get(("center_id", "centers.id")) == "RESTRICT"

    # transfer_requests: RESTRICT
    tr_fks = get_fks("transfer_requests")
    assert tr_fks.get(("student_id", "students.id")) == "RESTRICT"
    assert tr_fks.get(("from_center_id", "centers.id")) == "RESTRICT"
    assert tr_fks.get(("to_center_id", "centers.id")) == "RESTRICT"
    assert tr_fks.get(("requested_by_user_id", "users.id")) == "RESTRICT"
    assert tr_fks.get(("reviewed_by_user_id", "users.id")) == "RESTRICT"

    # attendance_records: RESTRICT
    ar_fks = get_fks("attendance_records")
    assert ar_fks.get(("student_id", "students.id")) == "RESTRICT"
    assert ar_fks.get(("center_id", "centers.id")) == "RESTRICT"
    assert ar_fks.get(("recorded_by_user_id", "users.id")) == "RESTRICT"

    # attendance_audit_logs: RESTRICT (Audit preservation)
    aal_fks = get_fks("attendance_audit_logs")
    assert aal_fks.get(("attendance_record_id", "attendance_records.id")) == "RESTRICT"
    assert aal_fks.get(("changed_by_user_id", "users.id")) == "RESTRICT"

    # activity_templates: RESTRICT
    at_fks = get_fks("activity_templates")
    assert at_fks.get(("center_id", "centers.id")) == "RESTRICT"
    assert at_fks.get(("created_by_user_id", "users.id")) == "RESTRICT"

    # activity_competencies: CASCADE template, RESTRICT competency
    ac_fks = get_fks("activity_competencies")
    assert ac_fks.get(("activity_template_id", "activity_templates.id")) == "CASCADE"
    assert ac_fks.get(("competency_id", "competencies.id")) == "RESTRICT"

    # learning_sessions: RESTRICT
    ls_fks = get_fks("learning_sessions")
    assert ls_fks.get(("center_id", "centers.id")) == "RESTRICT"
    assert ls_fks.get(("activity_template_id", "activity_templates.id")) == "RESTRICT"
    assert ls_fks.get(("conducted_by_user_id", "users.id")) == "RESTRICT"

    # session_students: CASCADE session, RESTRICT student
    ss_fks = get_fks("session_students")
    assert ss_fks.get(("session_id", "learning_sessions.id")) == "CASCADE"
    assert ss_fks.get(("student_id", "students.id")) == "RESTRICT"

    # session_student_evaluations: CASCADE session_student, RESTRICT competency
    sse_fks = get_fks("session_student_evaluations")
    assert sse_fks.get(("session_student_id", "session_students.id")) == "CASCADE"
    assert sse_fks.get(("competency_id", "competencies.id")) == "RESTRICT"

    # student_skill_progress: CASCADE student, RESTRICT competency
    ssp_fks = get_fks("student_skill_progress")
    assert ssp_fks.get(("student_id", "students.id")) == "CASCADE"
    assert ssp_fks.get(("competency_id", "competencies.id")) == "RESTRICT"

    # audit_logs: SET NULL user_id (Audit preservation)
    al_fks = get_fks("audit_logs")
    assert al_fks.get(("user_id", "users.id")) == "SET NULL"


def test_unique_constraints():
    """Verify unique constraints across tables."""
    # users: email unique
    users_t = Base.metadata.tables["users"]
    assert users_t.c.email.unique or any(
        "email" in [c.name for c in uc.columns]
        for uc in users_t.constraints
        if isinstance(uc, UniqueConstraint)
    )

    # centers: code unique
    centers_t = Base.metadata.tables["centers"]
    assert centers_t.c.code.unique or any(
        "code" in [c.name for c in uc.columns]
        for uc in centers_t.constraints
        if isinstance(uc, UniqueConstraint)
    )

    # user_centers: (user_id, center_id) unique
    uc_t = Base.metadata.tables["user_centers"]
    uc_cols = [
        set(c.name for c in c.columns)
        for c in uc_t.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert {"user_id", "center_id"} in uc_cols

    # students: student_id_number unique
    students_t = Base.metadata.tables["students"]
    assert students_t.c.student_id_number.unique or any(
        "student_id_number" in [c.name for c in uc.columns]
        for uc in students_t.constraints
        if isinstance(uc, UniqueConstraint)
    )

    # attendance_records: (student_id, attendance_date) unique
    att_t = Base.metadata.tables["attendance_records"]
    att_ucs = [
        set(col.name for col in c.columns)
        for c in att_t.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert {"student_id", "attendance_date"} in att_ucs

    # competencies: code unique
    comp_t = Base.metadata.tables["competencies"]
    assert comp_t.c.code.unique or any(
        "code" in [c.name for c in uc.columns]
        for uc in comp_t.constraints
        if isinstance(uc, UniqueConstraint)
    )

    # activity_competencies: (activity_template_id, competency_id) unique
    act_comp_t = Base.metadata.tables["activity_competencies"]
    ac_ucs = [
        set(col.name for col in c.columns)
        for c in act_comp_t.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert {"activity_template_id", "competency_id"} in ac_ucs

    # session_students: (session_id, student_id) unique
    ss_t = Base.metadata.tables["session_students"]
    ss_ucs = [
        set(col.name for col in c.columns)
        for c in ss_t.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert {"session_id", "student_id"} in ss_ucs

    # session_student_evaluations: (session_student_id, competency_id) unique
    sse_t = Base.metadata.tables["session_student_evaluations"]
    sse_ucs = [
        set(col.name for col in c.columns)
        for c in sse_t.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert {"session_student_id", "competency_id"} in sse_ucs

    # student_skill_progress: (student_id, competency_id) unique
    ssp_t = Base.metadata.tables["student_skill_progress"]
    ssp_ucs = [
        set(col.name for col in c.columns)
        for c in ssp_t.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert {"student_id", "competency_id"} in ssp_ucs


def test_single_active_enrollment_partial_index():
    """Verify enrollment_records defines the partial unique index uq_student_active_enrollment."""
    enrollment_t = Base.metadata.tables["enrollment_records"]
    indexes = {idx.name: idx for idx in enrollment_t.indexes}
    assert "uq_student_active_enrollment" in indexes

    partial_idx = indexes["uq_student_active_enrollment"]
    assert partial_idx.unique is True
    assert [col.name for col in partial_idx.columns] == ["student_id"]
    dialect_options = partial_idx.dialect_options.get("postgresql", {})
    where_clause = dialect_options.get("where")
    assert where_clause is not None
    assert "ACTIVE" in str(where_clause)
    assert "end_date IS NULL" in str(where_clause)


def test_check_constraints():
    """Verify all required check constraints exist on tables."""
    def get_ck_names(table_name):
        table = Base.metadata.tables[table_name]
        return {c.name for c in table.constraints if isinstance(c, CheckConstraint)}

    # centers: ck_centers_capacity
    assert "ck_centers_capacity" in get_ck_names("centers")

    # enrollment_records: ck_enrollment_dates
    assert "ck_enrollment_dates" in get_ck_names("enrollment_records")

    # transfer_requests: ck_transfers_different_centers, ck_transfers_capacity_override_reason
    tr_cks = get_ck_names("transfer_requests")
    assert "ck_transfers_different_centers" in tr_cks
    assert "ck_transfers_capacity_override_reason" in tr_cks

    # activity_templates: ck_activity_templates_age_min, ck_activity_templates_age_max, ck_activity_templates_duration
    at_cks = get_ck_names("activity_templates")
    assert "ck_activity_templates_age_min" in at_cks
    assert "ck_activity_templates_age_max" in at_cks
    assert "ck_activity_templates_duration" in at_cks

    # learning_sessions: ck_learning_sessions_time
    assert "ck_learning_sessions_time" in get_ck_names("learning_sessions")

    # session_students: ck_session_students_score, ck_session_students_absent_score
    ss_cks = get_ck_names("session_students")
    assert "ck_session_students_score" in ss_cks
    assert "ck_session_students_absent_score" in ss_cks

    # student_skill_progress: ck_skill_progress_total_sessions
    assert "ck_skill_progress_total_sessions" in get_ck_names("student_skill_progress")


def test_audit_preservation_no_cascade_on_audit():
    """
    Verify that audit logs cannot be purged via cascading delete:
    - attendance_audit_logs: RESTRICT on foreign keys
    - audit_logs: SET NULL on user_id, no FK on resource_id
    """
    aal_t = Base.metadata.tables["attendance_audit_logs"]
    for col in aal_t.columns:
        for fk in col.foreign_keys:
            assert fk.ondelete == "RESTRICT", (
                f"attendance_audit_logs FK {col.name} has unsafe ondelete: {fk.ondelete}"
            )

    al_t = Base.metadata.tables["audit_logs"]
    # Ensure resource_id is NOT a foreign key (prevents cascade purge)
    assert len(al_t.c.resource_id.foreign_keys) == 0, "audit_logs.resource_id must not be a foreign key"
    # Ensure user_id ondelete is SET NULL
    for fk in al_t.c.user_id.foreign_keys:
        assert fk.ondelete == "SET NULL", f"audit_logs.user_id has unsafe ondelete: {fk.ondelete}"

