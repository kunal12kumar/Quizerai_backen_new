from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.database.base import Base, TimestampMixin


class Teacher(Base, TimestampMixin):
    __tablename__ = "teachers"

    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
