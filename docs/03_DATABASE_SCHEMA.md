# QuizerAI — Database Schema

> **DB**: MySQL 8.0+ | ORM: SQLAlchemy 2.0 async | Migrations: Alembic
> All tables use `InnoDB`, `utf8mb4`, `CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`

---

## Entity Relationship Overview

```
institutions
    │
    ├──< school_admins          (1 institution → many admins)
    ├──< teachers               (1 institution → many teachers)
    ├──< students               (1 institution → many students)
    ├──< classrooms             (1 institution → many classrooms)
    │         │
    │         ├──< classroom_members    (many classrooms ↔ many students/teachers)
    │         └──< subjects             (1 classroom → many subjects)
    │
    ├──< quizzes                (1 institution → many quizzes)
    │         │
    │         ├──< quiz_questions      (1 quiz → many questions)
    │         └──< quiz_attempts       (1 quiz → many student attempts)
    │                   └──< quiz_attempt_answers
    │
    ├──< assignments            (1 institution → many assignments)
    │         └──< assignment_submissions
    │
    ├──< ai_sessions            (AI Tutor conversation history per student)
    └──< notifications
```

---

## DDL — All Tables

### `institutions`

```sql
CREATE TABLE institutions (
    id                      INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name                    VARCHAR(255)    NOT NULL,
    slug                    VARCHAR(100)    NOT NULL UNIQUE,
    institution_type        ENUM('school','coaching_institute','college',
                                 'university','training_center') NOT NULL,
    affiliation_board       ENUM('CBSE','ICSE','STATE_BOARD','IB','IGCSE','OTHER'),
    registration_number     VARCHAR(100),
    udise_code              VARCHAR(20)     UNIQUE,
    gst_number              VARCHAR(20),
    year_established        SMALLINT UNSIGNED,
    official_website        VARCHAR(255),
    logo_s3_key             VARCHAR(512),
    branding_assets_key     VARCHAR(512),
    principal_name          VARCHAR(255)    NOT NULL,
    founder_trustee_name    VARCHAR(255),
    admin_coordinator_name  VARCHAR(255),
    official_email          VARCHAR(255)    NOT NULL UNIQUE,
    secondary_email         VARCHAR(255),
    mobile_number           VARCHAR(15)     NOT NULL,
    secondary_mobile        VARCHAR(15),
    office_landline         VARCHAR(20),
    whatsapp_number         VARCHAR(15),
    address_line1           VARCHAR(500),
    address_line2           VARCHAR(500),
    city                    VARCHAR(100),
    state                   VARCHAR(100),
    pincode                 VARCHAR(10),
    country                 VARCHAR(100)    NOT NULL DEFAULT 'India',
    status                  ENUM('pending','active','suspended','inactive')
                                            NOT NULL DEFAULT 'pending',
    subscription_plan       ENUM('free','basic','pro','enterprise')
                                            NOT NULL DEFAULT 'free',
    subscription_expires_at DATE,
    is_verified             TINYINT(1)      NOT NULL DEFAULT 0,
    feature_flags           JSON,
    created_at              DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                            ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_institutions_status (status),
    INDEX ix_institutions_city_state (city, state),
    INDEX ix_institutions_type (institution_type)
);
```

### `global_admins`

```sql
CREATE TABLE global_admins (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name            VARCHAR(255)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    last_login_at   DATETIME(6),
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id)
);
```

### `school_admins`

