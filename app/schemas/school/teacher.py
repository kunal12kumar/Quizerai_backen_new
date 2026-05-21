from typing import Optional
from pydantic import BaseModel, EmailStr


class TeacherCreate(BaseModel):
    school_id: int
    email: EmailStr
    full_name: str
    password: str
    subject: Optional[str] = None
    phone: Optional[str] = None


class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    subject: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherResponse(BaseModel):
    id: int
    school_id: int
    email: str
    full_name: str
    subject: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
