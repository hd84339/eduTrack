# EduTrack — Student Learning & Activity Management Platform

EduTrack is an enterprise-grade, centralized management platform designed for educational organizations operating multiple distributed learning centers. It provides unified governance over student enrollment lifecycles, cross-center transfers, daily classroom attendance, curriculum activity templating, learning session observations with multi-competency evaluations, and longitudinal competency progress tracking.

---

## 1. Technology Stack

| Layer | Technology | Decision Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | **React.js 18+ (Vite)** | Blazing fast build tooling, component modularity, rich ecosystem. |
| **Frontend Styling** | **Tailwind CSS** | Utility-first CSS allowing rapid, consistent, responsive design without stylesheet bloat. |
| **Backend Framework** | **Python 3.11+ / FastAPI** | High performance (ASGI), automatic OpenAPI/Swagger documentation, strict Pydantic type validation. |
| **Database** | **PostgreSQL 15+** | Relational ACID guarantees, normalized multi-competency relational model, and transactional isolation. |
| **ORM & Migrations** | **SQLAlchemy 2.0 & Alembic** | Modern typed declarative ORM mapping, explicit connection pooling, and versioned database migrations. |
| **Authentication** | **JWT (JSON Web Tokens)** | Stateless token-based auth with short-lived access tokens and refresh token rotation. |
| **Architecture** | **Modular Monolith** | Combines the operational simplicity of a single deployment unit with the modular isolation of domain services. |

---

## 2. Core Functional Modules

1. **Authentication & Authorization:** Secure email/password login, JWT token issuance and rotation, role-based access control (RBAC), and center-level data scoping (ABAC) with active center switcher for multi-center staff.
2. **Learning Center Management:** Center provisioning, operational metadata, timezone configuration, capacity limits, and physical address tracking.
3. **Student Management:** Student demographic profiles, guardian and emergency contacts, non-sensitive administrative notes, and status management with Optimistic Concurrency Control (OCC).
4. **Student Enrollment & Center Transfers:** Longitudinal enrollment tracking, single-active-enrollment guarantee via partial unique index, cross-center transfer requests with Super Admin capacity override support.
5. **Attendance Management:** Daily single and bulk attendance capture, database-enforced single-entry-per-day constraints, timezone-aware date verification, and 24-hour correction audit trails.
6. **Competency Catalog & Activity Management:** Standardized curriculum competencies and activity templates with normalized multi-competency linkages.
7. **Learning Session Management:** Conducting and recording teacher-led sessions with granular per-competency mastery evaluations and qualitative observations.
8. **Student Progress Tracking:** Normalized aggregated competency progression tracking across 4 mastery tiers (`EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`).
9. **Dashboard & Analytics:** Real-time operational dashboards for Center Managers (occupancy, attendance, session volume) and organizational analytics for Super Admins.
10. **Reports:** Exportable attendance reports (CSV/JSON), center performance benchmarks, and comprehensive student longitudinal dossiers.
11. **User & Role Management:** Staff provisioning, role assignments (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`), and center mapping.
12. **Audit Logging:** System-wide immutable security and data modification logging with `ON DELETE RESTRICT` referential protection.

---

## 3. Architecture Overview

EduTrack follows a **Modular Monolith** architecture:

```
EduTrack/
├── frontend/               # React + Vite Single Page Application
│   ├── src/
│   │   ├── components/     # Common design system primitives
│   │   ├── features/       # Feature-driven slices (auth, students, attendance, etc.)
│   │   └── context/        # Client auth & active center context
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── core/           # Config, database engine, security, dependencies, timezones
│   │   └── modules/        # Domain modules (router, service, repository, schemas)
│   └── alembic/            # Database schema migration scripts
├── docs/                   # Architectural & System Documentation
│   ├── REQUIREMENTS.md     # Functional & Non-Functional Specifications
│   ├── ARCHITECTURE.md     # Detailed Architectural Blueprint
│   ├── DATABASE_DESIGN.md  # Relational Schema, Constraints & Clean Indexing
│   ├── ER_DIAGRAM.md       # Mermaid Entity-Relationship Diagram
│   └── API_DESIGN.md       # Comprehensive REST API Specification
├── docker-compose.yml      # Local development container orchestration
├── .gitignore              # Git ignore rules
└── README.md               # Project entry point
```

For in-depth architectural diagrams, concurrency strategies, and authorization rules, refer to [ARCHITECTURE.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ARCHITECTURE.md).

---

## 4. Key Engineering Highlights

- **Strict Referential & Uniqueness Guarantees:** Duplicate daily attendance is prevented at the database engine level via `UNIQUE (student_id, attendance_date)`. Redundant duplicate indexes on unique columns are explicitly avoided.
- **Single Active Enrollment Guarantee:** Enforced via a PostgreSQL partial unique index: `WHERE status = 'ACTIVE' AND end_date IS NULL`.
- **Normalized Multi-Competency Model:** Activities map to standardized competencies via `activity_competencies`, and session observations evaluate students per competency via `session_student_evaluations`.
- **Optimistic Concurrency Control (OCC):** Prevents lost updates during concurrent edits by multiple administrators through integer `version` checking.
- **Protected Audit Trails:** Corrections to attendance automatically write to `attendance_audit_logs`, protected by `ON DELETE RESTRICT` against accidental deletion.
- **Atomic Student Transfers:** Inter-center student relocations execute inside atomic ACID transactions, simultaneously closing old enrollments, establishing new enrollments, and updating active center pointers without breaking historical attendance ties.

---

## 5. Development Roadmap & Implementation Status

- [x] **Step 1: Project Foundation & Specification**
  - [x] Functional & Non-functional requirements specification ([REQUIREMENTS.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/REQUIREMENTS.md))
  - [x] Modular monolithic architecture blueprint ([ARCHITECTURE.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ARCHITECTURE.md))
  - [x] PostgreSQL relational schema & constraints design ([DATABASE_DESIGN.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/DATABASE_DESIGN.md))
  - [x] Mermaid ER diagram with complete cardinality mapping ([ER_DIAGRAM.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ER_DIAGRAM.md))
  - [x] RESTful API endpoints and contracts design ([API_DESIGN.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/API_DESIGN.md))
- [x] **Step 2: Specification Validation & Technical Readiness**
  - [x] Complete technical consistency review across all documentation
  - [x] Normalized competency model integration
  - [x] Single-active-enrollment and non-overlapping date protection
  - [x] Timezone-aware date boundary validation design
  - [x] Audit log cascading delete protection (`ON DELETE RESTRICT`)
  - [x] Clean index optimization (removed duplicate indexes on unique columns)
  - [x] Confirmation of all operational decisions (24h grace window, center switcher, capacity override)
- [x] **Step 3: Backend Foundation, Database Models & Alembic Migrations**
  - [x] FastAPI modular monolith scaffolding, Pydantic settings, and CORS middleware
  - [x] SQLAlchemy 2.0 declarative models for all 16 domain tables
  - [x] 8 native PostgreSQL enums and partial unique index `uq_student_active_enrollment`
  - [x] Alembic migration `69f79dd04f39_initial_schema` applied to live PostgreSQL 18
  - [x] Seed script ([seed.py](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/backend/seed.py)) with sample centers, staff accounts, competencies, activities, and students
- [x] **Step 4: Authentication & Authorization (RBAC & ABAC)**
  - [x] Argon2 password hashing and JWT access & refresh token rotation
  - [x] Role-Based Access Control (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`)
  - [x] Center-level attribute-based access control with `X-Center-ID` header validation
