from typing import Optional
from pydantic import BaseModel


class ClassroomCreate(BaseModel):
    school_id: int
    name: str
    section: Optional[str] = None
    grade: Optional[str] = None
    teacher_id: Optional[int] = None


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    section: Optional[str] = None
    grade: Optional[str] = None
    teacher_id: Optional[int] = None
    is_active: Optional[bool] = None


class ClassroomResponse(BaseModel):
    id: int
    school_id: int
    name: str
    section: Optional[str]
    grade: Optional[str]
    teacher_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True
