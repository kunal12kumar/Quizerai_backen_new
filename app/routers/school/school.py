from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_global_admin, require_school_admin
from app.schemas.school.school import SchoolCreate, SchoolResponse, SchoolUpdate
from app.services.school.school_service import SchoolService

router = APIRouter()


@router.post("/", response_model=SchoolResponse)
def create_school(
    payload: SchoolCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    return SchoolService.create_school(db, payload)


@router.get("/", response_model=List[SchoolResponse])
def list_schools(
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    return SchoolService.list_schools(db)


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_school_admin),
):
    return SchoolService.get_school(db, school_id)


@router.patch("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: int,
    payload: SchoolUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_school_admin),
):
    return SchoolService.update_school(db, school_id, payload)


@router.delete("/{school_id}", status_code=204)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_global_admin),
):
    SchoolService.delete_school(db, school_id)
