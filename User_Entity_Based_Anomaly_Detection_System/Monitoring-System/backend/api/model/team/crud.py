from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from model.team.models import Teams

def get_or_create_team(db: Session, team_name: str, department_id: uuid):
    try:
        instance = db.query(Teams).filter_by(
            team_name=team_name,
            department_id=department_id
        ).first()
        if instance:
            return instance

        obj = Teams(
            team_name=team_name,
            department_id=department_id
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError:
        db.rollback()
        raise ValueError("Team with same name already exists")