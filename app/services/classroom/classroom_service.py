from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.school.classroom import Classroom
from app.schemas.school.classroom import ClassroomCreate, ClassroomUpdate


class ClassroomService:

    @staticmethod
    def create_classroom(db: Session, payload: ClassroomCreate) -> Classroom:
        classroom = Classroom(**payload.model_dump())
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def list_by_school(db: Session, school_id: int) -> list:
        return db.query(Classroom).filter(Classroom.school_id == school_id).all()

    @staticmethod
    def get_classroom(db: Session, classroom_id: int) -> Classroom:
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")
        return classroom

    @staticmethod
    def update_classroom(db: Session, classroom_id: int, payload: ClassroomUpdate) -> Classroom:
        classroom = ClassroomService.get_classroom(db, classroom_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(classroom, field, value)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def delete_classroom(db: Session, classroom_id: int) -> None:
        classroom = ClassroomService.get_classroom(db, classroom_id)
        db.delete(classroom)
        db.commit()
