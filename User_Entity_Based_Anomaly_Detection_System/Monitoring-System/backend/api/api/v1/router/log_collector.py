from typing import Annotated, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from pydantic import ValidationError
import json
import secrets
import string

from model.database import get_db
from model.behavior_log import schemas as behavior_log_schemas
from model.behavior_log import crud as behavior_log_crud

from services.logon_pipeline.processor import LogonProcessor

router = APIRouter(
    prefix="/log_collector",
    tags=["Log Collector"],
    responses={404: {"description": "Not found"}},
)

def _parse_payload(raw: bytes) -> List[Dict[str, Any]]:
    """
    단일 JSON, JSON 배열, NDJSON(줄 단위) 모두 지원.
    0x1D(레코드 구분자)도 줄바꿈으로 정규화.
    """
    if not raw:
        return []

    text = raw.decode("utf-8", errors="replace").replace("\x1D", "\n").strip()

    # 1) 통으로 JSON 파싱 시도 (객체 or 배열)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return parsed  # 리스트 안에 dict들이 온다고 가정
    except json.JSONDecodeError:
        pass  # NDJSON 가능성으로 진행

    # 2) NDJSON: 줄 단위 파싱
    objs: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            objs.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail="Invalid JSON (NDJSON line)")
    return objs

ALNUM_UP = string.ascii_uppercase + string.digits
def _gen_event_id() -> str:
     """
     {XXXX-XXXXXXXX-XXXXXXXX} 패턴의 랜덤 ID 생성
     """
     def seg(n: int) -> str:
         return ''.join(secrets.choice(ALNUM_UP) for _ in range(n))
     return f'{{{seg(4)}-{seg(8)}-{seg(8)}}}'

@router.post("/post_log")
async def post_behavior_log(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Fluentd/Agent로부터 JSON 로그를 받아서 DB에 저장
    """
    try:
        raw_data = await request.body()
        print (raw_data)
        # JSON 파싱
        try:
            data_dicts = _parse_payload(raw_data)
        except HTTPException:
            raise

        if not data_dicts:
            raise HTTPException(status_code=400, detail="Empty payload")

        # 스키마 검증
        event_ids: List[str] = []
        for i, rec in enumerate(data_dicts, start=1):
            # event_id 주입
            rec = dict(rec)
            rec["event_id"] = _gen_event_id()

            try:
                log_data = behavior_log_schemas.BehaviorLogCreate(**rec)
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=e.errors())
            
            # DB 처리
            attempts = 0
            max_attempts = 5
            while True:
                try:
                    new_log = behavior_log_crud.create_behavior_log(db, log_data)
                    event_ids.append(new_log.event_id)
                    break
                except IntegrityError as ie:
                    # PK / FK / UNIQUE / NOT NULL 등 무결성 위반
                    db.rollback()
                    err_str = str(ie.orig)
                    # PK 중복인 경우에만 재시도
                    if attempts < max_attempts - 1 and (
                        "duplicate" in err_str.lower()
                        or "unique" in err_str.lower()
                        or "primary key" in err_str.lower()
                    ):
                        attempts += 1
                        new_id = _gen_event_id()

                        data_dict = log_data.model_dump() if hasattr(log_data, "model_dump") else log_data.dict()
                        data_dict["event_id"] = new_id
                        try:
                            log_data = behavior_log_schemas.BehaviorLogCreate(**data_dict)
                        except ValidationError as ve:
                            raise HTTPException(status_code=400, detail=ve.errors())
                        continue
                    raise HTTPException(status_code=409, detail=err_str)
                except DataError as de:
                    # 타입/길이 초과 등 데이터 문제
                    db.rollback()
                    raise HTTPException(status_code=400, detail=str(de.orig))
                except OperationalError:
                    # DB 접속/트랜잭션 문제
                    db.rollback()
                    raise HTTPException(status_code=503, detail="Database unavailable")

            # 이벤트 타입이 logon일 시, 로그온 처리를 위한 클래스 호출
            if log_data.event_type == "logon":
                logonprocessor = LogonProcessor(db, log_data)
                await logonprocessor.run()
                
        return {"msg": "로그가 성공적으로 저장되었습니다.", "count": len(event_ids), "event_ids": event_ids}

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal error")
