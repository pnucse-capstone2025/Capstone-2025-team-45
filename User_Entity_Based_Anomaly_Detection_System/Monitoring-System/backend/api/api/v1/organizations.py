"""
조직과 관련된 데이터를 관리하는 API 모듈입니다.
"""

from typing import Annotated

from core.security import verify_auth_code
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT

from model.database import get_db
from model.organization.crud import get_organization_by_id
from model.security_manager import crud as security_manager_crud
from model.security_manager import schemas as security_manager_schemas
from model.organization.models import Organizations

router = APIRouter(
    prefix='/organizations',
    tags=['Organizations'],
    responses={404: {'description': 'Not found'}},
)

@router.get('/{organization_id}/name&description')
def get_organization_info(
    organization_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    조직 이름 및 설명 반환
    """
    org = get_organization_by_id(db, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail='조직을 찾을 수 없습니다.')
    
    return {
        "organization_id": str(org.organization_id),
        "organization_name": org.organization_name,
        "description": org.description
    }


@router.post('/{organization_id}/verify')
def verify_organization_code(
    organization_id: str,
    payload: dict,
    db: Annotated[Session, Depends(get_db)]
):
    """
    조직 인증 코드 검증
    """
    org = get_organization_by_id(db, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail='조직을 찾을 수 없습니다.')

    if not verify_auth_code(payload.get('authentication_code'), org.authentication_code):
        raise HTTPException(status_code=403, detail='인증 코드가 일치하지 않습니다.')

    return {"msg": "조직 인증 완료"}


