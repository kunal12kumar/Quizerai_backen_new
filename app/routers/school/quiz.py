from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_teacher
from app.schemas.school.quiz import QuizCreate, QuizResponse, QuizUpdate
from app.services.school.quiz_service import QuizService

router = APIRouter()


@router.post("/", response_model=QuizResponse)
def create_quiz(
    payload: QuizCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_teacher),
):
    return QuizService.create_quiz(db, payload, current_user["user_id"])


@router.get("/school/{school_id}", response_model=List[QuizResponse])
def list_quizzes(
    school_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return QuizService.list_by_school(db, school_id)


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return QuizService.get_quiz(db, quiz_id)


@router.patch("/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: int,
    payload: QuizUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_teacher),
):
    return QuizService.update_quiz(db, quiz_id, payload)


@router.delete("/{quiz_id}", status_code=204)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_teacher),
):
    QuizService.delete_quiz(db, quiz_id)


@router.post("/{quiz_id}/attempt")
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return QuizService.start_attempt(db, quiz_id, current_user["user_id"])


@router.post("/{quiz_id}/attempt/submit")
def submit_quiz_attempt(
    quiz_id: int,
    answers: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return QuizService.submit_attempt(db, quiz_id, current_user["user_id"], answers)
