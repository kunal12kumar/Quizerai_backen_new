# QuizerAI — Middleware & Security

> **File**: `app/middleware/middleware.py`
> Middleware runs on EVERY request. Keep it lean — no DB calls inside middleware.

---

## Middleware Stack (Execution Order)

Middleware is executed in **reverse registration order** (bottom-up in `main.py`):

```
Incoming Request
       │
       ▼
1. RequestIDMiddleware       → inject X-Request-ID header
       │
       ▼
2. SchoolContextMiddleware   → decode JWT, attach user + school_id to request.state
       │
       ▼
3. RateLimitMiddleware       → check Redis sliding window, reject with 429 if exceeded
       │
       ▼
4. LoggingMiddleware         → log request start (structured JSON)
       │
       ▼
       Route Handler
       │
       ▼ (response bubbles back up)
4. LoggingMiddleware         → log request end (duration_ms, status_code)
       │
       ▼
Outgoing Response
```

---

## Full `middleware.py`

```python
# app/middleware/middleware.py

import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError, RateLimitError
from app.cache.redis_client import redis_client
from app.cache.keys import CacheKey
from app.core.config import settings

logger = structlog.get_logger()

# ── 1. Request ID ─────────────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# ── 2. School Context (JWT decode + tenant inject) ────────────────────────────

# Routes that don't need auth
PUBLIC_PATHS = {
    "/api/v1/auth/admin/login",
    "/api/v1/auth/admin/refresh",
    "/api/v1/auth/school/login",
    "/api/v1/auth/school/refresh",
    "/api/v1/auth/school/forgot-password",
    "/api/v1/auth/school/reset-password",
    "/api/v1/system/health",
    "/api/v1/system/ready",
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
}

class SchoolContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing or invalid Authorization header",
                        "request_id": getattr(request.state, "request_id", ""),
                    }
                },
            )

        token = auth_header.split(" ")[1]

        # Check token blacklist (for logged-out tokens)
        is_blacklisted = await redis_client.get(f"blacklist:{token}")
        if is_blacklisted:
            return JSONResponse(status_code=401, content={"error": {"code": "TOKEN_REVOKED", "message": "Token has been revoked"}})

        payload = decode_token(token)
        if not payload:
            return JSONResponse(status_code=401, content={"error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired"}})

        # Attach to request.state — available in all route handlers
        request.state.user_id    = payload.get("sub")
        request.state.role       = payload.get("role")
        request.state.school_id  = payload.get("school_id")   # None for global admin
        request.state.token      = token

        # RBAC: route prefix vs role
        path = request.url.path
        if path.startswith("/api/v1/admin/") and request.state.role != "global_admin":
            return JSONResponse(status_code=403, content={"error": {"code": "FORBIDDEN", "message": "Global admin access required"}})

        if path.startswith("/api/v1/school/") and request.state.role not in ("school_admin", "teacher", "student"):
            return JSONResponse(status_code=403, content={"error": {"code": "FORBIDDEN", "message": "School role required"}})

        return await call_next(request)

# ── 3. Rate Limiting (Redis sliding window) ───────────────────────────────────

AI_PATHS_PREFIX = "/api/v1/ai/"

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return await call_next(request)

        is_ai = request.url.path.startswith(AI_PATHS_PREFIX)
        limit = settings.RATE_LIMIT_AI_PER_MINUTE if is_ai else settings.RATE_LIMIT_PER_MINUTE
        endpoint_tag = "ai" if is_ai else "general"

        key = CacheKey.rate_limit(user_id, endpoint_tag)
        current = await redis_client.get(key)

        if current and int(current) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Limit: {limit}/min",
                        "request_id": getattr(request.state, "request_id", ""),
                    }
                },
                headers={"Retry-After": "60"},
            )

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        await pipe.execute()

        return await call_next(request)

# ── 4. Structured Logging ─────────────────────────────────────────────────────

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        log = logger.bind(
            request_id=getattr(request.state, "request_id", ""),
            method=request.method,
            path=request.url.path,
            user_id=getattr(request.state, "user_id", None),
            school_id=getattr(request.state, "school_id", None),
            role=getattr(request.state, "role", None),
            ip=request.client.host,
        )
        log.info("request_started")

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
```

---

## `app/core/security.py` — JWT + Password

```python
# app/core/security.py

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
import secrets, string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(alphabet) for _ in range(length))

# ── JWT ────────────────────────────────────────────────────────────────────────

def create_access_token(payload: dict) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    data["iat"] = datetime.now(timezone.utc)
    data["type"] = "access"
    return jwt.encode(data, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(payload: dict) -> str:
    data = {"sub": payload["sub"], "role": payload["role"]}
    data["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    data["type"] = "refresh"
    return jwt.encode(data, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None

# ── Access Token Payload by Role ───────────────────────────────────────────────

def build_token_payload(user, role: str, school_id: int | None = None) -> dict:
    return {
        "sub": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": role,
        "school_id": school_id,
    }
```

---

## `app/core/dependencies.py` — FastAPI Depends()

```python
# app/core/dependencies.py

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import AsyncSessionLocal
from app.core.exceptions import UnauthorizedError, ForbiddenError

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_current_user(request: Request) -> dict:
    """Extract user context from request.state (set by SchoolContextMiddleware)."""
    if not hasattr(request.state, "user_id") or not request.state.user_id:
        raise UnauthorizedError("Authentication required")
    return {
        "id": int(request.state.user_id),
        "role": request.state.role,
        "school_id": request.state.school_id,
        "token": request.state.token,
    }

def require_roles(*roles: str):
    """Factory for role-based route guards."""
    def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise ForbiddenError(
                f"Access denied. Required roles: {', '.join(roles)}"
            )
        return current_user
    return _check

# Shorthand guards
require_global_admin  = require_roles("global_admin")
require_school_admin  = require_roles("school_admin", "global_admin")
require_teacher       = require_roles("teacher", "school_admin", "global_admin")
require_student       = require_roles("student")
require_teacher_or_student = require_roles("teacher", "student", "school_admin", "global_admin")
```

---

## Route-Level Role Guard Usage

```python
# app/routers/school/teachers.py

from app.core.dependencies import (
    get_db, get_current_user, require_school_admin, require_teacher
)

router = APIRouter()

@router.get("/")
async def list_teachers(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_school_admin),   # SA or GA only
):
    teachers, total = await teacher_service.list(
        db, school_id=current_user["school_id"], page=page, limit=limit, search=search
    )
    return paginated_response(teachers, total, page, limit)

@router.post("/", status_code=201)
async def create_teacher(
    data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_school_admin),
):
    teacher = await teacher_service.create(db, data, current_user["school_id"])
    return TeacherResponse.model_validate(teacher)
```

---

## Security Checklist for Engineers

Before merging any PR, verify:

- [ ] `school_id` extracted from `current_user["school_id"]` (from JWT) — **never from request body**
- [ ] Every DB query that should be school-scoped has `.where(Model.institution_id == school_id)`
- [ ] Route has correct `Depends(require_*)` guard
- [ ] No sensitive data (passwords, tokens) in response schemas
- [ ] AI endpoints check institution feature flag before calling AI service
- [ ] File uploads validated for type (PDF/image only) and size (max 10MB)
- [ ] New env variables added to `.env.example`
- [ ] Rate limit headers included in 429 responses
