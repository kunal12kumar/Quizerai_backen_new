from typing import Optional
from pydantic import BaseModel, EmailStr


class GlobalAdminCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    is_superuser: bool = False


class GlobalAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class GlobalAdminResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
