
from fastapi import APIRouter, Depends, HTTPException, status
from model.database import get_db, engine
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime   

from services.network_controller.pc_access_control_service import NetworkAccessController
from model.pc.crud import set_pc_access_flag_by_id
from model.blocking_history import crud as blocking_history_crud    
from uuid import UUID

router = APIRouter(
    prefix='/network_access_control',
    tags=['Network Access Control'],
    responses={404: {'description': 'Not found'}},
)

@router.get('/{organization_id}/{pc_id}/{access_flag}')
def control_pc_network(
    organization_id: str,
    pc_id: str,
    access_flag: bool, 
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 PC 의 접근을 제어합니다. 
    """
    try:
        networkaccesscontroller = NetworkAccessController(db, pc_id=pc_id, access_flag=access_flag)
        result = networkaccesscontroller.run()
        if result is None or result is False:
            raise HTTPException(status_code=500, detail="접근 제어 실패 ")
        
        set_pc_access_flag_by_id(db, pc_id, access_flag)
        return {"message": "제어 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get('/{organization_id}/blocking-network-histories')
def get_block_network_histories(
    organization_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 조직의 네트워크 차단 이력을 조회합니다.
    """
    try:
        histories = blocking_history_crud.get_histories_by_oid(db, UUID(organization_id))
        return {"results": histories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))