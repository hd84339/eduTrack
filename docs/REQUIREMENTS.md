# EduTrack — System Requirements Document (SRS)

**Document Version:** 1.1.0<br>
**Status:** Validated for Development Readiness<br>
**Target Platform:** Web Application (React + Vite + FastAPI + PostgreSQL)

---

## 1. Executive Summary & Project Purpose

**EduTrack** is a centralized, multi-center Student Learning & Activity Management Platform designed for educational organizations running distributed learning centers. The platform serves as the single source of truth for:
- Multi-center operational administration.
- Student record keeping and cross-center historical tracking.
- Daily classroom attendance (single-student and bulk entry).
- Curriculum activity templating with normalized multi-competency mapping.
- Individual and group learning session observations with granular competency evaluation.
- Student competency progress tracking and longitudinal reporting.
- Role-based multi-tenant governance with comprehensive, non-cascade audit logging.

The system is architected as a modular monolith to maximize engineering velocity, ensure strict transactional data integrity, and minimize operational deployment overhead while remaining clean and modular for future scaling.

---

## 2. User Roles & Access Hierarchy

EduTrack defines three primary user roles with strictly partitioned operational scopes:

```
                  ┌──────────────────────┐
                  │     SUPER ADMIN      │
                  │ (Organization-Wide)  │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────┐
│    CENTER MANAGER    │          │    CENTER MANAGER    │
│      (Center A)      │          │      (Center B)      │
└───────────┬──────────┘          └───────────┬──────────┘
            │                                 │
     ┌──────┴──────┐                   ┌──────┴──────┐
     ▼             ▼                   ▼             ▼
┌─────────┐   ┌─────────┐         ┌─────────┐   ┌─────────┐
│ TEACHER │   │ TEACHER │         │ TEACHER │   │ TEACHER │
│(Center A│   │(Center A│         │(Center B│   │(Center B│
└─────────┘   └─────────┘         └─────────┘   └─────────┘
```

### 2.1 Role Matrix & Permissions

| Capability / Module | Super Admin | Center Manager | Teacher |
| :--- | :---: | :---: | :---: |
| **Manage Organizations & Settings** | Full | None | None |
| **Create / Modify Learning Centers** | Full | None | None |
| **User Management (Admins & Managers)**| Full | None | None |
| **User Management (Teachers)** | Full | Assigned Center(s) | None |
| **Assign Users to Centers** | Full | Assigned Center(s) (Teachers only) | None |
| **Student Registration & Profiles** | Full | Assigned Center(s) | View Assigned |
| **Initiate Student Transfer** | Full | Assigned Center (Source) | None |
| **Approve / Complete Student Transfer**| Full (Can Override Capacity) | Assigned Center (Destination) | None |
| **Mark Daily Attendance (Single/Bulk)** | Full | Assigned Center(s) | Assigned Center(s) |
| **Correct / Edit Historical Attendance** | Full | Assigned Center(s) | Within 24h of Creation |
| **Manage Competency Catalog** | Full | None | View Only |
| **Create Activity Templates** | Full | Assigned Center(s) | View Only |
| **Log Learning Sessions & Evaluations** | Full | Assigned Center(s) | Assigned Center(s) |
| **View Student Progress & Mastery** | Full | Assigned Center(s) | Assigned Center(s) |
| **Center-Level Operational Reports** | Full | Assigned Center(s) | Class / Cohort Only |
| **Organization-Wide Analytics** | Full | None | None |
| **System Audit Logs Access** | Read-Only (Full) | None | None |

---

## 3. Functional Requirements (FR)

### Module 1: Authentication & Authorization (AUTH)
- **FR-AUTH-01:** System must support email/password authentication issuing cryptographically signed JWT access tokens (short-lived, 30 mins) and refresh tokens (long-lived, 7 days).
- **FR-AUTH-02:** Role-based access control (RBAC) combined with center-level scoping (ABAC) must intercept every API request. Multi-center staff select active center context via an application dropdown in the UI.
- **FR-AUTH-03:** Password policies must enforce a minimum of 8 characters, at least one uppercase letter, one digit, and one special character, hashed via `bcrypt` with cost factor $\ge 12$.
- **FR-AUTH-04:** Tokens must carry minimal claims: `sub` (User ID), `role`, `assigned_centers` (IDs array), and token `exp`/`iat`.

### Module 2: Learning Center Management (CENTERS)
- **FR-CEN-01:** Super Admins can create, update, deactivate, and list learning centers.
- **FR-CEN-02:** Each center stores a unique code (e.g., `CEN-NORTH-01`), display name, physical address, contact details, active status, and capacity limits.
- **FR-CEN-03:** Centers cannot be hard-deleted if associated with existing enrollment, attendance, or session records (soft deactivation with referential integrity).

