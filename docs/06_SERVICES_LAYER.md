# QuizerAI — Services Layer

> Services = pure business logic. Zero FastAPI imports. Fully testable Python classes.
> Each service receives `(db: AsyncSession, ...)` and returns domain objects or raises exceptions.

---

## Services Directory Structure

```
app/services/
├── admin/
│   ├── institution_service.py      # CRUD institutions, verify, suspend
│   └── global_user_service.py      # Manage global admins
├── school/
│   ├── teacher_service.py          # Teacher CRUD, bulk import
│   ├── student_service.py          # Student CRUD, bulk import, performance
│   ├── classroom_service.py        # Classroom CRUD, enroll members
│   ├── subject_service.py          # Subject CRUD
│   └── quiz_service.py             # Quiz CRUD, attempt, grading
├── ai/
│   ├── tutor_service.py            # AI Tutor streaming, session management
│   ├── quiz_gen_service.py         # Quiz gen job dispatch + result retrieval
│   ├── summarize_service.py        # Summarization job dispatch
│   └── assignment_eval_service.py  # Assignment eval job dispatch
└── notification/
    └── notification_service.py     # Create, send, list notifications
```

---

## Service Pattern — Standard Template

Every service follows this pattern:

```python
# app/services/school/teacher_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.core.security import hash_password, generate_temp_password
from app.core.exceptions import NotFoundError, ConflictError
from app.cache.redis_client import redis_client
from app.cache.keys import CacheKey
from app.tasks.notification_task import send_welcome_email_task
import csv, io

class TeacherService:

    async def create(
        self,
        db: AsyncSession,
        data: TeacherCreate,
        school_id: int,
    ) -> Teacher:
        # Check duplicate email
        existing = await db.execute(
            select(Teacher).where(Teacher.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email {data.email} already registered")

        temp_password = generate_temp_password()
        teacher = Teacher(
            **data.model_dump(),
            institution_id=school_id,
            password_hash=hash_password(temp_password),
        )
        db.add(teacher)
        await db.flush()

        # Dispatch welcome email (async, non-blocking)
        send_welcome_email_task.delay(
            to=teacher.email,
            name=teacher.name,
            temp_password=temp_password,
            role="teacher",
        )

        # Invalidate school teacher list cache
        await redis_client.delete(CacheKey.teacher_list(school_id))
        return teacher

    async def get_by_id(
        self, db: AsyncSession, teacher_id: int, school_id: int
    ) -> Teacher:
        result = await db.execute(
            select(Teacher).where(
                Teacher.id == teacher_id,
                Teacher.institution_id == school_id,   # tenant scope ALWAYS
            )
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise NotFoundError(f"Teacher {teacher_id} not found")
        return teacher

    async def list(
        self,
        db: AsyncSession,
        school_id: int,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Teacher], int]:
        query = select(Teacher).where(Teacher.institution_id == school_id)

        if search:
            query = query.where(
                Teacher.name.ilike(f"%{search}%") |
                Teacher.email.ilike(f"%{search}%")
            )
        if is_active is not None:
            query = query.where(Teacher.is_active == is_active)

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()

        query = query.offset((page - 1) * limit).limit(limit).order_by(Teacher.name)
        result = await db.execute(query)
        return result.scalars().all(), total

    async def update(
        self, db: AsyncSession, teacher_id: int, school_id: int, data: TeacherUpdate
    ) -> Teacher:
        teacher = await self.get_by_id(db, teacher_id, school_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(teacher, field, value)
        await redis_client.delete(CacheKey.teacher(teacher_id))
        return teacher

    async def deactivate(
        self, db: AsyncSession, teacher_id: int, school_id: int
    ) -> Teacher:
        teacher = await self.get_by_id(db, teacher_id, school_id)
        teacher.is_active = False
        await redis_client.delete(CacheKey.teacher(teacher_id))
        return teacher

    async def bulk_import(
        self,
        db: AsyncSession,
        school_id: int,
        csv_content: bytes,
    ) -> dict:
        """Parse CSV and bulk-create teachers. Returns {created, skipped, errors}."""
        reader = csv.DictReader(io.StringIO(csv_content.decode()))
        created, skipped, errors = 0, 0, []

        required = {"name", "email", "mobile_number"}
        for i, row in enumerate(reader, start=2):
            if not required.issubset(row.keys()):
                errors.append(f"Row {i}: Missing columns {required - set(row.keys())}")
                continue
            try:
                await self.create(
                    db,
                    TeacherCreate(**{k: v for k, v in row.items() if v}),
                    school_id,
                )
                created += 1
            except ConflictError:
                skipped += 1
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        return {"created": created, "skipped": skipped, "errors": errors}
```

---

## Quiz Service (Most Complex)

