from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_school_admin
from app.schemas.school.classroom import ClassroomCreate, ClassroomResponse, ClassroomUpdate
from app.services.classroom.classroom_service import ClassroomService

router = APIRouter()


@router.post("/", response_model=ClassroomResponse)
def create_classroom(
    payload: ClassroomCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_school_admin),
):
    return ClassroomService.create_classroom(db, payload)


@router.get("/school/{school_id}", response_model=List[ClassroomResponse])
def list_classrooms(
    school_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_school_admin),
):
    return ClassroomService.list_by_school(db, school_id)


@router.get("/{classroom_id}", response_model=ClassroomResponse)
def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_school_admin),
):
    return ClassroomService.get_classroom(db, classroom_id)


@router.patch("/{classroom_id}", response_model=ClassroomResponse)
def update_classroom(
    classroom_id: int,
    payload: ClassroomUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_school_admin),
):
    return ClassroomService.update_classroom(db, classroom_id, payload)


@router.delete("/{classroom_id}", status_code=204)
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_school_admin),
):
    ClassroomService.delete_classroom(db, classroom_id)
