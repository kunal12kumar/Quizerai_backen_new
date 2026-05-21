from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.schemas.school.school import SchoolCreate, SchoolUpdate


class SchoolService:

    @staticmethod
    def create_school(db: Session, payload: SchoolCreate) -> School:
        if db.query(School).filter(School.code == payload.code).first():
            raise HTTPException(status_code=400, detail="School code already exists")
        school = School(**payload.model_dump())
        db.add(school)
        db.commit()
        db.refresh(school)
        return school

    @staticmethod
    def list_schools(db: Session) -> list:
        return db.query(School).all()

    @staticmethod
    def get_school(db: Session, school_id: int) -> School:
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            raise HTTPException(status_code=404, detail="School not found")
        return school

    @staticmethod
    def update_school(db: Session, school_id: int, payload: SchoolUpdate) -> School:
        school = SchoolService.get_school(db, school_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(school, field, value)
        db.commit()
        db.refresh(school)
        return school

    @staticmethod
    def delete_school(db: Session, school_id: int) -> None:
        school = SchoolService.get_school(db, school_id)
        db.delete(school)
        db.commit()
