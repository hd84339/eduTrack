# EduTrack — RESTful API Specification

**API Version:** `v1`  
**Base Path:** `/api/v1`  
**Protocol:** HTTPS / JSON  
**Authentication Scheme:** HTTP Bearer JWT  

---

## 1. Global Conventions & Standards

### 1.1 Standard Headers
- `Authorization: Bearer <jwt_access_token>` (Required for all protected routes)
- `Content-Type: application/json`
- `X-Request-ID: <uuid>` (Propagated for correlation across logs and audit trails)

### 1.2 Pagination & Sorting Standard
All collection endpoints support standardized pagination and sorting query parameters:
- `page`: 1-based page index (Default: `1`)
- `size`: Items per page (Default: `20`, Max: `100`)
- `sort_by`: Field identifier (e.g., `created_at`, `last_name`, `attendance_date`)
- `sort_dir`: `asc` or `desc` (Default: `desc`)

#### Standard Paginated Response Envelope:
```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_items": 142,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### 1.3 Standard Error Envelope
All error responses return a standardized structured payload:
```json
{
  "error": {
    "code": "CONCURRENCY_CONFLICT",
    "message": "The record has been updated by another user. Reload and re-apply changes.",
    "details": [
      {
        "field": "version",
        "issue": "Submitted version 3 does not match current database version 4"
      }
    ],
    "timestamp": "2026-11-15T13:30:00Z",
    "request_id": "req-9c8e2b"
  }
}
```

### 1.4 Common HTTP Status Codes
- `200 OK`: Successful read or idempotent update.
- `201 Created`: Successful creation.
- `204 No Content`: Successful deletion or state transition without response body.
- `400 Bad Request`: Malformed JSON or input validation failure.
- `401 Unauthorized`: Missing, expired, or invalid JWT bearer token.
- `403 Forbidden`: Authenticated user lacks role or center permissions.
- `404 Not Found`: Target resource does not exist.
- `409 Conflict`: Business rule violation or OCC version collision.
- `422 Unprocessable Entity`: Semantic/schema validation error.
- `500 Internal Server Error`: Unhandled server exception.

---

## 2. API Endpoints by Domain Module

### Module 1: Authentication & Authorization (`/auth`)

#### `POST /auth/login`
Authenticates user and returns JWT token pair.
- **Access:** Public
- **Request Body:**
  ```json
  {
    "email": "teacher.smith@edutrack.org",
    "password": "Password123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "e5b15b3a-4467-4f65-8bdf-1b4e9f7e8a01",
      "email": "teacher.smith@edutrack.org",
      "full_name": "Jane Smith",
      "role": "TEACHER",
      "assigned_centers": [
        {
          "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
          "code": "CEN-NORTH-01",
          "name": "North Ridge Learning Center"
        }
      ]
    }
  }
  ```

#### `POST /auth/refresh`
Rotates access token using a valid refresh token.
- **Access:** Public (Requires valid Refresh Token in payload)
- **Request Body:**
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "expires_in": 1800
  }
  ```

#### `GET /auth/me`
Retrieves currently authenticated user profile and permissions.
- **Access:** Authenticated (Any Role)
- **Response (200 OK):** Same user object as login.

---

### Module 2: Learning Center Management (`/centers`)

#### `GET /centers`
Lists all learning centers. Super Admins see all; Managers and Teachers see assigned centers.
- **Access:** Authenticated
- **Query Params:** `is_active=true`, `search=North`, `page=1`, `size=20`
- **Response (200 OK):** Paginated array of center summaries.

#### `POST /centers`
Creates a new learning center.
- **Access:** `SUPER_ADMIN`
- **Request Body:**
  ```json
  {
    "code": "CEN-SOUTH-02",
    "name": "South Bay Center",
    "address": "450 Ocean Ave, San Francisco, CA 94112",
    "contact_phone": "+1-555-0199",
    "contact_email": "southbay@edutrack.org",
    "capacity": 120
  }
  ```
- **Response (201 Created):** Full center record.

#### `GET /centers/{id}`
Fetches specific center details and current occupancy count.
- **Access:** `SUPER_ADMIN` or Assigned `CENTER_MANAGER` / `TEACHER`
- **Response (200 OK):** Center details.

#### `PUT /centers/{id}`
Updates center information.
- **Access:** `SUPER_ADMIN`

---

### Module 3: Student Management (`/students`)

