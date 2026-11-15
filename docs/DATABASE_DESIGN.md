# EduTrack — Database Design & Schema Specification

**Database Engine:** PostgreSQL 15+  
**ORM / Migration:** SQLAlchemy 2.0 / Alembic  
**Primary Key Convention:** UUIDv4 (`gen_random_uuid()` / `uuid_generate_v4()`)  
**Naming Conventions:** Table names: `plural_snake_case`; Column names: `snake_case`  

---

## 1. Schema Overview & Architecture Principles

The EduTrack relational schema is designed with the following core principles:
1. **Referential Integrity:** All relationships enforce foreign keys. Destructive cascading deletes (`CASCADE`) are disabled on operational data; foreign keys use `RESTRICT` or `SET NULL` to prevent accidental data loss.
2. **Immutability of Historical Data:** When a student transfers, historical attendance and session records maintain pointers to the centers where they occurred.
3. **Explicit Concurrency Control:** Concurrently editable tables (`students`, `attendance_records`) feature an integer `version` column for Optimistic Concurrency Control (OCC).
4. **Zero-Duplicate Attendance:** A compound unique index `UNIQUE (student_id, attendance_date)` strictly prevents more than one record per student per calendar day.
5. **Traceability:** Dedicated audit tables capture mutations, state transitions, and actor identities.

---

## 2. Enumerated Types (PostgreSQL ENUMs)

```sql
CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'CENTER_MANAGER', 'TEACHER');
CREATE TYPE user_status AS ENUM ('ACTIVE', 'INACTIVE', 'LOCKED');
CREATE TYPE student_status AS ENUM ('ACTIVE', 'INACTIVE', 'TRANSFERRED', 'GRADUATED', 'SUSPENDED');
CREATE TYPE enrollment_status AS ENUM ('ACTIVE', 'TRANSFERRED', 'COMPLETED', 'WITHDRAWN');
CREATE TYPE transfer_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED');
CREATE TYPE attendance_status AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED');
CREATE TYPE session_participation_status AS ENUM ('COMPLETED', 'PARTIAL', 'ABSENT');
CREATE TYPE mastery_level AS ENUM ('EMERGING', 'DEVELOPING', 'PROFICIENT', 'MASTERY');
```

---

## 3. Table Definitions & Specifications

### 3.1 `users`
Stores user identities, login credentials, and roles.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Unique user identifier |
| `email` | `VARCHAR(255)` | `NOT NULL UNIQUE` | Normalized login email address |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Adaptive bcrypt password hash |
| `full_name` | `VARCHAR(150)` | `NOT NULL` | Display name of staff member |
| `phone_number` | `VARCHAR(30)` | `NULL` | Contact phone number |
| `role` | `user_role` | `NOT NULL` | System role for RBAC |
| `status` | `user_status` | `NOT NULL DEFAULT 'ACTIVE'` | Account state |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record last updated timestamp |

- **Indexes:**
  - `idx_users_email` ON `users(email)`
  - `idx_users_role_status` ON `users(role, status)`

---

### 3.2 `centers`
Stores learning center entities across the organization.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Unique center identifier |
| `code` | `VARCHAR(30)` | `NOT NULL UNIQUE` | Organization center code (e.g. `CEN-01`) |
| `name` | `VARCHAR(150)` | `NOT NULL` | Center name (e.g. `North Ridge Center`) |
| `address` | `TEXT` | `NOT NULL` | Physical address |
| `contact_phone`| `VARCHAR(30)` | `NULL` | Official center phone |
| `contact_email`| `VARCHAR(255)` | `NULL` | Official center email |
| `capacity` | `INTEGER` | `NOT NULL DEFAULT 100` | Max active student capacity |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Soft-activation status flag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Center creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Center update timestamp |

- **Indexes:**
  - `idx_centers_code` ON `centers(code)`
  - `idx_centers_is_active` ON `centers(is_active)`

---

### 3.3 `user_centers` (Junction Table)
Maps staff (Center Managers & Teachers) to their assigned learning center(s).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Junction ID |
| `user_id` | `UUID` | `NOT NULL REFERENCES users(id) ON DELETE CASCADE` | Assigned staff member |
| `center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE CASCADE` | Assigned learning center |
| `assigned_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Assignment timestamp |

- **Constraints & Indexes:**
  - `UNIQUE (user_id, center_id)`
  - `idx_user_centers_user` ON `user_centers(user_id)`
  - `idx_user_centers_center` ON `user_centers(center_id)`

---

### 3.4 `students`
Stores current student profile information and demographics.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Unique student ID |
| `student_id_number` | `VARCHAR(50)` | `NOT NULL UNIQUE` | Official organization student ID |
| `current_center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Active center assignment |
| `first_name` | `VARCHAR(100)` | `NOT NULL` | Student first name |
| `last_name` | `VARCHAR(100)` | `NOT NULL` | Student last name |
| `date_of_birth` | `DATE` | `NOT NULL` | Birth date |
| `gender` | `VARCHAR(20)` | `NOT NULL` | Gender representation |
| `guardian_name` | `VARCHAR(150)` | `NOT NULL` | Primary guardian name |
| `guardian_phone`| `VARCHAR(30)` | `NOT NULL` | Guardian contact number |
| `guardian_email`| `VARCHAR(255)` | `NULL` | Guardian contact email |
| `guardian_relationship` | `VARCHAR(50)` | `NOT NULL DEFAULT 'Parent'` | Relationship to student |
| `emergency_contact` | `TEXT` | `NULL` | Backup contact info |
| `medical_notes` | `TEXT` | `NULL` | Allergies, special needs |
| `status` | `student_status`| `NOT NULL DEFAULT 'ACTIVE'` | Current status |
| `version` | `INTEGER` | `NOT NULL DEFAULT 1` | Optimistic Concurrency version |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record update timestamp |

