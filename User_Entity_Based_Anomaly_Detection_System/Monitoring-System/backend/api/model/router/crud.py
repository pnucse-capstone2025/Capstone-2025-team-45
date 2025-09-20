import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from model.router.models import Routers
from model.router.schemas import RouterCreate, RouterUpdate

def create_router(db: Session, router_data: RouterCreate) -> Routers:
    existing_router = db.query(Routers).filter_by(control_ip=router_data.control_ip).first()
    if existing_router:
        return
    new_router = Routers(**router_data.dict())
    db.add(new_router)
    try:
        db.commit()
        db.refresh(new_router)
        return new_router
    except IntegrityError:
        db.rollback()
        raise ValueError("Router with same IP address already exists")

def update_router_state(db: Session, update_data: RouterUpdate) -> Routers:
    router = db.query(Routers).filter(Routers.router_id == update_data.router_id and Routers.organization_id == update_data.organization_id).first()
    if not router:
        raise ValueError("Router not found")

    router.state = update_data.state
    router.connected_mac_addresses = update_data.connected_mac_addresses
    db.commit()
    db.refresh(router)
    return router

def get_routers_by_organization_id(db: Session, organization_id: uuid.UUID) -> list[Routers]:
    return db.query(Routers).filter(Routers.organization_id == organization_id).all()   

def get_router_by_connected_mac(db: Session, mac_address: str) -> Routers | None:
    return db.query(Routers).filter(Routers.connected_mac_addresses.contains([mac_address])).first()