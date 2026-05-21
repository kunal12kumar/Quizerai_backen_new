from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    hash_password,
    verify_password,
    verify_password_reset_token,
)
from app.models.admin.admin import GlobalAdmin
from app.schemas.admin.admin import GlobalAdminCreate, GlobalAdminUpdate, LoginRequest


class AdminService:

    @staticmethod
    def create_admin(db: Session, payload: GlobalAdminCreate) -> GlobalAdmin:
        if db.query(GlobalAdmin).filter(GlobalAdmin.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        admin = GlobalAdmin(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            is_superuser=payload.is_superuser,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def login(db: Session, payload: LoginRequest) -> dict:
        admin = db.query(GlobalAdmin).filter(GlobalAdmin.email == payload.email).first()
        if not admin or not verify_password(payload.password, admin.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")

        token_data = {"sub": str(admin.id), "role": "global_admin"}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
            "role": "global_admin",
        }

    @staticmethod
    def list_admins(db: Session) -> list:
        return db.query(GlobalAdmin).all()

    @staticmethod
    def get_admin(db: Session, admin_id: int) -> GlobalAdmin:
        admin = db.query(GlobalAdmin).filter(GlobalAdmin.id == admin_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return admin

    @staticmethod
    def update_admin(db: Session, admin_id: int, payload: GlobalAdminUpdate) -> GlobalAdmin:
        admin = AdminService.get_admin(db, admin_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(admin, field, value)
        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def delete_admin(db: Session, admin_id: int) -> None:
        admin = AdminService.get_admin(db, admin_id)
        db.delete(admin)
        db.commit()

    @staticmethod
    def request_password_reset(db: Session, email: str) -> None:
        admin = db.query(GlobalAdmin).filter(GlobalAdmin.email == email).first()
        if admin:
            token = generate_password_reset_token(email)
            # TODO: send token via email using notification service
            print(f"[DEV] Password reset token for {email}: {token}")

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        admin = db.query(GlobalAdmin).filter(GlobalAdmin.email == email).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        admin.hashed_password = hash_password(new_password)
        db.commit()
