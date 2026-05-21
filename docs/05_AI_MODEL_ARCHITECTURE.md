# QuizerAI — AI Model Architecture

> Source: `QuizerAI_2.pdf` architecture diagram + handwritten notes
> All AI features run as **Celery tasks** except AI Tutor (which is streaming SSE)

---

## AI Feature Overview

| Feature | Trigger | Model | Sync/Async | Output |
|---------|---------|-------|------------|--------|
| **AI Tutor** | Student chat | Multi-agent (OpenAI + Claude) | Sync SSE stream | Real-time tokens |
| **Quiz Generation** | Teacher triggers | LLM + RAG agents | Async Celery | Quiz questions JSON |
| **Summarization** | Teacher/Student uploads | Claude (iterative) | Async Celery | Structured summary |
| **Assignment Evaluation** | Teacher triggers | Textract OCR + Claude | Async Celery | Score + remarks |

---

## 1. AI Tutor

### Architecture

```
Student Input
  │
  ├─ Text ─────────────────────────────────────┐
  ├─ Image/PDF → AWS Textract (OCR) ──────────┤
  └─ Voice → Custom Whisper (STT) ────────────┤
                                               │
                                               ▼
                                    ┌─────────────────┐
                                    │   AI Tutor       │
                                    │   Chatbot        │
                                    │  (last 5 lessons │
                                    │   context kept)  │
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                     │
               ┌────────▼──────┐  ┌──────────▼──────┐  ┌────────▼──────┐
               │ Maths Agent   │  │ Explanation     │  │  Mentor       │
               │ (OpenAI GPT-4o│  │  Agent          │  │  Agent        │
               │  with tools)  │  │ (Claude Haiku   │  │ (Claude)      │
               └───────────────┘  │  — cost-eff.)   │  └───────────────┘
                                  └─────────────────┘
                        │                    │
               ┌────────▼──────┐  ┌──────────▼──────┐
               │ Roadmap Agent │  │ System Q&A      │
               │ (Claude with  │  │  Agent          │
               │  deep think)  │  │ (RAG → Claude)  │
               └───────────────┘  └─────────────────┘
                        │
                        ▼
               Student Analytics
               (every interaction logged
                → performance context fed
                  back into next session)
```

### Agent Routing Logic

```python
# app/services/ai/tutor_service.py

AGENT_ROUTING = {
    "maths":      {"model": "gpt-4o",           "provider": "openai"},
    "explanation": {"model": "claude-haiku-4-5", "provider": "anthropic"},
    "mentor":      {"model": "claude-sonnet-4-6","provider": "anthropic"},
    "roadmap":     {"model": "claude-opus-4-6",  "provider": "anthropic"},  # deep thinking
    "system_qa":   {"model": "claude-haiku-4-5", "provider": "anthropic",
                    "use_rag": True},
}

def route_agent(message: str, explicit_agent: str | None) -> str:
    """
    If teacher/student explicitly picks an agent, use it.
    Otherwise, classify message intent and auto-route.
    """
    if explicit_agent:
        return explicit_agent

    # Simple keyword-based routing (upgrade to classifier later)
    math_keywords = ["solve", "calculate", "integral", "derivative", "equation"]
    if any(kw in message.lower() for kw in math_keywords):
        return "maths"
    if "explain" in message.lower() or "what is" in message.lower():
        return "explanation"
    if "roadmap" in message.lower() or "how to prepare" in message.lower():
        return "roadmap"
    return "explanation"  # default
```

### Session Management (Last 5 Lessons)

```python
async def get_session_context(
    db: AsyncSession, student_id: int, session_id: str | None
) -> list[dict]:
    """Fetch last 5 AI Tutor sessions for this student as context."""
    result = await db.execute(
        select(AISession)
        .where(AISession.student_id == student_id)
        .order_by(AISession.created_at.desc())
        .limit(5)
    )
    sessions = result.scalars().all()
    # Flatten messages from all sessions into context window
    context = []
    for session in reversed(sessions):
        context.extend(session.messages[-4:])  # last 4 messages per session
    return context
```