- [x] **Step 5: Business Domain Modules & REST APIs**
  - [x] Student Management with Optimistic Concurrency Control (`409 Conflict` on stale version)
  - [x] Center Management with capacity enforcement and live occupancy
  - [x] Center Transfers with Super Admin capacity override and atomic enrollment transition
  - [x] Daily Attendance with bulk submission, timezone future date rejection, and 24h audit correction
  - [x] Curriculum Competency Catalog with 4-tier rubric definitions (`EMERGING`, `DEVELOPING`, `PROFICIENT`, `MASTERY`)
  - [x] Activity Templates & Conducted Learning Sessions with granular skill scorecards
  - [x] Longitudinal Student Skill Mastery progression tracking
  - [x] Operational Analytics & Super Admin Benchmarks
  - [x] Reports engine with streaming CSV export and student dossiers
  - [x] User Management and Immutable Security Audit Trail
- [x] **Step 6: React Frontend Application**
  - [x] React 18 + Vite 5 SPA (strict pure JavaScript, Tailwind CSS)
  - [x] Centralized Axios client with automatic Bearer token and `X-Center-ID` injection
  - [x] Multi-center context switcher, responsive navigation, role-protected routes
  - [x] Complete UI pages: Login, Dashboard, Student List/Create/Detail/Edit, Attendance Roll Call & Correction, Competency Catalog, Session List/Create, Transfer Review Modal, Center Management, Staff Management, Reports & CSV Export, System Audit Trail
  - [x] Production build verified (`npm run build`: 1,583 modules compiled, 0 errors, 0 warnings)
- [x] **Step 7: Testing & Quality Assurance**
  - [x] 122 backend unit and model tests passed (`100%`)
  - [x] 4 live PostgreSQL 18 integration tests passed (`100%`)
  - [x] Complete End-to-End user journey test suite passed ([test_e2e_workflow.py](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/backend/tests/test_e2e_workflow.py))

---

## 6. Quick Start & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 15+ (Running locally on `127.0.0.1:5432`)

---

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Configure environment variables:**
   Verify `backend/.env` contains your PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/edutrack
   JWT_SECRET_KEY=edutrack-super-secret-development-key-change-in-production-min-32-chars-long
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ENVIRONMENT=development
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Seed demo data:**
   ```bash
   python seed.py
   ```

6. **Start FastAPI backend server:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   API interactive documentation will be accessible at: `http://127.0.0.1:8000/docs`

---

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start Vite development server:**
   ```bash
   npm run dev
   ```
   The application will be accessible at: `http://localhost:3000`

4. **Verify production bundle build:**
   ```bash
   npm run build
   ```

---

### Test Credentials (Pre-Seeded)

All accounts are seeded with password: `Password123!`

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@edutrack.org` | `Password123!` | Global access across all centers & system audit logs |
| **Center Manager** | `manager.north@edutrack.org` | `Password123!` | Full operational authority for North Ridge Center |
| **Center Manager** | `manager.south@edutrack.org` | `Password123!` | Full operational authority for South Bay Center |
| **Teacher** | `teacher.smith@edutrack.org` | `Password123!` | Multi-center teacher assigned to North & South Centers |

---

### Running Automated Test Suites

From the `backend/` directory:

1. **Run full backend test suite (122 tests):**
   ```bash
   pytest tests/test_auth.py tests/test_authorization.py tests/test_backend_modules.py tests/test_health.py tests/test_models.py tests/test_schemas.py tests/test_students.py tests/test_postgres_integration.py -v
   ```

2. **Run End-to-End workflow integration test:**
   ```bash
   pytest tests/test_e2e_workflow.py -v
   ```
