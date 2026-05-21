# QuizerAI — Backend

> **FastAPI · SQLAlchemy 2.0 · MySQL 8 · Redis · Celery · JWT RS256 · AWS S3 · OpenAI · Anthropic Claude · Pinecone**

QuizerAI is a **multi-tenant, AI-powered EdTech SaaS** platform. This repository is the **backend API** — a FastAPI async application that powers institution onboarding, user management, quiz engine, AI features, notifications, and analytics.

---

## Table of Contents

1. [What This Repo Does](#1-what-this-repo-does)
2. [Tech Stack](#2-tech-stack)
3. [Multi-Tenancy — The Core Concept](#3-multi-tenancy--the-core-concept)
4. [User Roles](#4-user-roles)
5. [Project Structure](#5-project-structure)
6. [Key Concepts for New Engineers](#6-key-concepts-for-new-engineers)
7. [GitHub Issues — Sprint Breakdown](#7-github-issues--sprint-breakdown)
8. [API Overview](#8-api-overview)
9. [Development Setup](#9-development-setup)
10. [Engineering Rules](#10-engineering-rules)

---

## 1. What This Repo Does

The backend handles:

| Domain | Description |
|--------|-------------|
| **Institution Onboarding** | Schools/colleges register, Global Admin verifies them |
| **Auth (4 Roles)** | JWT RS256 login for GA, School Admin, Teacher, Student |
| **Quiz Engine** | CRUD for quizzes + questions, attempt lifecycle, auto-grading |
| **AI Tutor** | SSE streaming chat with multi-agent routing (GPT-4o / Claude) |
| **AI Quiz Generation** | Celery task — topic → RAG from Pinecone PYQ corpus → OpenAI → quiz |
| **Assignment Evaluation** | S3 upload → Textract OCR → Claude scoring + remarks |
| **Summarization** | Iterative refine pipeline (chunk → summarize → refine → recheck) |
| **Notifications** | In-app + FCM push notifications via Celery |
| **Analytics** | Student performance, teacher dashboards, platform metrics |

---

## 2. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | **FastAPI** (async) | Native async, auto OpenAPI, Pydantic v2 |
| ORM | **SQLAlchemy 2.0** (async) | Type-safe mapped columns, true async sessions |
| Database | **MySQL 8** | ACID, relational, battle-tested SaaS DB |
| Migrations | **Alembic** | Only way to change schema — never raw SQL |
| Cache / Broker | **Redis** | Rate limiting, session cache, Celery broker |
| Task Queue | **Celery** | Async AI jobs, notifications, heavy processing |
| Auth | **JWT RS256** + bcrypt | Asymmetric signing, stateless, distributed verify |
| File Storage | **AWS S3** | Logos, PDFs, assignment uploads |
| OCR | **AWS Textract** | Handwritten assignment extraction |
| AI — Maths | **OpenAI GPT-4o** | Best reasoning for maths |
| AI — Explanation | **Anthropic Claude** | Cost-efficient, high quality text |
| Vector DB | **Pinecone** | PYQ corpus semantic search (RAG) |
| Monitoring | **Prometheus + Grafana** | Metrics and alerting |
| Logging | **Structlog → ELK** | Structured JSON logs, searchable |
| Containers | **Docker + Docker Compose** | Dev parity |
| Orchestration | **Kubernetes (EKS)** | Autoscaling in production |
| CI/CD | **GitHub Actions** | Test → lint → build → deploy |

---

## 3. Multi-Tenancy — The Core Concept

QuizerAI uses a **shared database, shared schema** multi-tenancy model.

```
Global Admin (platform owner)
└── Institution A (e.g. "Delhi Public School")
      ├── School Admin
      ├── Teacher 1, Teacher 2 ...
      ├── Student 1, Student 2 ...
      └── Classrooms, Quizzes, Assignments
└── Institution B (e.g. "Resonance Coaching")
      └── (completely isolated data)
```

**How isolation works:**
- Every scoped table has an `institution_id` (FK to `institutions`)
- The **JWT payload** carries `institution_id` + `role`
- A **middleware** (`SchoolContextMiddleware`) decodes the JWT and injects `institution_id` into `request.state` on every request
- Service layer filters all queries with `WHERE institution_id = :current`
- **`institution_id` never comes from the request body** — always from the JWT

This means a teacher from Institution A can never see Institution B's data, even if they craft a malicious request.

---

## 4. User Roles

| Role | Code | What They Can Do |
|------|------|-----------------|
| **Global Admin** | `GA` | Sees all institutions, verifies/suspends them, manages subscriptions, platform analytics |
| **School Admin** | `SA` | Manages their institution's teachers, students, classrooms, settings |
| **Teacher** | `TE` | Creates/manages quizzes and assignments, views classroom analytics |
| **Student** | `ST` | Attempts quizzes, submits assignments, uses AI Tutor |

Role is embedded in the JWT and enforced by the `require_roles(*roles)` FastAPI dependency.

---

## 5. Project Structure

```
app/
├── main.py                   # App factory: create_app()
├── core/
│   ├── config.py             # Settings (Pydantic BaseSettings, reads .env)
│   ├── security.py           # JWT sign/verify, bcrypt hash/verify
│   ├── exceptions.py         # AppError, global exception handlers
│   └── logging.py            # Structlog configuration
├── database/
│   ├── base.py               # Base(DeclarativeBase) + TimestampMixin
│   └── session.py            # async engine + session factory
├── models/                   # SQLAlchemy ORM models
│   ├── institution.py        # Institution, enums (InstitutionType, etc.)
│   ├── users.py              # GlobalAdmin, SchoolAdmin, Teacher, Student
│   ├── classroom.py          # Classroom, ClassroomMember, Subject
│   ├── quiz.py               # Quiz, QuizQuestion, QuizAttempt, QuizAttemptAnswer
│   ├── assignment.py         # Assignment, AssignmentSubmission
│   ├── ai_session.py         # AISession, AIMessage
│   └── notification.py       # Notification
├── schemas/                  # Pydantic v2 schemas (request/response)
│   └── (mirrors models/)
├── api/
│   ├── dependencies.py       # get_db, get_current_user, require_roles factory
│   └── routes/
│       ├── auth.py           # Login, refresh, logout, forgot/reset password
│       ├── admin/            # Global Admin endpoints
│       ├── school/           # School Admin endpoints
│       ├── teacher/          # Teacher endpoints
│       ├── student/          # Student endpoints
│       ├── quiz.py           # Quiz CRUD + attempt lifecycle
│       ├── assignment.py     # Assignment CRUD + submission
│       ├── ai/               # AI Tutor, Quiz Gen, Summarizer, Assignment Eval
│       └── notifications.py  # Notification endpoints
├── services/                 # Business logic (no logic in routes)
│   ├── admin/
│   ├── school/
│   ├── quiz/
│   ├── ai/
│   ├── email/                # SendGrid / SES abstraction
│   ├── notification/         # FCM push service
│   └── rag/                  # Pinecone client
├── middleware/
│   ├── request_id.py         # Generates X-Request-ID per request
│   ├── school_context.py     # JWT decode → inject institution_id
│   ├── rate_limit.py         # Redis sliding window rate limiter
│   └── logging.py            # Structured request/response logging
├── workers/
│   ├── celery_app.py         # Celery app + beat schedule
│   └── tasks/
│       ├── quiz_tasks.py     # AI grading task
│       ├── ai_tasks.py       # Quiz gen, summarizer, assignment eval
│       ├── notification_tasks.py
│       └── rag_tasks.py      # PYQ ingestion pipeline
├── cache/
│   ├── redis_client.py       # Async Redis singleton
│   └── keys.py               # CacheKey constants
└── utils/
    └── s3.py                 # Presigned URL generation
```

---

## 6. Key Concepts for New Engineers

### 6.1 Request Lifecycle

Every authenticated API request flows through this middleware chain:

```
Client Request
    │
    ▼
RequestIDMiddleware         → generates UUID, sets X-Request-ID header
    │
    ▼
SchoolContextMiddleware     → decodes JWT → request.state.institution_id / role
    │
    ▼
RateLimitMiddleware         → Redis sliding window (100/min default, 10/min auth)
    │
    ▼
LoggingMiddleware           → logs request_id, school_id, user_id, path, duration_ms
    │
    ▼
Route Handler               → calls service (NO business logic in handler)
    │
    ▼
Service Layer               → DB queries (always filtered by institution_id)
    │
    ▼
Response
```

### 6.2 JWT Token Structure

```json
{
  "sub": "42",
  "role": "TEACHER",
  "institution_id": 7,
  "jti": "uuid-for-revocation",
  "exp": 1700000000
}
```

- **Access token**: 15-minute TTL, RS256 signed
- **Refresh token**: 7-day TTL, stored in Redis (`refresh:{jti}`), deleted on logout

### 6.3 Service Pattern

```python
# Route (thin — calls service, returns response)
@router.post("/quiz/", response_model=QuizResponse)
async def create_quiz(
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles("TEACHER")),
):
    return await quiz_service.create(db, data, current_user.institution_id)

# Service (all business logic lives here)
class QuizService:
    async def create(self, db, data, institution_id) -> Quiz:
        quiz = Quiz(**data.model_dump(), institution_id=institution_id)
        db.add(quiz)
        await db.flush()
        return quiz
```

### 6.4 Celery Async Jobs

Long-running AI tasks **never** run in the request cycle. They are dispatched to Celery:

```
POST /ai/quiz-gen/generate  →  returns task_id immediately
                                    │
                                    ▼ (background)
                             Celery Worker:
                             1. Embed topic (OpenAI)
                             2. Query Pinecone (RAG)
                             3. Generate questions (GPT-4o)
                             4. Save draft quiz to DB
                             5. Notify teacher

GET /ai/quiz-gen/status/{task_id}  →  poll until complete
```

### 6.5 AI Tutor SSE Streaming

```
POST /ai/tutor/session          → creates session, returns session_id
GET  /ai/tutor/session/{id}/stream?message=...
     → text/event-stream
     → Agent router classifies intent:
          "solve x^2 + 5x = 0" → MathsSolverAgent (GPT-4o)
          "explain photosynthesis" → ExplanationAgent (Claude)
          "how do I study better?" → MentorAgent (Claude)
     → streams tokens: data: {"token": "x =", "done": false}
     → final: data: {"token": "", "done": true}
```

---

## 7. GitHub Issues — Sprint Breakdown

All 55 backend issues are filed in this repo. Here is what each sprint covers and what to read before picking up a ticket.

### Sprint 1 — Project Foundation (BE-001 to BE-010)

**Goal**: Working skeleton — FastAPI app runs, connects to MySQL and Redis, has CI.

| Issue | Task | Key Files |
|-------|------|-----------|
| BE-001 | FastAPI app factory | `app/main.py`, `app/core/config.py` |
| BE-002 | Docker + Docker Compose | `Dockerfile`, `docker-compose.yml` |
| BE-003 | SQLAlchemy async engine | `app/database/session.py`, `app/database/base.py` |
| BE-004 | Alembic + initial migration | `alembic/`, 16 tables created |
| BE-005 | Redis client + CacheKey | `app/cache/redis_client.py`, `app/cache/keys.py` |
| BE-006 | Celery setup | `app/workers/celery_app.py` |
| BE-007 | GitHub Actions CI | `.github/workflows/ci.yml` |
| BE-008 | Structlog + request_id middleware | `app/middleware/logging.py`, `app/core/logging.py` |
| BE-009 | Global exception handlers | `app/core/exceptions.py` |
| BE-010 | Health check endpoints | `GET /health`, `/health/live`, `/health/ready` |

**Read first**: `docs/01_BACKEND_ARCHITECTURE.md`, `docs/03_DATABASE_SCHEMA.md`

---

### Sprint 2 — Auth & Institution (BE-011 to BE-020, BE-051 to BE-053)

**Goal**: Secure JWT auth for all roles, institution onboarding, RBAC working end-to-end.

| Issue | Task | Key Files |
|-------|------|-----------|
| BE-011 | JWT RS256 sign/verify/refresh | `app/core/security.py` |
| BE-012 | bcrypt password hashing | `app/core/security.py` |
| BE-013 | `require_roles` RBAC dependency | `app/api/dependencies.py` |
| BE-014 | Rate limiting middleware | `app/middleware/rate_limit.py` |
| BE-015 | SchoolContext middleware | `app/middleware/school_context.py` |
| BE-016 | Global Admin model + endpoints | `app/models/users.py`, routes `/admin/auth/` |
| BE-017 | Institution CRUD endpoints | `app/api/routes/admin/institutions.py` |
| BE-018 | School Admin auth + profile | routes `/school/auth/`, `/school/me` |
| BE-019 | Institution settings + feature flags | `app/cache/keys.py` (flag caching) |
| BE-020 | Auth + institution integration tests | `tests/test_auth.py`, `tests/test_institution.py` |
| BE-051 | Password reset (OTP flow) | `app/workers/tasks/notification_tasks.py` |
| BE-052 | Email service abstraction | `app/services/email/` |
| BE-053 | Input sanitisation + security audit | `bandit` CI scan |

**Read first**: `docs/07_MIDDLEWARE_AND_SECURITY.md`, `docs/02_INSTITUTION_MODEL.md`

---

### Sprint 3 — School Core (BE-021 to BE-026)

**Goal**: Teachers, students, classrooms, and subjects fully manageable by School Admin.

| Issue | Task |
|-------|------|
| BE-021 | Teacher model + invitation + CRUD |
| BE-022 | Student model + registration + bulk CSV import |
| BE-023 | Classroom model + teacher/student assignment |
| BE-024 | Subject model + CRUD |
| BE-025 | Student performance summary endpoint |
| BE-026 | Integration tests for school core |

**Read first**: `docs/03_DATABASE_SCHEMA.md` (classrooms, teachers, students tables)

---

### Sprint 4 — Quiz Engine (BE-027 to BE-032)

**Goal**: Full quiz lifecycle — create → publish → attempt → submit → auto-grade.

| Issue | Task |
|-------|------|
| BE-027 | Quiz model + question bank CRUD |
| BE-028 | Quiz attempt lifecycle (start/answer/submit) |
| BE-029 | Celery: AI grading for ONE_LINER and ASSERTION_REASON |
| BE-030 | Quiz analytics endpoints (teacher dashboard) |
| BE-031 | Assignment model + S3 submission endpoints |
| BE-032 | Quiz engine integration tests |

**Read first**: `docs/03_DATABASE_SCHEMA.md` (quiz_attempts, quiz_attempt_answers), `docs/06_SERVICES_LAYER.md`

---

### Sprint 5 — AI Features (BE-033 to BE-040)

**Goal**: AI Tutor (SSE), Quiz Gen (RAG), Summarizer, Assignment Eval all working via Celery.

| Issue | Task |
|-------|------|
| BE-033 | AI Tutor SSE streaming endpoint |
| BE-034 | AI Quiz Generation pipeline (Celery + Pinecone RAG) |
| BE-035 | Summarization iterative refine pipeline |
| BE-036 | Assignment evaluation (Textract OCR + Claude scoring) |
| BE-037 | Pinecone RAG pipeline + PYQ ingestion |
| BE-038 | AI session history + context management |
| BE-039 | Feature flag middleware + per-institution gating |
| BE-040 | AI feature integration tests |

**Read first**: `docs/05_AI_MODEL_ARCHITECTURE.md`

---

### Sprint 6 — Notifications & Analytics (BE-041 to BE-044)

| Issue | Task |
|-------|------|
| BE-041 | Notification model + in-app endpoints |
| BE-042 | FCM push notification integration |
| BE-043 | Celery beat: scheduled notification tasks |
| BE-044 | Platform-wide analytics endpoint (GA) |

---

### Sprint 7 — Production Hardening (BE-045 to BE-050, BE-054, BE-055)

| Issue | Task |
|-------|------|
| BE-045 | Kubernetes manifests + Helm chart |
| BE-046 | Prometheus metrics + Grafana dashboard |
| BE-047 | ELK structured log pipeline |
| BE-048 | Load testing with Locust (10K concurrent users target) |
| BE-049 | AWS S3 presigned URL service |
| BE-050 | API versioning strategy |
| BE-054 | Comprehensive OpenAPI documentation |
| BE-055 | DB connection pool monitoring + slow query logging |

---

## 8. API Overview

All routes are under `/api/v1/`. Full documentation available at `/docs` (Swagger UI) when running locally.

```
/api/v1/
├── auth/
│   ├── POST  /auth/login
│   ├── POST  /auth/refresh
│   ├── POST  /auth/logout
│   ├── POST  /auth/forgot-password
│   ├── POST  /auth/verify-otp
│   └── POST  /auth/reset-password
│
├── admin/               (Global Admin only)
│   ├── GET/POST  /admin/institutions/
│   ├── GET/PATCH /admin/institutions/{id}/
│   ├── PUT       /admin/institutions/{id}/verify
│   ├── PUT       /admin/institutions/{id}/suspend
│   ├── PUT       /admin/institutions/{id}/subscription
│   ├── PUT       /admin/institutions/{id}/feature-flags
│   ├── POST      /admin/rag/ingest
│   └── GET       /admin/analytics/overview
│
├── school/              (School Admin)
│   ├── GET/PATCH /school/institution
│   ├── CRUD      /school/teachers/
│   ├── CRUD      /school/students/
│   ├── POST      /school/students/bulk-import
│   ├── CRUD      /school/classrooms/
│   ├── CRUD      /school/subjects/
│   └── GET       /school/institution/feature-flags
│
├── quiz/                (Teacher + Student)
│   ├── CRUD      /quiz/
│   ├── CRUD      /quiz/{id}/questions
│   ├── POST      /quiz/{id}/publish
│   ├── POST      /quiz/{id}/attempts/start
│   ├── PUT       /quiz/{id}/attempts/{aid}/answers
│   ├── POST      /quiz/{id}/attempts/{aid}/submit
│   ├── GET       /quiz/{id}/attempts/{aid}/result
│   └── GET       /quiz/{id}/analytics
│
├── assignments/         (Teacher + Student)
│   ├── CRUD      /assignments/
│   ├── POST      /assignments/{id}/submit
│   └── GET       /assignments/{id}/submissions
│
├── ai/                  (Students + Teachers, feature-flagged)
│   ├── POST      /ai/tutor/session
│   ├── GET       /ai/tutor/session/{id}/stream   (SSE)
│   ├── POST      /ai/quiz-gen/generate
│   ├── GET       /ai/quiz-gen/status/{task_id}
│   ├── POST      /ai/summarize
│   └── GET       /ai/summarize/{task_id}
│
├── notifications/
│   ├── GET       /notifications/
│   ├── PUT       /notifications/{id}/read
│   ├── PUT       /notifications/read-all
│   └── DELETE    /notifications/{id}
│
└── health/
    ├── GET /health
    ├── GET /health/live
    └── GET /health/ready
```

---

## 9. Development Setup

### Prerequisites
- Python 3.11+
- Docker + Docker Compose
- Make (optional)

### Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/shashankbindal/QuizerAi_backend.git
cd QuizerAi_backend

# 2. Copy environment file
cp .env.example .env
# Edit .env with your DB password, Redis URL, OpenAI key, etc.

# 3. Start all services (MySQL, Redis, Celery worker)
docker-compose up -d db redis celery_worker

# 4. Install dependencies
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Run migrations
alembic upgrade head

# 6. Seed Global Admin
python scripts/seed_superadmin.py

# 7. Start API
uvicorn app.main:app --reload

# API running at: http://localhost:8000
# Swagger UI:     http://localhost:8000/docs
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_auth.py -v
```

### Environment Variables

```env
# Database
DATABASE_URL=mysql+aiomysql://root:password@localhost/quizerai

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (generate with: openssl genrsa -out private.pem 2048)
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=quizerai-uploads
AWS_REGION=ap-south-1

# AI
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=gcp-starter

# Email
EMAIL_PROVIDER=sendgrid  # or ses
SENDGRID_API_KEY=SG....

# Firebase (for push notifications)
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", ...}
```

---

## 10. Engineering Rules

These rules are **non-negotiable**. Every PR is reviewed against them.

1. **`institution_id` always comes from JWT** — never from request body. Prevents tenant data leakage.
2. **No business logic in route handlers** — routes call services only. Services are pure Python, independently testable.
3. **No blocking I/O anywhere** — all DB, Redis, HTTP, S3 calls are `async/await`.
4. **All AI jobs via Celery** — never call AI APIs synchronously in the request/response cycle.
5. **Alembic for every schema change** — never `ALTER TABLE` manually.
6. **Feature flags in Redis** — new AI features are gated per institution; not everyone gets them at once.
7. **Every endpoint has integration tests** — no merge without test coverage.
8. **Structured logging on every request** — log `request_id`, `school_id`, `user_id`, `duration_ms`.

---

## Documentation

All planning and architecture docs are in the [`docs/`](./docs/) folder:

| File | What It Covers |
|------|---------------|
| [ARCHITECTURE_MAP.md](./docs/ARCHITECTURE_MAP.md) | Full system map — read this first as a new engineer |
| [00_PROJECT_OVERVIEW.md](./docs/00_PROJECT_OVERVIEW.md) | Platform overview, tech stack decisions |
| [01_BACKEND_ARCHITECTURE.md](./docs/01_BACKEND_ARCHITECTURE.md) | Folder structure, module breakdown, request lifecycle |
| [02_INSTITUTION_MODEL.md](./docs/02_INSTITUTION_MODEL.md) | Institution ORM model + Pydantic schemas + service |
| [03_DATABASE_SCHEMA.md](./docs/03_DATABASE_SCHEMA.md) | All 16 MySQL tables — DDL + relationships |
| [04_API_ROUTES.md](./docs/04_API_ROUTES.md) | Every API endpoint — method, auth, payload, response |
| [05_AI_MODEL_ARCHITECTURE.md](./docs/05_AI_MODEL_ARCHITECTURE.md) | AI Tutor, Quiz Gen, Summarizer, Assignment Eval pipelines |
| [06_SERVICES_LAYER.md](./docs/06_SERVICES_LAYER.md) | Service structure, Celery tasks, Redis patterns |
| [07_MIDDLEWARE_AND_SECURITY.md](./docs/07_MIDDLEWARE_AND_SECURITY.md) | JWT, RBAC, rate limiting, middleware chain |

---

*QuizerAI Backend — built with FastAPI, scaled for 10,000 concurrent users.*
