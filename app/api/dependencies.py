from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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

    user_id: str = payload.get("sub")
    role: str = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    return {"user_id": user_id, "role": role, "db": db}


def require_roles(*roles: str):
    def guard(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {', '.join(roles)}",
            )
        return current_user
    return guard


require_global_admin = require_roles("global_admin")
require_school_admin = require_roles("global_admin", "school_admin")
require_teacher = require_roles("global_admin", "school_admin", "teacher")
require_student = require_roles("global_admin", "school_admin", "teacher", "student")
