# QuizerAI — Institution Model

> **File**: `app/models/institution.py` + `app/schemas/institution.py`
> This is the **root tenant entity**. Everything hangs off this.

---

## Institution Data Fields (from onboarding requirements)

### Section A — Institution Basic Information
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Institution Name | String | ✅ | Official registered name |
| Type of Institution | Enum | ✅ | School / Coaching Institute / College / University / Training Center |
| Affiliation Board | Enum | ✅ for schools | CBSE / ICSE / State Board / IB / IGCSE / OTHER |
| Registration Number | String | ❌ | Varies by type |
| UDISE Code | String | ❌ | Unique 11-digit govt code (schools) |
| GST Number | String | ❌ | If applicable |
| Year Established | Integer | ❌ | 4-digit year |
| Official Website | URL | ❌ | |
| Logo | File → S3 URL | ❌ | |
| Branding Assets | File → S3 URL | ❌ | ZIP of assets |

### Section B — Authorized Contact Details
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Principal / Director Name | String | ✅ | Primary decision maker |
| Founder / Trustee Name | String | ❌ | |
| Admin Coordinator Name | String | ❌ | Day-to-day operational contact |
| Official Email | Email | ✅ | Unique per institution |
| Secondary Email | Email | ❌ | |
| Mobile Number | String | ✅ | Primary contact |
| Secondary Mobile | String | ❌ | |
| Office Landline | String | ❌ | |
| WhatsApp Number | String | ❌ | |

---

## Enums

```python
# app/models/institution.py

from enum import Enum

class InstitutionType(str, Enum):
    SCHOOL             = "school"
    COACHING_INSTITUTE = "coaching_institute"
    COLLEGE            = "college"
    UNIVERSITY         = "university"
    TRAINING_CENTER    = "training_center"

class AffiliationBoard(str, Enum):
    CBSE        = "CBSE"
    ICSE        = "ICSE"
    STATE_BOARD = "STATE_BOARD"
    IB          = "IB"
    IGCSE       = "IGCSE"
    OTHER       = "OTHER"

class SubscriptionPlan(str, Enum):
    FREE       = "free"
    BASIC      = "basic"
    PRO        = "pro"
    ENTERPRISE = "enterprise"

class InstitutionStatus(str, Enum):
    PENDING  = "pending"    # just registered, not verified
    ACTIVE   = "active"     # verified, subscription active
    SUSPENDED = "suspended" # payment lapsed / policy violation
    INACTIVE = "inactive"   # self-deactivated
```

---

## SQLAlchemy ORM Model

