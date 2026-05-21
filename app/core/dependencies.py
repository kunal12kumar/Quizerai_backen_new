from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.connection import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("sub")
    role: str = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    return {"user_id": user_id, "role": role}


def require_global_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "global_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global admin access required",
        )
    return current_user


def require_school_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("global_admin", "school_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="School admin access required",
        )
    return current_user


def require_teacher(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("global_admin", "school_admin", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required",
        )
    return current_user
