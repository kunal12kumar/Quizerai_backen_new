from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.database.base import Base, TimestampMixin


class Classroom(Base, TimestampMixin):
    __tablename__ = "classrooms"

    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    section = Column(String(20), nullable=True)
    grade = Column(String(20), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