### Module 3: Student Management (STUDENTS)
- **FR-STU-01:** Support creating and maintaining student demographic records: unique student identification number (`student_id_number`), first/last name, date of birth, gender, primary guardian details (name, contact phone, email, relationship), emergency contact, and general non-sensitive administrative notes (`notes`). *Sensitive medical diagnostic data is excluded from the MVP scope to maintain strict privacy compliance.*
- **FR-STU-02:** Maintain current status: `ACTIVE`, `INACTIVE`, `TRANSFERRED`, `GRADUATED`, `SUSPENDED`.
- **FR-STU-03:** Provide full-text and parameterized searching (by name, student ID, center, and active status) with standard pagination.
- **FR-STU-04:** Support optimistic concurrency control via a `version` integer column to avoid concurrent overwrites during profile updates.

### Module 4: Student Enrollment & Center Transfers (TRANSFERS)
- **FR-ENR-01:** Record all enrollment history. When a student joins a center, an initial `EnrollmentRecord` is created with `start_date`, status `ACTIVE`, and `end_date = NULL`.
- **FR-ENR-02:** **Single Active Enrollment Guarantee:** A student can have only **one** active enrollment at any calendar moment. Enforced via a PostgreSQL partial unique index (`WHERE status = 'ACTIVE' AND end_date IS NULL`) and non-overlapping date range validation (`end_date IS NULL OR end_date >= start_date`).
- **FR-ENR-03:** **Atomic Cross-Center Transfers:**
  1. Source center manager initiates transfer request specifying destination center, reason, and effective date (`status = PENDING`).
  2. Target center manager or Super Admin reviews the request.
  3. Destination center capacity is checked against active enrollments. If full, approval is blocked unless a Super Admin executes a **Capacity Override** with a mandatory justification note.
  4. Upon approval, execute within a **single atomic database transaction**:
     - Close previous enrollment record (`end_date = effective_date`, `status = TRANSFERRED`).
     - Insert new enrollment record for destination center (`start_date = effective_date`, `end_date = NULL`, `status = ACTIVE`).
     - Update student record: `current_center_id = to_center_id`, increment `version`.
     - Update transfer request: `status = APPROVED`, approver ID, review timestamp, notes.
     - Insert audit log entry capturing transfer transition and any capacity override reason.
     - All prior historical attendance and learning records remain linked to historical centers.

### Module 5: Attendance Management (ATTENDANCE)
- **FR-ATT-01:** Daily attendance tracking supporting statuses: `PRESENT`, `ABSENT`, `LATE`, `EXCUSED`.
- **FR-ATT-02:** **Duplicate Prevention & Date Validation:** Strictly enforce exactly one attendance record per student per calendar date via database constraint: `UNIQUE (student_id, attendance_date)`. Future date attendance is prevented via backend service validation against center local timezone (avoiding fragile database-level `CURRENT_DATE` checks).
- **FR-ATT-03:** **Enrollment Date Alignment:** Attendance can only be recorded if the student has an active enrollment at the target center covering the attendance date (`start_date <= attendance_date AND (end_date IS NULL OR end_date >= attendance_date)`).
- **FR-ATT-04:** **Bulk Attendance Submission:** Teachers can submit attendance for an entire classroom in a single atomic payload. If any row violates business constraints, the transaction rolls back atomically.
- **FR-ATT-05:** **Attendance Correction & Traceability:**
  - Any modification to an attendance record creates an immutable entry in `attendance_audit_logs` detailing: `previous_status`, `new_status`, `changed_by_user_id`, `reason_for_change`, and timestamp.
  - Teachers may correct attendance within **24 hours of record creation** (`created_at + INTERVAL '24 hours'`). Beyond 24 hours, corrections require Center Manager or Super Admin privileges with a mandatory justification note.
  - Audit logs have referential integrity `ON DELETE RESTRICT` to guarantee audit trail preservation.

### Module 6: Learning Activity Management (ACTIVITIES)
- **FR-ACT-01:** Support standardized **Activity Templates** created by Super Admins and Center Managers.
- **FR-ACT-02:** **Normalized Competency Association:** Activity templates link to one or more standardized competencies from a central `competencies` catalog through a normalized junction table (`activity_competencies`), designating primary and secondary competencies.
- **FR-ACT-03:** Templates define: title, subject area, description, target age range, standard duration in minutes, and active status.
- **FR-ACT-04:** Templates can be marked `GLOBAL` (all centers) or `CENTER_SPECIFIC` (local center only).

