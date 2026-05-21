from typing import Optional
from pydantic import BaseModel, EmailStr


class SchoolCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class SchoolResponse(BaseModel):
    id: int
    name: str
    code: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
