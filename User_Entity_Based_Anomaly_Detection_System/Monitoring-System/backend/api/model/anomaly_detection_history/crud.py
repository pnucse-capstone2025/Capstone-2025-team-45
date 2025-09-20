from model.anomaly_detection_history import models 
from model.anomaly_detection_history import schemas
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

def create_anomaly_detection_history(db: Session, organization_id: uuid.UUID, results: str, start_date: datetime, end_date: datetime):
    new_history = models.AnomalyDetectionHistories(
        organization_id=organization_id,
        results=results,
        run_timestamp=datetime.utcnow(),
        start_date=start_date,
        end_date=end_date
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)
    return new_history

def get_anomaly_detection_history_by_duration(db: Session, organization_id: uuid.UUID, start_date: datetime, end_date: datetime):
    return db.query(models.AnomalyDetectionHistories).filter(
        models.AnomalyDetectionHistories.organization_id == organization_id,
        models.AnomalyDetectionHistories.start_date >= start_date,
        models.AnomalyDetectionHistories.end_date <= end_date
    ).first()

def get_anomaly_detection_histories(db: Session, organization_id: uuid.UUID):  
    return db.query(models.AnomalyDetectionHistories).filter(
        models.AnomalyDetectionHistories.organization_id == organization_id
    ).all()

import json

def get_anomaly_user_count_per_history(db: Session, organization_id: uuid.UUID):
    histories = db.query(models.AnomalyDetectionHistories).filter(
        models.AnomalyDetectionHistories.organization_id == organization_id
    ).all()
    result = []
    for history in histories:
        try:
            res_dict = json.loads(history.results)
        except Exception:
            res_dict = {}
        anomaly_count = sum(1 for v in res_dict.values() if isinstance(v, dict) and v.get('p_anomaly', 0) > 0.5)
        start_str = history.start_date.strftime('%Y-%m-%d') if history.start_date else ''
        end_str = history.end_date.strftime('%Y-%m-%d') if history.end_date else ''
        result.append({
            'history_id': str(history.anomaly_detection_history_id),
            'week': f'{start_str} - {end_str}',
            'anomaly_user_count': anomaly_count
        })
    return result

