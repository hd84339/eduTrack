# EduTrack — Student Learning & Activity Management Platform

EduTrack is an enterprise-grade, centralized management platform designed for educational organizations operating multiple distributed learning centers. It provides unified governance over student enrollment lifecycles, cross-center transfers, daily classroom attendance, curriculum activity templating, learning session observations, and longitudinal competency progress tracking.

---

## 1. Technology Stack

| Layer | Technology | Decision Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | **React.js 18+ (Vite)** | Blazing fast build tooling, component modularity, rich ecosystem. |
| **Frontend Styling** | **Tailwind CSS** | Utility-first CSS allowing rapid, consistent, responsive design without stylesheet bloat. |
| **Backend Framework** | **Python 3.11+ / FastAPI** | High performance (ASGI), automatic OpenAPI/Swagger documentation, strict Pydantic type validation. |
| **Database** | **PostgreSQL 15+** | Relational ACID guarantees, native JSONB support, robust composite indexing, and transactional isolation. |
| **ORM & Migrations** | **SQLAlchemy 2.0 & Alembic** | Modern typed declarative ORM mapping, explicit connection pooling, and versioned database migrations. |
| **Authentication** | **JWT (JSON Web Tokens)** | Stateless token-based auth with short-lived access tokens and refresh token rotation. |
| **Architecture** | **Modular Monolith** | Combines the operational simplicity of a single deployment unit with the modular isolation of domain services. |

---

## 2. Core Functional Modules

1. **Authentication & Authorization:** Secure email/password login, JWT token issuance and rotation, role-based access control (RBAC), and center-level data scoping (ABAC).
2. **Learning Center Management:** Center provisioning, operational metadata, capacity limits, and physical address tracking.
3. **Student Management:** Student demographic profiles, emergency contacts, medical/dietary notes, and status management with Optimistic Concurrency Control (OCC).
4. **Student Enrollment & Center Transfers:** Longitudinal enrollment tracking, cross-center transfer request workflows with dual-center validation and historical preservation.
5. **Attendance Management:** Daily single and bulk attendance capture, database-enforced single-entry-per-day constraints, and 24-hour correction audit trails.
6. **Learning Activity Management:** Standardized curriculum activity templates with age grading, durations, and competency mappings.
7. **Learning Session Management:** Conducting and recording teacher-led group or individual sessions with qualitative feedback and mastery assessments.
8. **Student Progress Tracking:** Aggregated competency progression tracking and skill mastery histories.
9. **Dashboard & Analytics:** Real-time operational dashboards for Center Managers and high-level organizational analytics for Super Admins.
10. **Reports:** Exportable attendance reports (CSV/JSON), center performance benchmarks, and comprehensive student longitudinal dossiers.
11. **User & Role Management:** Staff provisioning, role assignments (`SUPER_ADMIN`, `CENTER_MANAGER`, `TEACHER`), and center mapping.
12. **Audit Logging:** System-wide immutable security and data modification logging capturing actor, IP, timestamp, old values, and new values.

---

## 3. Architecture Overview

EduTrack follows a **Modular Monolith** architecture:

```
EduTrack/
├── frontend/               # React + Vite Single Page Application
│   ├── src/
│   │   ├── components/     # Common design system primitives
│   │   ├── features/       # Feature-driven slices (auth, students, attendance, etc.)
│   │   └── context/        # Client auth & global state
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── core/           # Config, database engine, security, dependencies
│   │   └── modules/        # Domain modules (router, service, repository, schemas)
│   └── alembic/            # Database schema migration scripts
├── docs/                   # Architectural & System Documentation
│   ├── REQUIREMENTS.md     # Functional & Non-Functional Specifications
│   ├── ARCHITECTURE.md     # Detailed Architectural Blueprint
│   ├── DATABASE_DESIGN.md  # Relational Schema, Constraints & Indexes
│   ├── ER_DIAGRAM.md       # Mermaid Entity-Relationship Diagram
│   └── API_DESIGN.md       # Comprehensive REST API Specification
├── docker-compose.yml      # Local development container orchestration
├── .gitignore              # Git ignore rules
└── README.md               # Project entry point
```

For in-depth architectural diagrams, concurrency strategies, and authorization rules, refer to [ARCHITECTURE.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ARCHITECTURE.md).

---

## 4. Key Engineering Highlights

- **Strict Referential & Uniqueness Guarantees:** Duplicate daily attendance is prevented at the database engine level via `UNIQUE (student_id, attendance_date)`.
- **Optimistic Concurrency Control (OCC):** Prevents lost updates during concurrent edits by multiple administrators through integer `version` checking.
- **Traceable Attendance Corrections:** Any historical attendance modification automatically writes to an append-only `attendance_audit_logs` table requiring a mandatory justification reason.
- **Atomic Student Transfers:** Inter-center student relocations execute inside atomic ACID transactions, simultaneously closing old enrollments, establishing new enrollments, and updating active center pointers without breaking historical attendance ties.

---

## 5. Development Roadmap

- [x] **Step 1: Project Foundation & Specification**
  - [x] Functional & Non-functional requirements specification ([REQUIREMENTS.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/REQUIREMENTS.md))
  - [x] Modular monolithic architecture blueprint ([ARCHITECTURE.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ARCHITECTURE.md))
  - [x] PostgreSQL relational schema & constraints design ([DATABASE_DESIGN.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/DATABASE_DESIGN.md))
  - [x] Mermaid ER diagram with complete cardinality mapping ([ER_DIAGRAM.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/ER_DIAGRAM.md))
  - [x] RESTful API endpoints and contracts design ([API_DESIGN.md](file:///c:/Users/hd843/OneDrive/Documents/eduTrack/docs/API_DESIGN.md))
- [ ] **Step 2: Backend Core Setup & Database Migrations**
  - [ ] FastAPI project initialization, Pydantic settings, and logging setup
  - [ ] PostgreSQL connection pool and SQLAlchemy 2.0 Base setup
  - [ ] Alembic migration initialization and initial schema migration
  - [ ] Seed script for super admin, sample centers, and permissions
- [ ] **Step 3: Authentication & Multi-Tenant Authorization**
  - [ ] JWT token issuance, refresh token rotation, and password hashing
  - [ ] RBAC & Center scoping FastAPI dependencies
- [ ] **Step 4: Student, Center & Transfer Management**
  - [ ] Center management CRUD
  - [ ] Student CRUD with OCC versioning
  - [ ] Transfer proposal and approval ACID workflow
- [ ] **Step 5: Attendance & Activity Engine**
  - [ ] Single and bulk attendance submission with duplicate rejection
  - [ ] Attendance correction audit trail
  - [ ] Activity template management and learning session scorecard recording
- [ ] **Step 6: Frontend Development (React + Vite + Tailwind)**
  - [ ] Project scaffolding, Tailwind design tokens, and layout (Sidebar, Navbar)
  - [ ] Auth state, protected routing, and center switcher
  - [ ] Student management and transfer modals
  - [ ] Daily attendance roster and bulk attendance grid
  - [ ] Session observation logging UI
  - [ ] Dashboard & report exports
- [ ] **Step 7: Verification, Automated Testing & Dockerization**
  - [ ] Pytest integration suite for core workflows
  - [ ] Frontend unit tests and build verification
  - [ ] Production-ready Docker Compose orchestration