#### `GET /students`
Lists students with multi-attribute filtering and pagination.
- **Access:** Authenticated (Scoped by assigned centers)
- **Query Params:** `center_id`, `status=ACTIVE`, `search=Doe`, `page=1`, `size=20`
- **Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "student_id_number": "STU-2026-0042",
        "first_name": "Alex",
        "last_name": "Johnson",
        "current_center_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "center_name": "North Ridge Learning Center",
        "date_of_birth": "2018-05-14",
        "status": "ACTIVE",
        "guardian_name": "Sarah Johnson",
        "guardian_phone": "+1-555-0144",
        "version": 1
      }
    ],
    "pagination": { "page": 1, "size": 20, "total_items": 1, "total_pages": 1, "has_next": false, "has_prev": false }
  }
  ```

#### `POST /students`
Registers a new student and atomically initializes their first `EnrollmentRecord`.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`
- **Request Body:**
  ```json
  {
    "student_id_number": "STU-2026-0099",
    "center_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "first_name": "Emma",
    "last_name": "Watson",
    "date_of_birth": "2017-09-20",
    "gender": "Female",
    "guardian_name": "David Watson",
    "guardian_phone": "+1-555-0188",
    "guardian_email": "david.w@example.com",
    "guardian_relationship": "Father",
    "emergency_contact": "Aunt Clara: +1-555-0189",
    "medical_notes": "Mild peanut allergy"
  }
  ```
- **Response (201 Created):** Full created student profile with `version: 1`.

#### `GET /students/{id}`
Returns complete student profile, active center, and latest enrollment summary.
- **Access:** `SUPER_ADMIN` or Assigned `CENTER_MANAGER` / `TEACHER`

#### `PUT /students/{id}` (OCC Protected)
Updates student profile. Requires submitting current `version`.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`
- **Request Body:**
  ```json
  {
    "first_name": "Emma",
    "last_name": "Watson-Smith",
    "guardian_phone": "+1-555-0999",
    "guardian_email": "david.ws@example.com",
    "emergency_contact": "Aunt Clara: +1-555-0189",
    "medical_notes": "Mild peanut allergy, carries EpiPen",
    "version": 1
  }
  ```
- **Response (200 OK):** Updated student object with `version: 2`.
- **Error (409 Conflict):** If submitted version does not match database version.

---

### Module 4: Student Enrollment & Center Transfers (`/transfers`)

#### `POST /transfers`
Initiates a transfer request from current center to a destination center.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER` (Source Center)
- **Request Body:**
  ```json
  {
    "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "to_center_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "effective_date": "2026-12-01",
    "request_reason": "Family relocated to South district"
  }
  ```
- **Response (201 Created):** Transfer request with status `PENDING`.

#### `GET /transfers`
Lists pending or past transfer requests filterable by center and status.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`
- **Query Params:** `status=PENDING`, `direction=incoming|outgoing`

#### `POST /transfers/{id}/review`
Approves or rejects a pending transfer request within an ACID transaction.
- **Access:** `SUPER_ADMIN` or `CENTER_MANAGER` (Destination Center)
- **Request Body:**
  ```json
  {
    "action": "APPROVE",
    "review_notes": "Seat confirmed in Cohort B"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "transfer_id": "a1c2e3f4-...",
    "status": "APPROVED",
    "student_id": "3fa85f64-...",
    "new_center_id": "d290f1ee-...",
    "closed_enrollment_id": "8f7e6d5c-...",
    "new_enrollment_id": "1a2b3c4d-..."
  }
  ```

---

### Module 5: Attendance Management (`/attendance`)

#### `GET /attendance`
Queries daily attendance roster for a center and date.
- **Access:** Authenticated (Scoped to center)
- **Query Params:** `center_id=...`, `date=2026-11-15`
- **Response (200 OK):** List of attendance entries for the date.

#### `POST /attendance/bulk`
Submits bulk daily attendance for multiple students in a single atomic transaction.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`
- **Request Body:**
  ```json
  {
    "center_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "attendance_date": "2026-11-15",
    "records": [
      {
        "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "PRESENT",
        "remarks": null
      },
      {
        "student_id": "7f8a9b0c-1234-5678-90ab-cdef12345678",
        "status": "LATE",
        "remarks": "Arrived 20 mins late due to transit"
      },
      {
        "student_id": "9a8b7c6d-5555-4444-3333-222211110000",
        "status": "EXCUSED",
        "remarks": "Medical appointment"
      }
    ]
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "message": "Bulk attendance recorded successfully",
    "processed_count": 3,
    "attendance_date": "2026-11-15"
  }
  ```
- **Error (409 Conflict):** If one or more students already have attendance recorded on `attendance_date`.

#### `PATCH /attendance/{id}`
Corrects an existing attendance record. Enforces OCC version checking and records an entry in `attendance_audit_logs`.
- **Access:** `TEACHER` (within 24h), `CENTER_MANAGER`, `SUPER_ADMIN`
- **Request Body:**
  ```json
  {
    "status": "PRESENT",
    "reason": "Student was marked absent by mistake, arrived at 09:15 AM",
    "version": 1
  }
  ```
- **Response (200 OK):** Updated attendance record with incremented version.