### Module 7: Learning Session Management (SESSIONS)
- **FR-SES-01:** Teachers log conducted learning sessions based on an Activity Template.
- **FR-SES-02:** Sessions record: center ID, instructor user ID, activity template ID, session date, start time, end time, topic summary, and general notes. Backend validates: `end_time >= start_time`, duration $\ge 5$ minutes, and session date cannot be in the future.
- **FR-SES-03:** **Normalized Multi-Competency Student Evaluations:**
  - For each participating student, records overall participation status (`COMPLETED`, `PARTIAL`, `ABSENT`), qualitative feedback, and optional overall score ($0.0 \le score \le 100.0$, must be `NULL` if absent).
  - For each competency targeted by the activity, records granular mastery assessment (`EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`) and teacher observational notes in `session_student_evaluations`.
- **FR-SES-04:** Sessions require that participating students were actively enrolled at the conducting center on the session date.

### Module 8: Student Progress Tracking (PROGRESS)
- **FR-PRG-01:** Automatically compute and aggregate student competency progression over time based on logged session observations across the 4-tier rubric.
- **FR-PRG-02:** Store normalized cumulative mastery in `student_skill_progress` referencing `competency_id`, updating total sessions count and latest evaluation timestamp.
- **FR-PRG-03:** Highlight learning gaps: identify competencies where a student remains at `EMERGING` or `DEVELOPING` after $N$ logged sessions.

### Module 9: Dashboard & Analytics (ANALYTICS)
- **FR-DSH-01:** Center-level dashboard for Center Managers:
  - Total active student count and capacity occupancy percentage.
  - Daily attendance rate (today, this week, 30-day moving average).
  - Sessions completed this week vs targets.
  - Pending incoming and outgoing transfer requests.
- **FR-DSH-02:** Organization-wide dashboard for Super Admins:
  - Center comparison benchmarks (attendance %, active students per center, activity volume).
  - System-wide growth trends (enrollment vs withdrawals/graduations).
- **FR-DSH-03:** Aggregations powered by indexed relational queries without in-memory calculation bottlenecks.

### Module 10: Reports (REPORTS)
- **FR-REP-01:** Attendance summary reports: filterable by center, date range, cohort, and status; exportable to CSV and JSON formats.
- **FR-REP-02:** Student comprehensive dossier: printable summary containing student bio, historical center enrollments, attendance rate, and competency mastery timeline.
- **FR-REP-03:** Center operational efficiency reports: teacher activity log volume, session frequencies, and transfer turnaround latency.

