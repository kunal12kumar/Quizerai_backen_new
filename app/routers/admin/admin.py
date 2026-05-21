from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_global_admin
from app.schemas.admin.admin import GlobalAdminCreate, GlobalAdminResponse, GlobalAdminUpdate
from app.services.admin.admin_service import AdminService

router = APIRouter()


@router.post("/", response_model=GlobalAdminResponse)
def create_admin(
    payload: GlobalAdminCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    return AdminService.create_admin(db, payload)


@router.get("/", response_model=List[GlobalAdminResponse])
def list_admins(
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    return AdminService.list_admins(db)


@router.get("/{admin_id}", response_model=GlobalAdminResponse)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    return AdminService.get_admin(db, admin_id)


@router.patch("/{admin_id}", response_model=GlobalAdminResponse)
def update_admin(
    admin_id: int,
    payload: GlobalAdminUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    return AdminService.update_admin(db, admin_id, payload)


@router.delete("/{admin_id}", status_code=204)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    AdminService.delete_admin(db, admin_id)
