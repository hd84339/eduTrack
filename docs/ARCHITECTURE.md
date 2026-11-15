# EduTrack — System Architecture Document

**Document Version:** 1.1.0<br>
**Pattern:** Modular Monolith<br>
**Tech Stack:** React (Vite) + FastAPI (Python) + PostgreSQL (SQLAlchemy + Alembic)

---

## 1. High-Level System Architecture

EduTrack is structured as a **Modular Monolith**. This pattern combines the operational simplicity and single-unit deployment of a monolith with the strict domain encapsulation, loose coupling, and maintainability of microservices.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT PRESENTATION LAYER                       │
│                   React + Vite SPA (Tailwind CSS)                      │
│            - Active Center Selector Dropdown (Multi-Center)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / REST (JSON)
                                    │ JWT Bearer Authentication
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      REVERSE PROXY / INGRESS                           │
│                   Nginx / Cloud Load Balancer                          │
│               - TLS Termination  - Static Assets Hosting               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Reverse Proxy (Port 8000)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   BACKEND APPLICATION LAYER (FastAPI)                  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     Cross-Cutting Core Layer                     │  │
│  │   Auth / Security  │  RBAC/ABAC Guard  │  DB Session Lifecycle   │  │
│  │   Logging / Audit  │  Global Error Hdl │  Pagination / Filters   │  │
│  │   Timezone Engine  │  OCC Interceptor  │  Transaction Manager    │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │                                  │
│  ┌──────────────────────────────────┴───────────────────────────────┐  │
│  │                      Domain Feature Modules                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │   auth/    │  │  centers/  │  │ students/  │  │transfers/  │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │attendance/ │  │activities/ │  │competencies│  │ sessions/  │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │ progress/  │  │analytics/  │  │  reports/  │  │   users/   │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │
│  │  ┌────────────┐                                                  │  │
│  │  │   audit/   │                                                  │  │
│  │  └────────────┘                                                  │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
└─────────────────────────────────────┼──────────────────────────────────┘
                                      │ SQLAlchemy 2.0 ORM / Connection Pool
                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                              │
│                    PostgreSQL Relational Database                      │
│            - Relational Constraints & Foreign Keys (RESTRICT)          │
│            - Unique & Partial Constraints (Zero Duplicates)            │
│            - Normalized Multi-Competency Model                         │
│            - Transactional ACID Guarantees                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Architecture (React + Vite)

The frontend is a single-page application (SPA) created with Vite and React.js, styled with Tailwind CSS.

### 2.1 Directory Structure
```
frontend/
├── public/                     # Static assets (favicons, logos)
├── src/
│   ├── assets/                 # SVGs, images, static styles
│   ├── components/             # Reusable global UI primitives
│   │   ├── ui/                 # Buttons, Inputs, Modals, Badges, Tables
│   │   ├── layout/             # Sidebar, Navbar, PageContainer, Breadcrumbs
│   │   └── feedback/           # Alert, Toast, Loader, Skeleton
│   ├── context/                # Global React contexts (AuthContext, ActiveCenterContext)
│   ├── features/               # Domain-driven feature packages
│   │   ├── auth/               # Login, Token storage, Password Reset
│   │   ├── centers/            # Center list, details, center switcher dropdown
│   │   ├── students/           # Student directory, profile, enrollment history
│   │   ├── transfers/          # Transfer request modal, capacity override workflow
│   │   ├── attendance/         # Daily roster, bulk attendance grid, 24h edit modal
│   │   ├── competencies/       # Competency catalog viewer & manager
│   │   ├── activities/         # Normalized activity templates (competency selector)
│   │   ├── sessions/           # Session logger, multi-competency observation scorecard
│   │   ├── progress/           # Student mastery progression radar/timeline
│   │   ├── dashboard/          # Metric cards, occupancy meter, activity feeds
│   │   ├── reports/            # Export generators, filters, tabular previews
│   │   └── users/              # Staff management, role assignments
│   ├── hooks/                  # Global custom hooks (useDebounce, usePagination, useActiveCenter)
│   ├── lib/                    # Third-party wrappers (axiosInstance, dateUtils)
│   ├── routes/                 # AppRoutes, ProtectedRoute, RoleGuard
│   ├── types/                  # Prop types and shared data contracts
│   ├── App.jsx
│   └── main.jsx
├── tailwind.config.js
├── vite.config.js
└── package.json
```

### 2.2 Key Frontend Architectural Decisions
1. **Server-State Management:** Server data is fetched and cached using `@tanstack/react-query` to manage caching, refetching, background invalidation, and pagination states without polluting global client state.
2. **Client Authentication & Center Context:**
   - `AuthContext`: Preserves user profile, JWT tokens, system role, and assigned centers.
   - `ActiveCenterContext`: Manages the currently selected active center for multi-center staff via an application header dropdown. The active `center_id` is passed as a query parameter or header to scoped API endpoints.
