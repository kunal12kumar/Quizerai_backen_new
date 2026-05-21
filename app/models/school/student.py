from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String

from app.database.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    roll_number = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
