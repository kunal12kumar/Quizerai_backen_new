from sqlalchemy import Boolean, Column, String, Text

from app.database.base import Base, TimestampMixin


class School(Base, TimestampMixin):
    __tablename__ = "schools"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
