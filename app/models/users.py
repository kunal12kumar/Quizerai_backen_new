from sqlalchemy import Boolean, Column, String

from app.database.base import Base, TimestampMixin


class GlobalAdmin(Base, TimestampMixin):
    __tablename__ = "global_admins"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


# TODO: implement SchoolAdmin model
# TODO: implement Teacher model
# TODO: implement Student model
