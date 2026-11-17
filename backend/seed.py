"""
Database Seed Script for EduTrack.
Populates initial centers, staff users, competencies, activity templates,
students, active enrollments, and initial attendance records in PostgreSQL.
"""
import uuid
from datetime import date, datetime, timedelta

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    ActivityCompetency,
    ActivityTemplate,
    AttendanceRecord,
    AuditLog,
    Center,
    Competency,
    EnrollmentRecord,
    LearningSession,
    SessionParticipationStatus,
    SessionStudent,
    SessionStudentEvaluation,
    Student,
    StudentSkillProgress,
    User,
    UserCenter,
    AttendanceStatus,
    EnrollmentStatus,
    MasteryLevel,
    StudentStatus,
    UserRole,
    UserStatus,
)


def seed_database():
    db = SessionLocal()
    try:
        print("🌱 Seeding EduTrack PostgreSQL database...")

        # 1. Centers
        centers = [
            Center(
                id=uuid.UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7"),
                code="CEN-NORTH-01",
                name="North Ridge Learning Center",
                address="100 North Ridge Way, Seattle, WA 98101",
                timezone="America/Los_Angeles",
                contact_phone="+1-555-0101",
                contact_email="northridge@edutrack.org",
                capacity=120,
                is_active=True,
            ),
            Center(
                id=uuid.UUID("d290f1ee-6c54-4b01-90e6-d701748f0851"),
                code="CEN-SOUTH-02",
                name="South Bay Learning Center",
                address="450 Ocean Ave, San Francisco, CA 94112",
                timezone="America/Los_Angeles",
                contact_phone="+1-555-0199",
                contact_email="southbay@edutrack.org",
                capacity=80,
                is_active=True,
            ),
            Center(
                id=uuid.UUID("3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f"),
                code="CEN-EAST-03",
                name="East Valley Innovation Center",
                address="780 Innovation Blvd, Austin, TX 78701",
                timezone="America/Chicago",
                contact_phone="+1-555-0255",
                contact_email="eastvalley@edutrack.org",
                capacity=60,
                is_active=True,
            ),
        ]
        for c in centers:
            if not db.get(Center, c.id):
                db.add(c)
        db.flush()

        # 2. Staff Users
        password_hash = hash_password("Password123!")

        users = [
            User(
                id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                email="admin@edutrack.org",
                password_hash=password_hash,
                full_name="Alexander Hamilton (Super Admin)",
                phone_number="+1-555-0001",
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
            ),
            User(
                id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                email="manager.north@edutrack.org",
                password_hash=password_hash,
                full_name="Sarah Connor (North Manager)",
                phone_number="+1-555-0002",
                role=UserRole.CENTER_MANAGER,
                status=UserStatus.ACTIVE,
            ),
            User(
                id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                email="manager.south@edutrack.org",
                password_hash=password_hash,
                full_name="David Watson (South Manager)",
                phone_number="+1-555-0003",
                role=UserRole.CENTER_MANAGER,
                status=UserStatus.ACTIVE,
            ),
            User(
                id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
                email="teacher.smith@edutrack.org",
                password_hash=password_hash,
                full_name="Jane Smith (Multi-Center Teacher)",
                phone_number="+1-555-0004",
                role=UserRole.TEACHER,
                status=UserStatus.ACTIVE,
            ),
            User(
                id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
                email="teacher.roberts@edutrack.org",
                password_hash=password_hash,
                full_name="Robert Roberts (Teacher)",
                phone_number="+1-555-0005",
                role=UserRole.TEACHER,
                status=UserStatus.ACTIVE,
            ),
        ]
        for u in users:
            if not db.get(User, u.id):
                db.add(u)
        db.flush()

        # Center Assignments (UserCenter)
        user_centers = [
            # Sarah manages North
            (uuid.UUID("22222222-2222-2222-2222-222222222222"), centers[0].id),
            # David manages South
            (uuid.UUID("33333333-3333-3333-3333-333333333333"), centers[1].id),
            # Jane teaches at North AND South
            (uuid.UUID("44444444-4444-4444-4444-444444444444"), centers[0].id),
            (uuid.UUID("44444444-4444-4444-4444-444444444444"), centers[1].id),
            # Robert teaches at North
            (uuid.UUID("55555555-5555-5555-5555-555555555555"), centers[0].id),
        ]
        for uid, cid in user_centers:
            exists = (
                db.query(UserCenter)
                .filter(UserCenter.user_id == uid, UserCenter.center_id == cid)
                .first()
            )
            if not exists:
                db.add(UserCenter(user_id=uid, center_id=cid))
        db.flush()

        # 3. Competencies
        competencies = [
            Competency(
                id=uuid.UUID("c1a2b3c4-1111-2222-3333-444455556666"),
                code="MATH-FRAC-01",
                name="Identifies Unit Fractions",
                domain="Mathematics",
                description="Recognizes and represents 1/2, 1/3, 1/4 using visual models and fraction tiles.",
            ),
            Competency(
                id=uuid.UUID("d2b3c4d5-2222-3333-4444-555566667777"),
                code="MATH-ADD-02",
                name="Multi-Digit Addition with Regrouping",
                domain="Mathematics",
                description="Accurately computes sums of two 3-digit integers with base-10 regrouping.",
            ),
            Competency(
                id=uuid.UUID("e3c4d5e6-3333-4444-5555-666677778888"),
                code="LIT-READ-01",
                name="Phonemic Blending & Fluency",
                domain="Literacy",
                description="Blends multi-syllable phonemes smoothly and reads grade-level text with expression.",
            ),
            Competency(
                id=uuid.UUID("f4d5e6f7-4444-5555-6666-777788889999"),
                code="LIT-COMP-02",
                name="Main Idea and Supporting Details",
                domain="Literacy",
                description="Identifies central message of informational paragraphs and cites 2 evidence points.",
            ),
            Competency(
                id=uuid.UUID("a5e6f7a8-5555-6666-7777-888899990000"),
                code="SCI-INQ-01",
                name="Scientific Observation & Hypothesis",
                domain="Science",
                description="Formulates testable predictions and records systematic quantitative measurements.",
            ),
        ]
        for comp in competencies:
            if not db.get(Competency, comp.id):
                db.add(comp)
        db.flush()

        # 4. Activity Templates
        templates = [
            ActivityTemplate(
                id=uuid.UUID("99999999-1111-1111-1111-111111111111"),
                center_id=None,
                created_by_user_id=users[0].id,
                title="Fraction Tiles Discovery Workshop",
                subject_area="Mathematics",
                description="Interactive hands-on exploration of equal parts, equivalence, and unit fractions.",
                target_age_min=6,
                target_age_max=10,
                duration_minutes=45,
                is_global=True,
                is_active=True,
            ),
            ActivityTemplate(
                id=uuid.UUID("99999999-2222-2222-2222-222222222222"),
                center_id=None,
                created_by_user_id=users[0].id,
                title="Story Arc & Critical Comprehension",
                subject_area="Literacy",
                description="Guided literary circle mapping inciting incidents, climaxes, and resolutions.",
                target_age_min=8,
                target_age_max=12,
                duration_minutes=50,
                is_global=True,
                is_active=True,
            ),
            ActivityTemplate(
                id=uuid.UUID("99999999-3333-3333-3333-333333333333"),
                center_id=centers[0].id,
                created_by_user_id=users[1].id,
                title="Botanical Microscopic Exploration",
                subject_area="Science",
                description="Specimen preparation, slide mounting, and cellular structure documentation.",
                target_age_min=9,
                target_age_max=14,
                duration_minutes=60,
                is_global=False,
                is_active=True,
            ),
        ]
        for tmpl in templates:
            if not db.get(ActivityTemplate, tmpl.id):
                db.add(tmpl)
        db.flush()

        # Link Activity Competencies
        activity_competencies = [
            (templates[0].id, competencies[0].id, True),
            (templates[0].id, competencies[1].id, False),
            (templates[1].id, competencies[2].id, True),
            (templates[1].id, competencies[3].id, False),
            (templates[2].id, competencies[4].id, True),
        ]
        for aid, cid, is_p in activity_competencies:
            exists = (
                db.query(ActivityCompetency)
                .filter(
                    ActivityCompetency.activity_template_id == aid,
                    ActivityCompetency.competency_id == cid,
                )
                .first()
            )
            if not exists:
                db.add(ActivityCompetency(activity_template_id=aid, competency_id=cid, is_primary=is_p))
        db.flush()

        # 5. Students & Active Enrollments
        students_data = [
            {
                "id": uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
                "student_id_number": "STU-2026-0042",
                "center_id": centers[0].id,
                "first_name": "Alex",
                "last_name": "Johnson",
                "date_of_birth": date(2018, 5, 14),
                "gender": "Male",
                "guardian_name": "Sarah Johnson",
                "guardian_phone": "+1-555-0144",
                "guardian_email": "sarah.j@example.com",
                "guardian_relationship": "Mother",
                "emergency_contact": "Grandmother Mary: +1-555-0145",
                "notes": "Prefers tactile learning aids",
            },
            {
                "id": uuid.UUID("7b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e"),
                "student_id_number": "STU-2026-0043",
                "center_id": centers[0].id,
                "first_name": "Emma",
                "last_name": "Watson",
                "date_of_birth": date(2017, 9, 20),
                "gender": "Female",
                "guardian_name": "David Watson",
                "guardian_phone": "+1-555-0188",
                "guardian_email": "david.w@example.com",
                "guardian_relationship": "Father",
                "emergency_contact": "Aunt Clara: +1-555-0189",
                "notes": "Fast reader in chapter books",
            },
            {
                "id": uuid.UUID("8c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f"),
                "student_id_number": "STU-2026-0044",
                "center_id": centers[0].id,
                "first_name": "Leo",
                "last_name": "Martinez",
                "date_of_birth": date(2018, 2, 10),
                "gender": "Male",
                "guardian_name": "Carlos Martinez",
                "guardian_phone": "+1-555-0210",
                "guardian_email": "carlos.m@example.com",
                "guardian_relationship": "Father",
                "emergency_contact": "Elena Martinez: +1-555-0211",
                "notes": "Bilingual Spanish/English",
            },
            {
                "id": uuid.UUID("9d3e4f5a-6b7c-8d9e-0f1a-2b3c4d5e6f7a"),
                "student_id_number": "STU-2026-0091",
                "center_id": centers[1].id,
                "first_name": "Maya",
                "last_name": "Lin",
                "date_of_birth": date(2017, 11, 4),
                "gender": "Female",
                "guardian_name": "Wei Lin",
                "guardian_phone": "+1-555-0311",
                "guardian_email": "wei.lin@example.com",
                "guardian_relationship": "Mother",
                "emergency_contact": "Uncle Ken: +1-555-0312",
                "notes": "Excels in mental math puzzles",
            },
            {
                "id": uuid.UUID("ae4f5a6b-7c8d-9e0f-1a2b-3c4d5e6f7a8b"),
                "student_id_number": "STU-2026-0092",
                "center_id": centers[1].id,
                "first_name": "Noah",
                "last_name": "Kim",
                "date_of_birth": date(2018, 7, 25),
                "gender": "Male",
                "guardian_name": "Grace Kim",
                "guardian_phone": "+1-555-0422",
                "guardian_email": "grace.kim@example.com",
                "guardian_relationship": "Mother",
                "emergency_contact": "Grandfather Jin: +1-555-0423",
                "notes": "Visual learner",
            },
        ]

        for s_dict in students_data:
            s_id = s_dict["id"]
            if not db.get(Student, s_id):
                st = Student(
                    id=s_id,
                    student_id_number=s_dict["student_id_number"],
                    current_center_id=s_dict["center_id"],
                    first_name=s_dict["first_name"],
                    last_name=s_dict["last_name"],
                    date_of_birth=s_dict["date_of_birth"],
                    gender=s_dict["gender"],
                    guardian_name=s_dict["guardian_name"],
                    guardian_phone=s_dict["guardian_phone"],
                    guardian_email=s_dict["guardian_email"],
                    guardian_relationship=s_dict["guardian_relationship"],
                    emergency_contact=s_dict["emergency_contact"],
                    notes=s_dict["notes"],
                    status=StudentStatus.ACTIVE,
                    version=1,
                )
                db.add(st)
                db.flush()

                # Add initial active enrollment record
                enr = EnrollmentRecord(
                    id=uuid.uuid4(),
                    student_id=st.id,
                    center_id=s_dict["center_id"],
                    start_date=date(2026, 9, 1),
                    end_date=None,
                    status=EnrollmentStatus.ACTIVE,
                    notes="Initial enrollment Fall 2026",
                )
                db.add(enr)
        db.flush()

        # 6. Today's Attendance for North Ridge
        today = date.today()
        for s_dict in students_data[:3]:
            existing_att = (
                db.query(AttendanceRecord)
                .filter(
                    AttendanceRecord.student_id == s_dict["id"],
                    AttendanceRecord.attendance_date == today,
                )
                .first()
            )
            if not existing_att:
                db.add(
                    AttendanceRecord(
                        student_id=s_dict["id"],
                        center_id=centers[0].id,
                        recorded_by_user_id=users[3].id,  # Jane Smith
                        attendance_date=today,
                        status=AttendanceStatus.PRESENT,
                        remarks="Present and energetic",
                        version=1,
                    )
                )

        # 7. Recorded Learning Session
        session_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        if not db.get(LearningSession, session_id):
            start_t = datetime.utcnow().replace(hour=9, minute=30, second=0, microsecond=0)
            end_t = start_t + timedelta(minutes=45)
            ses = LearningSession(
                id=session_id,
                center_id=centers[0].id,
                activity_template_id=templates[0].id,
                conducted_by_user_id=users[3].id,
                session_date=today,
                start_time=start_t,
                end_time=end_t,
                topic_summary="Visualizing Equivalence with Fraction Tiles",
                general_notes="Class grasped half and quarter relationships enthusiastically.",
            )
            db.add(ses)
            db.flush()

            # Add participating student observation
            st1_id = students_data[0]["id"]
            ss = SessionStudent(
                session_id=ses.id,
                student_id=st1_id,
                participation_status=SessionParticipationStatus.COMPLETED,
                qualitative_feedback="Quick grasp of unit fraction concepts.",
                score=95.0,
            )
            db.add(ss)
            db.flush()

            # Add competency evaluation
            db.add(
                SessionStudentEvaluation(
                    session_student_id=ss.id,
                    competency_id=competencies[0].id,
                    mastery_level=MasteryLevel.PROFICIENT,
                    teacher_notes="Constructed models independently.",
                )
            )

            # Cumulative Skill Progress
            prog = (
                db.query(StudentSkillProgress)
                .filter(
                    StudentSkillProgress.student_id == st1_id,
                    StudentSkillProgress.competency_id == competencies[0].id,
                )
                .first()
            )
            if not prog:
                db.add(
                    StudentSkillProgress(
                        student_id=st1_id,
                        competency_id=competencies[0].id,
                        current_level=MasteryLevel.PROFICIENT,
                        total_sessions_count=1,
                        last_evaluated_at=start_t,
                    )
                )

        db.commit()
        print("✅ Database seeding completed successfully!")
    except Exception as exc:
        db.rollback()
        print(f"❌ Database seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

