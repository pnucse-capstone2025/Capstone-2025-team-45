from model.blocking_history import models
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

def create_blocking_history(db: Session, organization_id: uuid.UUID, pc_id: str, employee_id: str, logon_time: datetime, blocking_time: datetime):  
    new_history = models.BlockingHistory(
        organization_id=organization_id,
        pc_id=pc_id,
        employee_id=employee_id,
        logon_time=logon_time,
        blocking_time=blocking_time
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)
    return new_history  

def get_histories_by_oid(db: Session, organization_id: uuid.UUID):
    return db.query(models.BlockingHistory).filter(models.BlockingHistory.organization_id == organization_id).all()