```sql
CREATE TABLE school_admins (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    name            VARCHAR(255)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    mobile_number   VARCHAR(15),
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    last_login_at   DATETIME(6),
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_school_admins_institution (institution_id),
    CONSTRAINT fk_school_admins_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `teachers`

```sql
CREATE TABLE teachers (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    name            VARCHAR(255)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    mobile_number   VARCHAR(15),
    employee_id     VARCHAR(50),
    subjects        JSON,                    -- ["Mathematics","Physics"]
    qualification   VARCHAR(255),
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    last_login_at   DATETIME(6),
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_teachers_institution (institution_id),
    CONSTRAINT fk_teachers_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `students`

```sql
CREATE TABLE students (
    id                  INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id      INT UNSIGNED    NOT NULL,
    name                VARCHAR(255)    NOT NULL,
    email               VARCHAR(255)    NOT NULL UNIQUE,
    password_hash       VARCHAR(255)    NOT NULL,
    roll_number         VARCHAR(50),
    date_of_birth       DATE,
    grade               VARCHAR(20),             -- "10", "12", "B.Tech Year 2"
    parent_mobile       VARCHAR(15),
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    last_login_at       DATETIME(6),
    created_at          DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at          DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_students_institution (institution_id),
    INDEX ix_students_grade (institution_id, grade),
    CONSTRAINT fk_students_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `classrooms`

```sql
CREATE TABLE classrooms (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    name            VARCHAR(255)    NOT NULL,    -- "Class 10 - A", "JEE Batch 2025"
    grade           VARCHAR(20),
    section         VARCHAR(10),
    academic_year   VARCHAR(10)     NOT NULL,    -- "2025-26"
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_classrooms_institution (institution_id),
    CONSTRAINT fk_classrooms_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `classroom_members`

```sql
CREATE TABLE classroom_members (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    classroom_id    INT UNSIGNED    NOT NULL,
    member_type     ENUM('teacher','student') NOT NULL,
    member_id       INT UNSIGNED    NOT NULL,    -- FK to teacher.id or student.id
    joined_at       DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE ix_unique_member (classroom_id, member_type, member_id),
    INDEX ix_classroom_members_classroom (classroom_id),
    CONSTRAINT fk_cm_classroom
        FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
);
```

### `subjects`

```sql
CREATE TABLE subjects (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    classroom_id    INT UNSIGNED,                -- NULL = institution-wide subject
    name            VARCHAR(255)    NOT NULL,
    code            VARCHAR(50),
    board           VARCHAR(50),
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_subjects_institution (institution_id),
    CONSTRAINT fk_subjects_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `quizzes`

```sql
CREATE TABLE quizzes (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    classroom_id    INT UNSIGNED,
    subject_id      INT UNSIGNED,
    teacher_id      INT UNSIGNED    NOT NULL,
    title           VARCHAR(255)    NOT NULL,
    description     TEXT,
    quiz_type       ENUM('manual','ai_generated') NOT NULL DEFAULT 'manual',
    status          ENUM('draft','published','closed') NOT NULL DEFAULT 'draft',
    difficulty      ENUM('easy','medium','hard','mixed') NOT NULL DEFAULT 'mixed',
    time_limit_min  SMALLINT UNSIGNED,           -- NULL = no time limit
    total_marks     SMALLINT UNSIGNED,
    passing_marks   SMALLINT UNSIGNED,
    starts_at       DATETIME(6),
    ends_at         DATETIME(6),
    -- AI Gen metadata
    ai_prompt       TEXT,                        -- what prompt was used to generate
    ai_board        VARCHAR(50),                 -- CBSE / JEE / NEET etc.
    ai_job_id       VARCHAR(100),               -- Celery task id
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_quizzes_institution (institution_id),
    INDEX ix_quizzes_classroom (classroom_id),
    INDEX ix_quizzes_status (status),
    CONSTRAINT fk_quizzes_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `quiz_questions`

```sql
CREATE TABLE quiz_questions (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    quiz_id         INT UNSIGNED    NOT NULL,
    question_type   ENUM('mcq','assertion_reason','one_word','one_liner') NOT NULL,
    difficulty      ENUM('easy','medium','hard') NOT NULL,
    question_text   TEXT            NOT NULL,
    option_a        TEXT,
    option_b        TEXT,
    option_c        TEXT,
    option_d        TEXT,
    correct_answer  VARCHAR(500)    NOT NULL,
    explanation     TEXT,
    marks           TINYINT UNSIGNED NOT NULL DEFAULT 1,
    order_index     SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    image_s3_key    VARCHAR(512),                -- if question has image
    source_pyq      VARCHAR(100),               -- "CBSE 2022 Q5"
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_quiz_questions_quiz (quiz_id),
    CONSTRAINT fk_qq_quiz
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);
```

### `quiz_attempts`

```sql
CREATE TABLE quiz_attempts (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    quiz_id         INT UNSIGNED    NOT NULL,
    student_id      INT UNSIGNED    NOT NULL,
    institution_id  INT UNSIGNED    NOT NULL,
    status          ENUM('in_progress','submitted','evaluated') NOT NULL DEFAULT 'in_progress',
    score           DECIMAL(5,2),
    total_marks     SMALLINT UNSIGNED,
    percentage      DECIMAL(5,2),
    started_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    submitted_at    DATETIME(6),
    time_taken_sec  INT UNSIGNED,
    PRIMARY KEY (id),
    UNIQUE ix_unique_attempt (quiz_id, student_id),   -- one attempt per student per quiz
    INDEX ix_attempts_student (student_id),
    INDEX ix_attempts_institution (institution_id),
    CONSTRAINT fk_attempt_quiz
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
    CONSTRAINT fk_attempt_student
        FOREIGN KEY (student_id) REFERENCES students(id)
);
```

### `quiz_attempt_answers`

```sql
CREATE TABLE quiz_attempt_answers (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    attempt_id      INT UNSIGNED    NOT NULL,
    question_id     INT UNSIGNED    NOT NULL,
    given_answer    TEXT,
    is_correct      TINYINT(1),
    marks_awarded   DECIMAL(4,2)    DEFAULT 0,
    PRIMARY KEY (id),
    INDEX ix_qaa_attempt (attempt_id),
    CONSTRAINT fk_qaa_attempt
        FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
);
```

### `assignments`

```sql
CREATE TABLE assignments (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    classroom_id    INT UNSIGNED    NOT NULL,
    teacher_id      INT UNSIGNED    NOT NULL,
    subject_id      INT UNSIGNED,
    title           VARCHAR(255)    NOT NULL,
    description     TEXT,
    instructions    TEXT,
    total_marks     SMALLINT UNSIGNED,
    due_date        DATETIME(6),
    allow_late      TINYINT(1)      NOT NULL DEFAULT 0,
    status          ENUM('draft','published','closed') NOT NULL DEFAULT 'draft',
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_assignments_institution (institution_id),
    INDEX ix_assignments_classroom (classroom_id),
    CONSTRAINT fk_assignments_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

### `assignment_submissions`

```sql
CREATE TABLE assignment_submissions (
    id                  INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    assignment_id       INT UNSIGNED    NOT NULL,
    student_id          INT UNSIGNED    NOT NULL,
    institution_id      INT UNSIGNED    NOT NULL,
    file_s3_key         VARCHAR(512),            -- uploaded PDF/image
    text_content        LONGTEXT,               -- OCR extracted text
    status              ENUM('submitted','ocr_processing','ai_evaluated','teacher_reviewed')
                                                NOT NULL DEFAULT 'submitted',
    -- AI Evaluation
    ai_score            DECIMAL(5,2),
    ai_remarks          TEXT,
    ai_improvements     JSON,                   -- ["Improve conclusion", "Add examples"]
    ai_job_id           VARCHAR(100),
    -- Teacher Override
    teacher_score       DECIMAL(5,2),
    teacher_feedback    TEXT,
    is_late             TINYINT(1)      NOT NULL DEFAULT 0,
    submitted_at        DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    evaluated_at        DATETIME(6),
    PRIMARY KEY (id),
    UNIQUE ix_unique_submission (assignment_id, student_id),
    INDEX ix_submissions_assignment (assignment_id),
    INDEX ix_submissions_student (student_id),
    CONSTRAINT fk_sub_assignment
        FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);
```

### `ai_sessions`

```sql
CREATE TABLE ai_sessions (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    student_id      INT UNSIGNED    NOT NULL,
    session_type    ENUM('tutor','summarize') NOT NULL DEFAULT 'tutor',
    agent_used      VARCHAR(50),                -- 'maths','explanation','mentor','roadmap','system_qa'
    messages        JSON            NOT NULL,   -- [{role, content, timestamp}] last 5 lessons
    input_type      ENUM('text','image','pdf','voice') DEFAULT 'text',
    input_s3_key    VARCHAR(512),
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_ai_sessions_student (student_id, session_type),
    INDEX ix_ai_sessions_institution (institution_id),
    CONSTRAINT fk_ai_session_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
```

### `notifications`

```sql
CREATE TABLE notifications (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    institution_id  INT UNSIGNED    NOT NULL,
    recipient_type  ENUM('school_admin','teacher','student','all') NOT NULL,
    recipient_id    INT UNSIGNED,               -- NULL if recipient_type='all'
    title           VARCHAR(255)    NOT NULL,
    body            TEXT            NOT NULL,
    notif_type      ENUM('quiz_assigned','assignment_due','result_published',
                         'system','announcement') NOT NULL,
    channel         SET('in_app','email','push') NOT NULL DEFAULT 'in_app',
    is_read         TINYINT(1)      NOT NULL DEFAULT 0,
    sent_at         DATETIME(6),
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX ix_notif_recipient (institution_id, recipient_type, recipient_id),
    INDEX ix_notif_unread (recipient_id, is_read),
    CONSTRAINT fk_notif_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
```

---

## Indexing Strategy

| Table | Index | Reason |
|-------|-------|--------|
| all scoped tables | `institution_id` | Every query filters by tenant |
| `students` | `(institution_id, grade)` | Grade-level analytics |
| `quiz_attempts` | `(student_id)` | Student result history |
| `quiz_attempts` | `(institution_id)` | School-wide analytics |
| `notifications` | `(recipient_id, is_read)` | Unread notification count |
| `ai_sessions` | `(student_id, session_type)` | Fetch last 5 sessions |

---

## Alembic Setup

```bash
# Generate new migration after model changes
alembic revision --autogenerate -m "add institution table"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

`alembic.ini`:
```ini
[alembic]
script_location = app/database/migrations
sqlalchemy.url = %(DATABASE_URL)s
```
