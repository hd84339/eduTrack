# EduTrack — Database Design & Schema Specification

**Database Engine:** PostgreSQL 15+<br>
**ORM / Migration:** SQLAlchemy 2.0 / Alembic<br>
**Primary Key Convention:** UUIDv4 (`gen_random_uuid()` / `uuid_generate_v4()`)<br>
**Naming Conventions:** Table names: `plural_snake_case`; Column names: `snake_case`<br>
**Document Version:** 1.1.0

---

## 1. Schema Overview & Architecture Principles

The EduTrack relational schema is designed with the following core principles:
1. **Referential Integrity & Audit Preservation:** Destructive cascading deletes (`CASCADE`) are strictly disabled on operational and audit records. Audit trails (`attendance_audit_logs`, `audit_logs`) use `ON DELETE RESTRICT` or `SET NULL` so historical records can never be accidentally purged.
2. **Normalized Multi-Competency Model:** Competencies are modeled as first-class relational entities (`competencies`, `activity_competencies`, `session_student_evaluations`), enabling strict foreign-key integrity, multi-competency activity designs, and granular student evaluations.
3. **Immutability of Historical Data:** When a student transfers, historical attendance and session records maintain pointers to the centers where they physically occurred.
4. **Explicit Concurrency Control:** Concurrently editable tables (`students`, `attendance_records`) feature an integer `version` column for Optimistic Concurrency Control (OCC).
5. **Zero-Duplicate Constraints & Clean Indexing:** Duplicate attendance is strictly prevented via `UNIQUE (student_id, attendance_date)`. Redundant duplicate indexes on unique constraint columns are explicitly eliminated to optimize write throughput and reduce storage overhead.
6. **Timezone-Aware Date Boundary:** Date boundary checks (preventing future attendance dates) are enforced at the backend application layer using center local time, avoiding fragile database-level `CURRENT_DATE` checks.

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
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Adaptive bcrypt password hash ($\ge 12$ rounds) |
| `full_name` | `VARCHAR(150)` | `NOT NULL` | Display name of staff member |
| `phone_number` | `VARCHAR(30)` | `NULL` | Contact phone number |
| `role` | `user_role` | `NOT NULL` | System role for RBAC |
| `status` | `user_status` | `NOT NULL DEFAULT 'ACTIVE'` | Account state |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record last updated timestamp |

- **Indexes:**
  - *(Note: `email` is indexed automatically by the `UNIQUE` constraint)*
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
| `timezone` | `VARCHAR(50)` | `NOT NULL DEFAULT 'UTC'` | IANA timezone (e.g. `America/Los_Angeles`)|
| `contact_phone`| `VARCHAR(30)` | `NULL` | Official center phone |
| `contact_email`| `VARCHAR(255)` | `NULL` | Official center email |
| `capacity` | `INTEGER` | `NOT NULL DEFAULT 100 CHECK (capacity > 0)` | Max active student capacity |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Soft-activation status flag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Center creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Center update timestamp |

- **Indexes:**
  - *(Note: `code` is indexed automatically by the `UNIQUE` constraint)*
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
  - `UNIQUE (user_id, center_id)` *(automatically indexes `(user_id, center_id)`)*
  - `idx_user_centers_center` ON `user_centers(center_id)` *(indexes reverse lookup by center)*

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
| `emergency_contact` | `TEXT` | `NULL` | Emergency contact details |
| `notes` | `TEXT` | `NULL` | Non-sensitive administrative notes |
| `status` | `student_status`| `NOT NULL DEFAULT 'ACTIVE'` | Current student status |
| `version` | `INTEGER` | `NOT NULL DEFAULT 1` | Optimistic Concurrency version tag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record update timestamp |

- **Indexes:**
  - *(Note: `student_id_number` is indexed automatically by the `UNIQUE` constraint)*
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
| `end_date` | `DATE` | `NULL` | Enrollment end date (NULL if currently active) |
| `status` | `enrollment_status` | `NOT NULL DEFAULT 'ACTIVE'` | Enrollment status |
| `notes` | `TEXT` | `NULL` | Administrative remarks |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record update timestamp |

