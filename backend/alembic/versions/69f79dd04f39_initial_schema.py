"""initial_schema

Revision ID: 69f79dd04f39
Revises: 
Create Date: 2026-11-15 15:49:44.334365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '69f79dd04f39'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# PostgreSQL Enum definitions (create_type=False so create_table does not re-create them)
user_role_enum = postgresql.ENUM('SUPER_ADMIN', 'CENTER_MANAGER', 'TEACHER', name='user_role', create_type=False)
user_status_enum = postgresql.ENUM('ACTIVE', 'INACTIVE', 'LOCKED', name='user_status', create_type=False)
student_status_enum = postgresql.ENUM('ACTIVE', 'INACTIVE', 'TRANSFERRED', 'GRADUATED', 'SUSPENDED', name='student_status', create_type=False)
enrollment_status_enum = postgresql.ENUM('ACTIVE', 'TRANSFERRED', 'COMPLETED', 'WITHDRAWN', name='enrollment_status', create_type=False)
transfer_status_enum = postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', name='transfer_status', create_type=False)
attendance_status_enum = postgresql.ENUM('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendance_status', create_type=False)
session_participation_status_enum = postgresql.ENUM('COMPLETED', 'PARTIAL', 'ABSENT', name='session_participation_status', create_type=False)
mastery_level_enum = postgresql.ENUM('EMERGING', 'DEVELOPING', 'PROFICIENT', 'MASTERY', name='mastery_level', create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Create PostgreSQL ENUM types explicitly
    sa.Enum('SUPER_ADMIN', 'CENTER_MANAGER', 'TEACHER', name='user_role').create(bind, checkfirst=True)
    sa.Enum('ACTIVE', 'INACTIVE', 'LOCKED', name='user_status').create(bind, checkfirst=True)
    sa.Enum('ACTIVE', 'INACTIVE', 'TRANSFERRED', 'GRADUATED', 'SUSPENDED', name='student_status').create(bind, checkfirst=True)
    sa.Enum('ACTIVE', 'TRANSFERRED', 'COMPLETED', 'WITHDRAWN', name='enrollment_status').create(bind, checkfirst=True)
    sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', name='transfer_status').create(bind, checkfirst=True)
    sa.Enum('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendance_status').create(bind, checkfirst=True)
    sa.Enum('COMPLETED', 'PARTIAL', 'ABSENT', name='session_participation_status').create(bind, checkfirst=True)
    sa.Enum('EMERGING', 'DEVELOPING', 'PROFICIENT', 'MASTERY', name='mastery_level').create(bind, checkfirst=True)

    # 2. Table: users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('phone_number', sa.String(length=30), nullable=True),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('status', user_status_enum, server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_role_status', 'users', ['role', 'status'], unique=False)

    # 3. Table: centers
    op.create_table(
        'centers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('timezone', sa.String(length=50), server_default=sa.text("'UTC'"), nullable=False),
        sa.Column('contact_phone', sa.String(length=30), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('capacity', sa.Integer(), server_default=sa.text('100'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('capacity > 0', name='ck_centers_capacity'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('idx_centers_is_active', 'centers', ['is_active'], unique=False)

    # 4. Table: user_centers
    op.create_table(
        'user_centers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'center_id', name='uq_user_centers'),
    )
    op.create_index('idx_user_centers_center', 'user_centers', ['center_id'], unique=False)

    # 5. Table: students
    op.create_table(
        'students',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id_number', sa.String(length=50), nullable=False),
        sa.Column('current_center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('guardian_name', sa.String(length=150), nullable=False),
        sa.Column('guardian_phone', sa.String(length=30), nullable=False),
        sa.Column('guardian_email', sa.String(length=255), nullable=True),
        sa.Column('guardian_relationship', sa.String(length=50), server_default=sa.text("'Parent'"), nullable=False),
        sa.Column('emergency_contact', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', student_status_enum, server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['current_center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id_number'),
    )
    op.create_index('idx_students_center_status', 'students', ['current_center_id', 'status'], unique=False)
    op.create_index('idx_students_name', 'students', ['last_name', 'first_name'], unique=False)

    # 6. Table: enrollment_records
    op.create_table(
        'enrollment_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', enrollment_status_enum, server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_enrollment_dates'),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_student_active_enrollment',
        'enrollment_records',
        ['student_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE' AND end_date IS NULL"),
    )
    op.create_index('idx_enrollment_student', 'enrollment_records', ['student_id'], unique=False)
    op.create_index('idx_enrollment_center_status', 'enrollment_records', ['center_id', 'status'], unique=False)

    # 7. Table: transfer_requests
    op.create_table(
        'transfer_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', transfer_status_enum, server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column('request_reason', sa.Text(), nullable=False),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('capacity_override', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('capacity_override_reason', sa.Text(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('from_center_id <> to_center_id', name='ck_transfers_different_centers'),
        sa.CheckConstraint(
            'capacity_override = FALSE OR capacity_override_reason IS NOT NULL',
            name='ck_transfers_capacity_override_reason',
        ),
        sa.ForeignKeyConstraint(['from_center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_transfers_from_center', 'transfer_requests', ['from_center_id'], unique=False)
    op.create_index('idx_transfers_status', 'transfer_requests', ['status'], unique=False)
    op.create_index('idx_transfers_student', 'transfer_requests', ['student_id'], unique=False)
    op.create_index('idx_transfers_to_center', 'transfer_requests', ['to_center_id'], unique=False)

    # 8. Table: attendance_records
    op.create_table(
        'attendance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recorded_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('status', attendance_status_enum, nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['recorded_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'attendance_date', name='uq_attendance_student_date'),
    )
    op.create_index('idx_attendance_center_date', 'attendance_records', ['center_id', 'attendance_date'], unique=False)

    # 9. Table: attendance_audit_logs
    op.create_table(
        'attendance_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('attendance_record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('previous_status', attendance_status_enum, nullable=False),
        sa.Column('new_status', attendance_status_enum, nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['attendance_record_id'], ['attendance_records.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_att_audit_changed_at', 'attendance_audit_logs', ['changed_at'], unique=False)
    op.create_index('idx_att_audit_record', 'attendance_audit_logs', ['attendance_record_id'], unique=False)

    # 10. Table: competencies
    op.create_table(
        'competencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('domain', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('idx_competencies_domain', 'competencies', ['domain'], unique=False)

    # 11. Table: activity_templates
    op.create_table(
        'activity_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('subject_area', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_age_min', sa.Integer(), server_default=sa.text('3'), nullable=False),
        sa.Column('target_age_max', sa.Integer(), server_default=sa.text('18'), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), server_default=sa.text('45'), nullable=False),
        sa.Column('is_global', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('duration_minutes >= 5', name='ck_activity_templates_duration'),
        sa.CheckConstraint('target_age_max >= target_age_min', name='ck_activity_templates_age_max'),
        sa.CheckConstraint('target_age_min >= 0', name='ck_activity_templates_age_min'),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_act_templates_center_global', 'activity_templates', ['center_id', 'is_global'], unique=False)
    op.create_index('idx_act_templates_subject', 'activity_templates', ['subject_area'], unique=False)

    # 12. Table: activity_competencies
    op.create_table(
        'activity_competencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('activity_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('competency_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.ForeignKeyConstraint(['activity_template_id'], ['activity_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('activity_template_id', 'competency_id', name='uq_activity_competencies'),
    )
    op.create_index('idx_act_comp_competency', 'activity_competencies', ['competency_id'], unique=False)

    # 13. Table: learning_sessions
    op.create_table(
        'learning_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conducted_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('topic_summary', sa.String(length=255), nullable=False),
        sa.Column('general_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('end_time >= start_time', name='ck_learning_sessions_time'),
        sa.ForeignKeyConstraint(['activity_template_id'], ['activity_templates.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['conducted_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sessions_center_date', 'learning_sessions', ['center_id', 'session_date'], unique=False)
    op.create_index('idx_sessions_teacher', 'learning_sessions', ['conducted_by_user_id'], unique=False)

    # 14. Table: session_students
    op.create_table(
        'session_students',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participation_status', session_participation_status_enum, server_default=sa.text("'COMPLETED'"), nullable=False),
        sa.Column('qualitative_feedback', sa.Text(), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("participation_status <> 'ABSENT' OR score IS NULL", name='ck_session_students_absent_score'),
        sa.CheckConstraint('score IS NULL OR (score >= 0.0 AND score <= 100.0)', name='ck_session_students_score'),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'student_id', name='uq_session_students'),
    )
    op.create_index('idx_session_students_student', 'session_students', ['student_id'], unique=False)

    # 15. Table: session_student_evaluations
    op.create_table(
        'session_student_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('competency_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mastery_level', mastery_level_enum, nullable=False),
        sa.Column('teacher_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['session_student_id'], ['session_students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_student_id', 'competency_id', name='uq_session_student_evaluations'),
    )
    op.create_index('idx_evaluations_competency', 'session_student_evaluations', ['competency_id'], unique=False)

    # 16. Table: student_skill_progress
    op.create_table(
        'student_skill_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('competency_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_level', mastery_level_enum, nullable=False),
        sa.Column('total_sessions_count', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('total_sessions_count > 0', name='ck_skill_progress_total_sessions'),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'competency_id', name='uq_student_skill_progress'),
    )
    op.create_index('idx_skill_progress_competency', 'student_skill_progress', ['competency_id'], unique=False)

    # 17. Table: audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_created_at', 'audit_logs', [sa.text('created_at DESC')], unique=False)
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('idx_audit_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    # Drop tables in reverse order of foreign key dependencies
    op.drop_table('audit_logs')
    op.drop_table('student_skill_progress')
    op.drop_table('session_student_evaluations')
    op.drop_table('session_students')
    op.drop_table('learning_sessions')
    op.drop_table('activity_competencies')
    op.drop_table('activity_templates')
    op.drop_table('competencies')
    op.drop_table('attendance_audit_logs')
    op.drop_table('attendance_records')
    op.drop_table('transfer_requests')
    op.drop_table('enrollment_records')
    op.drop_table('students')
    op.drop_table('user_centers')
    op.drop_table('centers')
    op.drop_table('users')

    # Drop PostgreSQL ENUM types
    sa.Enum(name='mastery_level').drop(bind, checkfirst=True)
    sa.Enum(name='session_participation_status').drop(bind, checkfirst=True)
    sa.Enum(name='attendance_status').drop(bind, checkfirst=True)
    sa.Enum(name='transfer_status').drop(bind, checkfirst=True)
    sa.Enum(name='enrollment_status').drop(bind, checkfirst=True)
    sa.Enum(name='student_status').drop(bind, checkfirst=True)
    sa.Enum(name='user_status').drop(bind, checkfirst=True)
    sa.Enum(name='user_role').drop(bind, checkfirst=True)
