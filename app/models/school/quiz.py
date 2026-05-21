from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database.base import Base, TimestampMixin


class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30)
    total_marks = Column(Integer, default=100)
    pass_marks = Column(Integer, default=40)
    scheduled_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_ai_generated = Column(Boolean, default=False)


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="mcq")  # mcq, true_false, short_answer
    marks = Column(Integer, default=1)
    order_index = Column(Integer, default=0)


class QuestionOption(Base, TimestampMixin):
    __tablename__ = "question_options"

    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)


class QuizAttempt(Base, TimestampMixin):
    __tablename__ = "quiz_attempts"

    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    score = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
