# QuizerAI — Backend Architecture

> **Repo**: `quizerai-backend` | Runtime: Python 3.12 | Framework: FastAPI (async)

---

## Complete Folder Structure

```
quizerai-backend/
│
├── app/
│   │
│   ├── core/                            # App-wide config, security, DI
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic Settings — reads .env
│   │   ├── security.py                  # bcrypt hash, JWT RS256 sign/verify
│   │   ├── dependencies.py              # FastAPI Depends() — db, current_user, role guards
│   │   └── exceptions.py               # Custom HTTP exceptions + global handlers
│   │
│   ├── database/                        # Async SQLAlchemy setup
│   │   ├── __init__.py
│   │   ├── connection.py               # AsyncEngine, AsyncSession factory, get_db()
│   │   ├── base.py                     # DeclarativeBase + TimestampMixin
│   │   └── migrations/                 # Alembic env + versions
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── middleware.py               # Request ID, school_id inject, RBAC, rate limit check, logging
│   │
│   ├── models/                          # SQLAlchemy ORM models (one file per domain)
│   │   ├── __init__.py
│   │   ├── global_admin.py
│   │   ├── institution.py
│   │   ├── school_admin.py
│   │   ├── teacher.py
│   │   ├── student.py
│   │   ├── classroom.py
│   │   ├── classroom_member.py
│   │   ├── subject.py
│   │   ├── quiz.py
│   │   ├── quiz_question.py
│   │   ├── quiz_attempt.py
│   │   ├── assignment.py
│   │   ├── assignment_submission.py
│   │   ├── notification.py
│   │   └── ai_session.py               # AI Tutor session history (last 5 lessons)
│   │
│   ├── schemas/                         # Pydantic v2 request/response models
│   │   ├── __init__.py
│   │   ├── common.py                   # PaginatedResponse, MessageResponse, etc.
│   │   ├── auth.py
│   │   ├── institution.py
│   │   ├── school_admin.py
│   │   ├── teacher.py
│   │   ├── student.py
│   │   ├── classroom.py
│   │   ├── subject.py
│   │   ├── quiz.py
│   │   ├── assignment.py
│   │   └── ai.py
│   │
│   ├── routers/                         # FastAPI APIRouter — thin handlers only
│   │   ├── __init__.py
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── global_admin_auth.py    # POST /auth/admin/login, /refresh, /logout
│   │   │   └── school_auth.py          # POST /auth/school/login (admin/teacher/student)
│   │   │
│   │   ├── admin/                       # Global Admin — sees all institutions
│   │   │   ├── __init__.py
│   │   │   ├── institutions.py         # CRUD institutions
│   │   │   ├── users.py                # Cross-institution user management
│   │   │   └── analytics.py            # Platform-wide stats
│   │   │
│   │   ├── school/                      # School-scoped — school_id from JWT
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py            # School dashboard stats
│   │   │   ├── school_admin.py         # School admin profile/settings
│   │   │   ├── teachers.py             # Teacher CRUD
│   │   │   ├── students.py             # Student CRUD
│   │   │   │
│   │   │   ├── classroom/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── classrooms.py       # Classroom CRUD
│   │   │   │   └── members.py          # Enroll / remove students & teachers
│   │   │   │
│   │   │   ├── learn/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── subjects.py         # Subject CRUD
│   │   │   │   └── content.py          # Learning content upload / list
│   │   │   │
│   │   │   └── quizes/
│   │   │       ├── __init__.py
│   │   │       ├── quiz.py             # Quiz CRUD + assign to classroom
│   │   │       ├── attempt.py          # Student quiz attempt + submit
│   │   │       └── assignment.py       # Assignment create / submit / grade
│   │   │
│   │   ├── ai/                          # AI feature endpoints
│   │   │   ├── __init__.py
│   │   │   ├── tutor.py                # AI Tutor chat (SSE streaming)
│   │   │   ├── quiz_gen.py             # Trigger AI quiz generation (Celery task)
│   │   │   ├── summarize.py            # Summarize document/lesson
│   │   │   └── assignment_eval.py      # Evaluate submitted assignment
│   │   │
│   │   └── system/
│   │       ├── __init__.py
│   │       ├── health.py               # GET /health, /ready, /metrics
│   │       └── notifications.py        # Notification list / mark read
│   │
│   ├── services/                        # Business logic — zero FastAPI imports
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── institution_service.py
│   │   │   └── global_user_service.py
│   │   ├── school/
│   │   │   ├── teacher_service.py
│   │   │   ├── student_service.py
│   │   │   ├── classroom_service.py
│   │   │   ├── subject_service.py
│   │   │   └── quiz_service.py
│   │   ├── ai/
│   │   │   ├── tutor_service.py
│   │   │   ├── quiz_gen_service.py
│   │   │   ├── summarize_service.py
│   │   │   └── assignment_eval_service.py
│   │   └── notification/
│   │       └── notification_service.py
│   │
│   ├── tasks/                           # Celery async tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py               # Celery app init + Redis broker config
│   │   ├── quiz_gen_task.py            # Heavy AI quiz generation
│   │   ├── assignment_eval_task.py     # OCR + AI evaluation pipeline
│   │   ├── summarize_task.py           # Document summarization pipeline
│   │   └── notification_task.py        # Email / push notification dispatch
│   │
│   ├── cache/                           # Redis cache layer
│   │   ├── __init__.py
│   │   ├── redis_client.py             # Async Redis client (aioredis)
│   │   ├── keys.py                     # Centralized Redis key constants
│   │   └── decorators.py              # @cache_response, @invalidate_cache
│   │
│   └── utils/
│       ├── __init__.py
│       ├── s3.py                       # S3 upload / signed URL / delete
│       ├── ocr.py                      # AWS Textract async wrapper
│       ├── rag.py                      # Pinecone query helpers
│       ├── pagination.py               # Cursor-based pagination util
│       └── logger.py                   # Structlog config — JSON output
│
├── tests/
│   ├── conftest.py                     # pytest-asyncio fixtures, test DB, test client
│   ├── unit/
│   │   └── services/                   # Pure service unit tests
│   └── integration/
│       ├── auth/
│       ├── admin/
│       ├── school/
│       └── ai/
│
├── main.py                             # FastAPI app factory, router include, middleware attach
├── alembic.ini
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml                  # Local: app + MySQL + Redis + Celery worker
└── .github/
    └── workflows/
        ├── ci.yml                      # Test + lint on PR
        └── deploy.yml                  # Build + push Docker → K8s deploy on main merge
```

