from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import hash_password
from app.database.connection import engine, SessionLocal
from app.database.base import Base
from app.middleware.middleware import register_middleware

# Import all models so SQLAlchemy registers them before create_all
import app.models.admin.admin          # noqa: F401
import app.models.school.school        # noqa: F401
import app.models.school.admin         # noqa: F401
import app.models.school.teacher       # noqa: F401
import app.models.school.student       # noqa: F401
import app.models.school.classroom     # noqa: F401
import app.models.school.quiz          # noqa: F401

from app.models.admin.admin import GlobalAdmin

# Routers
from app.routers.admin import auth as admin_auth_router
from app.routers.admin import admin as admin_router
from app.routers.school import school as school_router
from app.routers.school import classroom as classroom_router
from app.routers.school import learn as learn_router
from app.routers.school import quiz as quiz_router
from app.routers.ai import ai as ai_router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)

app.include_router(admin_auth_router.router, prefix="/api/v1/admin/auth",  tags=["Admin Auth"])
app.include_router(admin_router.router,      prefix="/api/v1/admin",       tags=["Admin"])
app.include_router(school_router.router,     prefix="/api/v1/school",      tags=["School"])
app.include_router(classroom_router.router,  prefix="/api/v1/school/classroom", tags=["Classroom"])
app.include_router(learn_router.router,      prefix="/api/v1/school/learn", tags=["Learn"])
app.include_router(quiz_router.router,       prefix="/api/v1/school/quiz",  tags=["Quiz"])
app.include_router(ai_router.router,         prefix="/api/v1/ai",           tags=["AI Services"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
