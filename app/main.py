from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import RequestLoggingMiddleware

# Register all models with SQLAlchemy before create_all
import app.models.users          # noqa: F401
import app.models.institution    # noqa: F401
import app.models.classroom      # noqa: F401
import app.models.quiz           # noqa: F401
import app.models.assignment     # noqa: F401
import app.models.ai_session     # noqa: F401
import app.models.notification   # noqa: F401

from app.models.users import GlobalAdmin

# Routes
from app.api.routes import auth as auth_router
from app.api.routes.admin import admins as admin_router
from app.api.routes.school import school as school_router
from app.api.routes.teacher import teacher as teacher_router
from app.api.routes.student import student as student_router
from app.api.routes import quiz as quiz_router
from app.api.routes import assignment as assignment_router
from app.api.routes.ai import ai as ai_router
from app.api.routes import notifications as notifications_router

configure_logging(debug=settings.DEBUG)
Base.metadata.create_all(bind=engine)


def seed_global_admin() -> None:
    db = SessionLocal()
    try:
        exists = db.query(GlobalAdmin).filter(GlobalAdmin.email == "quizerai2707@gmail.com").first()
        if not exists:
            admin = GlobalAdmin(
                email="quizerai2707@gmail.com",
                full_name="QuizerAI Admin",
                hashed_password=hash_password("quizerai12"),
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            db.commit()
            print("[seed] Global admin created: quizerai2707@gmail.com")
        else:
            print("[seed] Global admin already exists — skipping.")
    finally:
        db.close()


seed_global_admin()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)

app.include_router(auth_router.router,          prefix="/api/v1/auth",          tags=["Auth"])
app.include_router(admin_router.router,         prefix="/api/v1/admin",         tags=["Admin"])
app.include_router(school_router.router,        prefix="/api/v1/school",        tags=["School"])
app.include_router(teacher_router.router,       prefix="/api/v1/teacher",       tags=["Teacher"])
app.include_router(student_router.router,       prefix="/api/v1/student",       tags=["Student"])
app.include_router(quiz_router.router,          prefix="/api/v1/quiz",          tags=["Quiz"])
app.include_router(assignment_router.router,    prefix="/api/v1/assignment",    tags=["Assignment"])
app.include_router(ai_router.router,            prefix="/api/v1/ai",            tags=["AI"])
app.include_router(notifications_router.router, prefix="/api/v1/notifications", tags=["Notifications"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
