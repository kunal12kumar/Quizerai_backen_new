from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_teacher
from app.services.ai.ai_service import AIService

router = APIRouter()


@router.post("/quiz/generate")
def generate_quiz(
    topic: str,
    num_questions: int = 10,
    difficulty: str = "medium",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_teacher),
):
    return AIService.generate_quiz(topic, num_questions, difficulty, current_user["user_id"])


@router.post("/quiz/evaluate")
def evaluate_quiz_answer(
    question: str,
    answer: str,
    current_user: dict = Depends(require_teacher),
):
    return AIService.evaluate_answer(question, answer)


@router.post("/content/summarize")
def summarize_content(
    content: str,
    current_user: dict = Depends(require_teacher),
):
    return AIService.summarize_content(content)