```python
# app/models/institution.py

from sqlalchemy import (
    String, Integer, Boolean, Date, Text,
    Enum as SAEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

class Institution(Base, TimestampMixin):
    __tablename__ = "institutions"
    __table_args__ = (
        Index("ix_institutions_slug", "slug"),
        Index("ix_institutions_official_email", "official_email"),
        Index("ix_institutions_status", "status"),
    )

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Identity ─────────────────────────────────────────────────
    name: Mapped[str]       = mapped_column(String(255), nullable=False)
    slug: Mapped[str]       = mapped_column(String(100), unique=True, nullable=False)
    # slug = url-safe version of name e.g. "delhi-public-school-rohini"
    # auto-generated on create, used in subdomain routing

    # ── Classification ────────────────────────────────────────────
    institution_type: Mapped[str] = mapped_column(
        SAEnum(InstitutionType), nullable=False
    )
    affiliation_board: Mapped[str | None] = mapped_column(
        SAEnum(AffiliationBoard), nullable=True
    )

    # ── Official Registration ─────────────────────────────────────
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    udise_code:          Mapped[str | None] = mapped_column(String(20),  nullable=True, unique=True)
    gst_number:          Mapped[str | None] = mapped_column(String(20),  nullable=True)
    year_established:    Mapped[int | None] = mapped_column(Integer,     nullable=True)

    # ── Online Presence ───────────────────────────────────────────
    official_website:    Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_s3_key:         Mapped[str | None] = mapped_column(String(512), nullable=True)
    branding_assets_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Primary Decision Makers ───────────────────────────────────
    principal_name:        Mapped[str | None] = mapped_column(String(255), nullable=True)
    founder_trustee_name:  Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_coordinator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Contact Information ───────────────────────────────────────
    official_email:   Mapped[str]       = mapped_column(String(255), nullable=False, unique=True)
    secondary_email:  Mapped[str | None] = mapped_column(String(255), nullable=True)
    mobile_number:    Mapped[str]       = mapped_column(String(15),  nullable=False)
    secondary_mobile: Mapped[str | None] = mapped_column(String(15),  nullable=True)
    office_landline:  Mapped[str | None] = mapped_column(String(20),  nullable=True)
    whatsapp_number:  Mapped[str | None] = mapped_column(String(15),  nullable=True)

    # ── Address ───────────────────────────────────────────────────
    address_line1: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city:          Mapped[str | None] = mapped_column(String(100), nullable=True)
    state:         Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode:       Mapped[str | None] = mapped_column(String(10),  nullable=True)
    country:       Mapped[str]        = mapped_column(String(100), default="India")

    # ── Subscription & Status ─────────────────────────────────────
    status:                  Mapped[str]  = mapped_column(
        SAEnum(InstitutionStatus), default=InstitutionStatus.PENDING, nullable=False
    )
    subscription_plan:       Mapped[str]       = mapped_column(
        SAEnum(SubscriptionPlan), default=SubscriptionPlan.FREE
    )
    subscription_expires_at: Mapped[Date | None] = mapped_column(Date, nullable=True)
    is_verified:             Mapped[bool]      = mapped_column(Boolean, default=False)
    # is_verified = True when global admin manually verifies the institution

    # ── Feature Flags (JSON column) ───────────────────────────────
    feature_flags: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON string: {"ai_tutor": true, "quiz_gen": true, "assignment_eval": false}

    # ── Relationships ─────────────────────────────────────────────
    school_admins:  Mapped[list["SchoolAdmin"]]  = relationship(back_populates="institution", lazy="noload")
    teachers:       Mapped[list["Teacher"]]       = relationship(back_populates="institution", lazy="noload")
    students:       Mapped[list["Student"]]       = relationship(back_populates="institution", lazy="noload")
    classrooms:     Mapped[list["Classroom"]]     = relationship(back_populates="institution", lazy="noload")
    quizzes:        Mapped[list["Quiz"]]          = relationship(back_populates="institution", lazy="noload")
    notifications:  Mapped[list["Notification"]] = relationship(back_populates="institution", lazy="noload")
```

---

## `app/database/base.py` — Shared Base + TimestampMixin

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )
```

---

## Pydantic Schemas

```python
# app/schemas/institution.py

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator, model_validator
from typing import Optional
from datetime import date
import re

# ── Shared validators ────────────────────────────────────────────────────────

def validate_indian_mobile(v: str) -> str:
    cleaned = re.sub(r"[\s\-\+]", "", v)
    if not re.match(r"^[6-9]\d{9}$", cleaned):
        raise ValueError("Invalid Indian mobile number")
    return cleaned

def validate_gst(v: str) -> str:
    if v and not re.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$", v):
        raise ValueError("Invalid GST number format")
    return v

# ── Create (Institution Onboarding) ──────────────────────────────────────────

class InstitutionCreate(BaseModel):
    # Basic
    name:               str
    institution_type:   InstitutionType
    affiliation_board:  Optional[AffiliationBoard] = None
    registration_number: Optional[str] = None
    udise_code:         Optional[str] = None
    gst_number:         Optional[str] = None
    year_established:   Optional[int] = None
    official_website:   Optional[HttpUrl] = None

    # Decision Makers
    principal_name:         str
    founder_trustee_name:   Optional[str] = None
    admin_coordinator_name: Optional[str] = None

    # Contact
    official_email:   EmailStr
    secondary_email:  Optional[EmailStr] = None
    mobile_number:    str
    secondary_mobile: Optional[str] = None
    office_landline:  Optional[str] = None
    whatsapp_number:  Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city:          Optional[str] = None
    state:         Optional[str] = None
    pincode:       Optional[str] = None
    country:       str = "India"

    @field_validator("mobile_number", "secondary_mobile", "whatsapp_number", mode="before")
    @classmethod
    def validate_mobile(cls, v):
        if v:
            return validate_indian_mobile(v)
        return v

    @field_validator("gst_number", mode="before")
    @classmethod
    def validate_gst_field(cls, v):
        if v:
            return validate_gst(v)
        return v

    @field_validator("year_established")
    @classmethod
    def validate_year(cls, v):
        if v and (v < 1800 or v > 2025):
            raise ValueError("Year established must be between 1800 and 2025")
        return v


# ── Update (Partial) ──────────────────────────────────────────────────────────

