from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.school.quiz import Question, QuestionOption, Quiz, QuizAttempt
from app.schemas.school.quiz import QuizCreate, QuizUpdate


class QuizService:

    @staticmethod
    def create_quiz(db: Session, payload: QuizCreate, teacher_id: int) -> Quiz:
        questions = payload.questions
        quiz_data = payload.model_dump(exclude={"questions"})
        quiz = Quiz(**quiz_data, created_by=teacher_id)
        db.add(quiz)
        db.flush()

        for q_data in questions:
            options = q_data.options
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data.question_text,
                question_type=q_data.question_type,
                marks=q_data.marks,
                order_index=q_data.order_index,
            )
            db.add(question)
            db.flush()
            for opt in options:
                db.add(QuestionOption(question_id=question.id, **opt.model_dump()))

        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def list_by_school(db: Session, school_id: int) -> list:
        return db.query(Quiz).filter(Quiz.school_id == school_id).all()

    @staticmethod
    def get_quiz(db: Session, quiz_id: int) -> Quiz:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return quiz

    @staticmethod
    def update_quiz(db: Session, quiz_id: int, payload: QuizUpdate) -> Quiz:
        quiz = QuizService.get_quiz(db, quiz_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(quiz, field, value)
        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def delete_quiz(db: Session, quiz_id: int) -> None:
        quiz = QuizService.get_quiz(db, quiz_id)
        db.delete(quiz)
        db.commit()

    @staticmethod
    def start_attempt(db: Session, quiz_id: int, student_id: int) -> QuizAttempt:
        from datetime import datetime, timezone
        quiz = QuizService.get_quiz(db, quiz_id)
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            student_id=student_id,
            started_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def submit_attempt(db: Session, quiz_id: int, student_id: int, answers: dict) -> dict:
        from datetime import datetime, timezone
        attempt = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.student_id == student_id, QuizAttempt.is_completed == False)
            .first()
        )
        if not attempt:
            raise HTTPException(status_code=404, detail="No active attempt found")

        # TODO: implement answer evaluation logic
        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.is_completed = True
        db.commit()
        return {"message": "Quiz submitted", "attempt_id": attempt.id}
