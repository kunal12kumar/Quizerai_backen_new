# QuizerAI — Architecture Map & New Engineer Onboarding Guide

> **Read this before writing a single line of code.**
> This document is the single source of truth for how QuizerAI is structured, why decisions were made, and how every part connects.

---

## Table of Contents

1. [What Is QuizerAI?](#1-what-is-quizerai)
2. [Multi-Tenancy — The Core Concept](#2-multi-tenancy--the-core-concept)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [Full System Architecture](#4-full-system-architecture)
5. [Frontend Route Map (Next.js Pages)](#5-frontend-route-map-nextjs-pages)
6. [Backend API Route Map (FastAPI Endpoints)](#6-backend-api-route-map-fastapi-endpoints)
7. [Database Schema & Relationships](#7-database-schema--relationships)
8. [Authentication & JWT Flow](#8-authentication--jwt-flow)
9. [Request Lifecycle (Middleware Chain)](#9-request-lifecycle-middleware-chain)
10. [AI Feature Pipelines](#10-ai-feature-pipelines)
11. [Tech Stack — What, Why & Where](#11-tech-stack--what-why--where)
12. [Folder Structures (Backend + Frontend)](#12-folder-structures-backend--frontend)
13. [Development Setup](#13-development-setup)
14. [Key Engineering Rules](#14-key-engineering-rules)
15. [Sprint Roadmap](#15-sprint-roadmap)
16. [Glossary](#16-glossary)

---

## 1. What Is QuizerAI?

QuizerAI is a **multi-tenant, AI-powered EdTech SaaS platform**.

**In plain English**: Schools, colleges, coaching centers, and universities sign up as "institutions". Each institution gets its own fully isolated workspace. Inside that workspace, admins manage teachers and students, teachers create quizzes and assignments, and students learn with the help of AI.

### Core Features

| Feature | What It Does |
|---------|-------------|
| **Institution Management** | Onboard schools, manage their admin panel, control subscription/features |
| **User Management** | School Admins manage Teachers and Students with role-based access |
| **Quiz Engine** | Teachers create MCQ/AR/One-Word/One-Liner quizzes; students attempt them with auto-grading |
| **AI Quiz Generation** | AI generates quiz questions from topic + board (CBSE/JEE/NEET) using past year papers (RAG) |
| **AI Tutor** | Students chat with an AI tutor — routes to specialist agents (Maths, Explanation, Mentor, Roadmap) |
| **Assignment Evaluation** | Students submit PDFs/images; AI (via OCR + LLM) grades them with feedback |
| **Summarization** | AI summarizes lesson documents into structured notes |
| **Student Analytics** | Every quiz attempt and AI session feeds into a performance dashboard |

---

## 2. Multi-Tenancy — The Core Concept

This is the most important concept to understand. **Everything in the system is scoped to a `school_id`.**

```
                     ┌────────────────────────────┐
                     │    QuizerAI SaaS Platform   │
                     │    (Single Database)        │
                     └────────────┬───────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────▼──────┐  ┌─────────▼──────┐  ┌────────▼───────┐
    │  Institution A  │  │  Institution B  │  │ Institution C  │
    │  "DPS Rohini"   │  │  "JEE Academy"  │  │ "St. Xavier's" │
    │  school_id = 1  │  │  school_id = 2  │  │  school_id = 3 │
    │                 │  │                 │  │                │
    │  ├─ Admin       │  │  ├─ Admin       │  │  ├─ Admin      │
    │  ├─ 50 Teachers │  │  ├─ 20 Teachers │  │  ├─ 30 Teachers│
    │  └─ 800 Students│  │  └─ 400 Students│  │  └─ 600 Students│
    └─────────────────┘  └─────────────────┘  └────────────────┘
```

**How isolation works**:
1. Every table that belongs to a school has an `institution_id` column (FK to `institutions.id`)
2. When a user logs in, their JWT contains `school_id`
3. The `SchoolContextMiddleware` extracts `school_id` from the JWT and attaches it to `request.state`
4. Every service query adds `.where(Model.institution_id == school_id)`
5. **You never get `school_id` from the request body** — always from the JWT

**Why shared DB, not separate DBs?**
- Simpler operations and migrations (one Alembic run updates all)
- Cheaper at scale (1000 tenants = 1 DB, not 1000 DBs)
- `school_id` FK is always indexed — queries are fast

---

## 3. User Roles & Permissions

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ROLE HIERARCHY                               │
│                                                                      │
│   GLOBAL ADMIN (GA)                                                  │
│   ├── Sees ALL institutions, ALL data                                │
│   ├── Creates/verifies/suspends institutions                         │
│   ├── Platform-wide analytics                                        │
│   └── No school_id in JWT (it's null)                               │
│                                                                      │
│   SCHOOL ADMIN (SA)           ← scoped to their school_id           │
│   ├── Manages Teachers and Students                                  │
│   ├── Manages Classrooms and Subjects                                │
│   ├── Sees all quizzes/assignments in their school                   │
│   └── Updates institution profile                                    │
│                                                                      │
│   TEACHER (TE)                ← scoped to their school_id           │
│   ├── Creates and publishes Quizzes                                  │
│   ├── Creates and grades Assignments                                 │
│   ├── Views student performance in their classrooms                  │
│   └── Triggers AI quiz generation and tutor                         │
│                                                                      │
│   STUDENT (ST)                ← scoped to their school_id           │
│   ├── Attempts quizzes (read-only view of questions)                 │
│   ├── Submits assignments (file upload)                              │
│   ├── Uses AI Tutor                                                  │
│   └── Views own performance only                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Permissions Matrix

| Resource | GA | SA | TE | ST |
|----------|----|----|----|----|
| Create Institution | ✅ | ❌ | ❌ | ❌ |
| List All Institutions | ✅ | ❌ | ❌ | ❌ |
| Manage Teachers | ✅ | ✅ | ❌ | ❌ |
| Manage Students | ✅ | ✅ | ❌ | ❌ |
| View Student List | ✅ | ✅ | ✅ (own class) | ❌ |
| Create Quiz | ✅ | ✅ | ✅ | ❌ |
| Attempt Quiz | ❌ | ❌ | ❌ | ✅ |
| Create Assignment | ❌ | ❌ | ✅ | ❌ |
| Submit Assignment | ❌ | ❌ | ❌ | ✅ |
| Grade Assignment | ❌ | ❌ | ✅ | ❌ |
| Use AI Tutor | ❌ | ❌ | ✅ | ✅ |
| Trigger AI Quiz Gen | ❌ | ❌ | ✅ | ❌ |
| View Platform Analytics | ✅ | ❌ | ❌ | ❌ |

---

## 4. Full System Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         QUIZERAI PRODUCTION ARCHITECTURE                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CLIENTS                                                                     ║
║  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         ║
║  │  Browser    │  │  Mobile App │  │  3rd Party  │                         ║
║  │ (Next.js)   │  │  (future)   │  │  Integrators│                         ║
║  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                         ║
║         └────────────────┴────────────────┘                                 ║
║                           │  HTTPS                                           ║
║                           ▼                                                  ║
║  ┌────────────────────────────────────┐                                      ║
║  │   AWS API Gateway / Kong           │  ← DDoS protection, SSL termination  ║
║  │   Global rate limiting, WAF        │    API key validation, routing        ║
║  └───────────────────┬────────────────┘                                      ║
║                      │                                                       ║
║  ┌───────────────────▼────────────────┐                                      ║
║  │   Kubernetes Cluster (EKS/GKE)     │                                      ║
║  │                                    │                                      ║
║  │  ┌──────────────────────────────┐  │                                      ║
║  │  │  NGINX Ingress Controller    │  │                                      ║
║  │  └──────────────┬───────────────┘  │                                      ║
║  │                 │                  │                                      ║
║  │  ┌──────────────▼───────────────┐  │                                      ║
║  │  │  FastAPI Pods (HPA)          │  │  ← Min 2 / Max 50 replicas           ║
║  │  │  ┌────────────────────────┐  │  │    Scale on CPU > 60% or RPS > 500   ║
║  │  │  │  Middleware Chain:     │  │  │                                      ║
║  │  │  │  1. RequestID          │  │  │                                      ║
║  │  │  │  2. SchoolContext(JWT) │  │  │                                      ║
║  │  │  │  3. RateLimit(Redis)   │  │  │                                      ║
║  │  │  │  4. Logging            │  │  │                                      ║
║  │  │  └────────────────────────┘  │  │                                      ║
║  │  └──────────────┬───────────────┘  │                                      ║
║  │                 │                  │                                      ║
║  │  ┌──────────────▼───────────────┐  │                                      ║
║  │  │  Celery Workers (HPA)        │  │  ← Scale on queue depth              ║
║  │  │  Queues: ai_heavy, ai_light  │  │    ai_heavy: min 2 / max 10          ║
║  │  │           notifications      │  │                                      ║
║  │  └──────────────────────────────┘  │                                      ║
║  └────────────────────────────────────┘                                      ║
║                                                                              ║
║  DATA LAYER                                                                  ║
║  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐  ║
║  │   MySQL 8      │  │  Redis Cluster  │  │   AWS Services               │  ║
║  │  Primary +     │  │  ├─ Session     │  │   ├─ S3 (files/logos/PDFs)   │  ║
║  │  2 Read        │  │  ├─ Cache       │  │   ├─ Textract (OCR)          │  ║
║  │  Replicas      │  │  ├─ Rate Limit  │  │   └─ API Gateway             │  ║
║  └────────────────┘  │  └─ Job Results │  └──────────────────────────────┘  ║
║                      └─────────────────┘                                    ║
║  AI LAYER                                                                   ║
║  ┌─────────────────────────────────────────────────────────────┐            ║
║  │  OpenAI GPT-4o  │  Anthropic Claude  │  Custom Whisper STT  │            ║
║  │  (Maths agent)  │  (Explanation,     │  (Voice input for    │            ║
║  │                 │   Mentor, Roadmap, │   AI Tutor)          │            ║
║  │                 │   Eval, Summarize) │                      │            ║
║  └─────────────────────────────────────────────────────────────┘            ║
║                                                                              ║
║  VECTOR DB (RAG)             MONITORING                                      ║
║  ┌────────────────┐          ┌──────────────────────────────────┐           ║
║  │  Pinecone      │          │  Prometheus + Grafana (metrics)  │           ║
║  │  PYQ Corpus    │          │  ELK Stack (structured logs)     │           ║
║  │  Namespaces by │          └──────────────────────────────────┘           ║
║  │  board+level   │                                                          ║
║  └────────────────┘                                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Frontend Route Map (Next.js Pages)

All routes use Next.js 14 App Router. `[slug]` = dynamic segment.

```
app/
│
├── (auth)/                         ← Auth layout (no sidebar)
│   ├── login/                      → /login         — Role selector + login form
│   ├── admin/login/                → /admin/login   — Global admin login
│   ├── forgot-password/            → /forgot-password
│   └── reset-password/             → /reset-password?token=xxx
│
├── (global-admin)/                 ← Global Admin layout (GA sidebar)
│   │   middleware: require GA role
│   ├── dashboard/                  → /dashboard             — Platform stats
│   ├── institutions/               → /institutions          — List all institutions
│   │   ├── new/                    → /institutions/new      — Onboarding wizard
│   │   └── [id]/                   → /institutions/[id]     — Detail + edit
│   ├── users/                      → /users                 — Cross-institution users
│   └── analytics/                  → /analytics             — AI usage, quiz stats
│
├── (school-admin)/                 ← School Admin layout (SA sidebar)
│   │   middleware: require SA role
│   ├── dashboard/                  → /school/dashboard      — School stats
│   ├── teachers/                   → /school/teachers       — Teacher list
│   │   ├── new/                    → /school/teachers/new   — Create teacher
│   │   ├── import/                 → /school/teachers/import— CSV bulk import
│   │   └── [id]/                   → /school/teachers/[id]  — Detail + edit
│   ├── students/                   → /school/students       — Student list
│   │   ├── new/                    → /school/students/new
│   │   ├── import/                 → /school/students/import
│   │   └── [id]/                   → /school/students/[id]  — Profile + performance
│   ├── classrooms/                 → /school/classrooms     — Classroom list
│   │   ├── new/                    → /school/classrooms/new
│   │   └── [id]/                   → /school/classrooms/[id]— Detail + members
│   ├── subjects/                   → /school/subjects
│   ├── content/                    → /school/content
│   └── settings/                   → /school/settings       — Institution profile
│
├── (teacher)/                      ← Teacher layout (TE sidebar)
│   │   middleware: require TE role
│   ├── dashboard/                  → /teacher/dashboard     — My classrooms, quizzes
│   ├── quizzes/                    → /teacher/quizzes       — My quiz list
│   │   ├── new/                    → /teacher/quizzes/new   — Quiz builder
│   │   └── [id]/                   → /teacher/quizzes/[id]  — Quiz + results
│   │       └── edit/               → /teacher/quizzes/[id]/edit
│   ├── assignments/                → /teacher/assignments
│   │   ├── new/                    → /teacher/assignments/new
│   │   └── [id]/                   → /teacher/assignments/[id]
│   │       └── submissions/        → /teacher/assignments/[id]/submissions
│   ├── ai/
│   │   ├── quiz-gen/               → /teacher/ai/quiz-gen   — AI quiz generation
│   │   └── tutor/                  → /teacher/ai/tutor      — AI Tutor chat
│   └── content/                    → /teacher/content
│
├── (student)/                      ← Student layout (ST sidebar)
│   │   middleware: require ST role
│   ├── dashboard/                  → /student/dashboard     — My scores, upcoming
│   ├── quizzes/                    → /student/quizzes       — Available quizzes
│   │   └── [id]/                   → /student/quizzes/[id]
│   │       ├── attempt/            → /student/quizzes/[id]/attempt — Active quiz
│   │       └── result/             → /student/quizzes/[id]/result  — My result
│   ├── assignments/                → /student/assignments
│   │   └── [id]/                   → /student/assignments/[id]
│   │       └── submit/             → /student/assignments/[id]/submit
│   ├── ai/
│   │   ├── tutor/                  → /student/ai/tutor      — AI Tutor chat
│   │   └── summarize/             → /student/ai/summarize   — Summarizer
│   ├── performance/                → /student/performance   — My analytics
│   └── notifications/             → /student/notifications
│
└── api/                            ← Next.js API routes (thin proxies to FastAPI)
    └── auth/[...nextauth]/         — NextAuth.js session handling
```

---

## 6. Backend API Route Map (FastAPI Endpoints)

Base: `https://api.quizerai.com/api/v1`

```
/api/v1
│
├── /auth
│   ├── /admin
│   │   ├── POST   /login              — GA login → JWT pair
│   │   ├── POST   /refresh            — Refresh access token
│   │   └── POST   /logout             — Revoke token (Redis blacklist)
│   └── /school
│       ├── POST   /login              — SA/TE/ST login (role param)
│       ├── POST   /refresh
│       ├── POST   /logout
│       ├── POST   /forgot-password    — OTP to email
│       ├── POST   /reset-password     — Verify OTP + set new password
│       └── POST   /change-password    — Authenticated password change
│
├── /admin                             [GA ONLY]
│   ├── /institutions
│   │   ├── GET    /                   — List all (paginated, filterable)
│   │   ├── POST   /                   — Create/onboard institution
│   │   ├── GET    /{id}               — Institution detail
│   │   ├── PATCH  /{id}               — Update fields
│   │   ├── DELETE /{id}               — Soft delete
│   │   ├── POST   /{id}/verify        — Approve institution
│   │   ├── POST   /{id}/suspend       — Suspend
│   │   ├── POST   /{id}/activate      — Reactivate
│   │   ├── POST   /{id}/logo          — Upload logo (multipart)
│   │   └── GET    /{id}/stats         — Per-institution stats
│   ├── /users
│   │   ├── GET    /                   — All users across institutions
│   │   ├── GET    /{role}/{id}        — Specific user
│   │   ├── POST   /global-admin       — Create another GA
│   │   └── PATCH  /{role}/{id}/toggle-active
│   └── /analytics
│       ├── GET    /overview           — Total institutions, users, quizzes, AI usage
│       ├── GET    /growth             — Month-over-month growth
│       ├── GET    /ai-usage           — AI cost/usage per institution
│       └── GET    /quiz-stats         — Quiz completion rates platform-wide
│
├── /school                            [SA/TE/ST — scoped by school_id from JWT]
│   ├── /dashboard
│   │   ├── GET    /stats              — [SA] Counts: teachers, students, classrooms
│   │   ├── GET    /recent-activity    — [SA] Last 10 actions
│   │   ├── GET    /teacher-stats      — [TE] My classrooms, quizzes, submissions
│   │   └── GET    /student-stats      — [ST] My scores, upcoming quizzes
│   ├── /profile
│   │   ├── GET    /                   — [SA] Own profile
│   │   ├── PATCH  /                   — [SA] Update profile
│   │   ├── GET    /institution        — [SA] Institution details
│   │   └── PATCH  /institution        — [SA] Update institution info
│   ├── /teachers
│   │   ├── GET    /                   — [SA] List teachers
│   │   ├── POST   /                   — [SA] Create teacher (auto temp password + welcome email)
│   │   ├── GET    /{id}               — [SA] Teacher detail
│   │   ├── PATCH  /{id}               — [SA] Update
│   │   ├── DELETE /{id}               — [SA] Deactivate
│   │   ├── POST   /bulk-import        — [SA] CSV upload → bulk create
│   │   ├── GET    /{id}/classrooms    — [SA/TE] Teacher's classrooms
│   │   └── GET    /{id}/analytics     — [SA] Quiz/assignment activity
│   ├── /students
│   │   ├── GET    /                   — [SA/TE] List (filter by grade/classroom)
│   │   ├── POST   /                   — [SA] Create student
│   │   ├── GET    /{id}               — [SA/TE/ST] Profile
│   │   ├── PATCH  /{id}               — [SA/ST] Update
│   │   ├── DELETE /{id}               — [SA] Deactivate
│   │   ├── POST   /bulk-import        — [SA] CSV bulk import
│   │   ├── GET    /{id}/performance   — [SA/TE/ST] Quiz scores + AI usage
│   │   └── GET    /{id}/quiz-history  — [SA/TE/ST] All quiz attempts
│   ├── /classroom
│   │   ├── GET    /                   — [SA/TE] List classrooms
│   │   ├── POST   /                   — [SA] Create
│   │   ├── GET    /{id}               — Detail
│   │   ├── PATCH  /{id}               — [SA] Update
│   │   ├── DELETE /{id}               — [SA] Deactivate
│   │   ├── GET    /{id}/members       — List students + teachers
│   │   ├── POST   /{id}/members/students — Bulk enroll students
│   │   ├── POST   /{id}/members/teachers — Assign teachers
│   │   ├── DELETE /{id}/members/{member_id}
│   │   └── GET    /{id}/analytics     — Avg scores, completion rates
│   ├── /learn
│   │   ├── /subjects
│   │   │   ├── GET    /
│   │   │   ├── POST   /               — [SA] Create subject
│   │   │   ├── PATCH  /{id}
│   │   │   └── DELETE /{id}
│   │   └── /content
│   │       ├── GET    /               — List content (filter by subject)
│   │       ├── POST   /               — [TE] Upload (multipart → S3)
│   │       ├── GET    /{id}           — Get + signed S3 URL
│   │       └── DELETE /{id}
│   └── /quizes
│       ├── /quiz
│       │   ├── GET    /               — List (role-filtered)
│       │   ├── POST   /               — [TE] Create manual quiz
│       │   ├── GET    /{id}           — Detail (teachers see correct answers)
│       │   ├── PATCH  /{id}           — [TE] Update metadata
│       │   ├── DELETE /{id}           — [TE/SA] Delete draft
│       │   ├── POST   /{id}/publish   — [TE] Publish to classrooms
│       │   ├── POST   /{id}/close     — [TE] Close quiz
│       │   ├── POST   /{id}/questions — [TE] Add question
│       │   ├── PATCH  /{id}/questions/{qid}
│       │   ├── DELETE /{id}/questions/{qid}
│       │   ├── GET    /{id}/results   — [TE/SA] All student scores
│       │   └── GET    /{id}/leaderboard — Top 10
│       ├── /attempt
│       │   ├── POST   /{quiz_id}/start       — [ST] Start attempt
│       │   ├── POST   /{attempt_id}/answer   — [ST] Submit individual answer
│       │   ├── POST   /{attempt_id}/submit   — [ST] Final submit + auto-grade
│       │   ├── GET    /{attempt_id}/result   — Result with explanations
│       │   └── GET    /my-history            — [ST] All my attempts
│       └── /assignment
│           ├── GET    /               — List
│           ├── POST   /               — [TE] Create
│           ├── GET    /{id}           — Detail
│           ├── PATCH  /{id}
│           ├── POST   /{id}/publish
│           ├── POST   /{id}/submit    — [ST] File upload (multipart)
│           ├── GET    /{id}/submissions
│           ├── GET    /{id}/submissions/{sub_id}
│           └── PATCH  /{id}/submissions/{sub_id}/grade — [TE] Override grade
│
├── /ai                                [Stricter rate limit: 10/min. Feature flag required.]
│   ├── /tutor
│   │   ├── POST   /chat              — SSE stream (text/event-stream)
│   │   ├── GET    /sessions          — List recent sessions
│   │   ├── GET    /sessions/{id}     — Full session history
│   │   ├── DELETE /sessions/{id}     — Clear session
│   │   └── POST   /upload            — Upload PDF/image for context
│   ├── /quiz-gen
│   │   ├── POST   /generate          — Trigger Celery job → 202 + job_id
│   │   ├── GET    /job/{job_id}       — Poll status
│   │   ├── GET    /job/{job_id}/result
│   │   ├── POST   /job/{job_id}/accept — Save to quiz
│   │   └── POST   /job/{job_id}/regenerate
│   ├── /summarize
│   │   ├── POST   /document          — PDF upload → Celery job
│   │   ├── POST   /text              — Plain text → Celery job
│   │   ├── GET    /job/{job_id}
│   │   └── GET    /job/{job_id}/result
│   └── /assignment
│       ├── POST   /evaluate/{submission_id} — Trigger OCR+eval Celery job
│       ├── GET    /job/{job_id}
│       └── GET    /job/{job_id}/result
│
├── /notifications
│   ├── GET    /                      — My notifications (paginated)
│   ├── GET    /unread-count
│   ├── POST   /{id}/read
│   ├── POST   /read-all
│   └── POST   /send                  — [SA/TE] Send to classroom
│
└── /system
    ├── GET    /health                — Liveness check (no auth)
    ├── GET    /ready                 — Readiness: DB + Redis (no auth)
    └── GET    /metrics               — Prometheus scrape [GA only]
```

---

## 7. Database Schema & Relationships

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DATABASE ENTITY RELATIONSHIPS                      │
│                                                                      │
│  ┌───────────────┐                                                   │
│  │  global_admins│  (platform staff only, no school_id)              │
│  └───────────────┘                                                   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  institutions (id, name, slug, type, email, status, plan)   │    │
│  └──┬────────────────────────────────────────────────────────┬─┘    │
│     │ 1:many                                          1:many  │      │
│     ├──────────────────────────────────┐                      │      │
│     │              │                  │                       │      │
│  ┌──▼──────────┐ ┌─▼──────────┐ ┌────▼────────┐           ┌──▼───┐ │
│  │school_admins│ │  teachers  │ │   students  │           │quizzes│ │
│  │ (id,        │ │ (id,       │ │ (id,        │           │(id,  │ │
│  │  institution│ │  institution│ │  institution│           │ inst,│ │
│  │  _id, ...)  │ │  _id, ...) │ │  _id, ...)  │           │ ...)  │ │
│  └─────────────┘ └────────────┘ └──────┬──────┘           └──┬───┘ │
│                        │               │                      │     │
│                   ┌────▼───────────────▼──────────┐     ┌────▼───┐ │
│                   │        classrooms              │     │quiz_   │ │
│                   │  (id, institution_id, grade)   │     │question│ │
│                   └────────────┬──────────────────┘     └────┬───┘ │
│                                │                             │      │
│                   ┌────────────▼────────────┐         ┌─────▼────┐ │
│                   │   classroom_members     │         │quiz_     │ │
│                   │ (classroom_id,          │         │attempts  │ │
│                   │  member_type,           │         └──────────┘ │
│                   │  member_id)             │                       │
│                   └─────────────────────────┘                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ assignments → assignment_submissions (file, ai_score, ...)   │   │
│  │ ai_sessions  (tutor chat history, last 5 sessions per student)│   │
│  │ notifications (in-app + email + push per recipient)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Constraints
- `UNIQUE (quiz_id, student_id)` on `quiz_attempts` — one attempt per student per quiz
- `UNIQUE (assignment_id, student_id)` on `assignment_submissions`
- `UNIQUE (classroom_id, member_type, member_id)` on `classroom_members`
- All JSON columns (subjects, messages, feature_flags, ai_improvements) stored as MySQL JSON type
- All timestamps use `DATETIME(6)` (microsecond precision) with timezone awareness

---

## 8. Authentication & JWT Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION FLOW                             │
│                                                                      │
│  1. LOGIN                                                            │
│  ────────                                                            │
│  Client → POST /auth/school/login                                   │
│           { email, password, role: "teacher" }                       │
│                                                                      │
│  Backend:                                                            │
│   a. Look up teacher by email in DB                                  │
│   b. bcrypt.verify(password, teacher.password_hash)                  │
│   c. Build JWT payload:                                              │
│      { sub: "42", role: "teacher",                                  │
│        school_id: 5, name: "Ramesh Kumar" }                         │
│   d. Sign with RS256 PRIVATE key → access_token (1hr TTL)           │
│   e. Sign minimal payload → refresh_token (30 day TTL)              │
│                                                                      │
│  Response: { access_token, refresh_token, user }                    │
│                                                                      │
│  2. AUTHENTICATED REQUEST                                            │
│  ─────────────────────────                                           │
│  Client → GET /school/teachers                                       │
│           Authorization: Bearer eyJhbG...                           │
│                                                                      │
│  SchoolContextMiddleware:                                            │
│   a. Extract token from Authorization header                        │
│   b. Check Redis blacklist (is this token revoked?) → 401 if yes    │
│   c. jwt.decode(token, RS256 PUBLIC key)                            │
│   d. Attach to request.state:                                       │
│      { user_id: 42, role: "teacher", school_id: 5 }                │
│   e. RBAC check: /school/ paths require school role                 │
│                                                                      │
│  3. TOKEN REFRESH                                                    │
│  ────────────────                                                    │
│  Client → POST /auth/school/refresh                                  │
│           { refresh_token: "eyJ..." }                                │
│                                                                      │
│  Backend: verify refresh_token → issue new access_token             │
│                                                                      │
│  4. LOGOUT                                                           │
│  ─────────                                                           │
│  Client → POST /auth/school/logout                                   │
│  Backend: redis.setex(f"blacklist:{token}", ttl, "1")               │
│           → token is dead even before its exp                       │
│                                                                      │
│  KEY RULE: school_id is ALWAYS from JWT, NEVER from request body    │
└─────────────────────────────────────────────────────────────────────┘
```

### JWT Payload by Role

```python
# Global Admin
{ "sub": "1", "role": "global_admin", "school_id": None }

# School Admin
{ "sub": "10", "role": "school_admin", "school_id": 5 }

# Teacher
{ "sub": "42", "role": "teacher", "school_id": 5 }

# Student
{ "sub": "301", "role": "student", "school_id": 5 }
```

---

## 9. Request Lifecycle (Middleware Chain)

Every request goes through this exact sequence:

```
Incoming HTTP Request
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. RequestIDMiddleware                                          │
│    → X-Request-ID from header OR generate uuid4()              │
│    → attach to request.state.request_id                        │
│    → echo back in response header                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SchoolContextMiddleware                                      │
│    IF path in PUBLIC_PATHS → skip                               │
│    ELSE:                                                        │
│      a. Read Authorization: Bearer <token>                     │
│      b. Check Redis blacklist                                   │
│      c. Decode JWT (RS256)                                      │
│      d. request.state.{user_id, role, school_id, token}        │
│      e. RBAC: /admin/* requires global_admin                   │
│             /school/* requires school role                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RateLimitMiddleware                                          │
│    key = f"ratelimit:{user_id}:{'ai' if /ai/* else 'general'}" │
│    AI paths: 10 req/min                                         │
│    General: 60 req/min                                          │
│    Uses Redis INCR + EXPIRE (sliding window)                   │
│    → 429 with Retry-After: 60 header if exceeded               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LoggingMiddleware                                            │
│    → log request_started: { request_id, method, path,          │
│                              user_id, school_id, ip }          │
│    → call_next(request)                                         │
│    → log request_completed: { status_code, duration_ms }       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Route Handler                                                   │
│  → Pydantic validates request body → 422 if invalid            │
│  → Depends(get_db) → AsyncSession from pool                    │
│  → Depends(require_teacher) → checks role from state           │
│  → calls service.method(db, school_id, ...)                    │
│  → returns Pydantic response model (serialized JSON)           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
                   Outgoing Response
```

---

## 10. AI Feature Pipelines

### 10.1 AI Tutor (Synchronous SSE Stream)

```
Student sends chat message
        │
        ▼
POST /ai/tutor/chat
  { agent, message, session_id, input_type, file_key }
        │
        ├─ input_type = "voice"  → Custom Whisper STT → text
        ├─ input_type = "image"  → AWS Textract OCR → text
        ├─ input_type = "pdf"    → AWS Textract OCR → text
        └─ input_type = "text"   → use as-is
        │
        ▼
route_agent(message, explicit_agent)
  → keyword routing: "solve"/"integral" → maths
                     "explain"/"what is" → explanation
                     "roadmap"           → roadmap
                     default             → explanation
        │
        ▼
get_session_context(student_id)
  → fetch last 5 ai_sessions from DB
  → flatten to 20 messages context window
        │
        ▼
Agent dispatch:
  "maths"       → OpenAI GPT-4o (best math reasoning)
  "explanation" → Claude Haiku (cheap, fast)
  "mentor"      → Claude Sonnet
  "roadmap"     → Claude Opus (deep thinking)
  "system_qa"   → Claude Haiku + Pinecone RAG
        │
        ▼
SSE Stream to client:
  event: token\ndata: {"token": "The "}\n\n
  event: token\ndata: {"token": "answer "}\n\n
  ...
  event: done\ndata: {"full_response": "...", "session_id": "abc"}\n\n
        │
        ▼
Save session to ai_sessions table (async, after stream ends)
Log interaction to student analytics
```

### 10.2 AI Quiz Generation (Async Celery)

```
Teacher triggers POST /ai/quiz-gen/generate
  { subject, topic, grade, board, question_types,
    difficulty_distribution, total_questions, use_pyq }
        │
        ▼
Return 202: { job_id: "quiz-gen-abc", status: "queued" }
        │
        ▼
Celery task: quiz_gen_task (queue: ai_heavy)
        │
        ├─ [if use_pyq=True]
        │   RAG Query → Pinecone
        │   Namespace: "{board}-{difficulty}" (e.g. "cbse-hard")
        │   embed(topic + grade + difficulty) → top-5 PYQ examples
        │
        ▼
Parallel generation (3 agents):
  Easy Agent   → {easy_count} questions
  Medium Agent → {medium_count} questions
  Hard Agent   → {hard_count} questions
        │
        ▼
Pydantic validate each question:
  MCQ: has 4 options + correct_answer ∈ {A,B,C,D}
  AR:  has assertion + reason + correct_answer
  OneWord/OneLiner: has question_text + correct_answer
        │
        ▼
Store in Redis: key="ai:job:{job_id}", TTL=1hr
        │
        ▼
Teacher polls GET /ai/quiz-gen/job/{job_id}
  { status: "completed", progress: 100 }
Teacher reviews questions in UI
Teacher POSTs /accept → saves to quiz_questions table
```

### 10.3 Summarization (Async Celery)

```
Input: PDF file or plain text
        │
        ▼
Celery task: summarize_task (queue: ai_light)
        │
        ├─ PDF → extract text (pypdf, fallback to Textract for scanned)
        │
        ▼
Pass 1 — Initial Summary:
  Claude: "Summarize in {format}" (8000 token budget)
        │
        ▼
Pass 2..N — Refine/Recheck (default 2 passes):
  Claude: "Review for accuracy and completeness. Improve."
        │
        ▼
Structure Pass:
  Claude: "Format as: {title, key_points[], sections[]}"
        │
        ▼
Store result in Redis (job_id → JSON)
Client polls → receives structured summary
```

### 10.4 Assignment Evaluation (Async Celery)

```
Student submits PDF/image via POST /school/quizes/assignment/{id}/submit
  → stored in S3, metadata in assignment_submissions (status=submitted)
        │
Teacher triggers POST /ai/assignment/evaluate/{submission_id}
  { rubric: "...", max_score: 25 }
        │
        ▼
Celery task: assignment_eval_task (queue: ai_heavy)
        │
        ▼
Step 1: AWS Textract
  → start_document_text_detection(S3Object)
  → poll until SUCCEEDED
  → extract all text blocks
        │
        ▼
Step 2: Text cleaning
  → remove OCR noise, normalize whitespace
        │
        ▼
Step 3: Claude Evaluation
  System: "Indian school teacher, be fair and constructive"
  User:   assignment + rubric + extracted text → JSON response
  Returns: { score, remarks, improvements[], strengths[] }
        │
        ▼
Step 4: Update assignment_submissions
  { ai_score, ai_remarks, ai_improvements, status="ai_evaluated" }
        │
        ▼
Step 5: Notify teacher + student (notification_task → email + in_app)
```

---

## 11. Tech Stack — What, Why & Where

| Technology | Where Used | Why This Choice |
|-----------|-----------|-----------------|
| **FastAPI** | Backend web framework | Native async, auto OpenAPI docs, Pydantic v2 integration |
| **SQLAlchemy 2.0 async** | ORM | Type-safe `Mapped` columns, true async sessions |
| **MySQL 8** | Primary database | ACID, JSON columns, proven for SaaS multi-tenancy |
| **Alembic** | DB migrations | The only way to change schema. Never `ALTER TABLE` manually. |
| **Redis** | Cache + rate limit + job results + token blacklist | Single fast KV store for all ephemeral data |
| **Celery** | Async task queue | AI jobs never block HTTP thread. Scale workers independently. |
| **JWT RS256** | Auth tokens | Asymmetric — any replica can verify with public key, only auth service signs |
| **bcrypt** | Password hashing | Industry standard, adaptive cost factor |
| **AWS S3** | File storage (logos, PDFs, submissions) | Scalable object storage, pre-signed URLs for direct client download |
| **AWS Textract** | OCR for handwritten assignments | Best-in-class for Indian handwriting + document layout |
| **OpenAI GPT-4o** | Maths agent in AI Tutor | Superior multi-step reasoning and tool use |
| **Anthropic Claude** | Explanation, Mentor, Roadmap, Eval, Summarize | Cost-efficient for high-volume, high-quality responses |
| **Custom Whisper** | Voice input STT | Fine-tuned for Indian accent and educational vocabulary |
| **Pinecone** | Vector DB for RAG (PYQ corpus) | Managed, fast ANN search, namespace support for board/level segmentation |
| **Prometheus + Grafana** | Metrics & dashboards | Industry standard, integrates with K8s HPA custom metrics |
| **Structlog → ELK** | Structured logging | JSON logs searchable in Kibana; `request_id` correlation across services |
| **Docker + Compose** | Local dev | One `docker-compose up` = full stack with parity to prod |
| **Kubernetes (EKS)** | Production orchestration | HPA for zero-downtime scale, rolling deploys, resource isolation |
| **GitHub Actions** | CI/CD | Native to GitHub, matrix builds, secrets management |
| **Next.js 14** | Frontend framework | App Router, SSR, API routes, TypeScript first-class |
| **Tailwind CSS** | Frontend styling | Utility-first, fast iteration, consistent design tokens |
| **Zustand** | Frontend state | Lightweight, no boilerplate, works with App Router |

---

## 12. Folder Structures (Backend + Frontend)

### Backend (`quizerai-backend/`)

```
app/
├── core/               → Config (Settings), security (JWT/bcrypt), dependencies, exceptions
├── database/           → AsyncEngine, AsyncSession, Base, TimestampMixin, Alembic
├── middleware/         → RequestID, SchoolContext, RateLimit, Logging
├── models/             → SQLAlchemy ORM models (one file per domain entity)
├── schemas/            → Pydantic v2 request/response models
├── routers/            → FastAPI APIRouter (thin handlers — call service, return response)
│   ├── auth/           → Global admin auth + school auth
│   ├── admin/          → Institution CRUD, user management, platform analytics
│   ├── school/         → Dashboard, teachers, students, classroom, learn, quizes
│   ├── ai/             → Tutor, quiz-gen, summarize, assignment-eval
│   └── system/         → Health, metrics, notifications
├── services/           → Pure business logic (no FastAPI imports)
│   ├── admin/          → InstitutionService, GlobalUserService
│   ├── school/         → TeacherService, StudentService, ClassroomService, QuizService
│   ├── ai/             → TutorService, QuizGenService, SummarizeService, EvalService
│   └── notification/   → NotificationService
├── tasks/              → Celery app + task files (quiz_gen, assignment_eval, summarize, notify)
├── cache/              → Redis client, centralized CacheKey constants, decorators
└── utils/              → S3, OCR (Textract), RAG (Pinecone), pagination, logger
```

**Pattern rule**: Route → Service → DB/Cache/Task. Never skip layers.

### Frontend (`quizerai-frontend/`)

```
app/
├── (auth)/             → Login pages, no sidebar layout
├── (global-admin)/     → GA pages, GA sidebar layout
├── (school-admin)/     → SA pages, SA sidebar layout
├── (teacher)/          → Teacher pages, TE sidebar layout
├── (student)/          → Student pages, ST sidebar layout
├── layout.tsx          → Root layout (fonts, providers)
└── page.tsx            → Redirect to appropriate dashboard by role

components/
├── ui/                 → Primitive components (Button, Input, Modal, Table, Badge)
├── layout/             → Sidebar, Header, Breadcrumb, PageWrapper
├── forms/              → QuizBuilder, InstitutionForm, BulkImportForm
├── quiz/               → QuizAttempt, QuestionCard, Timer, Leaderboard
├── ai/                 → ChatInterface, StreamingMessage, AgentSelector, JobProgress
└── charts/             → PerformanceTrend, ScoreDistribution, AIUsageChart

lib/
├── api.ts              → Axios instance + interceptors (token refresh)
├── auth.ts             → Auth helpers + token storage
└── store/              → Zustand stores (auth, notifications)

hooks/
├── useAuth.ts          → Role check, redirect logic
├── useSSE.ts           → Server-Sent Events hook for AI Tutor
├── usePolling.ts       → Job status polling (AI quiz gen, summarize, eval)
└── useNotifications.ts → Unread count, mark-read
```

---

## 13. Development Setup

```bash
# Prerequisites: Docker, Docker Compose, Python 3.12, Node.js 20

# ── BACKEND ──────────────────────────────────────────────────────
git clone https://github.com/shashankbindal/QuizerAi_backend
cd QuizerAi_backend
cp .env.example .env          # Fill in secrets
docker-compose up -d          # Starts: FastAPI + MySQL + Redis + Celery + Flower

# Access points:
# API:    http://localhost:8000/api/v1
# Docs:   http://localhost:8000/api/docs   (Swagger UI)
# Flower: http://localhost:5555            (Celery task monitor)

# Run migrations
docker exec -it quizerai-api alembic upgrade head

# Run tests
docker exec -it quizerai-api pytest tests/ -v

# ── FRONTEND ─────────────────────────────────────────────────────
git clone https://github.com/shashankbindal/QuizerAi_frontend
cd QuizerAi_frontend
cp .env.local.example .env.local   # Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                         # http://localhost:3000

# ── COMMON WORKFLOW ───────────────────────────────────────────────
# 1. Branch from main: git checkout -b feature/ISSUE-BE-013-quiz-crud
# 2. Write code + tests
# 3. Pre-commit hooks run: black, isort, ruff (backend) / eslint, prettier (frontend)
# 4. Push → PR → CI runs → review → merge
```

---

## 14. Key Engineering Rules

These are non-negotiable. Violating them causes bugs, security holes, or data leaks.

| # | Rule | Why |
|---|------|-----|
| 1 | `school_id` always from `current_user["school_id"]` (JWT) — never request body | Prevents cross-tenant data access |
| 2 | Every DB query for school-scoped data: `.where(Model.institution_id == school_id)` | Tenant isolation |
| 3 | No business logic in route handlers — routes call services only | Testability, separation of concerns |
| 4 | No blocking I/O anywhere — all DB, Redis, HTTP, S3 calls are `async/await` | Throughput at scale |
| 5 | All AI jobs via Celery — never call AI APIs in HTTP request cycle for long jobs | HTTP timeout, UX responsiveness |
| 6 | Alembic for every schema change — never `ALTER TABLE` manually | Migration history, rollback capability |
| 7 | Feature flags in Redis/DB — new AI features go behind a flag per institution | Safe rollout, plan enforcement |
| 8 | Every endpoint has integration tests | Correctness, regression prevention |
| 9 | Structured logging on every request: `request_id`, `school_id`, `user_id`, `duration_ms` | Debuggability in prod |
| 10 | Students never see `correct_answer` in response schemas | Quiz integrity |
| 11 | File uploads: validate MIME type (PDF/image only) + max 10MB | Security, storage costs |
| 12 | New env vars must be added to `.env.example` | Onboarding, deployment |
| 13 | Pre-commit hooks must pass before push | Code quality consistency |
| 14 | Rate limit headers included in all 429 responses | Client retry logic |

---

## 15. Sprint Roadmap

```
SPRINT 1 — Foundation (Week 1–2)
  Backend:  Project scaffold, Docker, DB+Alembic, JWT auth, Middleware, Redis, Exceptions
  Frontend: Next.js setup, design system, API client, auth context, route guards, layouts

SPRINT 2 — Auth & Institution (Week 3–4)
  Backend:  Auth routes (login/refresh/logout/forgot-password), Institution CRUD
  Frontend: Login pages (all roles), Forgot/Reset password, Global Admin dashboard

SPRINT 3 — School Core (Week 5–6)
  Backend:  Teacher CRUD + bulk import, Student CRUD + bulk import, Classroom enrollment
  Frontend: School Admin dashboard, Teacher/Student management, Classroom UI

SPRINT 4 — Learn + Subjects (Week 7)
  Backend:  Subject CRUD, Learning content upload (S3), School dashboard stats
  Frontend: Subject management, Content upload/viewer

SPRINT 5 — Quiz Engine (Week 8–9)
  Backend:  Quiz CRUD, Question management, Publish/close flow, Attempt + auto-grade
  Frontend: Quiz builder (all 4 question types), Student attempt UI, Results + leaderboard

SPRINT 6 — Assignments (Week 10)
  Backend:  Assignment CRUD, File submission (S3), AI evaluation trigger, Teacher grading
  Frontend: Assignment creation, Student submission (file upload), Grade display

SPRINT 7 — AI Features (Week 11–13)
  Backend:  Celery setup, AI Tutor SSE, Quiz Gen RAG, Summarization, Assignment Eval
  Frontend: AI Tutor chat (SSE), Quiz Gen job UI, Summarizer upload, Eval result display

SPRINT 8 — Notifications + Analytics (Week 14)
  Backend:  Notification system, Email delivery (Celery), Unread count cache
  Frontend: Notification bell + list, Student performance charts, Teacher analytics

SPRINT 9 — Production Hardening (Week 15–16)
  Backend:  Prometheus metrics, ELK logging, Integration test suite (80+ tests)
  Frontend: E2E tests (Playwright), Accessibility audit, Dark mode, Responsive design
  Infra:    Kubernetes manifests + HPA, GitHub Actions CI/CD
```

---

## 16. Glossary

| Term | Meaning |
|------|---------|
| **GA** | Global Admin — platform staff with access to all institutions |
| **SA** | School Admin — manages a single institution |
| **TE** | Teacher — manages classrooms, quizzes, assignments |
| **ST** | Student — takes quizzes, submits assignments, uses AI |
| **school_id** | The `institution_id` value that scopes all data to one tenant |
| **JWT** | JSON Web Token — stateless auth token, signed with RS256 |
| **RS256** | RSA Signature with SHA-256 — asymmetric JWT algorithm |
| **Celery** | Python distributed task queue — runs async/background jobs |
| **RAG** | Retrieval-Augmented Generation — fetch relevant docs from Pinecone before LLM call |
| **PYQ** | Previous Year Questions — exam paper corpus used for AI quiz generation |
| **SSE** | Server-Sent Events — one-way stream from server to client (used for AI Tutor) |
| **HPA** | Horizontal Pod Autoscaler — Kubernetes feature to auto-scale pod count |
| **Alembic** | Python DB migration tool — tracks schema changes as versioned scripts |
| **Pydantic v2** | Data validation library — validates request/response schemas in FastAPI |
| **Structlog** | Structured logging library — outputs JSON logs with key-value pairs |
| **ELK** | Elasticsearch + Logstash + Kibana — log aggregation and search stack |
| **Pinecone** | Managed vector database — stores embeddings for semantic search |
| **Textract** | AWS OCR service — extracts text from PDFs and images |
| **Whisper** | OpenAI's speech-to-text model — converts voice to text for AI Tutor |
| **Feature flag** | Per-institution toggle stored in `institutions.feature_flags` JSON column |
| **Slug** | URL-safe version of institution name, e.g. `delhi-public-school-rohini` |
| **Pool pre-ping** | SQLAlchemy checks connection health before use (prevents stale connection errors) |
| **Token blacklist** | Redis key `blacklist:{token}` set on logout — invalidates token before expiry |