class InstitutionUpdate(BaseModel):
    name:                   Optional[str] = None
    affiliation_board:      Optional[AffiliationBoard] = None
    registration_number:    Optional[str] = None
    udise_code:             Optional[str] = None
    gst_number:             Optional[str] = None
    year_established:       Optional[int] = None
    official_website:       Optional[HttpUrl] = None
    principal_name:         Optional[str] = None
    founder_trustee_name:   Optional[str] = None
    admin_coordinator_name: Optional[str] = None
    secondary_email:        Optional[EmailStr] = None
    secondary_mobile:       Optional[str] = None
    office_landline:        Optional[str] = None
    whatsapp_number:        Optional[str] = None
    address_line1:          Optional[str] = None
    address_line2:          Optional[str] = None
    city:                   Optional[str] = None
    state:                  Optional[str] = None
    pincode:                Optional[str] = None


# ── Response ──────────────────────────────────────────────────────────────────

class InstitutionResponse(BaseModel):
    id:                     int
    name:                   str
    slug:                   str
    institution_type:       InstitutionType
    affiliation_board:      Optional[AffiliationBoard]
    registration_number:    Optional[str]
    udise_code:             Optional[str]
    gst_number:             Optional[str]
    year_established:       Optional[int]
    official_website:       Optional[str]
    logo_url:               Optional[str]        # pre-signed S3 URL
    principal_name:         Optional[str]
    founder_trustee_name:   Optional[str]
    admin_coordinator_name: Optional[str]
    official_email:         str
    secondary_email:        Optional[str]
    mobile_number:          str
    office_landline:        Optional[str]
    whatsapp_number:        Optional[str]
    city:                   Optional[str]
    state:                  Optional[str]
    country:                str
    status:                 InstitutionStatus
    subscription_plan:      SubscriptionPlan
    subscription_expires_at: Optional[date]
    is_verified:            bool
    created_at:             str
    updated_at:             str

    model_config = {"from_attributes": True}


class InstitutionListResponse(BaseModel):
    id:               int
    name:             str
    slug:             str
    institution_type: InstitutionType
    status:           InstitutionStatus
    city:             Optional[str]
    state:            Optional[str]
    is_verified:      bool
    created_at:       str

    model_config = {"from_attributes": True}
```

---

## Institution Service

```python
# app/services/admin/institution_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionUpdate
from app.utils.s3 import generate_presigned_url
from app.cache.redis_client import redis_client
from app.cache.keys import CacheKey
import json, re

def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")

class InstitutionService:

    async def create(
        self, db: AsyncSession, data: InstitutionCreate
    ) -> Institution:
        slug = await self._unique_slug(db, _slugify(data.name))
        institution = Institution(
            **data.model_dump(exclude={"official_website"}),
            slug=slug,
            official_website=str(data.official_website) if data.official_website else None,
        )
        db.add(institution)
        await db.flush()
        return institution

    async def get_by_id(
        self, db: AsyncSession, institution_id: int
    ) -> Institution | None:
        # Try cache first
        cache_key = CacheKey.institution(institution_id)
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)  # return dict; caller converts

        result = await db.execute(
            select(Institution).where(Institution.id == institution_id)
        )
        inst = result.scalar_one_or_none()
        if inst:
            await redis_client.setex(cache_key, 300, json.dumps(inst.__dict__))
        return inst

    async def list_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 20,
        status: str | None = None
    ) -> list[Institution]:
        q = select(Institution).offset(skip).limit(limit)
        if status:
            q = q.where(Institution.status == status)
        result = await db.execute(q)
        return result.scalars().all()

    async def update(
        self, db: AsyncSession, institution_id: int, data: InstitutionUpdate
    ) -> Institution:
        inst = await self.get_by_id(db, institution_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(inst, field, value)
        await redis_client.delete(CacheKey.institution(institution_id))
        return inst

    async def verify(self, db: AsyncSession, institution_id: int) -> Institution:
        inst = await self.get_by_id(db, institution_id)
        inst.is_verified = True
        inst.status = "active"
        await redis_client.delete(CacheKey.institution(institution_id))
        return inst

    async def _unique_slug(self, db: AsyncSession, base_slug: str) -> str:
        result = await db.execute(
            select(func.count()).where(Institution.slug.startswith(base_slug))
        )
        count = result.scalar()
        return base_slug if count == 0 else f"{base_slug}-{count}"
```