- **Indexes:**
  - `idx_students_student_id_number` ON `students(student_id_number)`
  - `idx_students_center_status` ON `students(current_center_id, status)`
  - `idx_students_name` ON `students(last_name, first_name)`

---

### 3.5 `enrollment_records`
Historical registry of center enrollments for longitudinal tracking.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Record ID |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE RESTRICT` | Associated student |
| `center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Enrolled center |
| `start_date` | `DATE` | `NOT NULL` | Enrollment start date |
| `end_date` | `DATE` | `NULL` | Enrollment end date (NULL if active) |
| `status` | `enrollment_status` | `NOT NULL DEFAULT 'ACTIVE'` | Enrollment status |
| `notes` | `TEXT` | `NULL` | Administrative remarks |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record update timestamp |

- **Indexes:**
  - `idx_enrollment_student` ON `enrollment_records(student_id)`
  - `idx_enrollment_center_status` ON `enrollment_records(center_id, status)`

---

### 3.6 `transfer_requests`
Manages inter-center student transfer workflow.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Transfer request ID |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE RESTRICT` | Student to transfer |
| `from_center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Current/Source center |
| `to_center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Destination center |
| `requested_by_user_id`| `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Staff who initiated request |
| `reviewed_by_user_id` | `UUID` | `NULL REFERENCES users(id) ON DELETE RESTRICT` | Staff who approved/rejected |
| `status` | `transfer_status` | `NOT NULL DEFAULT 'PENDING'` | Request state |
| `request_reason` | `TEXT` | `NOT NULL` | Justification for transfer |
| `review_notes` | `TEXT` | `NULL` | Approver feedback |
| `effective_date`| `DATE` | `NOT NULL` | Planned transition date |
| `requested_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Submission timestamp |
| `reviewed_at` | `TIMESTAMPTZ` | `NULL` | Approval/rejection timestamp |

- **Check Constraints & Indexes:**
  - `CHECK (from_center_id <> to_center_id)`
  - `idx_transfers_student` ON `transfer_requests(student_id)`
  - `idx_transfers_status` ON `transfer_requests(status)`
  - `idx_transfers_from_center` ON `transfer_requests(from_center_id)`
  - `idx_transfers_to_center` ON `transfer_requests(to_center_id)`

---

### 3.7 `attendance_records`
Daily student attendance ledger.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Attendance entry ID |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE RESTRICT` | Present/absent student |
| `center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Center where marked |
| `recorded_by_user_id`| `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Teacher/staff who marked |
| `attendance_date`| `DATE` | `NOT NULL` | Calendar date of attendance |
| `status` | `attendance_status`| `NOT NULL` | Attendance state |
| `remarks` | `VARCHAR(255)` | `NULL` | Optional note (e.g. sick note) |
| `version` | `INTEGER` | `NOT NULL DEFAULT 1` | Optimistic Concurrency version |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record update timestamp |

- **Unique Constraint (Strict Duplicate Prevention):**
  - `UNIQUE (student_id, attendance_date)`
- **Check Constraints & Indexes:**
  - `CHECK (attendance_date <= CURRENT_DATE)`
  - `idx_attendance_center_date` ON `attendance_records(center_id, attendance_date)`
  - `idx_attendance_student_date` ON `attendance_records(student_id, attendance_date)`

---

### 3.8 `attendance_audit_logs`
Fine-grained change log for attendance corrections.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Log ID |
| `attendance_record_id`| `UUID` | `NOT NULL REFERENCES attendance_records(id) ON DELETE CASCADE`| Altered attendance row |
| `changed_by_user_id` | `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Staff who made correction |
| `previous_status` | `attendance_status` | `NOT NULL` | Old attendance status |
| `new_status` | `attendance_status` | `NOT NULL` | Corrected attendance status |
| `reason` | `TEXT` | `NOT NULL` | Mandatory correction justification |
| `changed_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Timestamp of correction |

- **Indexes:**
  - `idx_att_audit_record` ON `attendance_audit_logs(attendance_record_id)`
  - `idx_att_audit_changed_at` ON `attendance_audit_logs(changed_at)`

---

