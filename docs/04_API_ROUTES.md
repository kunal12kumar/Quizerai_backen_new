# QuizerAI — API Routes (Complete)

> Base URL: `https://api.quizerai.com/api/v1`
> All routes require `Authorization: Bearer <access_token>` unless marked `[PUBLIC]`
> `school_id` is **always from JWT**, never from request body

---

## Auth Role Legend

| Symbol | Role |
|--------|------|
| `GA` | Global Admin |
| `SA` | School Admin |
| `TE` | Teacher |
| `ST` | Student |
| `[PUBLIC]` | No auth required |

---

## 1. Authentication — `/auth`

### Global Admin Auth — `/auth/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/admin/login` | `[PUBLIC]` | Global admin login |
| `POST` | `/auth/admin/refresh` | `[PUBLIC]` | Refresh access token |
| `POST` | `/auth/admin/logout` | `GA` | Revoke refresh token (Redis blacklist) |

**POST `/auth/admin/login`**
```json
// Request
{ "email": "admin@quizerai.com", "password": "..." }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": 1, "name": "Super Admin", "role": "global_admin" }
}
```

---

### School Auth — `/auth/school`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/school/login` | `[PUBLIC]` | Unified login for SA/TE/ST |
| `POST` | `/auth/school/refresh` | `[PUBLIC]` | Refresh token |
| `POST` | `/auth/school/logout` | `SA/TE/ST` | Logout (blacklist token) |
| `POST` | `/auth/school/forgot-password` | `[PUBLIC]` | Send OTP to email |
| `POST` | `/auth/school/reset-password` | `[PUBLIC]` | Reset with OTP |
| `POST` | `/auth/school/change-password` | `SA/TE/ST` | Change own password |

**POST `/auth/school/login`**
```json
// Request
{
  "email": "teacher@dps.edu",
  "password": "...",
  "role": "teacher"   // "school_admin" | "teacher" | "student"
}

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 42,
    "name": "Ramesh Kumar",
    "role": "teacher",
    "school_id": 5,
    "institution_name": "Delhi Public School"
  }
}
```

---

## 2. Global Admin — `/admin`

> All routes: `GA` only

### Institutions — `/admin/institutions`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/institutions` | List all institutions (paginated, filterable) |
| `POST` | `/admin/institutions` | Create / onboard new institution |
| `GET` | `/admin/institutions/{id}` | Get institution detail |
| `PATCH` | `/admin/institutions/{id}` | Update institution fields |
| `DELETE` | `/admin/institutions/{id}` | Soft-delete institution |
| `POST` | `/admin/institutions/{id}/verify` | Verify institution |
| `POST` | `/admin/institutions/{id}/suspend` | Suspend institution |
| `POST` | `/admin/institutions/{id}/activate` | Reactivate institution |
| `POST` | `/admin/institutions/{id}/logo` | Upload logo (multipart) |
| `GET` | `/admin/institutions/{id}/stats` | Institution-level stats |

**GET `/admin/institutions`** Query Params:
```
?page=1&limit=20&status=active&institution_type=school&city=Delhi&search=DPS
```

**POST `/admin/institutions`** Body: see `InstitutionCreate` schema in `02_INSTITUTION_MODEL.md`

---

### Global Users — `/admin/users`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/users` | List all users across institutions |
| `GET` | `/admin/users/{role}/{id}` | Get specific user |
| `POST` | `/admin/users/global-admin` | Create another global admin |
| `PATCH` | `/admin/users/{role}/{id}/toggle-active` | Activate / deactivate |

---

### Platform Analytics — `/admin/analytics`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/analytics/overview` | Total institutions, users, quizzes, AI usage |
| `GET` | `/admin/analytics/growth` | Month-over-month growth |
| `GET` | `/admin/analytics/ai-usage` | AI API cost / usage per institution |
| `GET` | `/admin/analytics/quiz-stats` | Quiz completion rates platform-wide |

---

## 3. School — `/school`

> All routes require valid JWT with `school_id` claim

### Dashboard — `/school/dashboard`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/dashboard/stats` | `SA` | Counts: teachers, students, classrooms, quizzes |
| `GET` | `/school/dashboard/recent-activity` | `SA` | Last 10 actions in school |
| `GET` | `/school/dashboard/teacher-stats` | `TE` | My classrooms, quizzes, submissions |
| `GET` | `/school/dashboard/student-stats` | `ST` | My scores, upcoming quizzes, AI sessions |

---

### School Admin Profile — `/school/profile`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/profile` | `SA` | Get own profile |
| `PATCH` | `/school/profile` | `SA` | Update own profile |
| `GET` | `/school/profile/institution` | `SA` | Get institution details |
| `PATCH` | `/school/profile/institution` | `SA` | Update institution info |

