# crud.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.security import get_auth_code_hash

from model.organization.models import Organizations
from model.organization.schemas import OrganizationCreate



def create_organization(db: Session, org_data: OrganizationCreate) -> Organizations:
    new_org = Organizations(
        organization_id=uuid.uuid4(),
        organization_name=org_data.organization_name,
        authentication_code=get_auth_code_hash(org_data.authentication_code),
        description=org_data.description
    )
    db.add(new_org)
    try:
        db.commit()
        db.refresh(new_org)
        return new_org
    except IntegrityError:
        db.rollback()
        raise ValueError("Organization with same name or code already exists")


def get_organization_by_id(db: Session, organization_id: uuid.UUID) -> Organizations:
    return db.query(Organizations).filter(Organizations.organization_id == organization_id).first()


def get_organization_by_code(db: Session, code: str) -> Organizations:
    return db.query(Organizations).filter(Organizations.authentication_code == code).first()


def get_all_organizations(db: Session):
    return db.query(Organizations).all()

def get_organization_by_name(db: Session, name: str) -> Organizations:
    return db.query(Organizations).filter(Organizations.organization_name == name).first()