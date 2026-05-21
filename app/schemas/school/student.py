from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    school_id: int
    classroom_id: Optional[int] = None
    email: EmailStr
    full_name: str
    password: str
    roll_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None


class StudentUpdate(BaseModel):
    classroom_id: Optional[int] = None
    full_name: Optional[str] = None
    roll_number: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    id: int
    school_id: int
    classroom_id: Optional[int]
    email: str
    full_name: str
    roll_number: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
