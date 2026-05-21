from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class QuestionOptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False
    order_index: int = 0


class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = "mcq"
    marks: int = 1
    order_index: int = 0
    options: List[QuestionOptionCreate] = []


class QuizCreate(BaseModel):
    school_id: int
    classroom_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    duration_minutes: int = 30
    total_marks: int = 100
    pass_marks: int = 40
    scheduled_at: Optional[datetime] = None
    is_ai_generated: bool = False
    questions: List[QuestionCreate] = []


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class QuestionOptionResponse(BaseModel):
    id: int
    option_text: str
    order_index: int

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: str
    marks: int
    order_index: int
    options: List[QuestionOptionResponse] = []

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: int
    school_id: int
    classroom_id: Optional[int]
    title: str
    description: Optional[str]
    duration_minutes: int
    total_marks: int
    pass_marks: int
    is_active: bool
    is_ai_generated: bool
    scheduled_at: Optional[datetime]

    class Config:
        from_attributes = True