### SSE Streaming Response

```python
# app/routers/ai/tutor.py

from fastapi.responses import StreamingResponse
import json

@router.post("/chat")
async def chat(
    body: TutorChatRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = route_agent(body.message, body.agent)

    async def event_stream():
        async for token in tutor_service.stream_response(
            db=db, student_id=current_user.id,
            session_id=body.session_id, agent=agent,
            message=body.message,
        ):
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

## 2. AI Quiz Generation

### Pipeline (Celery Task)

```
Teacher Request
  │  { subject, topic, grade, board, question_types, difficulty_dist, use_pyq }
  ▼
quiz_gen_task (Celery)
  │
  ├─ [if use_pyq=True]
  │   └─ RAG Query → Pinecone
  │       ├─ Easy questions → Easy PYQ index (State Board / ICSE)
  │       ├─ Medium questions → Medium PYQ index (NCERT PYQs)
  │       └─ Hard questions → Hard PYQ index (JEE / NEET / Olympiad)
  │
  ▼
LLM Generation (parallel per difficulty)
  │
  ├─ Easy Agent   → generate easy_count questions
  ├─ Medium Agent → generate medium_count questions
  └─ Hard Agent   → generate hard_count questions
  │
  ▼
Structure & Validate
  │  Pydantic validate each question
  │  Check: correct_answer exists, options complete for MCQ, etc.
  │
  ▼
Store in Redis (job_id → questions JSON) with 1hr TTL
Teacher polls GET /ai/quiz-gen/job/{job_id}
  │
  ▼
Teacher accepts → save to quiz_questions table
```

### Question Type Schemas

```python
# app/schemas/ai.py