3. **Route Guards & Granular Access:**
   - `<ProtectedRoute>` verifies JWT token validity.
   - `<RoleGuard allowedRoles={['SUPER_ADMIN', 'CENTER_MANAGER']}>` restricts navigation.
   - Unprivileged attempts automatically redirect to an unauthorized view or fallback dashboard.
4. **API Client & Interceptors:** Centralized Axios instance with:
   - Request interceptor injecting `Authorization: Bearer <token>` and `X-Center-ID: <active_center_id>`.
   - Response interceptor catching HTTP `401` to trigger seamless refresh token rotation or redirect to `/login`.
   - Concurrency conflict listener catching HTTP `409` to display an OCC resolution dialog ("Record was updated by another user. Reload latest data?").

---

## 3. Backend Architecture (FastAPI Modular Monolith)

The backend is built with Python 3.11+ using FastAPI, designed as independent cohesive modules adhering to separation of concerns.

### 3.1 Module Organization Pattern
Each domain feature in `backend/app/modules/` follows a standard 4-layer design:
```
backend/
├── app/
│   ├── core/                   # System-wide cross-cutting concerns
│   │   ├── config.py           # Pydantic BaseSettings (.env loading)
│   │   ├── database.py         # SQLAlchemy engine, sessionmaker, Base
│   │   ├── security.py         # Passlib (bcrypt) & PyJWT encoding/decoding
│   │   ├── dependencies.py     # Auth extraction, DB injection, center permission guards
│   │   ├── exceptions.py       # Custom domain exceptions & HTTP mapping
│   │   ├── pagination.py       # Standard pagination schemas & helpers
│   │   ├── timezones.py        # Center timezone resolution & date validation
│   │   └── middleware.py       # Logging, Request ID, CORS handling
│   ├── models/                 # Aggregated ORM models (imported into Base metadata)
│   ├── modules/
│   │   ├── auth/               # Auth routes, schemas, JWT service
│   │   ├── centers/            # Learning center service & endpoints
│   │   ├── students/           # Student profile service & endpoints
│   │   ├── enrollments/        # Enrollment and transfer workflow service
│   │   ├── attendance/         # Attendance single/bulk logic & audit
│   │   ├── competencies/       # Competency catalog management
│   │   ├── activities/         # Normalized activity template registry
│   │   ├── sessions/           # Learning session execution & multi-competency scoring
│   │   ├── progress/           # Competency analytics calculations
│   │   ├── dashboard/          # Aggregation queries for dashboard metrics
│   │   ├── reports/            # Data streaming / CSV generation
│   │   ├── users/              # User management & center assignments
│   │   └── audit/              # Audit log inquiry & event interceptors
│   ├── main.py                 # FastAPI application instantiation & router registry
│   └── tests/                  # Unit and integration test suites
├── alembic/                    # Database migration scripts
│   ├── versions/
│   └── env.py
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

### 3.2 Layered Architecture per Module
Within each domain module (e.g., `attendance/`):
1. **`router.py` (Presentation Layer):** Exposes HTTP paths, validates input schemas via Pydantic, calls services, and serializes output responses.
2. **`service.py` (Business Logic Layer):** Orchestrates business rules, transactions, permission validation, timezone checks, and calls repositories.
3. **`repository.py` (Data Access Layer):** Direct SQLAlchemy query builder executing database read/writes.
4. **`schemas.py` (Contract Layer):** Pydantic DTOs for `Create`, `Update`, `Read`, and `Filter` requests.

---

## 4. Database Communication, Date Validation & Transaction Management

```
FastAPI Request ──► Depends(get_db) ──► SessionLocal() ──► SQLAlchemy QueuePool (PostgreSQL)
        │                                                           │
        │─── Success: Service completes without errors ─────────────┼──► db.commit()
        │                                                           │
        └─── Exception: Validation / Business / DB Error ───────────┴──► db.rollback()