```python
# app/services/school/quiz_service.py — key methods only

class QuizService:

    async def start_attempt(
        self, db: AsyncSession, quiz_id: int, student_id: int, school_id: int
    ) -> dict:
        """Start a quiz attempt. Returns quiz with questions (shuffled, no correct answers)."""
        quiz = await self._get_published_quiz(db, quiz_id, school_id)

        # Check if already attempted
        existing = await db.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("You have already attempted this quiz")

        # Check time window
        now = datetime.utcnow()
        if quiz.starts_at and now < quiz.starts_at:
            raise BadRequestError("Quiz has not started yet")
        if quiz.ends_at and now > quiz.ends_at:
            raise BadRequestError("Quiz time has expired")

        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=student_id,
            institution_id=school_id,
            total_marks=quiz.total_marks,
            status="in_progress",
        )
        db.add(attempt)
        await db.flush()

        # Fetch questions without correct_answer field
        questions = await self._get_questions_for_student(db, quiz_id)
        return {"attempt_id": attempt.id, "quiz": quiz, "questions": questions}

    async def auto_grade(
        self, db: AsyncSession, attempt_id: int, student_id: int, answers: list[dict]
    ) -> dict:
        """Auto-grade objective questions. Returns score summary."""
        attempt = await self._get_attempt(db, attempt_id, student_id)
        questions = {q.id: q for q in await self._get_all_questions(db, attempt.quiz_id)}

        total_score = 0.0
        answer_records = []

        for ans in answers:
            q = questions.get(ans["question_id"])
            if not q:
                continue
            is_correct = self._check_answer(q, ans["given_answer"])
            marks = float(q.marks) if is_correct else 0.0
            total_score += marks
            answer_records.append(
                QuizAttemptAnswer(
                    attempt_id=attempt_id,
                    question_id=q.id,
                    given_answer=ans["given_answer"],
                    is_correct=is_correct,
                    marks_awarded=marks,
                )
            )

        db.add_all(answer_records)
        attempt.score = total_score
        attempt.percentage = (total_score / attempt.total_marks * 100) if attempt.total_marks else 0
        attempt.status = "submitted"
        attempt.submitted_at = datetime.utcnow()

        return {
            "score": total_score,
            "total_marks": attempt.total_marks,
            "percentage": attempt.percentage,
            "passed": attempt.percentage >= (attempt.quiz.passing_marks / attempt.total_marks * 100),
        }

    def _check_answer(self, question: QuizQuestion, given: str) -> bool:
        if question.question_type == "mcq":
            return given.strip().upper() == question.correct_answer.strip().upper()
        # For one_word: case-insensitive, strip whitespace
        if question.question_type == "one_word":
            return given.strip().lower() == question.correct_answer.strip().lower()
        # one_liner / assertion_reason: flag for teacher review (not auto-graded)
        return False
```

---

## Cache Keys — Centralized

```python
# app/cache/keys.py

class CacheKey:
    @staticmethod
    def institution(institution_id: int) -> str:
        return f"institution:{institution_id}"

    @staticmethod
    def teacher(teacher_id: int) -> str:
        return f"teacher:{teacher_id}"

    @staticmethod
    def teacher_list(school_id: int) -> str:
        return f"school:{school_id}:teachers"

    @staticmethod
    def student(student_id: int) -> str:
        return f"student:{student_id}"

    @staticmethod
    def student_list(school_id: int, grade: str | None = None) -> str:
        suffix = f":{grade}" if grade else ""
        return f"school:{school_id}:students{suffix}"

    @staticmethod
    def quiz(quiz_id: int) -> str:
        return f"quiz:{quiz_id}"

    @staticmethod
    def quiz_list(school_id: int, classroom_id: int | None = None) -> str:
        suffix = f":classroom:{classroom_id}" if classroom_id else ""
        return f"school:{school_id}:quizzes{suffix}"

    @staticmethod
    def ai_job(job_id: str) -> str:
        return f"ai:job:{job_id}"

    @staticmethod
    def rate_limit(user_id: int, endpoint: str) -> str:
        return f"ratelimit:{user_id}:{endpoint}"

    @staticmethod
    def notification_count(user_id: int) -> str:
        return f"notif:unread:{user_id}"
```

---

## Notification Service

```python
# app/services/notification/notification_service.py

class NotificationService:

    async def create_and_send(
        self,
        db: AsyncSession,
        institution_id: int,
        recipient_type: str,
        recipient_id: int | None,
        title: str,
        body: str,
        notif_type: str,
        channels: list[str] = ["in_app"],
    ) -> Notification:
        notif = Notification(
            institution_id=institution_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            title=title,
            body=body,
            notif_type=notif_type,
            channel=",".join(channels),
        )
        db.add(notif)
        await db.flush()

        # Dispatch delivery tasks
        if "email" in channels and recipient_id:
            send_email_notification_task.delay(notif.id)
        if "push" in channels and recipient_id:
            send_push_notification_task.delay(notif.id)

        # Invalidate unread count cache
        if recipient_id:
            await redis_client.delete(CacheKey.notification_count(recipient_id))

        return notif

    async def get_unread_count(self, db: AsyncSession, user_id: int) -> int:
        cache_key = CacheKey.notification_count(user_id)
        cached = await redis_client.get(cache_key)
        if cached:
            return int(cached)

        result = await db.execute(
            select(func.count(Notification.id))
            .where(Notification.recipient_id == user_id, Notification.is_read == False)
        )
        count = result.scalar()
        await redis_client.setex(cache_key, 60, str(count))
        return count
```

---

## Redis Client Setup

```python
# app/cache/redis_client.py

import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis = None

async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )

async def close_redis():
    if redis_client:
        await redis_client.close()
```

---

## Custom Exceptions

```python
# app/core/exceptions.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

class QuizerAIError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    def __init__(self, message: str):
        self.message = message

class NotFoundError(QuizerAIError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"

class ConflictError(QuizerAIError):
    status_code = 409
    code = "CONFLICT"

class BadRequestError(QuizerAIError):
    status_code = 400
    code = "BAD_REQUEST"

class ForbiddenError(QuizerAIError):
    status_code = 403
    code = "FORBIDDEN"

class UnauthorizedError(QuizerAIError):
    status_code = 401
    code = "UNAUTHORIZED"

class RateLimitError(QuizerAIError):
    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(QuizerAIError)
    async def quizerai_error_handler(request: Request, exc: QuizerAIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": request.state.request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )
```