---

### Teachers — `/school/teachers`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/teachers` | `SA` | List all teachers (paginated) |
| `POST` | `/school/teachers` | `SA` | Create teacher (send welcome email) |
| `GET` | `/school/teachers/{id}` | `SA` | Get teacher detail |
| `PATCH` | `/school/teachers/{id}` | `SA` | Update teacher |
| `DELETE` | `/school/teachers/{id}` | `SA` | Deactivate teacher |
| `POST` | `/school/teachers/bulk-import` | `SA` | CSV bulk import |
| `GET` | `/school/teachers/{id}/classrooms` | `SA/TE` | Teacher's classrooms |
| `GET` | `/school/teachers/{id}/analytics` | `SA` | Quiz/assignment activity |

**POST `/school/teachers`**
```json
{
  "name": "Ramesh Kumar",
  "email": "ramesh@dps.edu",
  "mobile_number": "9876543210",
  "employee_id": "EMP001",
  "subjects": ["Mathematics", "Physics"],
  "qualification": "M.Sc Mathematics"
}
// System auto-generates a temporary password and sends welcome email
```

---

### Students — `/school/students`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/students` | `SA/TE` | List students (filterable by grade/classroom) |
| `POST` | `/school/students` | `SA` | Create student |
| `GET` | `/school/students/{id}` | `SA/TE/ST` | Get student profile |
| `PATCH` | `/school/students/{id}` | `SA/ST` | Update student |
| `DELETE` | `/school/students/{id}` | `SA` | Deactivate student |
| `POST` | `/school/students/bulk-import` | `SA` | CSV bulk import |
| `GET` | `/school/students/{id}/performance` | `SA/TE/ST` | Quiz scores, AI usage |
| `GET` | `/school/students/{id}/quiz-history` | `SA/TE/ST` | All quiz attempts |

**GET `/school/students`** Query Params:
```
?page=1&limit=20&grade=10&classroom_id=3&search=Rahul&is_active=true
```

---

### Classrooms — `/school/classroom`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/classroom` | `SA/TE` | List classrooms |
| `POST` | `/school/classroom` | `SA` | Create classroom |
| `GET` | `/school/classroom/{id}` | `SA/TE` | Classroom detail |
| `PATCH` | `/school/classroom/{id}` | `SA` | Update classroom |
| `DELETE` | `/school/classroom/{id}` | `SA` | Deactivate |
| `GET` | `/school/classroom/{id}/members` | `SA/TE` | List students + teachers |
| `POST` | `/school/classroom/{id}/members/students` | `SA` | Enroll students |
| `POST` | `/school/classroom/{id}/members/teachers` | `SA` | Assign teachers |
| `DELETE` | `/school/classroom/{id}/members/{member_id}` | `SA` | Remove member |
| `GET` | `/school/classroom/{id}/analytics` | `SA/TE` | Classroom avg scores |

**POST `/school/classroom/{id}/members/students`**
```json
{ "student_ids": [10, 11, 12, 45] }
```

---

### Learn — `/school/learn`

#### Subjects — `/school/learn/subjects`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/learn/subjects` | `SA/TE/ST` | List subjects |
| `POST` | `/school/learn/subjects` | `SA` | Create subject |
| `PATCH` | `/school/learn/subjects/{id}` | `SA` | Update subject |
| `DELETE` | `/school/learn/subjects/{id}` | `SA` | Delete subject |

#### Content — `/school/learn/content`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/learn/content` | `SA/TE/ST` | List content (filterable by subject) |
| `POST` | `/school/learn/content` | `TE` | Upload content (PDF/doc) |
| `GET` | `/school/learn/content/{id}` | `SA/TE/ST` | Get content + signed S3 URL |
| `DELETE` | `/school/learn/content/{id}` | `TE/SA` | Delete content |

---

### Quizes — `/school/quizes`

#### Quiz CRUD — `/school/quizes/quiz`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/quizes/quiz` | `SA/TE/ST` | List quizzes (role-filtered) |
| `POST` | `/school/quizes/quiz` | `TE` | Create manual quiz |
| `GET` | `/school/quizes/quiz/{id}` | `SA/TE/ST` | Quiz detail (with questions if teacher) |
| `PATCH` | `/school/quizes/quiz/{id}` | `TE` | Update quiz metadata |
| `DELETE` | `/school/quizes/quiz/{id}` | `TE/SA` | Delete draft quiz |
| `POST` | `/school/quizes/quiz/{id}/publish` | `TE` | Publish quiz to classrooms |
| `POST` | `/school/quizes/quiz/{id}/close` | `TE` | Close quiz |
| `POST` | `/school/quizes/quiz/{id}/questions` | `TE` | Add question to quiz |
| `PATCH` | `/school/quizes/quiz/{id}/questions/{qid}` | `TE` | Update question |
| `DELETE` | `/school/quizes/quiz/{id}/questions/{qid}` | `TE` | Remove question |
| `GET` | `/school/quizes/quiz/{id}/results` | `TE/SA` | All student results for quiz |
| `GET` | `/school/quizes/quiz/{id}/leaderboard` | `SA/TE/ST` | Top 10 scores |