```

- **Connection Pool:** Managed via SQLAlchemy `QueuePool` with parameters:
  - `pool_size = 20`
  - `max_overflow = 10`
  - `pool_recycle = 1800` (recycles connections older than 30 minutes).
  - `pool_pre_ping = True` (executes `SELECT 1` on checkout to avoid stale socket drops).

- **Date Validation Strategy (Timezone Aware):**
  - Database-level `CHECK (attendance_date <= CURRENT_DATE)` is explicitly avoided because `CURRENT_DATE` depends on the database server session timezone and can reject legitimate records or accept invalid future dates for distributed centers across multiple timezones.
  - Instead, the backend service resolves the target learning center's local timezone (e.g., `America/Los_Angeles`), determines the center's current local calendar date, and validates that `attendance_date <= center_current_date`.

- **Atomic Transaction Sequences:** Multi-table state mutations are wrapped in explicit database transactions (`async with db.begin()` or `with db.begin()`):

  #### 1. Student Transfer Execution Sequence:
  ```python
  # Atomic Transfer Execution:
  async with db.begin():
      # 1. Verify target center capacity (throw 422 if full, unless super admin override provided)
      # 2. Close source enrollment: end_date = effective_date, status = 'TRANSFERRED'
      # 3. Create destination enrollment: start_date = effective_date, end_date = NULL, status = 'ACTIVE'
      # 4. Update student: current_center_id = destination_center_id, version = version + 1
      # 5. Update transfer_request: status = 'APPROVED', reviewed_by = reviewer_id, reviewed_at = NOW()
      # 6. Insert audit_log: action = 'TRANSFER_APPROVE', capturing any capacity_override_reason
  ```

  #### 2. Multi-Competency Session Evaluation Sequence:
  ```python
  # Atomic Session & Evaluation Ingestion:
  async with db.begin():
      # 1. Validate student enrollment at center on session_date
      # 2. Insert learning_sessions record
      # 3. Insert session_students records (participation, feedback, optional score)
      # 4. Insert session_student_evaluations records (per targeted competency)
      # 5. Recalculate and upsert student_skill_progress
  ```

---

## 5. Authentication & Authorization Flow

### 5.1 Authentication Flow (JWT with Refresh Token Rotation)

```
[ Client ]                          [ Auth API ]                   [ Database ]
    │                                     │                              │
    │── 1. POST /api/v1/auth/login ──────►│                              │
    │      { email, password }            │── 2. Query user by email ───►│
    │                                     │◄── 3. Return user + hash ────│
    │                                     │                              │
    │                                     │── 4. Verify password (bcrypt)│
    │                                     │   Generate access_token      │
    │                                     │   Generate refresh_token     │
    │                                     │                              │
    │◄── 5. Return tokens + user profile ─│                              │
    │                                     │                              │
    │── 6. GET /api/v1/resource ─────────►│                              │
    │      Header: Bearer <access_token>  │── 7. Validate signature/exp  │
    │      Header: X-Center-ID: <uuid>    │   Extract sub, role, centers │
    │◄── 8. Return 200 Protected Data ────│                              │
```

### 5.2 Authorization Flow: Role-Based + Center Scoping (RBAC + ABAC)

Every protected route executes a two-stage authorization verification:

1. **Role Check (RBAC):**
   - Validates if the authenticated user's `role` is permitted for the action (e.g., only `SUPER_ADMIN` can create a new center).
2. **Center Scoping Check (ABAC):**
   - For `SUPER_ADMIN`: Automatic bypass; granted access across all centers.
   - For `CENTER_MANAGER` and `TEACHER`: The requested resource's `center_id` is inspected against the user's assigned center list (`user_centers`).
   - If `requested_center_id NOT IN user.assigned_center_ids`, the request immediately aborts with HTTP `403 Forbidden`.

---

## 6. Concurrency Strategy (Optimistic Concurrency Control - OCC)

In educational centers, multiple administrators or teachers may view and modify student data simultaneously. To avoid silent data loss ("last write wins"), EduTrack implements **Optimistic Concurrency Control (OCC)** on critical editable records (`students`, `attendance_records`).

### 6.1 OCC Mechanism
1. Every editable entity includes an integer `version` field (starts at `1`).
2. When a client fetches a record, the payload includes the current `version`.
3. When submitting an update (`PUT` or `PATCH`), the client must send back the `version` it read.
4. The database update executes an atomic conditional mutation:
   ```sql
   UPDATE students
   SET first_name = :first_name,
       last_name = :last_name,
       version = version + 1,
       updated_at = NOW()
   WHERE id = :id AND version = :expected_version;
   ```
5. If the number of affected rows is `0`:
   - It indicates another user updated the record in the interim.
   - The backend raises an `HTTP 409 Conflict` exception with payload:
     ```json
     {
       "error": {
         "code": "CONCURRENCY_CONFLICT",
         "message": "The record has been updated by another user. Please reload the latest data."
       }
     }
     ```
6. The frontend prompts the user to review diffs or refresh before reapplying changes.

---

## 7. Scalability & Evolution Strategy

Although starting as a clean monolithic deployment, EduTrack is engineered for vertical and horizontal scalability:

1. **Stateless API Scale-Out:**
   - The FastAPI backend application holds zero in-memory user session state; all authorization is derived from signed JWTs and database state.
   - Multiple backend replicas can run behind an Nginx or Kubernetes ingress without sticky sessions.
2. **Database Read/Write Splitting Readiness:**
   - Aggregation-heavy modules (`reports/`, `analytics/`) are decoupled into standalone queries, ready to point to a PostgreSQL read replica without altering domain logic.
3. **Database Indexing & Partitioning Strategy:**
   - Composite indexes on high-frequency query patterns (`(center_id, attendance_date)`, `(status, center_id)`).
   - If attendance data grows beyond millions of records, `attendance_records` can be partitioned by calendar year (`RANGE (attendance_date)`) seamlessly using PostgreSQL table partitioning.
4. **Asynchronous Background Processing (Future Phase):**
   - For generation of large multi-center PDF dossiers or historical CSV exports, FastAPI's `BackgroundTasks` or a Celery/Redis queue can be introduced without disrupting synchronous APIs.
