# EduTrack — System Requirements Document (SRS)

**Document Version:** 1.0.0  
**Status:** Approved for Architecture & Design  
**Target Platform:** Web Application (React + Vite + FastAPI + PostgreSQL)  

---

## 1. Executive Summary & Project Purpose

**EduTrack** is a centralized, multi-center Student Learning & Activity Management Platform designed for educational organizations running distributed learning centers. The platform serves as the single source of truth for:
- Multi-center operational administration.
- Student record keeping and cross-center historical tracking.
- Daily classroom attendance (single-student and bulk entry).
- Curriculum activity templating and individual/group learning session recording.
- Student competency progress tracking and longitudinal reporting.
- Role-based multi-tenant governance with comprehensive audit logging.

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
| **Approve / Complete Student Transfer**| Full | Assigned Center (Destination) | None |
| **Mark Daily Attendance (Single/Bulk)** | Full | Assigned Center(s) | Assigned Center(s) |
| **Correct / Edit Historical Attendance** | Full | Assigned Center(s) | Within Grace Window (24h) |
| **Create Activity Templates** | Full | Assigned Center(s) | View Only |
| **Log Learning Sessions** | Full | Assigned Center(s) | Assigned Center(s) |
| **View Student Progress & Mastery** | Full | Assigned Center(s) | Assigned Center(s) |
| **Center-Level Operational Reports** | Full | Assigned Center(s) | Class / Cohort Only |
| **Organization-Wide Analytics** | Full | None | None |
| **System Audit Logs Access** | Read-Only (Full) | None | None |

---

## 3. Functional Requirements (FR)

### Module 1: Authentication & Authorization (AUTH)
- **FR-AUTH-01:** System must support email/password authentication issuing cryptographically signed JWT access tokens (short-lived, e.g., 30 mins) and refresh tokens (long-lived, e.g., 7 days).
- **FR-AUTH-02:** Role-based access control (RBAC) combined with center-level scoping (Attribute-Based Access Control / ABAC filter) must intercept every API request.
- **FR-AUTH-03:** Password policies must enforce a minimum of 8 characters, at least one uppercase letter, one digit, and one special character, hashed via `bcrypt` (or `argon2id`).
- **FR-AUTH-04:** Tokens must carry minimal claims: `sub` (User ID), `role`, `assigned_centers` (IDs array), and token `exp`/`iat`.

### Module 2: Learning Center Management (CENTERS)
- **FR-CEN-01:** Super Admins can create, update, deactivate, and list learning centers.
- **FR-CEN-02:** Each center must store a unique code (e.g., `CEN-NORTH-01`), display name, physical address, contact details, active status, and capacity limits.
- **FR-CEN-03:** Centers cannot be hard-deleted if associated with existing enrollment, attendance, or session records (soft deactivation with referential integrity).

### Module 3: Student Management (STUDENTS)
- **FR-STU-01:** Support creating and maintaining complete student demographic records: unique student identification number (`student_id_number`), first/last name, date of birth, gender, primary guardian details (name, contact phone, email, relationship), emergency contact, and medical/dietary notes.
- **FR-STU-02:** Maintain current status: `ACTIVE`, `INACTIVE`, `TRANSFERRED`, `GRADUATED`, `SUSPENDED`.
- **FR-STU-03:** Provide full-text and parameterized searching (by name, student ID, center, grade level, and active status) with cursor or offset pagination.
- **FR-STU-04:** Support optimistic concurrency control via a `version` integer column to avoid concurrent overwrites during profile updates.

### Module 4: Student Enrollment & Center Transfers (TRANSFERS)
- **FR-ENR-01:** Record all enrollment history. When a student joins a center, an initial `EnrollmentRecord` is created with `start_date`, status `ACTIVE`, and `end_date = NULL`.
- **FR-ENR-02:** A student can have only **one** active enrollment at any given calendar moment.
- **FR-ENR-03:** Support cross-center transfer requests:
  1. Source center manager initiates transfer request specifying target center, reason, and effective date (`status = PENDING`).
  2. Target center manager (or Super Admin) reviews and approves or rejects the request.
  3. Upon approval within a database transaction:
     - The previous enrollment record is closed with `end_date` and marked `TRANSFERRED`.
     - A new enrollment record is opened for the destination center.
     - The student's `current_center_id` is atomically updated.
     - All prior historical attendance and learning records remain linked to the historical centers where they occurred.

