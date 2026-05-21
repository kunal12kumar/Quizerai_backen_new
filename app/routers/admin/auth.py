from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.admin.admin import LoginRequest, PasswordResetConfirm, PasswordResetRequest, TokenResponse
from app.services.admin.admin_service import AdminService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AdminService.login(db, payload)


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    AdminService.request_password_reset(db, payload.email)
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    AdminService.reset_password(db, payload.token, payload.new_password)
    return {"message": "Password updated successfully."}