**POST `/school/quizes/quiz`**
```json
{
  "title": "Chapter 5 - Gravitation Test",
  "classroom_id": 3,
  "subject_id": 2,
  "difficulty": "medium",
  "time_limit_min": 30,
  "total_marks": 25,
  "passing_marks": 10,
  "starts_at": "2025-06-01T09:00:00Z",
  "ends_at": "2025-06-01T09:30:00Z"
}
```

#### Quiz Attempts — `/school/quizes/attempt`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/school/quizes/attempt/{quiz_id}/start` | `ST` | Start attempt (get questions) |
| `POST` | `/school/quizes/attempt/{attempt_id}/answer` | `ST` | Submit individual answer |
| `POST` | `/school/quizes/attempt/{attempt_id}/submit` | `ST` | Final submit + auto-grade |
| `GET` | `/school/quizes/attempt/{attempt_id}/result` | `ST/TE` | Get result with explanations |
| `GET` | `/school/quizes/attempt/my-history` | `ST` | All my past attempts |

**POST `/school/quizes/attempt/{attempt_id}/submit`**
```json
{
  "answers": [
    { "question_id": 101, "given_answer": "B" },
    { "question_id": 102, "given_answer": "Force equals mass times acceleration" }
  ]
}
// Response: { score, percentage, correct_count, wrong_count, result_detail }
```

#### Assignments — `/school/quizes/assignment`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/school/quizes/assignment` | `SA/TE/ST` | List assignments |
| `POST` | `/school/quizes/assignment` | `TE` | Create assignment |
| `GET` | `/school/quizes/assignment/{id}` | `SA/TE/ST` | Assignment detail |
| `PATCH` | `/school/quizes/assignment/{id}` | `TE` | Update assignment |
| `POST` | `/school/quizes/assignment/{id}/publish` | `TE` | Publish to classroom |
| `POST` | `/school/quizes/assignment/{id}/submit` | `ST` | Submit (multipart file) |
| `GET` | `/school/quizes/assignment/{id}/submissions` | `TE/SA` | All submissions |
| `GET` | `/school/quizes/assignment/{id}/submissions/{sub_id}` | `TE/ST` | Single submission |
| `PATCH` | `/school/quizes/assignment/{id}/submissions/{sub_id}/grade` | `TE` | Teacher override grade |

**POST `/school/quizes/assignment/{id}/submit`** — multipart/form-data
```
file: <PDF or image binary>
text_content: optional typed answer
```

---

## 4. AI — `/ai`

> Stricter rate limit: 10 req/min per user
> All AI routes require active `school_id` in JWT + institution feature flag check

### AI Tutor — `/ai/tutor`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/ai/tutor/chat` | `ST/TE` | Send message — streaming SSE response |
| `GET` | `/ai/tutor/sessions` | `ST` | List my recent sessions (last 10) |
| `GET` | `/ai/tutor/sessions/{id}` | `ST` | Full session history |
| `DELETE` | `/ai/tutor/sessions/{id}` | `ST` | Clear session |
| `POST` | `/ai/tutor/upload` | `ST` | Upload PDF/image for tutor context |

**POST `/ai/tutor/chat`**
```json
{
  "session_id": "optional-existing-session-id",
  "agent": "maths",             // "maths" | "explanation" | "mentor" | "roadmap" | "system_qa"
  "message": "Solve this: integral of x^2 from 0 to 3",
  "input_type": "text",         // "text" | "image" | "pdf" | "voice"
  "file_key": null              // S3 key if input_type != text
}

// Response: Server-Sent Events (SSE) stream
// event: token
// data: {"token": "The ", "session_id": "abc123"}
// ...
// event: done
// data: {"full_response": "...", "agent_used": "maths", "session_id": "abc123"}
```

---

### AI Quiz Generation — `/ai/quiz-gen`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/ai/quiz-gen/generate` | `TE` | Trigger AI quiz gen (async Celery job) |
| `GET` | `/ai/quiz-gen/job/{job_id}` | `TE` | Poll job status |
| `GET` | `/ai/quiz-gen/job/{job_id}/result` | `TE` | Get generated questions |
| `POST` | `/ai/quiz-gen/job/{job_id}/accept` | `TE` | Accept + save to quiz |
| `POST` | `/ai/quiz-gen/job/{job_id}/regenerate` | `TE` | Regenerate with tweaks |

