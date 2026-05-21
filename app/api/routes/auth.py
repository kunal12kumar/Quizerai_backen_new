from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.security import decode_token, create_access_token, create_refresh_token
from app.schemas.users import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services.admin.admin_service import AdminService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AdminService.login(db, payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    token_data = {"sub": data["sub"], "role": data["role"]}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "role": data["role"],
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout():
    # Token invalidation is handled client-side; extend with a blocklist if needed.
    return {"message": "Logged out successfully."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    AdminService.request_password_reset(db, payload.email)
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    AdminService.reset_password(db, payload.token, payload.new_password)
    return {"message": "Password updated successfully."}
