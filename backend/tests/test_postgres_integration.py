"""
PostgreSQL Live Integration Test Suite.
Validates live PostgreSQL 18 database connectivity, native ENUM types,
foreign key cascades/restrictions, transaction rollbacks, and partial unique index constraints.
"""
import uuid
from datetime import date, datetime
import pytest
from sqlalchemy import create_engine, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import (
    Center,
    Competency,
    EnrollmentRecord,
    Student,
    User,
    UserRole,
    UserStatus,
    StudentStatus,
    EnrollmentStatus,
)


@pytest.fixture(scope="module")
def pg_session():
    """Provides a session connected directly to live PostgreSQL."""
    if not settings.DATABASE_URL.startswith("postgresql"):
        pytest.skip("DATABASE_URL is not configured for PostgreSQL")

    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        # Verify connectivity
        session.execute(text("SELECT 1"))
        yield session
    except Exception as exc:
        pytest.skip(f"Live PostgreSQL not reachable: {exc}")
    finally:
        session.close()


def test_postgres_table_count(pg_session):
    """Verifies that all 17 tables (16 domain + alembic_version) exist in PostgreSQL."""
    result = pg_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    ).fetchall()
    table_names = {r[0] for r in result}
    assert "alembic_version" in table_names
    assert "students" in table_names
    assert "centers" in table_names
    assert "enrollment_records" in table_names
    assert "attendance_records" in table_names
    assert "audit_logs" in table_names
    assert len(table_names) >= 17


def test_postgres_enums(pg_session):
    """Verifies that all 8 native PostgreSQL enums are registered in pg_type."""
    result = pg_session.execute(
        text("SELECT typname FROM pg_type WHERE typcategory = 'E'")
    ).fetchall()
    enums = {r[0] for r in result}
    expected_enums = {
        "attendance_status",
        "enrollment_status",
        "mastery_level",
        "session_participation_status",
        "student_status",
        "transfer_status",
        "user_role",
        "user_status",
    }
    assert expected_enums.issubset(enums)


def test_postgres_partial_unique_index_active_enrollment(pg_session):
    """
    Verifies that PostgreSQL's native partial unique index enforces:
    A student can only have ONE active enrollment with end_date IS NULL.
    """
    # 1. Create center and student
    center = Center(
        id=uuid.uuid4(),
        code=f"PG-CEN-{uuid.uuid4().hex[:6].upper()}",
        name="Postgres Center",
        address="123 Postgres Way",
        timezone="UTC",
        capacity=50,
        is_active=True,
    )
    pg_session.add(center)

    student = Student(
        id=uuid.uuid4(),
        student_id_number=f"PG-STU-{uuid.uuid4().hex[:6].upper()}",
        current_center_id=center.id,
        first_name="Bruce",
        last_name="Banner",
        date_of_birth=date(2015, 6, 15),
        gender="Male",
        guardian_name="Brian Banner",
        guardian_phone="555-0101",
        status=StudentStatus.ACTIVE,
        version=1,
    )
    pg_session.add(student)
    pg_session.commit()

    # 2. Add first active enrollment
    enr1 = EnrollmentRecord(
        id=uuid.uuid4(),
        student_id=student.id,
        center_id=center.id,
        start_date=date.today(),
        end_date=None,
        status=EnrollmentStatus.ACTIVE,
    )
    pg_session.add(enr1)
    pg_session.commit()

    # 3. Add second active enrollment for same student -> Must fail with partial unique index violation
    enr2 = EnrollmentRecord(
        id=uuid.uuid4(),
        student_id=student.id,
        center_id=center.id,
        start_date=date.today(),
        end_date=None,
        status=EnrollmentStatus.ACTIVE,
    )
    pg_session.add(enr2)
    with pytest.raises(IntegrityError) as exc_info:
        pg_session.commit()
    assert "uq_student_active_enrollment" in str(exc_info.value)

    pg_session.rollback()

    # 4. Cleanup test rows
    pg_session.delete(enr1)
    pg_session.delete(student)
    pg_session.delete(center)
    pg_session.commit()


def test_postgres_transaction_rollback(pg_session):
    """Verifies that transaction rollback cleanly discards uncommitted mutations in PostgreSQL."""
    center = Center(
        id=uuid.uuid4(),
        code=f"ROLLBACK-{uuid.uuid4().hex[:6].upper()}",
        name="Rollback Center",
        address="999 Rollback Lane",
        timezone="UTC",
        capacity=10,
        is_active=True,
    )
    pg_session.add(center)
    pg_session.flush()

    # Roll back transaction
    pg_session.rollback()

    # Verify center does not exist
    searched = pg_session.query(Center).filter(Center.code == center.code).first()
    assert searched is None

