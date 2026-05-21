from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user

router = APIRouter()


@router.get("/classroom/{classroom_id}/materials")
def get_learning_materials(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # TODO: implement learning materials service
    return {"classroom_id": classroom_id, "materials": []}


@router.get("/student/{student_id}/progress")
def get_student_progress(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # TODO: implement progress tracking service
    return {"student_id": student_id, "progress": []}