### 3.9 `activity_templates`
Reusable curriculum activity definitions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Template ID |
| `center_id` | `UUID` | `NULL REFERENCES centers(id) ON DELETE RESTRICT` | NULL if global, Center ID if local |
| `created_by_user_id`| `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Author staff member |
| `title` | `VARCHAR(150)` | `NOT NULL` | Activity title |
| `subject_area` | `VARCHAR(100)` | `NOT NULL` | E.g., Mathematics, Literacy, Science |
| `description` | `TEXT` | `NOT NULL` | Learning objectives and instructions |
| `target_age_min` | `INTEGER` | `NOT NULL DEFAULT 3` | Min target age |
| `target_age_max` | `INTEGER` | `NOT NULL DEFAULT 18` | Max target age |
| `duration_minutes` | `INTEGER` | `NOT NULL DEFAULT 45` | Standard activity duration |
| `competencies` | `JSONB` | `NOT NULL DEFAULT '[]'::jsonb` | Targeted competencies array |
| `is_global` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Flag for org-wide availability |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Active template status |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Update timestamp |

- **Indexes:**
  - `idx_act_templates_subject` ON `activity_templates(subject_area)`
  - `idx_act_templates_center_global` ON `activity_templates(center_id, is_global)`

---

### 3.10 `learning_sessions`
Conducted teaching session instances.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Session instance ID |
| `center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Center where conducted |
| `activity_template_id`| `UUID` | `NOT NULL REFERENCES activity_templates(id) ON DELETE RESTRICT` | Applied template |
| `conducted_by_user_id`| `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Instructor teacher |
| `session_date` | `DATE` | `NOT NULL` | Session date |
| `start_time` | `TIMESTAMPTZ` | `NOT NULL` | Session start time |
| `end_time` | `TIMESTAMPTZ` | `NOT NULL` | Session end time |
| `topic_summary` | `VARCHAR(255)` | `NOT NULL` | Specific focus of this instance |
| `general_notes` | `TEXT` | `NULL` | Overall teacher notes |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Update timestamp |

- **Check Constraints & Indexes:**
  - `CHECK (end_time >= start_time)`
  - `idx_sessions_center_date` ON `learning_sessions(center_id, session_date)`
  - `idx_sessions_teacher` ON `learning_sessions(conducted_by_user_id)`

---

### 3.11 `session_students`
Junction recording individual student participation and observations in a session.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Participation record ID |
| `session_id` | `UUID` | `NOT NULL REFERENCES learning_sessions(id) ON DELETE CASCADE` | Associated session |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE RESTRICT` | Participating student |
| `participation_status`| `session_participation_status` | `NOT NULL DEFAULT 'COMPLETED'` | Completion state |
| `mastery_level` | `mastery_level` | `NOT NULL` | Observed competency level |
| `qualitative_feedback`| `TEXT` | `NULL` | Individual teacher feedback |
| `score` | `NUMERIC(5,2)` | `NULL` | Numeric score (optional, 0-100) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Entry timestamp |

- **Constraints & Indexes:**
  - `UNIQUE (session_id, student_id)`
  - `idx_session_students_student` ON `session_students(student_id)`
  - `idx_session_students_session` ON `session_students(session_id)`

---

### 3.12 `student_skill_progress`
Aggregated mastery index per student per competency.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Progress record ID |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE CASCADE` | Associated student |
| `competency_key` | `VARCHAR(100)` | `NOT NULL` | Unique skill identifier (e.g. `MATH-FRAC-01`)|
| `current_level` | `mastery_level` | `NOT NULL` | Current aggregated mastery level |
| `total_sessions_count`| `INTEGER` | `NOT NULL DEFAULT 1` | Cumulative sessions attended for skill |
| `last_evaluated_at` | `TIMESTAMPTZ` | `NOT NULL` | Date of latest assessment |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Calculation update timestamp |

- **Constraints & Indexes:**
  - `UNIQUE (student_id, competency_key)`
  - `idx_skill_progress_student` ON `student_skill_progress(student_id)`

---

### 3.13 `audit_logs`
Global immutable security and operational audit trail.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Audit event ID |
| `user_id` | `UUID` | `NULL REFERENCES users(id) ON DELETE SET NULL` | Actor user (NULL for system) |
| `action` | `VARCHAR(50)` | `NOT NULL` | E.g. `CREATE`, `UPDATE`, `TRANSFER_APPROVE`|
| `resource_type` | `VARCHAR(50)` | `NOT NULL` | E.g. `STUDENT`, `ATTENDANCE`, `TRANSFER` |
| `resource_id` | `UUID` | `NOT NULL` | ID of altered target |
| `client_ip` | `VARCHAR(45)` | `NULL` | IPv4 or IPv6 client address |
| `old_values` | `JSONB` | `NULL` | State prior to modification |
| `new_values` | `JSONB` | `NULL` | State after modification |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Timestamp of event |

- **Indexes:**
  - `idx_audit_resource` ON `audit_logs(resource_type, resource_id)`
  - `idx_audit_user_created` ON `audit_logs(user_id, created_at)`
  - `idx_audit_created_at` ON `audit_logs(created_at DESC)`