### Module 5: Attendance Management (ATTENDANCE)
- **FR-ATT-01:** Daily attendance tracking supporting statuses: `PRESENT`, `ABSENT`, `LATE`, `EXCUSED`.
- **FR-ATT-02:** **Duplicate Prevention:** Strictly enforce exactly one attendance record per student per calendar date via a unique constraint: `UNIQUE (student_id, attendance_date)`.
- **FR-ATT-03:** **Bulk Attendance Submission:** Teachers can submit attendance for an entire classroom/batch in a single atomic payload. If any row violates business constraints, the transaction rolls back with granular error validation.
- **FR-ATT-04:** **Attendance Correction & Traceability:**
  - Any modification to an existing attendance record requires recording an entry in `attendance_audit_logs` detailing: `previous_status`, `new_status`, `changed_by_user_id`, `reason_for_change`, and timestamp.
  - Teachers may correct attendance within 24 hours of recording. Beyond 24 hours, correction requires Center Manager or Super Admin approval/privileges.

### Module 6: Learning Activity Management (ACTIVITIES)
- **FR-ACT-01:** Support standard **Activity Templates** created by Super Admins and Center Managers.
- **FR-ACT-02:** Templates define: title, subject/domain (e.g., Literacy, STEM, Arts, Motor Skills), description, target age/grade range, standard learning outcomes/competencies, and default duration in minutes.
- **FR-ACT-03:** Templates can be marked `GLOBAL` (usable across all centers) or `CENTER_SPECIFIC` (visible only to assigned center).

### Module 7: Learning Session Management (SESSIONS)
- **FR-SES-01:** Teachers log conducted learning sessions based on an Activity Template.
- **FR-SES-02:** A session can be individual (one student) or group (multiple participating students).
- **FR-SES-03:** For each participating student, the session captures: participation status (`COMPLETED`, `PARTIAL`, `ABSENT`), observed mastery level (e.g., `EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`), teacher qualitative notes, and performance scores.
- **FR-SES-04:** Ensure sessions are timestamped and tied to the center where the session was physically conducted.

### Module 8: Student Progress Tracking (PROGRESS)
- **FR-PRG-01:** Automatically compute and aggregate student competency progression over time based on logged session observations.
- **FR-PRG-02:** Provide historical skill mastery timelines: display date-stamped ratings and qualitative feedback per learning competency.
- **FR-PRG-03:** Highlight learning gaps: identify competencies where a student hasn't reached target proficiency after $N$ sessions.

### Module 9: Dashboard & Analytics (ANALYTICS)
- **FR-DSH-01:** Center-level dashboard for Center Managers:
  - Total active student count.
  - Daily attendance rate (today, this week, 30-day moving average).
  - Sessions completed this week vs targets.
  - Pending transfer requests (incoming and outgoing).
- **FR-DSH-02:** Organization-wide dashboard for Super Admins:
  - Center comparison benchmarks (attendance %, active students per center, activity coverage).
  - System-wide growth trends (enrollment vs dropouts/graduations).
- **FR-DSH-03:** Real-time summary views powered by indexed relational aggregation queries.

### Module 10: Reports (REPORTS)
- **FR-REP-01:** Attendance summary reports: filterable by center, date range, cohort, and status; exportable to CSV and JSON formats.
- **FR-REP-02:** Student comprehensive dossier: PDF/print-ready view containing student bio, historical center enrollments, attendance rate, and session mastery timeline.
- **FR-REP-03:** Center operational efficiency reports: teacher activity log volume, session frequencies, and transfer turnaround latency.