class MCQQuestion(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str
    difficulty: Literal["easy", "medium", "hard"]
    source_pyq: str | None = None

class AssertionReasonQuestion(BaseModel):
    assertion: str
    reason: str
    correct_answer: Literal["A", "B", "C", "D"]
    # A: Both A and R true, R explains A
    # B: Both true, R does not explain A
    # C: A true, R false
    # D: A false, R true
    explanation: str
    difficulty: Literal["easy", "medium", "hard"]

class OneWordQuestion(BaseModel):
    question_text: str
    correct_answer: str
    explanation: str
    difficulty: Literal["easy", "medium", "hard"]

class OneLinerQuestion(BaseModel):
    question_text: str
    correct_answer: str       # 1-2 sentence answer
    keywords: list[str]       # for flexible grading
    explanation: str
    difficulty: Literal["easy", "medium", "hard"]
```

### RAG Strategy

```
Pinecone Index: "quizerai-pyq"
│
├── Namespace: "cbse-easy"      ← CBSE State Board easy PYQs
├── Namespace: "cbse-medium"    ← CBSE NCERT standard PYQs
├── Namespace: "cbse-hard"      ← CBSE advanced PYQs
├── Namespace: "icse-easy"
├── Namespace: "icse-medium"
├── Namespace: "jee-hard"       ← JEE Main + Advanced
├── Namespace: "neet-hard"      ← NEET Biology/Chemistry
└── Namespace: "olympiad-hard"  ← Science Olympiad

Query: embed(topic + grade + difficulty) → top-5 similar PYQs → include as few-shot examples in prompt
```

---

## 3. Summarization

### Pipeline

```
Input (PDF / plain text)
  │
  ├─ If PDF → extract text (pypdf / Textract fallback for scanned)
  │
  ▼
summarize_task (Celery)
  │
  ├─ Pass 1: Initial Summary
  │   └─ Claude: "Summarize this document in {summary_type} format"
  │
  ├─ Pass 2: Refine/Recheck (N times, default=2)
  │   └─ Claude: "Review this summary for accuracy and completeness. Improve it."
  │
  ├─ Structure Pass
  │   └─ Claude: "Format into: title, key_points[], sections[{heading, content}]"
  │
  ▼
Store result in Redis → poll → return to client
```

### Prompt Strategy

```python
SUMMARIZE_SYSTEM_PROMPT = """
You are an expert educational content summarizer for Indian students.
Always output well-structured summaries that are:
- Accurate and factually correct
- Age-appropriate for the given grade level
- Aligned with Indian curriculum standards
- Highlighting key concepts, formulas, and definitions
"""

def build_summarize_prompt(text: str, summary_type: str) -> str:
    formats = {
        "bullet_points": "as a structured list of bullet points grouped by subtopic",
        "paragraph": "as clear, flowing paragraphs",
        "structured": "with clear headings, subheadings, key points, and a conclusion",
    }
    return f"""
Summarize the following educational content {formats[summary_type]}.

Content:
{text[:8000]}  # token budget control

Output JSON with keys: title, summary, key_points (list), sections (list of heading+content)
"""
```

---

## 4. Assignment Evaluation

### Pipeline

```
Student Submission (PDF / image)
  │
assignment_eval_task (Celery)
  │
  ├─ Step 1: OCR — AWS Textract (async)
  │   └─ Extract handwritten/typed text from PDF/image
  │
  ├─ Step 2: Text Clean & Structure
  │   └─ Remove OCR noise, normalize whitespace
  │
  ├─ Step 3: AI Evaluation — Claude
  │   Input:
  │     - Extracted student text
  │     - Assignment question/description
  │     - Rubric (optional teacher-provided)
  │     - Max score
  │   Output:
  │     - score (float)
  │     - remarks (string)
  │     - improvements (list of strings)
  │
  ├─ Step 4: Store result in assignment_submissions
  │
  └─ Step 5: Notify teacher + student (notification_task)
```

### Evaluation Prompt

```python
EVAL_SYSTEM_PROMPT = """
You are an experienced Indian school teacher evaluating a student's assignment.
Be fair, constructive, and specific. Follow the rubric if provided.
Output ONLY valid JSON.
"""

def build_eval_prompt(student_text: str, assignment: dict, rubric: str, max_score: int) -> str:
    return f"""
Assignment: {assignment['title']}
Description: {assignment['description']}
Rubric: {rubric or 'General academic quality, accuracy, and clarity'}
Maximum Score: {max_score}

Student's Answer:
{student_text[:4000]}

Evaluate and return JSON:
{{
  "score": <float, 0 to {max_score}>,
  "remarks": "<2-3 sentence overall feedback>",
  "improvements": ["<specific improvement 1>", "<specific improvement 2>"],
  "strengths": ["<what they did well>"]
}}
"""
```

---

## Celery Tasks Reference

```python
# app/tasks/celery_app.py

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "quizerai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    task_routes={
        "app.tasks.quiz_gen_task.*":        {"queue": "ai_heavy"},
        "app.tasks.assignment_eval_task.*": {"queue": "ai_heavy"},
        "app.tasks.summarize_task.*":       {"queue": "ai_light"},
        "app.tasks.notification_task.*":    {"queue": "notifications"},
    },
    task_time_limit=300,        # 5 min max per task
    task_soft_time_limit=240,
    worker_max_tasks_per_child=100,
)
```

### Queue Architecture

| Queue | Workers | Tasks |
|-------|---------|-------|
| `ai_heavy` | 2–5 pods (scale on depth) | Quiz Gen, Assignment Eval |
| `ai_light` | 2–3 pods | Summarization |
| `notifications` | 1–2 pods | Email, push notifications |
| `default` | 2 pods | General tasks |

---

## Cost Control Measures

| Measure | Detail |
|---------|--------|
| **Model routing** | Use Claude Haiku for explanation (cheap), GPT-4o only for maths |
| **Token budget** | Hard cap input at 8K tokens; chunk large docs |
| **Caching** | Cache AI results in Redis for 1hr — same question same answer |
| **Rate limits** | 10 AI requests/min per user; institution-level monthly quotas |
| **Async jobs** | Never block HTTP thread for AI calls — always Celery |
| **Feature flags** | Per-institution toggle — disable AI for free plan or trial expiry |
