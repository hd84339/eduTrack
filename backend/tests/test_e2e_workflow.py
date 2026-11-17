"""
Comprehensive End-to-End Workflow Integration Test.
Validates the complete operational lifecycle against the live PostgreSQL database:
1. Super Admin authentication & system-wide analytics.
2. Center Manager registration of students & OCC conflict validation.
3. Teacher bulk daily attendance & 24h audit correction.
4. Learning session conduct & 4-tier rubric competency progression.
5. Inter-center student transfer workflow (Request -> Review & Approval -> Enrollment Handover).
6. Comprehensive attendance CSV/JSON export.
7. Immutable security and operational audit trail verification.
"""
from datetime import date, datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.enums import AttendanceStatus, MasteryLevel, StudentStatus, TransferStatus
from app.models.student import Student


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_complete_e2e_workflow(client: TestClient):
    # -------------------------------------------------------------
    # 1. Super Admin Login & Analytics Overview
    # -------------------------------------------------------------
    admin_login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@edutrack.org", "password": "Password123!"},
    )
    assert admin_login_res.status_code == 200, admin_login_res.text
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Verify /auth/me
    me_res = client.get("/api/v1/auth/me", headers=admin_headers)
    assert me_res.status_code == 200
    assert me_res.json()["role"] == "SUPER_ADMIN"

    # Query overview analytics
    ov_res = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert ov_res.status_code == 200
    ov_data = ov_res.json()
    assert ov_data["total_centers"] >= 3
    assert ov_data["total_active_students"] >= 5

    # -------------------------------------------------------------
    # 2. Center Manager Login & Student Registration
    # -------------------------------------------------------------
    mgr_login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "manager.north@edutrack.org", "password": "Password123!"},
    )
    assert mgr_login_res.status_code == 200
    mgr_data = mgr_login_res.json()
    mgr_token = mgr_data["access_token"]
    north_center = mgr_data["user"]["assigned_centers"][0]
    north_center_id = north_center["id"]

    mgr_headers = {
        "Authorization": f"Bearer {mgr_token}",
        "X-Center-ID": north_center_id,
    }

    # Register new student
    student_payload = {
        "student_id_number": f"STU-E2E-{datetime.now().strftime('%M%S')}",
        "center_id": north_center_id,
        "first_name": "Oliver",
        "last_name": "Twist",
        "date_of_birth": "2015-06-15",
        "gender": "male",
        "guardian_name": "Mr. Brownlow",
        "guardian_phone": "+1 555-019-8822",
        "guardian_email": "brownlow@example.org",
        "guardian_relationship": "Guardian",
        "emergency_contact": "Mrs. Bedwin (+1 555-019-8823)",
        "notes": "E2E automated testing student",
    }
    create_stu_res = client.post("/api/v1/students", json=student_payload, headers=mgr_headers)
    assert create_stu_res.status_code == 201, create_stu_res.text
    created_student = create_stu_res.json()
    student_id = created_student["id"]
    initial_version = created_student["version"]
    assert initial_version == 1

    # -------------------------------------------------------------
    # 3. Optimistic Concurrency Control (OCC) Verification
    # -------------------------------------------------------------
    # Valid update with version 1 -> should succeed and bump version to 2
    update_res = client.put(
        f"/api/v1/students/{student_id}",
        json={
            "first_name": "Oliver",
            "last_name": "Twist-Brownlow",
            "version": initial_version,
        },
        headers=mgr_headers,
    )
    assert update_res.status_code == 200, update_res.text
    assert update_res.json()["version"] == 2
    assert update_res.json()["last_name"] == "Twist-Brownlow"

    # Stale update attempting with version 1 -> must be rejected with 409 Conflict
    stale_update_res = client.put(
        f"/api/v1/students/{student_id}",
        json={
            "first_name": "Oliver",
            "last_name": "Collision-Attempt",
            "version": initial_version,  # Stale version 1
        },
        headers=mgr_headers,
    )
    assert stale_update_res.status_code == 409, "Outdated OCC version must return 409 Conflict"

    # -------------------------------------------------------------
    # 4. Teacher Daily Attendance & Bulk Roll Call
    # -------------------------------------------------------------
    teacher_login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher.smith@edutrack.org", "password": "Password123!"},
    )
    assert teacher_login_res.status_code == 200
    teacher_token = teacher_login_res.json()["access_token"]
    teacher_headers = {
        "Authorization": f"Bearer {teacher_token}",
        "X-Center-ID": north_center_id,
    }

    # Record bulk attendance for center local date
    from zoneinfo import ZoneInfo
    center_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    test_date = center_today.isoformat()
    bulk_att_res = client.post(
        "/api/v1/attendance/bulk",
        json={
            "center_id": north_center_id,
            "attendance_date": test_date,
            "records": [
                {
                    "student_id": student_id,
                    "status": "PRESENT",
                    "remarks": "On time and prepared",
                }
            ],
        },
        headers=teacher_headers,
    )
    assert bulk_att_res.status_code == 201, bulk_att_res.text

    # Fetch daily attendance records
    att_list_res = client.get(
        f"/api/v1/attendance?date={test_date}",
        headers=teacher_headers,
    )
    assert att_list_res.status_code == 200
    records = att_list_res.json()
    assert len(records) >= 1
    target_record = next(r for r in records if r["student_id"] == student_id)
    assert target_record["status"] == "PRESENT"
    record_id = target_record["id"]
    att_version = target_record["version"]

    # 24h Attendance correction with justification reason
    correction_res = client.put(
        f"/api/v1/attendance/{record_id}",
        json={
            "status": "LATE",
            "reason": "Traffic delay verified with parent note",
            "remarks": "Arrived 15 minutes late",
            "version": att_version,
        },
        headers=teacher_headers,
    )
    assert correction_res.status_code == 200, correction_res.text
    assert correction_res.json()["status"] == "LATE"
    assert correction_res.json()["version"] == att_version + 1

    # -------------------------------------------------------------
    # 5. Conduct Learning Session & 4-Tier Rubric Evaluation
    # -------------------------------------------------------------
    # Fetch an activity template and competency
    act_res = client.get("/api/v1/activities", headers=teacher_headers)
    assert act_res.status_code == 200
    activities = act_res.json()["items"]
    assert len(activities) > 0
    activity_id = activities[0]["id"]

    comp_res = client.get("/api/v1/competencies", headers=teacher_headers)
    assert comp_res.status_code == 200
    competencies = comp_res.json()["items"]
    assert len(competencies) > 0
    competency_id = competencies[0]["id"]

    now = datetime.now()
    session_payload = {
        "center_id": north_center_id,
        "activity_template_id": activity_id,
        "session_date": center_today.isoformat(),
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
        "topic_summary": "Interactive Problem Solving Workshop",
        "general_notes": "All students actively engaged in cooperative teams.",
        "students": [
            {
                "student_id": student_id,
                "participation_status": "COMPLETED",
                "score": 92.5,
                "qualitative_feedback": "Demonstrated excellent leadership and conceptual grasp.",
                "evaluations": [
                    {
                        "competency_id": competency_id,
                        "mastery_level": "PROFICIENT",
                        "teacher_notes": "Independently solved challenging multi-step scenario.",
                    }
                ],
            }
        ],
    }

    create_sess_res = client.post("/api/v1/sessions", json=session_payload, headers=teacher_headers)
    assert create_sess_res.status_code == 201, create_sess_res.text
    sess_data = create_sess_res.json()
    assert sess_data["topic_summary"] == "Interactive Problem Solving Workshop"

    # Verify that student longitudinal progress was updated
    progress_res = client.get(f"/api/v1/progress/students/{student_id}", headers=teacher_headers)
    assert progress_res.status_code == 200, progress_res.text
    prog_data = progress_res.json()
    assert len(prog_data["competencies"]) >= 1
    evaluated_comp = next(c for c in prog_data["competencies"] if c["competency_id"] == competency_id)
    assert evaluated_comp["current_level"] == "PROFICIENT"
    assert evaluated_comp["total_sessions_count"] >= 1

    # -------------------------------------------------------------
    # 6. Inter-Center Student Transfer Workflow
    # -------------------------------------------------------------
    # Find South Center ID
    south_center = next(c for c in client.get("/api/v1/centers", headers=admin_headers).json()["items"] if c["code"] == "CEN-SOUTH-02")
    south_center_id = south_center["id"]

    # Origin Manager requests transfer to South Center
    transfer_create_res = client.post(
        "/api/v1/transfers",
        json={
            "student_id": student_id,
            "to_center_id": south_center_id,
            "effective_date": (date.today() + timedelta(days=3)).isoformat(),
            "request_reason": "Family moving closer to South Hub facility.",
        },
        headers=mgr_headers,
    )
    assert transfer_create_res.status_code == 201, transfer_create_res.text
    transfer_id = transfer_create_res.json()["id"]
    assert transfer_create_res.json()["status"] == "PENDING"

    # Destination Manager logs in to review & approve
    south_mgr_res = client.post(
        "/api/v1/auth/login",
        json={"email": "manager.south@edutrack.org", "password": "Password123!"},
    )
    assert south_mgr_res.status_code == 200
    south_mgr_token = south_mgr_res.json()["access_token"]
    south_mgr_headers = {
        "Authorization": f"Bearer {south_mgr_token}",
        "X-Center-ID": south_center_id,
    }

    # Review & approve
    review_res = client.post(
        f"/api/v1/transfers/{transfer_id}/review",
        json={
            "action": "APPROVE",
            "review_notes": "Welcome to South Hub! Enrollment quota verified and available.",
        },
        headers=south_mgr_headers,
    )
    assert review_res.status_code == 200, review_res.text
    assert review_res.json()["status"] == "APPROVED"

    # Verify student now belongs to South Center
    updated_stu_res = client.get(
        f"/api/v1/students/{student_id}",
        headers=south_mgr_headers,
    )
    assert updated_stu_res.status_code == 200
    updated_stu = updated_stu_res.json()
    assert updated_stu["current_center_id"] == south_center_id
    assert updated_stu["status"] == "ACTIVE"

    # -------------------------------------------------------------
    # 7. Reporting & CSV Export
    # -------------------------------------------------------------
    report_res = client.get(
        f"/api/v1/reports/attendance?center_id={north_center_id}&start_date={test_date}&end_date={date.today().isoformat()}&format=csv",
        headers=mgr_headers,
    )
    assert report_res.status_code == 200
    assert "text/csv" in report_res.headers["content-type"]
    assert "attendance_date,center_name,student_id_number,student_name,status,remarks" in report_res.text

    # -------------------------------------------------------------
    # 8. Immutable System Audit Trail Verification
    # -------------------------------------------------------------
    audit_res = client.get(
        f"/api/v1/audit-logs?resource_type=TRANSFER_REQUEST",
        headers=admin_headers,
    )
    assert audit_res.status_code == 200, audit_res.text
    audit_items = audit_res.json()["items"]
    assert len(audit_items) >= 1
    transfer_audit = next(a for a in audit_items if a["resource_id"] == transfer_id)
    assert transfer_audit["action"] in ["CREATE", "TRANSFER_APPROVE"]
    assert transfer_audit["new_values"] is not None

