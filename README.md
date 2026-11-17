# EduTrack — Multi-Center Student Learning & Activity Management Platform

EduTrack is an enterprise-grade, centralized management platform engineered for educational organizations operating multiple distributed learning centers. It provides unified, multi-tenant governance over student enrollment lifecycles, cross-center transfers, daily attendance roll call, curriculum activity templating, learning session observations with multi-competency scorecards, and longitudinal skill progress tracking.

The system is built as a **staff-facing Modular Monolith** that pairs a high-performance **FastAPI** backend and **PostgreSQL 18** database with a responsive **React 18** single-page application styled with **Tailwind CSS**.

---

## Table of Contents

1. [Project Title and Overview](#1-project-title-and-overview)
2. [Project Highlights](#2-project-highlights)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [Application Roles and Permissions](#5-application-roles-and-permissions)
6. [Major Features and Modules](#6-major-features-and-modules)
7. [Business Rules and Data Integrity](#7-business-rules-and-data-integrity)
8. [Database Design](#8-database-design)
9. [Project Directory Structure](#9-project-directory-structure)
10. [Prerequisites](#10-prerequisites)
11. [Local Installation and Setup](#11-local-installation-and-setup)
12. [Environment Variables](#12-environment-variables)
13. [Database Migration and Seeding](#13-database-migration-and-seeding)
14. [API Documentation](#14-api-documentation)
15. [Authentication and Security](#15-authentication-and-security)
16. [Frontend Application](#16-frontend-application)
17. [Testing](#17-testing)
18. [Production Deployment](#18-production-deployment)
19. [Troubleshooting](#19-troubleshooting)
20. [Development Workflow](#20-development-workflow)
21. [Known Limitations and Future Improvements](#21-known-limitations-and-future-improvements)
22. [Project Status](#22-project-status)
23. [License and Contribution](#23-license-and-contribution)
24. [Contact and Repository](#24-contact-and-repository)

---

## 1. Project Title and Overview

- **Project Name:** EduTrack
- **Project Type:** Full-Stack Multi-Center Student Learning & Activity Management Platform
- **Architecture:** Modular Monolith (FastAPI + PostgreSQL + React SPA)

### The Problem EduTrack Solves
Multi-center educational networks frequently struggle with fragmented data silos across decentralized physical locations. This leads to operational friction:
- **Dual Enrollment & Record Collisions:** Students inadvertently enrolled in multiple centers simultaneously without coordinated records.
- **Lost Educational History:** Student progress and session evaluations lost or duplicated during inter-center transfers.
- **Un-Audited Attendance Edits:** Roll call modifications performed retroactively without accountability or justification audit trails.
- **Concurrent Update Collisions:** Multiple administrators overwriting student demographic profiles simultaneously without concurrency protection.
- **Inflexible Scoping:** Teachers working across multiple physical centers unable to switch contexts cleanly while preserving center-level data isolation.

### Target Users
EduTrack is specifically designed for:
1. **Network Executives & Super Administrators:** Requiring organization-wide operational benchmarks, compliance auditing, and global center provisioning.
2. **Center Directors & Operational Managers:** Managing student enrollment capacity, verifying guardian information, and executing inter-center transfer reviews.
3. **Instructors & Multi-Center Teachers:** Marking classroom roll calls, conducting structured curriculum sessions, and rating student developmental competencies against standardized rubrics.

> **Important Scope Note:** EduTrack is strictly a **staff-facing management platform** for administrators, managers, and teachers. It does not provide a public student/parent login portal.

---

## 2. Project Highlights

All capabilities listed below are fully implemented in the codebase and verified by automated test suites:

- **Center-Scoped Multi-Tenancy:** Center-level data isolation where staff can only access records belonging to their assigned centers. Multi-center teachers can dynamically toggle active centers via the UI navbar.
- **Single Active Enrollment Guarantee:** Enforced at the PostgreSQL engine level via a partial unique index, guaranteeing a student can have at most one active enrollment across the entire organization.
- **ACID Inter-Center Transfers:** Atomic workflow that closes a student's prior enrollment, establishes a new active enrollment at the destination center, and updates center pointers in a single transaction.
- **Timezone-Aware Attendance:** Roll call date validation calculated against each center's IANA timezone, preventing accidental attendance submission for future calendar dates.
- **24-Hour Attendance Correction Window:** Teachers may correct daily attendance only within a 24-hour grace window from creation, requiring a mandatory audit justification reason.
- **Optimistic Concurrency Control (OCC):** Prevents lost updates during concurrent edits on student records and attendance corrections using integer version tracking (`version`). Concurrent conflicts return HTTP `409 Conflict`.
- **Standardized 4-Tier Competency Rubrics:** Evaluates student mastery across 4 standardized tiers (`EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`), automatically aggregating cumulative session counts.
- **Structured Activity Templates & Scorecards:** Instructors conduct learning sessions mapped to curriculum templates, recording individual attendance, numerical scores (0-100), qualitative feedback, and competency ratings.
- **Live Occupancy Gauges & Analytics:** Real-time occupancy calculations, center capacity utilization percentages, 30-day attendance trends, and organization-wide benchmarks.
- **Streaming CSV Reports:** Downloadable compliance attendance datasets and comprehensive longitudinal student dossiers.
- **Cryptographic Immutable Audit Trail:** Security and data modification ledger with before/after JSON snapshot states, protected against cascade deletion via `ON DELETE RESTRICT`.

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose in EduTrack |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | **React.js** | `^18.3.1` | Component-based Single-Page Application (SPA) architecture |
| **Build Tool & Dev Server**| **Vite** | `^5.2.10` | High-speed ESM bundling, fast HMR, and production distribution builds |
| **Language (Frontend)** | **JavaScript (ES Modules)** | ES2022 | Pure JavaScript JSX implementation (strictly no TypeScript) |
| **Styling** | **Tailwind CSS** | `^3.4.3` | Utility-first responsive CSS styling with zero stylesheet bloat |
| **Icons** | **Lucide React** | `^0.378.0` | Accessible, consistent SVG iconography across navigation and widgets |
| **Routing** | **React Router DOM** | `^6.23.0` | Client-side routing, protected route guards, and nested layout outlets |
| **HTTP Client** | **Axios** | `^1.6.8` | Centralized API client with Bearer token & `X-Center-ID` request interceptors |
| **Backend Framework** | **FastAPI** | `>=0.110.0` | High-throughput asynchronous ASGI REST API with automatic OpenAPI docs |
| **Language (Backend)** | **Python** | `3.11+` | Core backend programming language (tested with Python 3.14.2) |
| **ASGI Server** | **Uvicorn** | `>=0.28.0` | Lightning-fast production ASGI web server |
| **Database Engine** | **PostgreSQL** | `15+` (18 verified) | Relational ACID storage, partial indexes, native ENUMs, and foreign key cascades |
| **Database Driver** | **psycopg** | `>=3.1.18` | Modern psycopg v3 binary driver for PostgreSQL connection pooling |
| **ORM** | **SQLAlchemy** | `2.0+` | Declarative relational mappings, joinedload query optimization, transactions |
| **Schema Migrations** | **Alembic** | `>=1.13.1` | Version-controlled database schema migrations and history tracking |
| **Data Validation** | **Pydantic v2** | `>=2.6.4` | Strict request/response schema validation and type coercion |
| **Settings Management** | **pydantic-settings** | `>=2.2.1` | Environment variable parsing with production safety validators |
| **Password Hashing** | **bcrypt / passlib** | `>=4.1.0` | Secure adaptive hashing for staff passwords (12 rounds) |
| **Authentication** | **PyJWT** | `>=2.8.0` | Stateless HMAC-SHA256 JWT access and refresh token pair signing |
| **Testing Suite** | **Pytest** | `>=8.1.1` | Unit, authorization, PostgreSQL integration, and end-to-end test runner |
| **Test Client** | **HTTPX** | `>=0.27.0` | ASGI in-process test client for testing FastAPI routers |

### Why These Technologies Were Chosen
- **FastAPI + Pydantic v2:** Provides sub-millisecond route handling, automatic interactive Swagger UI generation, and compile-time data validation ensuring malformed payloads never reach the service layer.
- **SQLAlchemy 2.0:** Delivers explicit transactional control needed for complex operations (such as atomic inter-center student transfers), preventing orphan records.
- **PostgreSQL 18:** Selected over NoSQL solutions because multi-center educational tracking requires strict relational integrity, partial unique constraints (e.g. guaranteeing one active enrollment per student), and foreign key cascade controls.
- **React 18 + Vite (JavaScript):** Ensures immediate developer ramp-up without complex TypeScript compilation overhead, while delivering an interactive desktop/tablet experience for center staff.

---

## 4. System Architecture

EduTrack is designed as a **Modular Monolith**. All functional capabilities reside within a single deployable backend service, cleanly decoupled into domain modules (API Routers, Business Services, SQLAlchemy Models, and Pydantic Schemas).

### Mermaid Architecture Diagram

```mermaid
graph TD
    subgraph Client Layer ["Client Layer (Browser)"]
        Browser["React 18 Single-Page Application"]
        AxiosClient["Centralized Axios Client (api/client.js)"]
        Browser --> AxiosClient
    end

    subgraph Security Layer ["Security & Context Gateway"]
        AuthHeader["Authorization: Bearer <JWT>"]
        CenterHeader["X-Center-ID: <UUID>"]
        AxiosClient -->|Injects Headers| AuthHeader
        AxiosClient -->|Injects Headers| CenterHeader
    end

    subgraph Backend Layer ["FastAPI Modular Monolith (/api/v1)"]
        FastAPIGateway["FastAPI Application Gateway (main.py)"]
        AuthHeader --> FastAPIGateway
        CenterHeader --> FastAPIGateway

        subgraph Middleware ["Middleware & Dependencies"]
            CORSMiddleware["CORS Middleware"]
            AuthDep["get_current_user (JWT Validation)"]
            RBACDep["require_roles (SUPER_ADMIN, CENTER_MANAGER, TEACHER)"]
            CenterDep["get_center_context (X-Center-ID Scoping)"]
        end

        FastAPIGateway --> CORSMiddleware
        CORSMiddleware --> AuthDep
        AuthDep --> RBACDep
        RBACDep --> CenterDep

        subgraph Domain Services ["Business Service Layer"]
            UserSvc["user_service.py"]
            CenterSvc["center_service.py"]
            StudentSvc["student_service.py (OCC)"]
            TransferSvc["transfer_service.py (ACID)"]
            AttendanceSvc["attendance_service.py (24h Window)"]
            CompetencySvc["competency_service.py (4-Tier)"]
            ActivitySvc["activity_service.py"]
            SessionSvc["session_service.py"]
            AnalyticsSvc["analytics_service.py"]
            ReportSvc["report_service.py"]
            AuditSvc["audit_service.py"]
        end

        CenterDep --> DomainServices
    end

    subgraph Persistence Layer ["Database Layer (PostgreSQL 18)"]
        SQLAlchemyORM["SQLAlchemy 2.0 Declarative Models"]
        DomainServices --> SQLAlchemyORM
        
        subgraph Tables ["16 Relational Tables"]
            LiveDB[("PostgreSQL 18 Engine")]
            PartialIdx["Partial Unique Index: uq_student_active_enrollment"]
            AuditRestrict["Audit Preservation: ON DELETE RESTRICT"]
        end

        SQLAlchemyORM --> LiveDB
        LiveDB --- PartialIdx
        LiveDB --- AuditRestrict
    end
```

### Communication Flow
1. **User Action:** Staff member interacts with a React view (e.g. submitting daily roll call).
2. **Axios Interceptor:** The client interceptor attaches `Authorization: Bearer <access_token>` and `X-Center-ID: <active_center_id>`.
3. **FastAPI Dependencies:** FastAPI validates the JWT signature, resolves the active user, checks role permissions (RBAC), and verifies that the staff member is authorized for the center specified in `X-Center-ID` (ABAC).
4. **Business Services:** The service validates domain rules (e.g. checking center timezone so attendance cannot be logged for future dates, verifying OCC `version`).
5. **Database Transaction:** SQLAlchemy commits the operation to PostgreSQL 18 inside an ACID transaction and logs an immutable entry in `audit_logs`.

---

## 5. Application Roles and Permissions

EduTrack enforces dual-tier authorization combining **Role-Based Access Control (RBAC)** and **Center-Level Attribute-Based Access Control (ABAC)**.

### Implemented Roles

#### 1. SUPER_ADMIN (Executive Authority)
- **Global Scope:** Bypasses center-level restrictions; can view and manage all centers across the organization.
- **Center Provisioning:** Creates and updates learning centers, setting capacities and IANA timezones.
- **Staff Provisioning:** Can provision users with any role (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`) and map them to centers.
- **Capacity Overrides:** Authorized to override center capacity limits during student transfers with mandatory justification.
- **System Auditing:** Exclusive access to the immutable system audit trail (`/api/v1/audit-logs`).
- **Organization Benchmarks:** Views aggregate network-wide analytics across all campuses.

#### 2. CENTER_MANAGER (Campus Director)
- **Assigned Center Scope:** Limited to centers explicitly assigned in `user_centers`.
- **Student Lifecycles:** Registers new students, updates demographic information with OCC concurrency control.
- **Transfer Reviews:** Initiates inter-center transfer requests and reviews/approves incoming transfer requests.
- **Staff Provisioning:** Permitted to provision `TEACHER` accounts strictly for their assigned centers.
- **Center Analytics & Reports:** Inspects daily center occupancy, capacity utilization gauges, and exports attendance CSVs.

#### 3. TEACHER (Instructional Staff)
- **Assigned Center Scope:** Restricted strictly to assigned learning centers. Can belong to multiple centers and switch between them using the UI center switcher.
- **Daily Roll Call:** Submits atomic daily attendance rosters for students with active enrollments.
- **24-Hour Corrections:** Corrects attendance records within 24 hours of creation with mandatory justification.
- **Conducted Learning Sessions:** Logs completed sessions, records numerical scores, writes qualitative notes, and grades students against standardized competency rubrics.
- **Student Progress:** Inspects longitudinal competency progression for students in their assigned centers.

### Role Comparison Matrix

| Feature / Operation | SUPER_ADMIN | CENTER_MANAGER | TEACHER | Enforcing Mechanism |
| :--- | :---: | :---: | :---: | :--- |
| **System Audit Logs (`/audit-logs`)** | ✅ Yes | ❌ No | ❌ No | `require_super_admin` |
| **Create Learning Centers (`POST /centers`)** | ✅ Yes | ❌ No | ❌ No | `require_super_admin` |
| **Provision Center Managers (`POST /users`)** | ✅ Yes | ❌ No | ❌ No | `require_super_admin` |
| **Transfer Capacity Override** | ✅ Yes | ❌ No | ❌ No | Service level check |
| **Global Analytics Overview** | ✅ Yes | ❌ No | ❌ No | `require_super_admin` |
| **Provision Teachers (`POST /users`)** | ✅ Yes | ✅ Assigned Centers | ❌ No | `require_center_manager` |
| **Register Students (`POST /students`)** | ✅ Yes | ✅ Assigned Centers | ❌ No | `require_center_manager` |
| **Approve Transfers (`POST /transfers/review`)** | ✅ Yes | ✅ Destination Center | ❌ No | `require_center_manager` |
| **Export Attendance CSV (`GET /reports/attendance`)**| ✅ Yes | ✅ Assigned Centers | ❌ No | `require_center_manager` |
| **Mark Daily Attendance (`POST /attendance/bulk`)** | ✅ Yes | ✅ Assigned Centers | ✅ Assigned Centers | `require_teacher` |
| **24-Hour Attendance Correction** | ✅ Anytime | ✅ Anytime | ✅ Within 24 Hours | Service level cutoff |
| **Log Learning Sessions (`POST /sessions`)** | ✅ Yes | ✅ Assigned Centers | ✅ Assigned Centers | `require_teacher` |
| **Grade Competency Rubrics** | ✅ Yes | ✅ Assigned Centers | ✅ Assigned Centers | `require_teacher` |
| **View Student Dossier & Skill Progress** | ✅ Yes | ✅ Assigned Centers | ✅ Assigned Centers | `verify_user_center_access`|

---

## 6. Major Features and Modules

### 6.1 Authentication & Session Management
- **Purpose:** Secure identity verification and stateless session tracking.
- **Backend:** `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`.
- **Frontend:** [LoginPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/auth/LoginPage.jsx) with 1-click test credentials and [AuthContext.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/context/AuthContext.jsx).
- **Business Rules:** Passwords verified against bcrypt hashes (12 rounds). Locked or inactive accounts are rejected with HTTP `403 Forbidden`. Tokens expire in 30 minutes; refresh tokens rotate with a 7-day TTL.

### 6.2 Center Management & Capacity Planning
- **Purpose:** Campus profile administration, timezone assignment, and enrollment capacity planning.
- **Backend:** `GET /api/v1/centers`, `POST /api/v1/centers`, `GET /api/v1/centers/{id}`, `PUT /api/v1/centers/{id}`.
- **Frontend:** [CenterManagementPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/admin/CenterManagementPage.jsx).
- **Business Rules:** Capacity must be strictly positive (`> 0`). Centers define an IANA timezone (e.g. `America/Los_Angeles`) governing all local date validations.

### 6.3 Student Management
- **Purpose:** Student demographic profiles, guardian contacts, emergency information, and notes.
- **Backend:** `GET /api/v1/students`, `POST /api/v1/students`, `GET /api/v1/students/{id}`, `PUT /api/v1/students/{id}`.
- **Frontend:** [StudentListPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/students/StudentListPage.jsx), [StudentCreatePage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/students/StudentCreatePage.jsx), [StudentDetailPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/students/StudentDetailPage.jsx), [StudentEditPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/students/StudentEditPage.jsx).
- **Business Rules:** Student ID numbers are unique across the organization. Updates require submitting the existing `version` integer; collisions trigger HTTP `409 Conflict`. Creating a student atomically initializes their first `EnrollmentRecord`.

### 6.4 Enrollment Management
- **Purpose:** Tracking historical and active student memberships across centers.
- **Backend:** Handled automatically via `student_service.py` and `transfer_service.py`.
- **Business Rules:** A student can have at most one active enrollment in the entire system (`status = 'ACTIVE'` and `end_date IS NULL`), enforced by PostgreSQL partial unique index `uq_student_active_enrollment`.

### 6.5 Inter-Center Student Transfers
- **Purpose:** Facilitating student relocations between centers with capacity checks.
- **Backend:** `POST /api/v1/transfers`, `GET /api/v1/transfers`, `POST /api/v1/transfers/{id}/review`.
- **Frontend:** [TransferListPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/transfers/TransferListPage.jsx) and modal in [StudentDetailPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/students/StudentDetailPage.jsx).
- **Business Rules:** Origin Manager requests transfer. Destination Manager approves or rejects. Approval executes inside an ACID transaction: closes old enrollment, opens new enrollment, and updates `students.current_center_id`. If destination center is at capacity, approval fails with `422` unless Super Admin enables `capacity_override` with a reason.

### 6.6 Attendance Roll Call & 24-Hour Corrections
- **Purpose:** Daily classroom attendance tracking and audited corrections.
- **Backend:** `GET /api/v1/attendance`, `POST /api/v1/attendance/bulk`, `PUT /api/v1/attendance/{id}`.
- **Frontend:** [AttendancePage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/attendance/AttendancePage.jsx).
- **Business Rules:** Duplicate attendance on the same date is rejected. Attendance cannot be submitted for future dates according to the center's timezone. Teachers can only correct attendance within 24 hours of creation; all corrections record before/after states in `attendance_audit_logs`.

### 6.7 Learning Activity Templates
- **Purpose:** Standardized curriculum activity templates mapped to subject areas.
- **Backend:** `GET /api/v1/activities`, `POST /api/v1/activities`, `GET /api/v1/activities/{id}`, `PUT /api/v1/activities/{id}`.
- **Frontend:** Activity selection integrated within [SessionCreatePage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/sessions/SessionCreatePage.jsx).
- **Business Rules:** Templates specify minimum and maximum age bounds (`min_age <= max_age`) and link to competencies via `activity_competencies`.

### 6.8 Learning Sessions & Scorecards
- **Purpose:** Logging completed classroom sessions with student rosters and evaluations.
- **Backend:** `GET /api/v1/sessions`, `POST /api/v1/sessions`, `GET /api/v1/sessions/{id}`.
- **Frontend:** [SessionListPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/sessions/SessionListPage.jsx) and [SessionCreatePage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/sessions/SessionCreatePage.jsx).
- **Business Rules:** Validates `start_time <= end_time`. Students must have an active enrollment on the session date. Instructors record numerical score (0-100), participation status (`COMPLETED`, `PARTIAL`, `ABSENT`), and qualitative feedback.

### 6.9 Competency Catalog
- **Purpose:** Standardized curriculum developmental rubrics across domains.
- **Backend:** `GET /api/v1/competencies`, `POST /api/v1/competencies`.
- **Frontend:** [CompetencyCatalogPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/competencies/CompetencyCatalogPage.jsx).
- **Business Rules:** Standardized 4-tier rubric definitions: `EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`. Competency codes (e.g. `MATH-FRAC-01`) are unique.

### 6.10 Longitudinal Student Progress Tracking
- **Purpose:** Tracking cumulative developmental mastery per competency.
- **Backend:** `GET /api/v1/progress/students/{student_id}`.
- **Frontend:** Integrated progress table in [StudentDetailPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/students/StudentDetailPage.jsx).
- **Business Rules:** Whenever a learning session records a competency evaluation for a student, `student_skill_progress` automatically increments `total_sessions_count`, updates `current_level`, and updates `last_evaluated_at`.

### 6.11 Operational Dashboards
- **Purpose:** Role-tailored operational KPIs and benchmark metrics.
- **Backend:** `GET /api/v1/analytics/overview` (Super Admin), `GET /api/v1/analytics/centers/{id}` (Manager).
- **Frontend:** [DashboardPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/dashboard/DashboardPage.jsx).
- **Business Rules:** Super Admins view total active centers, total active students, network attendance rate, monthly session volume, and pending transfers. Managers view center capacity utilization, today's attendance rate, and weekly session counts.

### 6.12 Compliance Reports & CSV Exports
- **Purpose:** Exporting compliance attendance datasets and comprehensive dossiers.
- **Backend:** `GET /api/v1/reports/attendance?format=csv` (or `json`), `GET /api/v1/reports/students/{id}/dossier`.
- **Frontend:** [ReportsPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/admin/ReportsPage.jsx).
- **Business Rules:** Generates streaming RFC-4180 compliant CSV exports with headers (`attendance_date,center_name,student_id_number,student_name,status,remarks`).

### 6.13 Immutable Security Audit Trail
- **Purpose:** Tamper-evident logging of sensitive operations.
- **Backend:** `GET /api/v1/audit-logs`.
- **Frontend:** [AuditLogsPage.jsx](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/src/pages/admin/AuditLogsPage.jsx).
- **Business Rules:** Accessible only to `SUPER_ADMIN`. Captures actor user ID, client IP, action name, resource type, resource ID, and full `old_values` and `new_values` JSON state snapshots. Protected by `ON DELETE RESTRICT` foreign keys.

---

## 7. Business Rules and Data Integrity

The following key business rules are enforced in the application:

1. **One Active Enrollment Per Student (BR-ENR-01):** A student can only be enrolled in one center at any given time. This is strictly enforced in PostgreSQL by a partial unique index:
   ```sql
   CREATE UNIQUE INDEX uq_student_active_enrollment 
   ON enrollment_records (student_id) 
   WHERE status = 'ACTIVE' AND end_date IS NULL;
   ```
2. **Center-Level Data Isolation (ABAC):** Requests requiring center context must supply the `X-Center-ID: <UUID>` header. The authorization dependency verifies that the authenticated user has an active membership in `user_centers` for that center ID.
3. **Multi-Center Dynamic Context Switching:** Staff assigned to multiple centers can switch active center context at runtime. The frontend navbar updates `X-Center-ID` on all subsequent HTTP calls. Super Admins hold global clearance across all centers.
4. **Atomic Inter-Center Transfers (ACID):** Transfer approvals execute within a single database transaction: the previous enrollment record is closed with `end_date = effective_date` and `status = 'TRANSFERRED'`, a new enrollment record is inserted at the destination center, and `students.current_center_id` is updated. If any step fails, the entire transaction rolls back.
5. **Active Enrollment Required for Attendance & Sessions:** A student cannot be marked present or evaluated in a session unless they had an active enrollment at that center covering the calendar date.
6. **Timezone-Aware Future Date Prevention:** Attendance submission is evaluated against the center's local date (`datetime.now(ZoneInfo(center.timezone)).date()`), rejecting any future date submissions with HTTP `422`.
7. **24-Hour Attendance Edit Window for Teachers:** Teachers can only edit attendance within 24 hours of creation (`record.created_at + 24 hours`). Center Managers and Super Admins retain override authority for retroactive corrections.
8. **Mandatory Audit Justification:** All attendance corrections require a non-empty `reason` string, permanently recorded in `attendance_audit_logs`.
9. **Center Capacity Enforcement & Override:** If a student transfer would cause a destination center to exceed its configured `capacity`, approval is blocked with HTTP `422 Unprocessable Entity` unless a Super Admin explicitly checks `capacity_override` and provides a `capacity_override_reason`.
10. **Optimistic Concurrency Control (OCC):** Modifying a student or correcting attendance requires submitting the entity's current `version`. If another staff member updated the record in the interim, the update is rejected with HTTP `409 Conflict`, preventing overwrite collisions.
11. **Standardized 4-Tier Rubric Framework:** All competency mastery evaluations must belong to one of four levels: `EMERGING` (initial guidance), `DEVELOPING` (partial support), `PROFICIENT` (independent mastery), or `MASTERY` (peer guidance).
12. **Audit Preservation (`ON DELETE RESTRICT`):** Deleting a user or entity referenced in `audit_logs` or `attendance_audit_logs` is restricted by foreign key constraints, preventing destruction of compliance audit trails.

---

## 8. Database Design

EduTrack utilizes a normalized relational schema in **PostgreSQL 18** managed via **SQLAlchemy 2.0 ORM** and **Alembic**.

### Implemented Models & Tables

| Model Class | Database Table | Purpose | Key Relationships |
| :--- | :--- | :--- | :--- |
| `User` | `users` | Staff credentials, roles, and status | `assigned_centers` (1:N to `UserCenter`) |
| `Center` | `centers` | Physical campus profiles, timezone, capacity | `staff_assignments`, `students`, `enrollments` |
| `UserCenter` | `user_centers` | Staff-to-center multi-assignment junction | FK to `User` and `Center` (`UNIQUE (user_id, center_id)`) |
| `Student` | `students` | Demographics, guardian info, OCC `version` | FK to `Center`, `enrollments`, `attendance_records` |
| `EnrollmentRecord`| `enrollment_records` | Student enrollment history & active status | FK to `Student` and `Center` (Partial Unique Index) |
| `TransferRequest` | `transfer_requests` | Inter-center transfer proposals & approvals | FK to `Student`, `from_center`, `to_center`, `users` |
| `AttendanceRecord`| `attendance_records` | Daily classroom attendance roll call | FK to `Student`, `Center`, `User` (`UNIQUE(student, date)`) |
| `AttendanceAuditLog`| `attendance_audit_logs` | Immutable 24h attendance correction logs | FK to `AttendanceRecord` and `User` (`RESTRICT`) |
| `Competency` | `competencies` | Standardized curriculum developmental rubrics | FK from `ActivityCompetency`, `SessionStudentEvaluation` |
| `StudentSkillProgress`| `student_skill_progress`| Longitudinal mastery summaries per skill | FK to `Student` and `Competency` (`UNIQUE(student, comp)`) |
| `ActivityTemplate`| `activity_templates`| Structured curriculum activity templates | FK to `Center` (optional), `activity_competencies` |
| `ActivityCompetency`| `activity_competencies` | Activity-to-competency junction table | FK to `ActivityTemplate` and `Competency` |
| `LearningSession` | `learning_sessions` | Conducted classroom session logs | FK to `Center`, `ActivityTemplate`, `User`, `student_roster` |
| `SessionStudent` | `session_students` | Session participant scores and feedback | FK to `LearningSession` and `Student` |
| `SessionStudentEvaluation`| `session_student_evaluations`| Granular rubric ratings per competency | FK to `SessionStudent` and `Competency` |
| `AuditLog` | `audit_logs` | System-wide immutable security audit trail | FK to `User` (`RESTRICT`), before/after JSON states |

### Native PostgreSQL Enums Verified
1. `user_role_enum`: `SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`
2. `user_status_enum`: `ACTIVE`, `INACTIVE`, `LOCKED`
3. `student_status_enum`: `ACTIVE`, `INACTIVE`, `TRANSFERRED`, `ARCHIVED`
4. `enrollment_status_enum`: `ACTIVE`, `TRANSFERRED`, `COMPLETED`, `WITHDRAWN`
5. `transfer_status_enum`: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`
6. `attendance_status_enum`: `PRESENT`, `LATE`, `ABSENT`, `EXCUSED`
7. `session_participation_status_enum`: `COMPLETED`, `PARTIAL`, `ABSENT`
8. `mastery_level_enum`: `EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`

### Mermaid Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o{ user_centers : "assigned to"
    centers ||--o{ user_centers : "has staff"
    centers ||--o{ students : "currently enrolls"
    students ||--o{ enrollment_records : "has history"
    centers ||--o{ enrollment_records : "houses"
    students ||--o{ transfer_requests : "transferred via"
    centers ||--o{ transfer_requests : "origin / destination"
    students ||--o{ attendance_records : "recorded in"
    centers ||--o{ attendance_records : "conducted at"
    attendance_records ||--o{ attendance_audit_logs : "corrected via"
    competencies ||--o{ student_skill_progress : "tracked in"
    students ||--o{ student_skill_progress : "achieves"
    activity_templates ||--o{ activity_competencies : "targets"
    competencies ||--o{ activity_competencies : "linked to"
    centers ||--o{ learning_sessions : "hosts"
    activity_templates ||--o{ learning_sessions : "executes"
    users ||--o{ learning_sessions : "teaches"
    learning_sessions ||--o{ session_students : "roster"
    students ||--o{ session_students : "participates"
    session_students ||--o{ session_student_evaluations : "evaluated on"
    competencies ||--o{ session_student_evaluations : "rated against"
    users ||--o{ audit_logs : "triggers"
```

---

## 9. Project Directory Structure

```
eduTrack/
├── backend/                             # FastAPI Modular Monolith Backend
│   ├── alembic/                         # Database Migration Scripts
│   │   ├── versions/                    # Versioned Migration Files
│   │   │   └── 69f79dd04f39_initial_schema.py # Initial baseline migration
│   │   ├── env.py                       # Alembic environment configuration
│   │   └── script.py.mako               # Migration template
│   ├── app/                             # Application Source Code
│   │   ├── api/                         # FastAPI Route Handlers (REST Endpoints)
│   │   │   ├── activities.py            # Activity template routes
│   │   │   ├── analytics.py             # Dashboard analytics routes
│   │   │   ├── attendance.py            # Daily attendance & bulk routes
│   │   │   ├── audit_logs.py            # Immutable audit trail routes
│   │   │   ├── auth.py                  # Login, refresh, /auth/me routes
│   │   │   ├── centers.py               # Center management routes
│   │   │   ├── competencies.py          # Competency catalog routes
│   │   │   ├── deps.py                  # Core auth & user dependencies
│   │   │   ├── permissions.py           # RBAC & center ABAC guards
│   │   │   ├── progress.py              # Student competency progress routes
│   │   │   ├── reports.py               # Attendance CSV & dossier routes
│   │   │   ├── sessions.py              # Learning session routes
│   │   │   ├── students.py              # Student management & OCC routes
│   │   │   ├── transfers.py             # Inter-center transfer routes
│   │   │   └── users.py                 # Staff management routes
│   │   ├── core/                        # Core Configuration & Security
│   │   │   ├── config.py                # Pydantic Settings v2 configuration
│   │   │   └── security.py              # Password hashing & JWT logic
│   │   ├── db/                          # Database Session & Base
│   │   │   ├── base.py                  # SQLAlchemy declarative base
│   │   │   └── session.py               # Engine & SessionLocal provider
│   │   ├── models/                      # SQLAlchemy 2.0 ORM Models (16 Tables)
│   │   │   ├── activity.py              # ActivityTemplate & ActivityCompetency
│   │   │   ├── attendance.py            # AttendanceRecord & AttendanceAuditLog
│   │   │   ├── audit.py                 # AuditLog model
│   │   │   ├── center.py                # Center model
│   │   │   ├── competency.py            # Competency & StudentSkillProgress
│   │   │   ├── enums.py                 # 8 native PostgreSQL Enum classes
│   │   │   ├── session.py               # LearningSession, SessionStudent, Evaluations
│   │   │   ├── student.py               # Student, EnrollmentRecord, TransferRequest
│   │   │   └── user.py                  # User & UserCenter junction
│   │   ├── schemas/                     # Pydantic v2 Request/Response Schemas
│   │   │   ├── activity.py              # Activity validation schemas
│   │   │   ├── analytics.py             # Analytics payload schemas
│   │   │   ├── attendance.py            # Attendance & bulk schemas
│   │   │   ├── audit.py                 # Audit log schemas
│   │   │   ├── center.py                # Center schemas
│   │   │   ├── common.py                # PaginatedResponse & Error envelopes
│   │   │   ├── competency.py            # Competency & progress schemas
│   │   │   ├── enrollment.py            # Enrollment schemas
│   │   │   ├── session.py               # Learning session schemas
│   │   │   ├── student.py               # Student CRUD & OCC update schemas
│   │   │   ├── transfer.py              # Transfer request & review schemas
│   │   │   └── user.py                  # User & token response schemas
│   │   ├── services/                    # Business Service Logic Layer
│   │   │   ├── activity_service.py      # Template business logic
│   │   │   ├── analytics_service.py     # Aggregation & metrics queries
│   │   │   ├── attendance_service.py    # Bulk attendance & 24h grace window
│   │   │   ├── audit_service.py         # Immutable audit query service
│   │   │   ├── center_service.py        # Center operations & occupancy
│   │   │   ├── competency_service.py    # Rubric catalog & progress calculation
│   │   │   ├── report_service.py        # CSV stream generator & dossiers
│   │   │   ├── session_service.py       # Session execution & scoring
│   │   │   ├── student_service.py       # Student CRUD & OCC collision checks
│   │   │   ├── transfer_service.py      # Atomic ACID transfers & overrides
│   │   │   └── user_service.py          # Staff provisioning & center linking
│   │   └── main.py                      # FastAPI app entry point & CORS
│   ├── tests/                           # Automated Test Suite (123 Tests)
│   │   ├── conftest.py                  # Pytest fixtures and DB setup
│   │   ├── test_auth.py                 # 21 tests: Auth, password hashing, JWT
│   │   ├── test_authorization.py        # 25 tests: RBAC & ABAC center scoping
│   │   ├── test_backend_modules.py      # 7 tests: Domain services
│   │   ├── test_e2e_workflow.py         # 1 comprehensive end-to-end test
│   │   ├── test_health.py               # 3 tests: Liveness & DB connectivity
│   │   ├── test_models.py               # 10 tests: ORM models & constraints
│   │   ├── test_postgres_integration.py # 4 tests: Live PostgreSQL 18 tests
│   │   ├── test_schemas.py              # 30 tests: Pydantic v2 schemas
│   │   └── test_students.py             # 22 tests: Student management & OCC
│   ├── alembic.ini                      # Alembic CLI configuration
│   ├── pytest.ini                       # Pytest configuration
│   ├── requirements.txt                 # Python dependencies
│   └── seed.py                          # Database seed script
├── frontend/                            # React 18 + Vite Frontend Application
│   ├── src/                             # Frontend Source Code
│   │   ├── api/                         # Centralized API Client
│   │   │   └── client.js                # Axios instance with auth interceptors
│   │   ├── components/                  # Reusable UI Components
│   │   │   ├── common/                  # Generic UI Elements
│   │   │   │   ├── AlertBanner.jsx      # Success/error/warning alerts
│   │   │   │   ├── Badge.jsx            # Status, role & rubric badges
│   │   │   │   ├── LoadingSpinner.jsx   # Animated loading indicators
│   │   │   │   └── Pagination.jsx       # Standard table pagination
│   │   │   └── layout/                  # Structural Layout Components
│   │   │       ├── Layout.jsx           # App shell layout
│   │   │       ├── Navbar.jsx           # Top header & active center switcher
│   │   │       ├── ProtectedRoute.jsx   # RBAC & authentication route guard
│   │   │       └── Sidebar.jsx          # Role-filtered navigation sidebar
│   │   ├── context/                     # React Context Providers
│   │   │   └── AuthContext.jsx          # Auth state, login/logout, center switch
│   │   ├── pages/                       # Application Views (Screens)
│   │   │   ├── admin/                   # Administrative Screens
│   │   │   │   ├── AuditLogsPage.jsx    # Immutable audit trail explorer
│   │   │   │   ├── CenterManagementPage.jsx # Center directory & provisioning
│   │   │   │   ├── ReportsPage.jsx      # Attendance CSV export & dossiers
│   │   │   │   └── UserManagementPage.jsx   # Staff management & center mapping
│   │   │   ├── attendance/              # Attendance Module
│   │   │   │   └── AttendancePage.jsx   # Daily roll call & 24h correction modal
│   │   │   ├── auth/                    # Authentication Views
│   │   │   │   └── LoginPage.jsx        # Login card with 1-click test fill
│   │   │   ├── competencies/            # Curriculum Module
│   │   │   │   └── CompetencyCatalogPage.jsx # 4-tier rubric catalog
│   │   │   ├── dashboard/               # Operational Overview
│   │   │   │   └── DashboardPage.jsx    # Metrics, occupancy gauges, benchmarks
│   │   │   ├── sessions/                # Learning Activity Module
│   │   │   │   ├── SessionCreatePage.jsx# Conduct session & grade competencies
│   │   │   │   └── SessionListPage.jsx  # Completed sessions history
│   │   │   ├── students/                # Student Management Module
│   │   │   │   ├── StudentCreatePage.jsx# Student enrollment form
│   │   │   │   ├── StudentDetailPage.jsx# Profile, skill progress & transfer modal
│   │   │   │   ├── StudentEditPage.jsx  # OCC-protected profile editor
│   │   │   │   └── StudentListPage.jsx  # Filterable, paginated student roster
│   │   │   └── transfers/               # Student Mobility Module
│   │   │       └── TransferListPage.jsx # Transfer approval & capacity override
│   │   ├── App.jsx                      # Client router configuration
│   │   ├── index.css                    # Tailwind CSS directives
│   │   └── main.jsx                     # React DOM root mounting
│   ├── index.html                       # HTML template
│   ├── package.json                     # Node.js dependencies and scripts
│   ├── postcss.config.js                # PostCSS configuration
│   ├── tailwind.config.js               # Tailwind design system configuration
│   └── vite.config.js                   # Vite dev server & proxy settings
├── docs/                                # Technical Specifications & Designs
│   ├── API_DESIGN.md                    # REST API Contracts & Endpoint Matrix
│   ├── ARCHITECTURE.md                  # System Architecture & Component Design
│   ├── DATABASE_DESIGN.md               # PostgreSQL Schema, Constraints & Rules
│   ├── ER_DIAGRAM.md                    # Entity-Relationship Mermaid Diagrams
│   └── REQUIREMENTS.md                  # Functional & Non-Functional Requirements
├── .gitignore                           # Git ignore rules
└── README.md                            # Comprehensive Project Documentation
```

---

## 10. Prerequisites

Before installing EduTrack locally, verify that your development environment satisfies these minimum requirements:

| Tool | Minimum Version | Verified Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11+` | `3.14.2` | Backend runtime |
| **Node.js** | `18.0+` | `20.x+` | Frontend JavaScript runtime |
| **npm** | `9.0+` | `10.x+` | Frontend package manager |
| **PostgreSQL**| `15+` | `18.0` | Relational database engine |
| **Git** | `2.30+` | `2.40+` | Version control |

### Verifying Prerequisites in Windows PowerShell
Run the following commands in PowerShell to confirm your installed versions:
```powershell
python --version
node --version
npm --version
psql --version
git --version
```

---

## 11. Local Installation and Setup

Follow these step-by-step instructions to set up and run EduTrack on a local machine.

### A. Clone the Repository
Open Windows PowerShell and clone the project:
```powershell
git clone https://github.com/hd84339/eduTrack.git
cd eduTrack
```

---

### B. Backend Setup (FastAPI & PostgreSQL)

1. **Navigate to the backend directory:**
   ```powershell
   cd backend
   ```

2. **Create and activate a Python virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install backend dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure backend environment variables:**
   Create a `.env` file in the `backend/` directory (or verify `backend/.env` exists):
   ```ini
   APP_NAME=EduTrack
   APP_ENV=development
   DEBUG=true
   API_V1_PREFIX=/api/v1
   DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/edutrack
   JWT_SECRET_KEY=change-this-to-a-secure-random-32-byte-hex-secret-in-production
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   BCRYPT_ROUNDS=12
   ```

5. **Ensure PostgreSQL is running and create the database:**
   Ensure your local PostgreSQL 18 service is running on `127.0.0.1:5432`. Connect using `psql` and create the `edutrack` database:
   ```sql
   CREATE DATABASE edutrack;
   ```

6. **Apply Alembic database migrations:**
   ```powershell
   alembic upgrade head
   ```

7. **Seed development data:**
   Populate the database with sample centers, staff accounts, competencies, activities, and students:
   ```powershell
   python seed.py
   ```

8. **Start the FastAPI backend server:**
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - **API Server:** `http://127.0.0.1:8000`
   - **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
   - **Health Liveness Check:** `http://127.0.0.1:8000/health`
   - **Database Health Check:** `http://127.0.0.1:8000/health/db`

---

### C. Frontend Setup (React & Vite)

1. **Open a new Windows PowerShell terminal and navigate to the frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install frontend dependencies:**
   ```powershell
   npm install
   ```

3. **Verify frontend environment configuration:**
   Ensure `frontend/.env` contains the API base path:
   ```ini
   VITE_API_BASE_URL=/api/v1
   ```
   *(During local development, Vite proxies `/api` directly to `http://127.0.0.1:8000` as configured in `vite.config.js`)*.

4. **Start the Vite development server:**
   ```powershell
   npm run dev -- --port 3000
   ```
   - **Frontend Application:** `http://localhost:3000`

---

### Pre-Seeded Test Credentials

All pre-seeded test accounts use the password: `Password123!`

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@edutrack.org` | `Password123!` | Global access across all centers & system audit logs |
| **Center Manager** | `manager.north@edutrack.org` | `Password123!` | Full operational authority for North Ridge Center |
| **Center Manager** | `manager.south@edutrack.org` | `Password123!` | Full operational authority for South Bay Center |
| **Teacher** | `teacher.smith@edutrack.org` | `Password123!` | Multi-center teacher assigned to North Ridge & South Bay |
| **Teacher** | `teacher.davis@edutrack.org` | `Password123!` | Teacher assigned to East Valley Center |

*(The [Login Page](http://localhost:3000/login) includes **1-click Quick Test Accounts** buttons to auto-populate credentials for instant evaluation)*.

---

## 12. Environment Variables

### Backend Environment Variables (`backend/.env`)

| Variable | Description | Required? | Default / Example Value |
| :--- | :--- | :---: | :--- |
| `APP_NAME` | Display name of the application | No | `EduTrack` |
| `APP_ENV` | Application environment (`development`, `testing`, `staging`, `production`) | Yes | `development` |
| `DEBUG` | Enables detailed error traces and auto-reloading | No | `true` |
| `API_V1_PREFIX` | Prefix for versioned REST API routes | No | `/api/v1` |
| `DATABASE_URL` | SQLAlchemy connection string (requires `postgresql+psycopg://` driver) | **Yes** | `postgresql+psycopg://postgres:postgres@localhost:5432/edutrack` |
| `JWT_SECRET_KEY` | Secret key used for signing HMAC-SHA256 JWT tokens (>= 32 chars in prod) | **Yes** | `change-this-to-a-secure-random-32-byte-hex-secret-in-production` |
| `JWT_ALGORITHM` | Cryptographic algorithm for JWT signing | No | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan in minutes | No | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifespan in days | No | `7` |
| `BCRYPT_ROUNDS` | Cost factor for adaptive password hashing (minimum 12 in production) | No | `12` |

> **Security Rule:** In `APP_ENV=production`, `Settings` automatically validates that `JWT_SECRET_KEY` is at least 32 characters long and does not contain the word `insecure`. Never commit `.env` files with production secrets to GitHub.

### Frontend Environment Variables (`frontend/.env`)

| Variable | Description | Required? | Example Value |
| :--- | :--- | :---: | :--- |
| `VITE_API_BASE_URL` | Base endpoint path for backend API requests | **Yes** | `/api/v1` (local) or `https://edutrack-api.onrender.com/api/v1` (prod) |

---

## 13. Database Migration and Seeding

EduTrack uses **Alembic** for schema migrations.

### Creating a New Migration
When ORM models in `backend/app/models/` are modified, generate an autodetected migration script:
```powershell
cd backend
alembic revision --autogenerate -m "describe_schema_changes"
```

### Applying Migrations
Apply all unapplied migrations up to the latest revision:
```powershell
alembic upgrade head
```

### Checking Migration Version
Inspect the currently applied migration revision hash:
```powershell
alembic current
```

### Rolling Back Migrations
Roll back the most recently applied migration:
```powershell
alembic downgrade -1
```

### Seeding Development Data
Run the idempotent seed script to populate initial centers, staff accounts, competencies, activities, and students:
```powershell
python seed.py
```
- **Duplicate Prevention:** `seed.py` queries existing entities by UUID and code before inserting. Re-running `seed.py` will not duplicate records.

---

## 14. API Documentation

When the FastAPI backend is running, complete interactive documentation is available in your browser:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc UI:** `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON Specification:** `http://127.0.0.1:8000/openapi.json`

### Complete Endpoint Reference

| Module | Method | Endpoint | Purpose | Authentication & Scope |
| :--- | :---: | :--- | :--- | :--- |
| **System** | `GET` | `/health` | Basic application liveness check | Public (No auth) |
| **System** | `GET` | `/health/db` | PostgreSQL connectivity probe | Public (No auth) |
| **Auth** | `POST` | `/api/v1/auth/login` | Staff authentication & JWT pair issuance | Public (No auth) |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Rotate access token using valid refresh token | Refresh Token |
| **Auth** | `GET` | `/api/v1/auth/me` | Fetch active user profile and assigned centers | Bearer Token (Any staff) |
| **Centers**| `GET` | `/api/v1/centers` | List all operational learning centers | Bearer Token |
| **Centers**| `POST` | `/api/v1/centers` | Provision a new learning center | `SUPER_ADMIN` |
| **Centers**| `GET` | `/api/v1/centers/{id}` | Retrieve center details with live occupancy | Bearer Token (Assigned) |
| **Centers**| `PUT` | `/api/v1/centers/{id}` | Update center details and capacity | `SUPER_ADMIN` |
| **Students**| `POST` | `/api/v1/students` | Register student & initialize enrollment | `SUPER_ADMIN`, `CENTER_MANAGER` (`X-Center-ID`) |
| **Students**| `GET` | `/api/v1/students` | List center students (search, status, pagination)| `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` (`X-Center-ID`) |
| **Students**| `GET` | `/api/v1/students/{id}` | Retrieve student profile and active enrollment | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Students**| `PUT` | `/api/v1/students/{id}` | Update student profile with OCC version check | `CENTER_MANAGER`, `SUPER_ADMIN` (Requires `version`) |
| **Transfers**| `POST`| `/api/v1/transfers` | Initiate inter-center student transfer request | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Transfers**| `GET` | `/api/v1/transfers` | List transfers (filter by status and direction) | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Transfers**| `POST`| `/api/v1/transfers/{id}/review` | Approve/reject transfer with capacity override | `CENTER_MANAGER` (Dest), `SUPER_ADMIN` |
| **Attendance**| `GET`| `/api/v1/attendance` | Query daily attendance roster for a date | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` (`X-Center-ID`) |
| **Attendance**| `POST`| `/api/v1/attendance/bulk` | Submit daily classroom roll call atomically | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` (`X-Center-ID`) |
| **Attendance**| `PUT` | `/api/v1/attendance/{id}`| Correct attendance (24h window for teachers) | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` (Requires `version`, `reason`) |
| **Competencies**| `GET`| `/api/v1/competencies` | List standardized developmental competencies | Bearer Token |
| **Competencies**| `POST`| `/api/v1/competencies` | Add new competency to curriculum catalog | `SUPER_ADMIN` |
| **Activities**| `GET` | `/api/v1/activities` | List curriculum activity templates | Bearer Token |
| **Activities**| `POST`| `/api/v1/activities` | Create a new learning activity template | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Activities**| `GET` | `/api/v1/activities/{id}` | Retrieve specific activity template details | Bearer Token |
| **Activities**| `PUT` | `/api/v1/activities/{id}` | Update activity template attributes | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Sessions**| `GET` | `/api/v1/sessions` | List conducted classroom learning sessions | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Sessions**| `POST`| `/api/v1/sessions` | Log session, student scores, and rubric ratings| `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` (`X-Center-ID`) |
| **Sessions**| `GET` | `/api/v1/sessions/{id}` | Retrieve session details with scorecards | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Progress**| `GET` | `/api/v1/progress/students/{id}` | Retrieve longitudinal skill mastery progression | Bearer Token (Verified Center Access) |
| **Analytics**| `GET`| `/api/v1/analytics/overview` | Organization-wide benchmarks for Super Admins | `SUPER_ADMIN` |
| **Analytics**| `GET`| `/api/v1/analytics/centers/{id}` | Operational metrics for a specific center | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Reports** | `GET` | `/api/v1/reports/attendance` | Stream attendance report as downloadable CSV | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Reports** | `GET` | `/api/v1/reports/students/{id}/dossier` | Longitudinal student developmental dossier | `TEACHER`, `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Users** | `GET` | `/api/v1/users` | List staff accounts (role and center filtered) | `CENTER_MANAGER`, `SUPER_ADMIN` |
| **Users** | `POST`| `/api/v1/users` | Provision a new staff user account | `CENTER_MANAGER` (Teachers only), `SUPER_ADMIN` |
| **Users** | `PUT` | `/api/v1/users/{id}/centers` | Assign staff member to learning centers | `SUPER_ADMIN` |
| **Audit Logs**| `GET`| `/api/v1/audit-logs` | Query immutable system-wide audit records | `SUPER_ADMIN` |

---

## 15. Authentication and Security

- **JWT Authentication:** Stateful user authentication via stateless HMAC-SHA256 signed JSON Web Tokens. Access tokens carry subject user UUID claims and expire after 30 minutes. Refresh tokens carry unique session claims and rotate every 7 days.
- **Adaptive Password Hashing:** Uses `bcrypt` with configurable salt work factor (`BCRYPT_ROUNDS=12`). Plaintext passwords are never stored in memory or persisted to the database.
- **Hierarchical Role-Based Access Control (RBAC):** Every endpoint enforces strict role verification dependencies (`require_super_admin`, `require_center_manager`, `require_teacher`).
- **Center-Level Data Isolation (ABAC):** Multi-center security prevents a staff member at Center A from inspecting or editing records belonging to Center B.
- **Input Validation:** Strict Pydantic v2 schemas reject unexpected attributes, malformed emails, out-of-bounds numbers, and invalid dates before database execution.
- **CORS Protection:** FastAPI CORS middleware is configured to whitelist authorized client origins.
- **Audit Logging:** Sensitive modifications record actor user ID, client IP address, action code, timestamp, and old/new JSON states.

---

## 16. Frontend Application

The frontend is a single-page application built with **React 18**, **Vite 5**, and **Tailwind CSS**, written strictly in pure JavaScript.

### Application Architecture
- **State Management:** `AuthContext.jsx` provides global authentication state, token storage, assigned center lists, active center switcher, and role predicates (`isSuperAdmin`, `isCenterManager`, `isTeacher`).
- **Centralized API Client:** `api/client.js` configures an Axios instance with request and response interceptors. The request interceptor dynamically attaches `Authorization: Bearer <token>` and `X-Center-ID: <active_center_id>`. The response interceptor catches HTTP 401s, clears expired tokens, and redirects to `/login`.
- **Role-Based Navigation:** `Sidebar.jsx` and `ProtectedRoute.jsx` filter visible links and route access according to the authenticated user's role.

### Implemented Views & Screens

| Route Path | Component | Description |
| :--- | :--- | :--- |
| `/login` | `LoginPage.jsx` | Authentication card with 1-click test fill for Super Admin, Manager, and Teacher |
| `/dashboard` | `DashboardPage.jsx` | Live occupancy gauges, attendance trends, quick actions, and org benchmarks |
| `/students` | `StudentListPage.jsx` | Center-scoped student table with name/ID search, status filter, and pagination |
| `/students/new` | `StudentCreatePage.jsx` | Multi-section student registration form with guardian details |
| `/students/:id` | `StudentDetailPage.jsx` | Demographic overview, longitudinal skill progress table, and transfer request modal |
| `/students/:id/edit` | `StudentEditPage.jsx` | OCC-protected student editor with version conflict alerts |
| `/transfers` | `TransferListPage.jsx` | Pending/completed transfer table with approval modal & Super Admin capacity override |
| `/attendance` | `AttendancePage.jsx` | Calendar roll call table, bulk status toggle, and 24h audit correction modal |
| `/competencies` | `CompetencyCatalogPage.jsx` | Standardized 4-tier rubric reference guide with subject domain filtering |
| `/sessions` | `SessionListPage.jsx` | Completed classroom sessions list with participant detail inspect modal |
| `/sessions/new` | `SessionCreatePage.jsx` | Form to log conducted session, student scores, and rate individual competencies |
| `/admin/centers` | `CenterManagementPage.jsx` | Campus locations list, capacity utilization, and center provisioning modal |
| `/admin/users` | `UserManagementPage.jsx` | Staff directory, role badges, and user provisioning modal |
| `/admin/reports` | `ReportsPage.jsx` | Attendance dataset date range filter, preview table, and streaming CSV export |
| `/admin/audit-logs`| `AuditLogsPage.jsx` | Immutable audit trail explorer with before/after JSON snapshot modal |

---

## 17. Testing

The codebase includes **123 automated test cases passing with a 100% success rate**.

### Test Suite Categories

1. **Authentication Tests (`tests/test_auth.py` — 21 tests):**
   - Password hashing and verification routines.
   - JWT token issuance, decoding, expiration rejection, and token-type mismatch prevention.
   - Login endpoint validation, locked/inactive account rejection, and token rotation.
2. **Authorization Tests (`tests/test_authorization.py` — 25 tests):**
   - RBAC role hierarchy verification (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`).
   - Center-level ABAC scoping via `X-Center-ID`.
   - Multi-center teacher context switching validation.
   - Super Admin global cross-center access verification.
3. **Domain Service Tests (`tests/test_backend_modules.py` — 7 tests):**
   - CRUD and business operations across Centers, Users, Transfers, Attendance, Competencies, Sessions, Reports, and Audit Logs.
4. **Student Management & OCC Tests (`tests/test_students.py` — 22 tests):**
   - Student creation, duplicate ID prevention, and atomic enrollment initialization.
   - Center-scoped student listing, multi-attribute filtering, and pagination.
   - Optimistic Concurrency Control (OCC) version collision rejection (`409 Conflict`).
5. **Database Model & Constraint Tests (`tests/test_models.py` — 10 tests):**
   - Table definitions, primary key UUID generation, foreign keys, cascade delete rules, check constraints, and audit preservation.
6. **Pydantic Schema Tests (`tests/test_schemas.py` — 30 tests):**
   - Request and response serialization across all domain schemas.
   - Date range validations, score limits (0-100), and email normalization.
7. **System Health Tests (`tests/test_health.py` — 3 tests):**
   - Basic liveness endpoint (`/health`), database connectivity probe (`/health/db`), and OpenAPI spec generation.
8. **Live PostgreSQL Integration Tests (`tests/test_postgres_integration.py` — 4 tests):**
   - Executed against a live PostgreSQL 18 instance.
   - Verifies all 17 tables, 8 native PostgreSQL enums, partial unique index rejection on duplicate active enrollments, and transaction rollback integrity.
9. **End-to-End Workflow Integration Test (`tests/test_e2e_workflow.py` — 1 comprehensive test):**
   - Validates the complete operational journey in a single multi-role execution:
     - Super Admin login and global benchmark analytics.
     - Center Manager login and student registration (`version=1`).
     - OCC verification: valid update succeeds (`version=2`); stale update with `version=1` is rejected with `409 Conflict`.
     - Multi-Center Teacher login, bulk attendance recording, and 24-hour audit-tracked correction.
     - Conducting a learning session and evaluating student against a curriculum competency.
     - Verification of automatic longitudinal skill progress progression.
     - Origin Manager transfer request; Destination Manager review and approval.
     - Atomic enrollment transition: old enrollment closed, new enrollment opened.
     - Attendance compliance report generation and streaming CSV download.
     - Verification of immutable before/after state snapshots in `audit_logs`.

### Running Tests in Windows PowerShell

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# 1. Run all 123 tests:
pytest -v

# 2. Run unit and authorization suites:
pytest tests/test_auth.py tests/test_authorization.py tests/test_schemas.py -v

# 3. Run student OCC and domain modules:
pytest tests/test_students.py tests/test_backend_modules.py -v

# 4. Run live PostgreSQL 18 integration tests:
pytest tests/test_postgres_integration.py -v

# 5. Run the complete End-to-End workflow test:
pytest tests/test_e2e_workflow.py -v
```

---

## 18. Production Deployment

The recommended production deployment architecture separates the static frontend SPA from the backend API and database:

```
Browser ──> Vercel (React Vite SPA) ──> Render (FastAPI Web Service) ──> Render (Managed PostgreSQL)
```

---

### A. PostgreSQL Database Deployment (Render)

1. Log in to [Render](https://render.com) and create a **New PostgreSQL Database**.
2. **Name:** `edutrack-db`
3. **Region:** Select the region closest to your users (e.g. `Oregon (US West)` or `Frankfurt (EU Central)`).
4. **PostgreSQL Version:** Select `15` or `16`.
5. Note the connection strings provided by Render:
   - **Internal Database URL:** Used by backend web services hosted on Render (faster, no egress fees).
   - **External Database URL:** Used for local migration management or external access.
6. **Important Connection String Format:**
   Render provides URLs starting with `postgres://...`. You must update the protocol prefix to `postgresql+psycopg://` so SQLAlchemy loads the psycopg v3 driver:
   ```
   postgresql+psycopg://username:password@dpg-xxxxxx.render.com/edutrack_db
   ```
7. *(Free-Tier Warning: Render free databases expire after 30 days unless upgraded to a paid instance)*.

---

### B. Backend Deployment (Render Web Service)

1. In Render, select **New Web Service** and connect your GitHub repository: `https://github.com/hd84339/eduTrack.git`.
2. Configure the deployment settings:
   - **Name:** `edutrack-api`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Region:** Must match the region selected for your PostgreSQL database.
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
3. Configure **Environment Variables** in Render:
   - `APP_NAME`: `EduTrack`
   - `APP_ENV`: `production`
   - `DEBUG`: `false`
   - `API_V1_PREFIX`: `/api/v1`
   - `CORS_ORIGINS`: `https://your-edutrack.vercel.app` (or `*` to allow all; automatic regex support is also enabled for `*.vercel.app` preview URLs).
   - `DATABASE_URL`: Your Render **Internal Database URL** (the app automatically normalizes `postgres://` or `postgresql://` into `postgresql+psycopg://`).
   - `JWT_SECRET_KEY`: A cryptographically secure random string of at least 32 characters (e.g. generate via `openssl rand -hex 32`).
   - `JWT_ALGORITHM`: `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `30`
   - `REFRESH_TOKEN_EXPIRE_DAYS`: `7`
   - `BCRYPT_ROUNDS`: `12`
4. Set the **Health Check Path** to `/health`.
5. Deploy the web service. Render will automatically install dependencies, execute `alembic upgrade head` to build the database tables, and start the Uvicorn server.
6. **Initial Database Seeding (First Deploy Only):**
   Open the Render **Shell** tab in the dashboard and run:
   ```bash
   python seed.py
   ```
   This seeds the initial centers, staff accounts (password `Password123!`), competencies, and sample students.

---

### C. Frontend Deployment (Vercel)

1. Log in to [Vercel](https://vercel.com) and click **Add New > Project**, importing `https://github.com/hd84339/eduTrack.git`.
2. Configure the project settings:
   - **Project Name:** `edutrack`
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and select `frontend` (crucial so Vercel detects Vite and `frontend/package.json`).
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`
3. Add **Environment Variables** in Vercel:
   - `VITE_API_BASE_URL`: The production URL of your Render backend (e.g. `https://edutrack-api.onrender.com/api/v1`).
     *(Must include `https://` and `/api/v1`, with no trailing slash)*.
4. **SPA Client-Side Routing Fallback (Resolves Page Refresh 404s):**
   The repository already includes [frontend/vercel.json](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/frontend/vercel.json) with SPA rewrite rules:
   ```json
   {
     "rewrites": [
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
   This ensures that refreshing sub-routes (such as `/students`, `/transfers`, or `/dashboard`) routes directly to `index.html` where React Router handles the URL client-side.
5. Click **Deploy**. Vercel will build and distribute the production bundle globally on its Edge Network.

---

### D. Production Verification Checklist

After deploying, run through this verification checklist:

- [ ] Probe backend health endpoint: `GET https://your-backend.onrender.com/health` returns `{"status": "ok"}`.
- [ ] Probe database health endpoint: `GET https://your-backend.onrender.com/health/db` returns `{"status": "ok", "database": "connected"}`.
- [ ] Open the frontend URL in your browser: `https://your-app.vercel.app`.
- [ ] Log in as Super Admin, Center Manager, and Teacher to verify role routing.
- [ ] Switch active center context using the navbar dropdown.
- [ ] Enroll a new student and verify automatic initial enrollment creation.
- [ ] Mark classroom attendance for today's date.
- [ ] Conduct a learning session and evaluate a competency rubric.
- [ ] Initiate and approve an inter-center student transfer.
- [ ] Generate and download an attendance CSV export.
- [ ] Inspect the immutable audit log as Super Admin to verify captured event snapshots.

---

## 19. Troubleshooting

### 1. PostgreSQL Connection Refused (`connection to server at "127.0.0.1", port 5432 failed`)
- **Cause:** PostgreSQL service is stopped or not listening on `127.0.0.1:5432`.
- **Solution:** Verify the service is running. On Windows, check Windows Services (`services.msc`) for `postgresql-x64-18`, or start the PostgreSQL process manually pointing to your data directory.

### 2. Invalid Driver / `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgresql.psycopg`
- **Cause:** `DATABASE_URL` is formatted as `postgres://` or `postgresql://` without specifying the driver.
- **Solution:** Update `DATABASE_URL` to explicitly use the psycopg v3 binary driver:
  ```ini
  DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/edutrack
  ```

### 3. Alembic Migration / Schema Out of Sync
- **Cause:** Database contains manual tables or is out of sync with Alembic revisions.
- **Solution:** Inspect current revision using `alembic current`. To reset, drop the database schema, recreate the database, and execute `alembic upgrade head`.

### 4. CORS Errors in Browser Console (`Access-Control-Allow-Origin`)
- **Cause:** The frontend origin is not allowed by FastAPI CORS middleware.
- **Solution:** In `backend/app/main.py`, verify `CORSMiddleware` includes your frontend domain in `allow_origins`.

### 5. 404 Error When Refreshing Frontend Routes on Vercel
- **Cause:** Vercel looks for a static file matching the route path (e.g. `/students/new`) instead of routing to `/index.html`.
- **Solution:** Add `frontend/vercel.json` with a rewrite rule directing all requests to `/index.html`.

### 6. HTTP 409 Conflict When Updating a Student
- **Cause:** Optimistic Concurrency Control (OCC) collision. The submitted `version` does not match the current database version.
- **Solution:** Reload the latest student data from the server, apply your changes to the latest version, and re-submit.

### 7. HTTP 422 Unprocessable Entity When Recording Attendance
- **Cause:** Timezone validation failure. The attendance date submitted is in the future relative to the center's configured timezone.
- **Solution:** Ensure the date matches the center's current local date (`center.timezone`).

### 8. Production JWT_SECRET_KEY Validation Error on Startup
- **Cause:** `APP_ENV=production` is set, but `JWT_SECRET_KEY` is shorter than 32 characters or contains the word `insecure`.
- **Solution:** Set a strong 32+ character random secret in your production environment variables.

---

## 20. Development Workflow

Follow this standard workflow when developing features for EduTrack:

1. **Pull Latest Changes:**
   ```powershell
   git pull origin main
   ```
2. **Activate Backend Environment:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   ```
3. **Verify PostgreSQL Service:** Ensure local PostgreSQL is listening on `127.0.0.1:5432`.
4. **Start Backend Server:**
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
5. **Start Frontend Dev Server (in a separate terminal):**
   ```powershell
   cd frontend
   npm run dev -- --port 3000
   ```
6. **Implement Code Changes:** Make modifications to backend routers/services or frontend components.
7. **Run Test Suites:**
   ```powershell
   cd backend
   pytest -v
   ```
8. **Verify Frontend Production Build:**
   ```powershell
   cd frontend
   npm run build
   ```
9. **Inspect Git Status & Diff:**
   ```powershell
   git status
   git diff
   ```

---

## 21. Known Limitations and Future Improvements

### Current Implemented Functionality (MVP)
- Full 16-table relational schema with partial unique indexes and native PostgreSQL enums.
- All 13 business services and REST API modules mounted under `/api/v1`.
- Dual-tier RBAC and center-level ABAC authorization with dynamic center switching.
- React 18 single-page application with 14 functional screens.
- 123 automated test cases passing with 100% success rate.

### Known Limitations
- **In-Memory Async Processing:** CSV reports and analytics aggregations execute synchronously in-process. High-volume reporting over millions of records would benefit from an asynchronous task queue (e.g. Celery / Redis).
- **Session Timeout UX:** When a token expires after 30 minutes, the user is redirected to `/login?expired=1`. In-flight form state is not preserved across re-authentication.

### Planned Future Improvements (Future Scope)
- **Parent / Guardian Portal:** A dedicated, restricted portal for guardians to view student attendance history, competency growth curves, and teacher session feedback.
- **Automated Check-In Kiosks:** On-campus tablet kiosk check-in support with barcode or QR code scanning for daily attendance roll call.
- **PDF Report Dossier Generation:** Server-side PDF rendering of comprehensive student developmental portfolios with printable charts.
- **Automated Email & SMS Alerts:** Integration with communication gateways (e.g. SendGrid, Twilio) for automated absence notifications sent to primary guardians.
- **SSO / Google Workspace Login:** OAuth2 Single Sign-On integration allowing staff to authenticate using corporate Google Workspace or Microsoft Azure AD accounts.

---

## 22. Project Status

| Area | Component | Implementation Status | Test Status |
| :--- | :--- | :---: | :---: |
| **Specifications** | Requirements, Architecture, Database, ER, API Docs | **Completed** | Verified |
| **Database** | 16 PostgreSQL Models & Alembic Migration | **Completed** | 100% Passing (10 Model + 4 Integration tests) |
| **Auth & Security** | JWT Authentication, Argon2/Bcrypt, RBAC & ABAC | **Completed** | 100% Passing (21 Auth + 25 Authz tests) |
| **Student Domain** | Student CRUD, OCC Concurrency, Enrollment Lifecycle | **Completed** | 100% Passing (22 Student tests) |
| **Transfers** | Inter-Center Transfer Proposals & Capacity Overrides | **Completed** | 100% Passing (Integrated in E2E) |
| **Attendance** | Daily Roll Call, Timezone Check, 24h Correction Audit | **Completed** | 100% Passing (Integrated in E2E) |
| **Curriculum** | 4-Tier Competencies, Activity Templates, Sessions | **Completed** | 100% Passing (Integrated in E2E) |
| **Analytics** | Dashboard KPIs, Org Benchmarks, CSV Reports Engine | **Completed** | 100% Passing (Integrated in E2E) |
| **Audit Logging** | Immutable Event Ledger with JSON Snapshots | **Completed** | 100% Passing (Integrated in E2E) |
| **Frontend** | React 18 SPA, Tailwind CSS, 14 Operational Screens | **Completed** | Production Build Verified (0 errors) |
| **Total Test Suite**| 123 Automated Tests | **Completed** | **123 Passed, 0 Failed, 0 Warnings** |

---

## 23. License and Contribution

### License
A formal software license has not yet been specified for this project. All rights are reserved by the project owners.

### Contribution Guidelines
Contributions to EduTrack are welcome by authorized team members. Please adhere to the following workflow:
1. Create a feature branch from `main`:
   ```powershell
   git checkout -b feature/your-feature-name
   ```
2. Follow existing architectural conventions (FastAPI modular services, Pydantic schemas, React pure JavaScript JSX).
3. Do not modify or bypass database integrity constraints or audit logging protections.
4. Add automated Pytest test cases covering any new business logic or API endpoints.
5. Verify that all test suites pass with zero failures:
   ```powershell
   pytest -v
   ```
6. Verify that the frontend production bundle compiles cleanly:
   ```powershell
   cd frontend
   npm run build
   ```
7. Open a Pull Request detailing your changes and test verification results.

---

## 24. Contact and Repository

- **GitHub Repository:** [https://github.com/hd84339/eduTrack.git](https://github.com/hd84339/eduTrack.git)
- **Primary Documentation Directory:** [docs/](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/)
  - [Functional Requirements (`REQUIREMENTS.md`)](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/REQUIREMENTS.md)
  - [System Architecture Blueprint (`ARCHITECTURE.md`)](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ARCHITECTURE.md)
  - [Database Design & Integrity Constraints (`DATABASE_DESIGN.md`)](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/DATABASE_DESIGN.md)
  - [Entity-Relationship Diagram (`ER_DIAGRAM.md`)](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ER_DIAGRAM.md)
  - [REST API Specification (`API_DESIGN.md`)](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/API_DESIGN.md)