### Module 11: User & Role Management (USERS)
- **FR-USR-01:** Create and manage staff accounts: email, full name, phone, role (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`), and account status (`ACTIVE`, `INACTIVE`, `LOCKED`).
- **FR-USR-02:** Center-Staff Association: Assign Center Managers and Teachers to one or more centers via `user_centers`. Multi-center teachers toggle active center context via UI dropdown.
- **FR-USR-03:** User deactivation preserves referential integrity; foreign keys to user records for attendance/audit are preserved.

### Module 12: Audit Logging (AUDIT)
- **FR-AUD-01:** System maintains an append-only, immutable `audit_logs` table. Audit records cannot be deleted through cascading foreign keys (`ON DELETE RESTRICT` or `SET NULL`).
- **FR-AUD-02:** Critical events recorded:
  - User authentication and failed login attempts.
  - Student record creation, updates, and status changes.
  - Transfer initiation, review, approval, rejection, and capacity overrides.
  - Attendance corrections and retroactive modifications.
  - User role and center assignment alterations.
- **FR-AUD-03:** Every audit record captures: `timestamp`, `user_id`, `client_ip`, `action`, `resource_type`, `resource_id`, `old_values` (JSONB), and `new_values` (JSONB).

---

## 4. Non-Functional Requirements (NFR)

### 4.1 Performance & Latency
- **NFR-PERF-01:** Standard CRUD API endpoints must respond with $p95 < 150\text{ ms}$ under nominal load.
- **NFR-PERF-02:** Bulk attendance ingestion (up to 100 students in a single batch) must process and commit in $< 500\text{ ms}$.
- **NFR-PERF-03:** Analytics dashboard aggregations must respond in $< 300\text{ ms}$ utilizing composite indexes and targeted aggregate projections.

### 4.2 Data Integrity & Concurrency
- **NFR-INT-01:** ACID transactions must wrap all multi-table mutations (student transfers, bulk attendance, and session evaluations).
- **NFR-INT-02:** Optimistic Concurrency Control (OCC) must be enforced on concurrent mutable entities (`students`, `attendance_records`) using integer version tags. An edit submitted with a stale version must fail with HTTP `409 Conflict`.
- **NFR-INT-03:** Strict foreign keys and database constraints prevent orphan records and invalid domain states. Date boundaries (e.g. future dates) are validated in backend application business logic against center local time.

### 4.3 Security & Compliance
- **NFR-SEC-01:** All passwords stored using adaptive one-way hashing (`bcrypt` with cost factor $\ge 12$).
- **NFR-SEC-02:** All endpoints (except public authentication routes) require valid JWT bearer tokens in the `Authorization` header.
- **NFR-SEC-03:** Center isolation: An authenticated user can never access or modify data belonging to a center they are not actively mapped to, verified at the backend service/dependency layer.
- **NFR-SEC-04:** Protection against OWASP Top 10 vulnerabilities: SQL injection mitigated via SQLAlchemy parameterized queries; XSS mitigated via React output escaping; CSRF mitigated via Stateless JWT architecture.

### 4.4 Reliability & Maintainability
- **NFR-REL-01:** Modular monolithic codebase: clean boundaries between business domains enabling future migration to independent services if organization size demands it.
- **NFR-REL-02:** Database schema migrations must be fully automated, tracked, and reversible via Alembic.
- **NFR-REL-03:** Comprehensive structured logging (JSON formatted in production) capturing request correlation IDs.

---

## 5. Business Rules (BR)

- **BR-01 (Single Daily Attendance):** A student cannot have more than one attendance record per calendar day across the entire system.
- **BR-02 (Active Center Enrollment):** Attendance and learning sessions can only be recorded for students who have an `ACTIVE` enrollment at that center covering the event date (`start_date <= event_date AND (end_date IS NULL OR end_date >= event_date)`).
- **BR-03 (Transfer Integrity & Capacity):** A student cannot be transferred to the same center they currently reside in. A transfer cannot be approved if the destination center is at maximum capacity, unless a Super Admin executes an approved capacity override with an audit explanation.
- **BR-04 (Attendance Edit Window):** Teachers can edit attendance records created by themselves within 24 hours of creation (`created_at + INTERVAL '24 hours'`). Edits after 24 hours require Center Manager or Super Admin privileges and a mandatory justification note.
- **BR-05 (Audit Immutability):** Records in `audit_logs` and `attendance_audit_logs` can never be edited or deleted by any user, including Super Admins. Foreign keys must never cascade-delete audit entries.
- **BR-06 (No Overwrite Policy):** Concurrent updates to student records or attendance are governed by Optimistic Concurrency Control (OCC). Stale versions trigger an immediate HTTP `409 Conflict`.
- **BR-07 (Multi-Center Teacher Scope):** Teachers assigned to multiple centers operate within one active center context at a time, selectable via an application header dropdown in the MVP.

---

## 6. Edge Cases & Handling Strategies

1. **Retroactive Attendance for Transferred Student:**
   - *Scenario:* A teacher needs to mark or correct attendance for last Friday, but the student was transferred to another center on Monday.
   - *Handling:* The system queries historical `enrollment_records`. Because the student was enrolled in the teacher's center on Friday, the operation is permitted, attributing the attendance to the historical center.
2. **Bulk Attendance with Mixed Student States:**
   - *Scenario:* A teacher submits bulk attendance for 30 students, but 1 student was transferred or deactivated earlier that morning.
   - *Handling:* The transaction validates every student's active enrollment for the date. The entire batch fails atomically with a 422 Unprocessable Entity detailing the specific invalid student ID.
3. **Mid-Day Transfer Collision:**
   - *Scenario:* Student transfer takes effect on date $D$, and attendance was already marked at Center 1 on date $D$. Center 2 attempts to mark attendance on date $D$.
   - *Handling:* Database constraint `UNIQUE (student_id, attendance_date)` triggers a conflict. System prevents duplicate recording and alerts the user that attendance was already captured at Center 1.
4. **Network Re-try / Double Submission:**
   - *Scenario:* A teacher clicks "Submit Attendance" twice due to network latency.
   - *Handling:* Database unique constraint rejects the second write gracefully without creating duplicates or corrupting audit tables.

---

## 7. MVP Scope Definition

### In-Scope for MVP (Phase 1):
1. Complete Authentication & RBAC (Super Admin, Center Manager, Teacher) with UI center switcher.
2. Multi-center management and user-to-center assignments.
3. Student profile CRUD with version-based OCC (excluding sensitive medical data).
4. Student enrollment lifecycle and atomic center-to-center transfers with Super Admin capacity override.
5. Single and Bulk Daily Attendance with unique constraint enforcement, timezone date check, and 24h correction audit trail.
6. Normalized competency catalog and activity templates.
7. Learning session logging with multi-competency student observation scorecards.
8. Basic student competency progress view across the 4-tier rubric.
9. Operational center dashboard and super admin metrics overview.
10. Immutable audit logging for all critical operations.

### Out-of-Scope for MVP (Deferred to Phase 2):
1. Automated email/SMS notifications for student absence or transfer requests.
2. Direct parent portal login and guardian communications.
3. Offline-first PWA sync for attendance recording in low-connectivity areas.
4. Custom printable certificate generation and rich report card builder.
5. Biometric hardware integration for attendance capture.
6. In-depth medical diagnostic and health tracking module.