**POST `/ai/quiz-gen/generate`**
```json
{
  "subject": "Physics",
  "topic": "Gravitation",
  "grade": "11",
  "board": "CBSE",                          // "CBSE" | "ICSE" | "JEE" | "NEET" | "STATE_BOARD" | "OLYMPIAD"
  "question_types": ["mcq", "one_liner"],
  "difficulty_distribution": {
    "easy": 3,
    "medium": 5,
    "hard": 2
  },
  "total_questions": 10,
  "use_pyq": true,                          // use RAG from PYQ corpus
  "human_review_required": false,
  "target_quiz_id": 55                      // optional — attach to existing quiz
}

// Response 202 Accepted
{ "job_id": "quiz-gen-abc123", "status": "queued", "estimated_seconds": 15 }
```

**GET `/ai/quiz-gen/job/{job_id}`**
```json
{ "job_id": "...", "status": "processing | completed | failed", "progress": 60 }
```

---

### Summarizer — `/ai/summarize`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/ai/summarize/document` | `TE/ST` | Summarize uploaded PDF/doc |
| `POST` | `/ai/summarize/text` | `TE/ST` | Summarize plain text |
| `GET` | `/ai/summarize/job/{job_id}` | `TE/ST` | Poll job status |
| `GET` | `/ai/summarize/job/{job_id}/result` | `TE/ST` | Get structured summary |

**POST `/ai/summarize/document`** — multipart/form-data
```
file: <PDF binary>
summary_type: "bullet_points" | "paragraph" | "structured"
refine_passes: 2          // number of refine-recheck iterations
```

**GET `/ai/summarize/job/{job_id}/result`**
```json
{
  "title": "Chapter 5 - Gravitation",
  "summary": "...",
  "key_points": ["...", "..."],
  "sections": [
    { "heading": "Introduction", "content": "..." }
  ],
  "word_count": 450
}
```

---

### Assignment Evaluation — `/ai/assignment`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/ai/assignment/evaluate/{submission_id}` | `TE/SA` | Trigger AI evaluation |
| `GET` | `/ai/assignment/job/{job_id}` | `TE` | Poll job status |
| `GET` | `/ai/assignment/job/{job_id}/result` | `TE/ST` | Get evaluation result |

**POST `/ai/assignment/evaluate/{submission_id}`**
```json
{
  "rubric": "Check for Newton's Laws accuracy, clarity, and examples",
  "max_score": 25
}
// Triggers: OCR (Textract) → text extraction → Claude evaluation → store result
// Response 202: { "job_id": "eval-xyz789", "status": "queued" }
```

**GET `/ai/assignment/job/{job_id}/result`**
```json
{
  "score": 19.5,
  "max_score": 25,
  "percentage": 78,
  "remarks": "Good understanding of Newton's second law...",
  "improvements": [
    "Add numerical examples for Newton's third law",
    "Conclusion needs strengthening"
  ],
  "ocr_text_preview": "The student wrote..."
}
```

---

## 5. System — `/system`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/system/health` | `[PUBLIC]` | Liveness check — `{ "status": "ok" }` |
| `GET` | `/system/ready` | `[PUBLIC]` | Readiness — checks DB + Redis connectivity |
| `GET` | `/system/metrics` | `GA` | Prometheus metrics (scraped by K8s) |

---

## 6. Notifications — `/notifications`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/notifications` | `SA/TE/ST` | My notifications (paginated) |
| `GET` | `/notifications/unread-count` | `SA/TE/ST` | Count of unread notifications |
| `POST` | `/notifications/{id}/read` | `SA/TE/ST` | Mark one as read |
| `POST` | `/notifications/read-all` | `SA/TE/ST` | Mark all as read |
| `POST` | `/notifications/send` | `SA/TE` | Send custom notification to classroom |

---

## Error Response Format (All Routes)

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Student with id 99 not found in your institution",
    "request_id": "req_abc123",
    "timestamp": "2025-05-19T14:30:00Z"
  }
}
```

| HTTP Code | When |
|-----------|------|
| `400` | Validation error / bad request |
| `401` | Missing or invalid JWT |
| `403` | Authenticated but insufficient role |
| `404` | Resource not found (scoped to institution) |
| `409` | Conflict (duplicate email, etc.) |
| `422` | Pydantic validation failure |
| `429` | Rate limit exceeded |
| `500` | Internal server error (logged + alerted) |

---

## Pagination Standard

All list endpoints return:

```json
{
  "data": [...],
  "pagination": {
    "total": 245,
    "page": 1,
    "limit": 20,
    "pages": 13,
    "has_next": true,
    "has_prev": false
  }
}
```
