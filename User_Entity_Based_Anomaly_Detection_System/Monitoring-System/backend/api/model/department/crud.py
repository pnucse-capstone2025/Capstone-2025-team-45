from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from model.department.models import Departments

def get_or_create_department(db: Session, department_name: str, functional_unit_id: uuid):
    try:
        instance = db.query(Departments).filter_by(
            department_name=department_name,
            functional_unit_id=functional_unit_id
        ).first()
        if instance:
            return instance

        obj = Departments(
            department_name=department_name,
            functional_unit_id=functional_unit_id
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError:
        db.rollback()
        raise ValueError("Department with same name already exists")
