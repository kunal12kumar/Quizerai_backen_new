from sqlalchemy import Boolean, Column, String

from app.database.base import Base, TimestampMixin


class GlobalAdmin(Base, TimestampMixin):
    """Global admin — has visibility and control over everything in the platform."""

    __tablename__ = "global_admins"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