### Module 11: User & Role Management (USERS)
- **FR-USR-01:** Create and manage staff accounts: email, full name, phone, role (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`), and account status (`ACTIVE`, `INACTIVE`, `LOCKED`).
- **FR-USR-02:** Center-Staff Association: Assign Center Managers and Teachers to one or more centers via many-to-many associations.
- **FR-USR-03:** Password reset workflows, account deactivation without breaking historical references (foreign keys to user records for attendance/audit are preserved).

### Module 12: Audit Logging (AUDIT)
- **FR-AUD-01:** System must maintain an append-only, immutable `audit_logs` table.
- **FR-AUD-02:** Critical events recorded:
  - User login/logout and failed authentication attempts.
  - Student record creation, modification, and status transitions.
  - Transfer initiation, approval, and rejection.
  - Attendance overrides and retrospective updates.
  - User role and center assignment alterations.
- **FR-AUD-03:** Every audit record captures: `timestamp`, `user_id`, `client_ip`, `action` (CREATE, UPDATE, DELETE, OVERRIDE), `resource_type`, `resource_id`, `old_values` (JSONB), and `new_values` (JSONB).

---

## 4. Non-Functional Requirements (NFR)

### 4.1 Performance & Latency
- **NFR-PERF-01:** Standard CRUD API endpoints must respond with $p95 < 150\text{ ms}$ under nominal load.
- **NFR-PERF-02:** Bulk attendance ingestion (up to 100 students in a single batch) must process and commit in $< 500\text{ ms}$.
- **NFR-PERF-03:** Analytics dashboard aggregations must respond in $< 300\text{ ms}$ utilizing composite indexes and targeted aggregate projections.

### 4.2 Data Integrity & Concurrency
- **NFR-INT-01:** ACID transactions must wrap all multi-table mutations (e.g., student transfer execution, bulk attendance, audit logging alongside mutation).
- **NFR-INT-02:** Optimistic Concurrency Control (OCC) must be enforced on concurrent mutable entities (e.g., student profile updates) using integer version tags. An edit submitted with a stale version must fail with HTTP `409 Conflict`.
- **NFR-INT-03:** Strict foreign keys and database check constraints must prevent orphan records and invalid domain states (e.g., `CHECK (attendance_date <= CURRENT_DATE)`).

### 4.3 Security & Compliance
- **NFR-SEC-01:** All passwords stored using standard adaptive one-way hashing algorithms (`bcrypt` with cost factor $\ge 12$).
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
- **BR-02 (Active Center Enrollment):** Attendance and learning sessions can only be recorded for students who have an `ACTIVE` enrollment at that center on the given date.
- **BR-03 (Transfer Integrity):** A student cannot be transferred to the same center they currently reside in. A transfer cannot be approved if the student has pending unresolved transfer requests elsewhere.
- **BR-04 (Attendance Edit Window):** Teachers can edit attendance records created by themselves within 24 hours. Edits after 24 hours require Center Manager authorization and mandatory justification note.
- **BR-05 (Audit Immutability):** Records in `audit_logs` and `attendance_audit_logs` can never be edited or deleted by any user, including Super Admins.
- **BR-06 (No Overwrite Policy):** If two managers attempt to edit the same student profile simultaneously, the second submitter must receive an OCC conflict notification and be forced to refresh.

---

## 6. Edge Cases & Handling Strategies

1. **Retroactive Attendance for Transferred Student:**
   - *Scenario:* A teacher needs to mark or correct attendance for last Friday, but the student was transferred to another center on Monday.
   - *Handling:* The system queries historical `enrollment_records`. If the student was enrolled in the teacher's center on the target date, the operation is permitted, attributing the attendance to the historical center.
2. **Bulk Attendance with Mixed Student States:**
   - *Scenario:* A teacher submits bulk attendance for 30 students, but 1 student was transferred or deactivated earlier in the morning.
   - *Handling:* The transaction validates every student's eligibility. The entire batch fails atomically with a 422 Unprocessable Entity detailing the specific invalid student ID, preventing partial or inconsistent classroom states.
3. **Mid-Day Transfer Collision:**
   - *Scenario:* Student transfer takes effect on date $D$, and attendance was already marked at Center 1 on date $D$. Center 2 attempts to mark attendance on date $D$.
   - *Handling:* Database constraint `UNIQUE (student_id, attendance_date)` triggers a conflict. System prevents duplicate recording and alerts the user that attendance was already captured at Center 1.
4. **Network Re-try / Double Submission:**
   - *Scenario:* A teacher clicks "Submit Attendance" twice due to network latency.
   - *Handling:* Database unique constraint rejects the second write gracefully without creating duplicates or corrupting audit tables.

---

## 7. MVP Scope Definition

To ensure disciplined execution without feature creep, the project is partitioned into MVP (Phase 1) and Post-MVP enhancements:

### In-Scope for MVP (Phase 1):
1. Complete Authentication & RBAC (Super Admin, Center Manager, Teacher).
2. Multi-center management and user-to-center assignments.
3. Student profile CRUD with version-based OCC.
4. Student enrollment lifecycle and center-to-center transfers with approval workflow.
5. Single and Bulk Daily Attendance with unique constraint enforcement and 24h correction audit trail.
6. Activity template library and learning session logging.
7. Basic student competency progress view.
8. Operational center dashboard and super admin metrics overview.
9. Structured audit logging for all critical operations.

### Out-of-Scope for MVP (Deferred to Phase 2):
1. Automated email/SMS notifications for student absence or transfer requests.
2. Direct parent portal login and guardian communications.
3. Offline-first PWA sync for attendance recording in low-connectivity areas.
4. Custom printable certificate generation and rich report card builder.
5. Biometric hardware integration for attendance capture.
