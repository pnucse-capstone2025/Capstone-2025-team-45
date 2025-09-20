from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from model.functional_unit.models import FunctionalUnits

def get_or_create_functional_unit(db: Session, functional_unit_name: str, organization_id: uuid):
    instance = db.query(FunctionalUnits).filter_by(
        functional_unit_name=functional_unit_name,
        organization_id=organization_id
    ).first()
    if instance:
        return instance

    obj = FunctionalUnits(
        functional_unit_name=functional_unit_name,
        organization_id=organization_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