---

## `main.py` — App Factory Pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.middleware import (
    RequestIDMiddleware,
    SchoolContextMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware,
)
from app.core.exceptions import register_exception_handlers
from app.database.connection import init_db
from app.cache.redis_client import init_redis
from app.routers.auth import global_admin_auth, school_auth
from app.routers.admin import institutions, users, analytics
from app.routers.school import (
    dashboard, teachers, students,
    classroom, learn, quizes
)
from app.routers.ai import tutor, quiz_gen, summarize, assignment_eval
from app.routers.system import health, notifications

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    yield
    # cleanup on shutdown

def create_app() -> FastAPI:
    app = FastAPI(
        title="QuizerAI API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Middleware — ORDER MATTERS (bottom registered = first executed)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SchoolContextMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    register_exception_handlers(app)

    PREFIX = "/api/v1"

    # Auth
    app.include_router(global_admin_auth.router, prefix=f"{PREFIX}/auth/admin", tags=["Auth"])
    app.include_router(school_auth.router,       prefix=f"{PREFIX}/auth/school", tags=["Auth"])

    # Global Admin
    app.include_router(institutions.router, prefix=f"{PREFIX}/admin/institutions", tags=["Admin"])
    app.include_router(users.router,        prefix=f"{PREFIX}/admin/users",        tags=["Admin"])
    app.include_router(analytics.router,    prefix=f"{PREFIX}/admin/analytics",    tags=["Admin"])

    # School-scoped
    app.include_router(dashboard.router,  prefix=f"{PREFIX}/school",             tags=["School"])
    app.include_router(teachers.router,   prefix=f"{PREFIX}/school/teachers",    tags=["School"])
    app.include_router(students.router,   prefix=f"{PREFIX}/school/students",    tags=["School"])
    app.include_router(classroom.router,  prefix=f"{PREFIX}/school/classroom",   tags=["Classroom"])
    app.include_router(learn.router,      prefix=f"{PREFIX}/school/learn",       tags=["Learn"])
    app.include_router(quizes.router,     prefix=f"{PREFIX}/school/quizes",      tags=["Quizes"])

    # AI
    app.include_router(tutor.router,           prefix=f"{PREFIX}/ai/tutor",      tags=["AI"])
    app.include_router(quiz_gen.router,        prefix=f"{PREFIX}/ai/quiz-gen",   tags=["AI"])
    app.include_router(summarize.router,       prefix=f"{PREFIX}/ai/summarize",  tags=["AI"])
    app.include_router(assignment_eval.router, prefix=f"{PREFIX}/ai/assignment", tags=["AI"])

    # System
    app.include_router(health.router,        prefix=f"{PREFIX}/system",          tags=["System"])
    app.include_router(notifications.router, prefix=f"{PREFIX}/notifications",   tags=["Notifications"])

    return app

app = create_app()
```

---

## `app/database/connection.py` — Production Async DB

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,                 # mysql+asyncmy://...
    pool_size=20,                          # base connection pool
    max_overflow=40,                       # burst connections
    pool_timeout=30,
    pool_recycle=1800,                     # recycle connections every 30min
    pool_pre_ping=True,                    # detect stale connections
    echo=settings.APP_ENV == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## `app/core/config.py` — All Environment Variables

```python
from pydantic_settings import BaseSettings
from typing import list

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    WORKERS: int = 4                          # Gunicorn/Uvicorn workers
    CORS_ORIGINS: list[str] = ["*"]

    # JWT — RS256 asymmetric
    JWT_PRIVATE_KEY: str                      # RSA private key (PEM)
    JWT_PUBLIC_KEY: str                       # RSA public key (PEM)
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str                         # mysql+asyncmy://user:pass@host:3306/quizerai
    DATABASE_READ_REPLICA_URL: str = ""       # Read replica for analytics

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300               # 5 min default cache TTL

    # Celery
    CELERY_BROKER_URL: str                   # Redis or RabbitMQ
    CELERY_RESULT_BACKEND: str

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str

    # AI
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # Vector DB (RAG)
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "quizerai-pyq"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AI_PER_MINUTE: int = 10       # Stricter for AI endpoints

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Request Lifecycle (Production)

```
Client
  │
  ▼
AWS API Gateway / Kong
  │  DDoS protection, SSL termination, global rate limit
  ▼
Kubernetes Ingress (nginx)
  │
  ▼
FastAPI Pod (HPA: 2–50 replicas based on CPU/RPS)
  │
  ├─ RequestIDMiddleware     → inject x-request-id header
  ├─ LoggingMiddleware       → log request start (request_id, path, method)
  ├─ RateLimitMiddleware     → check Redis sliding window counter
  ├─ SchoolContextMiddleware → decode JWT → attach user + school_id to request.state
  │
  ▼
Router Handler (thin)
  │  Pydantic validation → 422 auto
  │  Depends(get_db) → async session from pool
  │  Depends(get_current_user) → user from request.state
  │
  ▼
Service Layer (pure business logic)
  │
  ├─ MySQL (async, primary for writes)
  ├─ MySQL Read Replica (analytics/reporting)
  ├─ Redis (cache hit? return early)
  └─ Celery task dispatch (for AI jobs → async)
  │
  ▼
Response (Pydantic serialized JSON)
  │
  ├─ LoggingMiddleware → log request end (duration_ms, status_code)
  └─ Client
```

---

## Scalability Architecture

```
                    ┌──────────────────────────────┐
                    │     AWS API Gateway / Kong    │
                    │  Rate limit, Auth, SSL, WAF   │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │     Kubernetes Cluster        │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │  FastAPI Pods (HPA)      │  │
                    │  │  Min: 2 / Max: 50        │  │
                    │  │  Scale on: CPU > 60%     │  │
                    │  │           RPS > 500/pod  │  │
                    │  └────────────┬────────────┘  │
                    │               │               │
                    │  ┌────────────▼────────────┐  │
                    │  │  Celery Workers (HPA)   │  │
                    │  │  Scale on: queue depth  │  │
                    │  └────────────┬────────────┘  │
                    └───────────────┼───────────────┘
                                    │
          ┌─────────────────────────┼──────────────────────┐
          │                         │                       │
   ┌──────▼──────┐        ┌─────────▼──────┐    ┌─────────▼───────┐
   │  MySQL 8    │        │  Redis Cluster │    │  Pinecone / S3  │
   │  Primary +  │        │  Cache + Queue │    │  Vector + Files │
   │  2 Replicas │        │  + Rate Limit  │    │                 │
   └─────────────┘        └────────────────┘    └─────────────────┘
```
