# QuizerAI — Project Overview

> **Internal Engineering Reference** | v1.0 | Status: Active Planning
> Pass this doc to every engineer joining the org. Read all linked docs before writing a single line.

---

## What Is QuizerAI?

QuizerAI is a **multi-tenant, AI-powered EdTech SaaS** platform. Educational institutions — schools, coaching institutes, colleges, universities, training centers — onboard as tenants. Each gets their own isolated data scope with a full suite of AI tools for teaching and learning.

---

## Core Product Pillars

| Pillar | What It Does |
|--------|-------------|
| **Institution Management** | Onboarding, school admin panel, multi-role access control |
| **AI Quiz Generation** | LLM-generated MCQ / Assertion-Reason / One Word / One Liner across Easy / Medium / Hard, RAG-backed from PYQ corpora |
| **AI Tutor** | Agentic chatbot — Maths solver, Explanation, Mentor, Roadmap, System Q&A agents |
| **Assignment Evaluation** | OCR submission intake → AI scoring with remarks + improvement feedback |
| **Summarization** | Document/lesson summarize with iterative refine-recheck pipeline |
| **Student Analytics** | Performance tracking wired into every AI interaction |

---

## Tech Stack — Non-Negotiable Decisions

### Backend
| Layer | Choice | Why |
|-------|--------|-----|
| Framework | **FastAPI** (async) | Native async, auto OpenAPI, Pydantic v2 |
| ORM | **SQLAlchemy 2.0** (async) | True async sessions, type-safe mapped columns |
| DB | **MySQL 8** | Relational, ACID, battle-tested for SaaS |
| Migrations | **Alembic** | Only way to touch schema |
| Cache / Queue Broker | **Redis** | Rate limiting, session cache, Celery broker |
| Task Queue | **Celery** | Async AI jobs, notifications, heavy processing |
| Auth | **JWT (RS256)** + bcrypt | Stateless, asymmetric signing for distributed verify |
| File Storage | **AWS S3** | Logos, PDFs, assignment uploads |
| OCR | **AWS Textract** | Handwritten assignment extraction |
| AI — Maths | **OpenAI GPT-4o** | Best reasoning for maths |
| AI — Explanation | **Anthropic Claude** | Cost-efficient, high quality |
| AI — Voice | Custom Whisper model | STT for AI tutor voice input |
| Vector DB / RAG | **Pinecone** (or Weaviate) | PYQ corpora semantic search |
| Monitoring | **Prometheus + Grafana** | Metrics, alerting |
| Logging | **Structlog → ELK** | Structured JSON logs, searchable |
| Containerization | **Docker + Docker Compose** | Dev parity |
| Orchestration | **Kubernetes (EKS/GKE)** | Autoscaling in prod |
| CI/CD | **GitHub Actions** | Test → lint → build → deploy |
| API Gateway | **AWS API Gateway / Kong** | Rate limiting, DDoS protection at edge |

### Scalability Targets
- **10K concurrent users** without degradation
- **Horizontal pod autoscaling** (HPA) on Kubernetes — scale FastAPI workers on CPU/RPS
- **Celery workers** scale independently on queue depth
- **Read replicas** on MySQL for analytics/reporting queries
- **Redis Cluster** for cache HA

---

## Multi-Tenancy Architecture

```
Global Admin (SuperAdmin)
│  sees ALL institutions, ALL data, platform analytics
│
└── Institution (School / College / Coaching / University / Training Center)
      │  isolated by school_id FK on every table
      │
      ├── School Admin        manages their institution only
      ├── Teacher             manages classrooms, assigns quizzes, views student analytics
      ├── Student             attempts quizzes, submits assignments, uses AI Tutor
      └── Classroom           grouping entity — links Teacher ↔ Students ↔ Subject
```

**Tenant isolation strategy**: Shared database, shared schema, `school_id` FK on every scoped table. Middleware injects and validates `school_id` from JWT on every request. No cross-tenant data leakage possible without a compromised JWT.

---

## Repository Layout (GitHub Org: `quizerai-org`)

```
quizerai-org/
├── quizerai-backend/          ← FastAPI — this is the main focus
├── quizerai-frontend/         ← React / Next.js (separate team)
├── quizerai-ai-workers/       ← Celery workers for heavy AI jobs
├── quizerai-rag-pipeline/     ← PYQ ingestion, chunking, embedding, Pinecone upsert
├── quizerai-infra/            ← Terraform, Helm charts, K8s manifests
└── quizerai-docs/             ← THIS repo — all planning & architecture docs
```

---

## Key Engineering Rules (Read Before Coding)

1. **`school_id` always comes from JWT** — never from request body. Prevents tenant leakage.
2. **No business logic in route handlers** — routes call services only. Services are testable pure Python.
3. **No blocking I/O anywhere** — all DB, Redis, HTTP, S3 calls are `async/await`.
4. **All AI jobs via Celery** — never call AI APIs in the request/response cycle for long jobs.
5. **Alembic for every schema change** — never `ALTER TABLE` manually.
6. **Feature flags in Redis** — new AI features go behind a flag, enabled per institution.
7. **Every endpoint has integration tests** — pytest-asyncio + TestClient. No merge without tests.
8. **Structured logging on every request** — log `request_id`, `school_id`, `user_id`, `duration_ms`.

---

## Related Documents

| Doc | What It Covers |
|-----|---------------|
| [`01_BACKEND_ARCHITECTURE.md`](./01_BACKEND_ARCHITECTURE.md) | Full folder structure, module breakdown, request lifecycle |
| [`02_INSTITUTION_MODEL.md`](./02_INSTITUTION_MODEL.md) | Institution ORM model + Pydantic schemas |
| [`03_DATABASE_SCHEMA.md`](./03_DATABASE_SCHEMA.md) | All MySQL tables — DDL + relationships |
| [`04_API_ROUTES.md`](./04_API_ROUTES.md) | Every API endpoint — method, auth, payload, response |
| [`05_AI_MODEL_ARCHITECTURE.md`](./05_AI_MODEL_ARCHITECTURE.md) | AI Tutor, Quiz Gen, Assignment Eval, Summarizer pipelines |
| [`06_SERVICES_LAYER.md`](./06_SERVICES_LAYER.md) | Services structure, Celery tasks, Redis patterns |
| [`07_MIDDLEWARE_AND_SECURITY.md`](./07_MIDDLEWARE_AND_SECURITY.md) | JWT, RBAC, rate limiting, middleware chain |
| [`08_GITHUB_ISSUES.md`](./08_GITHUB_ISSUES.md) | Sprint-ready GitHub issues — copy-paste into GitHub |
