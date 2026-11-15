# EduTrack — Entity-Relationship (ER) Diagram

This document contains the visual data model for EduTrack, specifying all entities, attributes, primary keys (`PK`), foreign keys (`FK`), and relational cardinalities.

---

## 1. High-Level Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ USER_CENTERS : "assigned_to"
    CENTERS ||--o{ USER_CENTERS : "employs"

    CENTERS ||--o{ STUDENTS : "current_home_of"
    STUDENTS ||--o{ ENROLLMENT_RECORDS : "enrollment_history"
    CENTERS ||--o{ ENROLLMENT_RECORDS : "enrolled_at"

    STUDENTS ||--o{ TRANSFER_REQUESTS : "subject_of"
    CENTERS ||--o{ TRANSFER_REQUESTS : "source_center"
    CENTERS ||--o{ TRANSFER_REQUESTS : "dest_center"
    USERS ||--o{ TRANSFER_REQUESTS : "requested_by"
    USERS ||--o{ TRANSFER_REQUESTS : "reviewed_by"

    STUDENTS ||--o{ ATTENDANCE_RECORDS : "attended_by"
    CENTERS ||--o{ ATTENDANCE_RECORDS : "recorded_at"
    USERS ||--o{ ATTENDANCE_RECORDS : "marked_by"

    ATTENDANCE_RECORDS ||--o{ ATTENDANCE_AUDIT_LOGS : "correction_trail"
    USERS ||--o{ ATTENDANCE_AUDIT_LOGS : "corrected_by"

    CENTERS ||--o{ ACTIVITY_TEMPLATES : "local_templates"
    USERS ||--o{ ACTIVITY_TEMPLATES : "authored_by"

    ACTIVITY_TEMPLATES ||--o{ LEARNING_SESSIONS : "template_instance"
    CENTERS ||--o{ LEARNING_SESSIONS : "conducted_at"
    USERS ||--o{ LEARNING_SESSIONS : "instructor"

    LEARNING_SESSIONS ||--|{ SESSION_STUDENTS : "includes"
    STUDENTS ||--o{ SESSION_STUDENTS : "attends"

    STUDENTS ||--o{ STUDENT_SKILL_PROGRESS : "tracks"
    USERS ||--o{ AUDIT_LOGS : "performed_by"

    USERS {
        uuid id PK
        string email
        string password_hash
        string full_name
        string role
        string status
        timestamptz created_at
    }

    CENTERS {
        uuid id PK
        string code
        string name
        string address
        int capacity
        boolean is_active
        timestamptz created_at
    }

    USER_CENTERS {
        uuid id PK
        uuid user_id FK
        uuid center_id FK
        timestamptz assigned_at
    }

    STUDENTS {
        uuid id PK
        string student_id_number
        uuid current_center_id FK
        string first_name
        string last_name
        date date_of_birth
        string gender
        string guardian_name
        string guardian_phone
        string status
        int version
        timestamptz created_at
    }

    ENROLLMENT_RECORDS {
        uuid id PK
        uuid student_id FK
        uuid center_id FK
        date start_date
        date end_date
        string status
    }

    TRANSFER_REQUESTS {
        uuid id PK
        uuid student_id FK
        uuid from_center_id FK
        uuid to_center_id FK
        uuid requested_by_user_id FK
        uuid reviewed_by_user_id FK
        string status
        string request_reason
        date effective_date
    }

    ATTENDANCE_RECORDS {
        uuid id PK
        uuid student_id FK
        uuid center_id FK
        uuid recorded_by_user_id FK
        date attendance_date
        string status
        int version
    }

    ATTENDANCE_AUDIT_LOGS {
        uuid id PK
        uuid attendance_record_id FK
        uuid changed_by_user_id FK
        string previous_status
        string new_status
        string reason
        timestamptz changed_at
    }

    ACTIVITY_TEMPLATES {
        uuid id PK
        uuid center_id FK
        uuid created_by_user_id FK
        string title
        string subject_area
        int duration_minutes
        jsonb competencies
        boolean is_global
    }

    LEARNING_SESSIONS {
        uuid id PK
        uuid center_id FK
        uuid activity_template_id FK
        uuid conducted_by_user_id FK
        date session_date
        timestamptz start_time
        timestamptz end_time
        string topic_summary
    }

    SESSION_STUDENTS {
        uuid id PK
        uuid session_id FK
        uuid student_id FK
        string participation_status
        string mastery_level
        numeric score
    }

    STUDENT_SKILL_PROGRESS {
        uuid id PK
        uuid student_id FK
        string competency_key
        string current_level
        int total_sessions_count
        timestamptz last_evaluated_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string action
        string resource_type
        uuid resource_id
        jsonb old_values
        jsonb new_values
        timestamptz created_at
    }
```

---

## 2. Cardinality & Relational Semantics

| Parent Entity | Child Entity | Cardinality | Semantics / Delete Rule |
| :--- | :--- | :--- | :--- |
| **`users`** | `user_centers` | $1 : N$ | Deleting a user cascades to remove center associations (`CASCADE`). |
| **`centers`** | `user_centers` | $1 : N$ | Deleting a center cascades to remove user assignments (`CASCADE`). |
| **`centers`** | `students` | $1 : N$ | Centers cannot be deleted if active students exist (`RESTRICT`). |
| **`students`** | `enrollment_records` | $1 : N$ | Preserves full chronological center migration history (`RESTRICT`). |
| **`centers`** | `enrollment_records` | $1 : N$ | Historical enrollments remain tied to center (`RESTRICT`). |
| **`students`** | `transfer_requests` | $1 : N$ | All transfer proposals are archived per student (`RESTRICT`). |
| **`students`** | `attendance_records` | $1 : N$ | Student cannot be purged if attendance history exists (`RESTRICT`). |
| **`attendance_records`** | `attendance_audit_logs` | $1 : N$ | If an attendance entry is removed, its corrections cascade (`CASCADE`). |
| **`activity_templates`** | `learning_sessions` | $1 : N$ | Templates with recorded sessions cannot be hard-deleted (`RESTRICT`). |
| **`learning_sessions`** | `session_students` | $1 : N$ | Deleting a session instance removes student participation entries (`CASCADE`). |
| **`students`** | `student_skill_progress`| $1 : N$ | Aggregated competency progress directly tied to student (`CASCADE`). |
| **`users`** | `audit_logs` | $1 : N$ | Actor references preserved or set to `NULL` on deletion (`SET NULL`). |

---

## 3. Structural Constraints Summary

1. **Many-to-Many Relationships Handled via Pure Junctions:**
   - Users $\longleftrightarrow$ Centers: Managed by `user_centers` with `UNIQUE (user_id, center_id)`.
   - Learning Sessions $\longleftrightarrow$ Students: Managed by `session_students` with `UNIQUE (session_id, student_id)`.
2. **Compound Uniqueness Constraints:**
   - Single Daily Attendance: `attendance_records (student_id, attendance_date) UNIQUE`.
   - Aggregated Skill Progress: `student_skill_progress (student_id, competency_key) UNIQUE`.
   - Unique Center Codes: `centers (code) UNIQUE`.
   - Unique User Identities: `users (email) UNIQUE`.
   - Unique Student Registration: `students (student_id_number) UNIQUE`.