- **Constraints & Indexes:**
  - `CHECK (end_date IS NULL OR end_date >= start_date)`
  - **Single Active Enrollment Unique Partial Index:** `CREATE UNIQUE INDEX uq_student_active_enrollment ON enrollment_records (student_id) WHERE status = 'ACTIVE' AND end_date IS NULL;`
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
| `capacity_override` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Flag if Super Admin overrode capacity |
| `capacity_override_reason` | `TEXT` | `NULL` | Mandatory reason if capacity was overriden |
| `effective_date`| `DATE` | `NOT NULL` | Planned transition date |
| `requested_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Submission timestamp |
| `reviewed_at` | `TIMESTAMPTZ` | `NULL` | Approval/rejection timestamp |

- **Check Constraints & Indexes:**
  - `CHECK (from_center_id <> to_center_id)`
  - `CHECK (capacity_override = FALSE OR capacity_override_reason IS NOT NULL)`
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
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE RESTRICT` | Enrolled student |
| `center_id` | `UUID` | `NOT NULL REFERENCES centers(id) ON DELETE RESTRICT` | Center where marked |
| `recorded_by_user_id`| `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Teacher/staff who marked |
| `attendance_date`| `DATE` | `NOT NULL` | Calendar date of attendance |
| `status` | `attendance_status`| `NOT NULL` | Attendance state |
| `remarks` | `VARCHAR(255)` | `NULL` | Optional note |
| `version` | `INTEGER` | `NOT NULL DEFAULT 1` | Optimistic Concurrency version |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Record update timestamp |

- **Unique Constraint & Clean Indexes:**
  - `UNIQUE (student_id, attendance_date)` *(automatically indexes `(student_id, attendance_date)`)*
  - `idx_attendance_center_date` ON `attendance_records(center_id, attendance_date)`
- *Architectural Note: Date boundary checks (preventing future dates) are validated by the FastAPI service layer using center local time, avoiding database-level `CURRENT_DATE` timezone discrepancies.*

---

### 3.8 `attendance_audit_logs`
Fine-grained, immutable change log for attendance corrections.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Log ID |
| `attendance_record_id`| `UUID` | `NOT NULL REFERENCES attendance_records(id) ON DELETE RESTRICT`| Altered attendance row |
| `changed_by_user_id` | `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Staff who made correction |
| `previous_status` | `attendance_status` | `NOT NULL` | Old attendance status |
| `new_status` | `attendance_status` | `NOT NULL` | Corrected attendance status |
| `reason` | `TEXT` | `NOT NULL` | Mandatory correction justification |
| `changed_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Timestamp of correction |

- **Constraints & Indexes:**
  - Referential integrity `ON DELETE RESTRICT` guarantees the audit trail is never destroyed.
  - `idx_att_audit_record` ON `attendance_audit_logs(attendance_record_id)`
  - `idx_att_audit_changed_at` ON `attendance_audit_logs(changed_at)`

---

### 3.9 `competencies` (Normalized Competency Catalog)
Standardized curriculum competencies and learning objectives.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Competency ID |
| `code` | `VARCHAR(50)` | `NOT NULL UNIQUE` | Official competency code (e.g. `MATH-FRAC-01`)|
| `name` | `VARCHAR(150)` | `NOT NULL` | Display title (e.g. `Identifies Unit Fractions`)|
| `domain` | `VARCHAR(100)` | `NOT NULL` | Subject domain (e.g. `Mathematics`, `Literacy`)|
| `description` | `TEXT` | `NULL` | Detailed mastery description & rubrics |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Catalog creation timestamp |

- **Indexes:**
  - *(Note: `code` is indexed automatically by the `UNIQUE` constraint)*
  - `idx_competencies_domain` ON `competencies(domain)`

---

### 3.10 `activity_templates`
Reusable curriculum activity definitions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Template ID |
| `center_id` | `UUID` | `NULL REFERENCES centers(id) ON DELETE RESTRICT` | NULL if global, Center ID if local |
| `created_by_user_id`| `UUID` | `NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Author staff member |
| `title` | `VARCHAR(150)` | `NOT NULL` | Activity title |
| `subject_area` | `VARCHAR(100)` | `NOT NULL` | E.g., Mathematics, Literacy, Science |
| `description` | `TEXT` | `NOT NULL` | Learning objectives and instructions |
| `target_age_min` | `INTEGER` | `NOT NULL DEFAULT 3 CHECK (target_age_min >= 0)` | Min target age |
| `target_age_max` | `INTEGER` | `NOT NULL DEFAULT 18 CHECK (target_age_max >= target_age_min)`| Max target age |
| `duration_minutes` | `INTEGER` | `NOT NULL DEFAULT 45 CHECK (duration_minutes >= 5)` | Standard activity duration |
| `is_global` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Flag for org-wide availability |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Active template status |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Update timestamp |

- **Indexes:**
  - `idx_act_templates_subject` ON `activity_templates(subject_area)`
  - `idx_act_templates_center_global` ON `activity_templates(center_id, is_global)`