#### `GET /attendance/{id}/audit-trail`
Fetches the immutable correction history for a specific attendance record.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`

---

### Module 6: Learning Activity Management (`/activities/templates`)

#### `GET /activities/templates`
Retrieves activity templates (Global templates + templates scoped to assigned centers).
- **Access:** Authenticated
- **Query Params:** `subject_area=Mathematics`, `is_active=true`

#### `POST /activities/templates`
Creates a new activity template.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`
- **Request Body:**
  ```json
  {
    "center_id": null,
    "is_global": true,
    "title": "Fraction Foundations with Manipulatives",
    "subject_area": "Mathematics",
    "description": "Hands-on exploration of half, quarter, and eighth fractions using physical blocks.",
    "target_age_min": 7,
    "target_age_max": 10,
    "duration_minutes": 45,
    "competencies": [
      { "key": "MATH-FRAC-01", "name": "Identifies Unit Fractions" },
      { "key": "MATH-FRAC-02", "name": "Compares Equivalent Fractions" }
    ]
  }
  ```
- **Response (201 Created):** Template object.

---

### Module 7: Learning Session Management (`/sessions`)

#### `POST /sessions`
Logs a conducted learning session along with participating student scorecards.
- **Access:** `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN`
- **Request Body:**
  ```json
  {
    "center_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "activity_template_id": "11112222-3333-4444-5555-666677778888",
    "session_date": "2026-11-15",
    "start_time": "2026-11-15T10:00:00Z",
    "end_time": "2026-11-15T10:45:00Z",
    "topic_summary": "Introduction to Unit Fractions",
    "general_notes": "Class engaged enthusiastically with fraction tiles.",
    "students": [
      {
        "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "participation_status": "COMPLETED",
        "mastery_level": "PROFICIENT",
        "qualitative_feedback": "Demonstrated immediate grasp of 1/2 vs 1/4 representation.",
        "score": 90.0
      }
    ]
  }
  ```
- **Response (201 Created):** Session object including nested `session_students`.

#### `GET /sessions`
Lists learning sessions with filters (`center_id`, `date_range`, `template_id`).
- **Access:** Authenticated

---

### Module 8: Student Progress Tracking (`/progress`)

#### `GET /progress/students/{student_id}`
Returns aggregated competency mastery levels and timeline for a student.
- **Access:** Authenticated
- **Response (200 OK):**
  ```json
  {
    "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "competencies": [
      {
        "competency_key": "MATH-FRAC-01",
        "competency_name": "Identifies Unit Fractions",
        "current_level": "PROFICIENT",
        "total_sessions_count": 3,
        "last_evaluated_at": "2026-11-15T10:45:00Z"
      }
    ]
  }
  ```

---

### Module 9: Dashboard & Analytics (`/analytics`)

#### `GET /analytics/overview`
Organization-wide summary for Super Admins.
- **Access:** `SUPER_ADMIN`
- **Response (200 OK):** Total centers, total active students, system-wide attendance rate today, monthly enrollment growth.

#### `GET /analytics/centers/{center_id}`
Operational metrics for a specific center.
- **Access:** `SUPER_ADMIN` or Assigned `CENTER_MANAGER`
- **Response (200 OK):** Active student count, attendance rate (today & 30-day average), weekly completed sessions count, pending transfer requests count.

---

### Module 10: Reports (`/reports`)

#### `GET /reports/attendance`
Generates downloadable attendance reports.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER`
- **Query Params:** `center_id`, `start_date`, `end_date`, `format=csv|json`
- **Response:** CSV attachment stream or JSON array.

#### `GET /reports/students/{student_id}/dossier`
Produces comprehensive student longitudinal dossier (bio, enrollment history, attendance summary, mastery history).
- **Access:** `SUPER_ADMIN` or Assigned `CENTER_MANAGER` / `TEACHER`

---

### Module 11: User & Staff Management (`/users`)

#### `GET /users`
Lists staff members with role and center assignment filters.
- **Access:** `SUPER_ADMIN`, `CENTER_MANAGER` (Teachers only)

#### `POST /users`
Provisions a new staff user.
- **Access:** `SUPER_ADMIN` (any role), `CENTER_MANAGER` (Teachers in assigned center)
- **Request Body:**
  ```json
  {
    "email": "teacher.roberts@edutrack.org",
    "password": "InitialSecurePass1!",
    "full_name": "Robert Roberts",
    "phone_number": "+1-555-0123",
    "role": "TEACHER",
    "center_ids": ["7c9e6679-7425-40de-944b-e07fc1f90ae7"]
  }
  ```
- **Response (201 Created):** Created user profile (without password hash).

#### `PUT /users/{id}/centers`
Updates center assignments for a staff member.
- **Access:** `SUPER_ADMIN`

---

### Module 12: Audit Logging (`/audit-logs`)

#### `GET /audit-logs`
Queries system-wide audit records.
- **Access:** `SUPER_ADMIN`
- **Query Params:** `user_id`, `action`, `resource_type`, `start_date`, `end_date`, `page`, `size`
- **Response (200 OK):** Paginated list of immutable audit entries with `old_values` and `new_values` JSON structures.
