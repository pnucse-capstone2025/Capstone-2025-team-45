from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from sqlalchemy.orm import Session
from typing import Annotated

from model.database import get_db

# 모델 및 CRUD
from model.security_manager import models as security_manager_models
from model.security_manager.crud import get_security_manager_by_manager_id_and_org_id

# 토폴로지 생성 서비스
from services.network_controller.topology_service import genereate_topology_for_organization
router = APIRouter()


@router.get("/network_topology")
async def get_network_topology(
    Authorize: Annotated[AuthJWT, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        Authorize.jwt_required()
    except AuthJWTException:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    current_manager_id = Authorize.get_jwt_subject()
    claims = Authorize.get_raw_jwt()
    current_organization_id = claims.get("organization_id")

    manager = get_security_manager_by_manager_id_and_org_id(db, current_manager_id, current_organization_id)

    if not manager:
        raise HTTPException(status_code=404, detail="올바르지 않은 접근입니다. 관리자 정보를 찾을 수 없습니다.")
    
    org_id = manager.organization_id

    nodes, edges = genereate_topology_for_organization(db, org_id)

    return {"nodes": nodes, "edges": edges}