---

### 3.11 `activity_competencies` (Junction Table)
Normalized link associating activity templates with one or more competencies.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Junction ID |
| `activity_template_id`| `UUID` | `NOT NULL REFERENCES activity_templates(id) ON DELETE CASCADE`| Associated activity template |
| `competency_id` | `UUID` | `NOT NULL REFERENCES competencies(id) ON DELETE RESTRICT` | Targeted competency |
| `is_primary` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Flag if primary target competency |

- **Constraints & Indexes:**
  - `UNIQUE (activity_template_id, competency_id)`
  - `idx_act_comp_competency` ON `activity_competencies(competency_id)`

---

### 3.12 `learning_sessions`
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

### 3.13 `session_students`
Records student participation and overall feedback for a session.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Participation record ID |
| `session_id` | `UUID` | `NOT NULL REFERENCES learning_sessions(id) ON DELETE CASCADE` | Associated session |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE RESTRICT` | Participating student |
| `participation_status`| `session_participation_status` | `NOT NULL DEFAULT 'COMPLETED'` | Completion state |
| `qualitative_feedback`| `TEXT` | `NULL` | Overall student feedback |
| `score` | `NUMERIC(5,2)` | `NULL CHECK (score IS NULL OR (score >= 0.0 AND score <= 100.0))`| Optional numeric score |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Entry timestamp |

- **Constraints & Indexes:**
  - `UNIQUE (session_id, student_id)` *(automatically indexes `(session_id, student_id)`)*
  - `CHECK (participation_status <> 'ABSENT' OR score IS NULL)`
  - `idx_session_students_student` ON `session_students(student_id)`

---

### 3.14 `session_student_evaluations`
Granular mastery ratings per competency for each participating student in a session.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Evaluation ID |
| `session_student_id` | `UUID` | `NOT NULL REFERENCES session_students(id) ON DELETE CASCADE`| Participating student session row |
| `competency_id` | `UUID` | `NOT NULL REFERENCES competencies(id) ON DELETE RESTRICT` | Evaluated competency |
| `mastery_level` | `mastery_level` | `NOT NULL` | Observed competency level |
| `teacher_notes` | `TEXT` | `NULL` | Competency-specific observation notes |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Evaluation timestamp |

- **Constraints & Indexes:**
  - `UNIQUE (session_student_id, competency_id)`
  - `idx_evaluations_competency` ON `session_student_evaluations(competency_id)`

---

### 3.15 `student_skill_progress`
Aggregated mastery index per student per competency.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Progress record ID |
| `student_id` | `UUID` | `NOT NULL REFERENCES students(id) ON DELETE CASCADE` | Associated student |
| `competency_id` | `UUID` | `NOT NULL REFERENCES competencies(id) ON DELETE RESTRICT` | Associated competency |
| `current_level` | `mastery_level` | `NOT NULL` | Current aggregated mastery level |
| `total_sessions_count`| `INTEGER` | `NOT NULL DEFAULT 1 CHECK (total_sessions_count > 0)` | Cumulative evaluated sessions |
| `last_evaluated_at` | `TIMESTAMPTZ` | `NOT NULL` | Date of latest assessment |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Calculation update timestamp |

- **Constraints & Indexes:**
  - `UNIQUE (student_id, competency_id)` *(automatically indexes `(student_id, competency_id)`)*
  - `idx_skill_progress_competency` ON `student_skill_progress(competency_id)`

---

### 3.16 `audit_logs`
Global immutable security and operational audit trail.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Audit event ID |
| `user_id` | `UUID` | `NULL REFERENCES users(id) ON DELETE SET NULL` | Actor user (NULL for system) |
| `action` | `VARCHAR(50)` | `NOT NULL` | E.g. `CREATE`, `UPDATE`, `TRANSFER_APPROVE`|
| `resource_type` | `VARCHAR(50)` | `NOT NULL` | E.g. `STUDENT`, `ATTENDANCE`, `TRANSFER` |
| `resource_id` | `UUID` | `NOT NULL` | ID of altered target (no cascade delete)|
| `client_ip` | `VARCHAR(45)` | `NULL` | IPv4 or IPv6 client address |
| `old_values` | `JSONB` | `NULL` | State prior to modification |
| `new_values` | `JSONB` | `NULL` | State after modification |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Timestamp of event |

- **Indexes:**
  - `idx_audit_resource` ON `audit_logs(resource_type, resource_id)`
  - `idx_audit_user_created` ON `audit_logs(user_id, created_at)`
  - `idx_audit_created_at` ON `audit_logs(created_at DESC)`
