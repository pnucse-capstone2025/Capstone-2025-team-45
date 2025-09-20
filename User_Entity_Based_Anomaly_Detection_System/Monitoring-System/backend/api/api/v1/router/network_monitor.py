"""
네트워크 모니터링을 위한 FastAPI 엔드포인트를 정의합니다.
"""
from typing import Annotated
from uuid import UUID

from core.security import verify_auth_code
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT

from model.database import get_db

from model.router import schemas as router_schemas
from model.router import crud as router_crud

router = APIRouter(
    prefix = '/network_monitor',
    tags = ['Network Monitor'],
    responses = {404: {'description': 'Not found'}},
)

# @router.post('/post_mac_list')
# def post_mac_list(
#     update: router_schemas.RouterUpdate,
#     db: Annotated[Session, Depends(get_db)]
# ):
#     """
#     OpenWRT 라우터로부터 MAC 주소 목록을 받아 데이터베이스에 저장합니다.
#     """
#     try:
#         router_crud.update_router_state(db, update)
#         return {"msg": "라우터 정보가 성공적으로 저장되었습니다."}
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))