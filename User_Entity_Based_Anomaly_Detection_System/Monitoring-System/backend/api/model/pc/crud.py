# crud.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import case, desc
    
from model.pc.models import Pcs, LogonState
from model.pc.schemas import PcsCreate


def create_pc(db: Session, pc_data: PcsCreate) -> Pcs:
    if get_pc_by_id(db, pc_data.pc_id):
        return
    
    new_pc = Pcs(**pc_data.dict())
    db.add(new_pc)
    try:
        db.commit()
        db.refresh(new_pc)
        return new_pc
    except IntegrityError:
        db.rollback()
        raise ValueError("PC with same IP or MAC address already exists")
    

def get_pcs_by_organization_id(db: Session, organization_id: uuid.UUID) -> list[Pcs]:
    return db.query(Pcs).filter(Pcs.organization_id == organization_id).all()

def get_pc_by_id(db: Session, pc_id: str) -> Pcs | None:
    return db.query(Pcs).filter(Pcs.pc_id == pc_id).first()

def set_pc_current_state_and_present_user_id_by_pc_id(db: Session, pc_id: str, current_state: LogonState, present_user_id: str):
    pc = get_pc_by_id(db, pc_id)
    if not pc:
        return None
    pc.current_state = current_state
    pc.present_user_id = present_user_id
    db.commit()
    db.refresh(pc)
    return pc

def set_pc_access_flag_by_id(db: Session, pc_id: str, access_flag: bool):
    pc = get_pc_by_id(db, pc_id)
    if not pc:
        return None
    pc.access_flag = access_flag
    db.commit()
    db.refresh(pc)
    return pc

def get_ip_and_mac_address_by_id(db:Session, pc_id: str) -> tuple[str | None, str | None] | None:
    pc = get_pc_by_id(db, pc_id)
    if not pc:
        return None
    return (pc.ip_address, pc.mac_address)

def get_logon_pc_percent_by_organization_id(db:Session, organization_id: uuid.UUID) -> float:
    total_pcs = db.query(Pcs).filter(Pcs.organization_id == organization_id).count()
    if total_pcs == 0:
        return 0.0
    logged_on_pcs = db.query(Pcs).filter(
        Pcs.organization_id == organization_id,
        Pcs.current_state == LogonState.ON
    ).count()
    return (logged_on_pcs / total_pcs) * 100.0

def get_logon_pc_count_by_organization_id(db: Session, organization_id: uuid.UUID) -> int:
    """
    해당 조직에서 현재 로그인 상태(ON)인 PC의 수를 반환
    """
    return db.query(Pcs).filter(
        Pcs.organization_id == organization_id,
        Pcs.current_state == LogonState.ON
    ).count()

def get_total_pc_count_by_organization_id(db: Session, organization_id: uuid.UUID) -> int:
    """
    해당 조직의 전체 PC 숫자를 반환
    """
    return db.query(Pcs).filter(Pcs.organization_id == organization_id).count()

def get_organization_id_by_pc_id(db:Session, pc_id: str) -> uuid.UUID | None:
    pc = get_pc_by_id(db, pc_id)
    if not pc:
        return None
    return pc.organization_id   

def get_pcs_status_by_organization_id(db: Session, organization_id: uuid.UUID) -> list[dict]:
    # present_user_id가 NULL이 아니면 1, 아니면 0
    is_active = case(
        (Pcs.present_user_id.isnot(None), 1),
        else_=0
    )

    # ip_address가 'test'가 아닌 경우를 우선
    has_valid_ip = case(
        (Pcs.ip_address != '-', 1),
        else_=0
    )

    pcs_list = (
        db.query(Pcs)
          .filter(Pcs.organization_id == organization_id)
          .order_by(desc(is_active), desc(has_valid_ip), Pcs.pc_id.asc())
          .all()
    )

    return [
        {
            "pc_id": pc.pc_id,
            "ip_address": pc.ip_address,
            "mac_address": pc.mac_address,
            "current_state": pc.current_state.value if hasattr(pc.current_state, "value") else pc.current_state,
            "present_user_id": pc.present_user_id,
            "access_flag": pc.access_flag,
        }
        for pc in pcs_list
    ]