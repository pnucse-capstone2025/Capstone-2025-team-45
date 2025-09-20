# api/api/behavior_logs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from model.database import get_db
from model.behavior_log.crud import (
    get_behavior_logs_by_employee_id,
    get_monthly_event_type_counts,
    get_weekly_event_type_counts,
)
from model.security_manager.crud import get_security_manager_by_manager_id_and_org_id

from services.behavior_logs.behavior_logs_service import (
    list_behavior_logs_for_org,
    list_behavior_facets_for_org,
)

router = APIRouter()

@router.get("/behavior-logs")
async def get_behavior_logs(
    Authorize: Annotated[AuthJWT, Depends()],
    db: Annotated[Session, Depends(get_db)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    department: Optional[str] = None,
    team: Optional[str] = None,
    user: Optional[str] = Query(None, alias="user"),
    pc: Optional[str] = Query(None, alias="pc"),
    event_types: Optional[str] = None,
    sort_by: str = Query("time", regex="^(time|department|team|user)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    include_total: bool = Query(False),
):
    # 인증
    try:
        Authorize.jwt_required()
    except AuthJWTException:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    # 조직 컨텍스트 확인
    current_manager_id = Authorize.get_jwt_subject()
    claims = Authorize.get_raw_jwt()
    org_id = claims.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="organization_id 클레임이 없습니다.")

    manager = get_security_manager_by_manager_id_and_org_id(db, current_manager_id, org_id)
    if not manager:
        raise HTTPException(status_code=404, detail="올바르지 않은 접근입니다. 관리자 정보를 찾을 수 없습니다.")

    # 서비스 호출 (조직 필터 포함)
    result = list_behavior_logs_for_org(
        db=db,
        org_id=org_id,
        offset=offset,
        limit=limit,
        department=department,
        team=team,
        user=user,
        pc=pc,
        event_types=event_types,
        sort_by=sort_by,
        sort_order=sort_order,
        date_from=date_from,
        date_to=date_to,
        include_total=include_total,
    )

    return result


@router.get("/behavior-logs/facets")
async def get_behavior_log_facets(
    Authorize: Annotated[AuthJWT, Depends()],
    db: Annotated[Session, Depends(get_db)],
    department: Optional[str] = None,
    team: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str]   = Query(None, description="YYYY-MM-DD"),
    event_types: Optional[str] = None,
):
    try:
        Authorize.jwt_required()
    except AuthJWTException:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    current_manager_id = Authorize.get_jwt_subject()
    claims = Authorize.get_raw_jwt()
    org_id = claims.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="organization_id 클레임이 없습니다.")

    manager = get_security_manager_by_manager_id_and_org_id(db, current_manager_id, org_id)
    if not manager:
        raise HTTPException(status_code=404, detail="올바르지 않은 접근입니다. 관리자 정보를 찾을 수 없습니다.")

    return list_behavior_facets_for_org(
        db=db, org_id=org_id,
        department=department, team=team,
        date_from=date_from, date_to=date_to,
        event_types=event_types,
    )


@router.get("/behavior-log/user")
async def get_user_behavior_logs(
    db: Annotated[Session, Depends(get_db)],
    employee_id: str
):
    try:
        result = get_behavior_logs_by_employee_id(db, employee_id=employee_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior-log/monthly-type-counts")
def monthly_or_weekly_type_counts(
    month: Optional[str] = Query(default=None, description="YYYY-MM 또는 MM(1~12)"),
    db: Session = Depends(get_db),
):
    if month is None:
        return get_monthly_event_type_counts(db)

    mraw = month.strip()
    if not mraw or mraw.lower() == "nan":
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM or MM.")

    if "-" in mraw:
        try:
            _, m_str = mraw.split("-", 1)
            month_i = int(m_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM or MM.")
    else:
        try:
            month_i = int(mraw)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM or MM.")

    if not (1 <= month_i <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")

    weeks, counts = get_weekly_event_type_counts(db, month_i)
    return {"weeks": weeks, "counts": counts}
