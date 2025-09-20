
from fastapi import APIRouter, Depends, HTTPException, status
from model.database import get_db, engine
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime   
from uuid import UUID
import json 
from services.anomaly_classification.anomaly_detector import AnomalyDetector
from model.anomaly_detection_history import crud as anomaly_detection_history_crud
from model.employee import crud as employee_crud
router = APIRouter(
    prefix='/anomalydetect',
    tags=['Anomaly Detect'],
    responses={404: {'description': 'Not found'}},
)

@router.get('/{organization_id}/')
def get_anomaly_detection_results(
    organization_id: str,
    start_dt: datetime,
    end_dt: datetime,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 기간 동안의 이상 탐지 결과를 조회합니다.
    date 형식: 
    2010-10-11T00:00:00+00:00
    2010-10-18T00:00:00+00:00
    """
    try:
        # 이미 해당 기간에 대한 기록이 있는지 확인 및 있으면 반환
        history = anomaly_detection_history_crud.get_anomaly_detection_history_by_duration(db, UUID(organization_id), start_dt, end_dt)
        if history:
            results = history.results
            payload = json.loads(results) if isinstance(results, str) else results
            return {"results": payload}

        anomalydetector = AnomalyDetector(engine, db, start_dt, end_dt, organization_id=UUID(organization_id))
        results = anomalydetector.run()
        print(results)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/{organization_id}/anomaly_employees')
def get_anomaly_employees(
    organization_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 조직의 악성 의심 사용자 목록을 조회합니다.
    """
    try:
        # 이미 해당 기간에 대한 기록이 있는지 확인 및 있으면 반환
        anomaly_usrs = employee_crud.get_anomaly_employees_by_oid(db, UUID(organization_id))
        return anomaly_usrs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/get-histories/{organization_id}/')
def get_anomaly_detection_histories(
    organization_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 조직의 이상 탐지 이력을 조회합니다.
    """
    try:
        histories = anomaly_detection_history_crud.get_anomaly_detection_histories(db, UUID(organization_id))
        return {"results": histories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/get-anomaly-user-counts-by-week/{organization_id}/')
def get_anomaly_user_counts_by_week(
    organization_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 조직의 주별 이상 탐지 사용자 수를 조회합니다.
    """
    try:
        result = anomaly_detection_history_crud.get_anomaly_user_count_per_history(db, UUID(organization_id))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
