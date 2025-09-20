from __future__ import annotations
import pandas as pd
from typing import Annotated, Dict, List
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect as sqla_inspect
from fastapi import Depends
from model.database import engine, get_db, Base, SessionLocal

from model.behavior_log import crud as behavior_log_crud    


TARGET_COLUMNS = [
    "date", "user", "pc", "activity", "type",
    "to", "cc", "bcc", "from", "size", "#att", "url/fname"
]

class LogMerger:
    """
    베이스 로그 DF([event_id, employee_id, pc_id, timestamp, event_type])를 받아
    타입별 상세 테이블을 조회하여 표준 포맷 DF로 병합.
    """
    def __init__(self, engine: Engine, db: Session, df: pd.DataFrame):
        self.engine = engine
        self.db = db
        self.df = df.copy()

    def run(self) -> pd.DataFrame:
        """
        병합된 표준 포맷 DataFrame 반환
        """
        base = self.df.copy()
        if base.empty:
            return pd.DataFrame(columns=TARGET_COLUMNS)
        
        parts: List[pd.DataFrame] = []
        for event_type, sub in base.groupby("event_type", sort= False):
            detail_df = self._fetch_details(event_type, sub["event_id"].tolist())
            merged = pd.merge(sub, detail_df, on="event_id", how="left")
            parts.append(merged)  
        out = pd.concat(parts, ignore_index=True) if parts else base
        return self._finalize(out)
        
    def _fetch_details(self, event_type: str, event_ids: List[str]) -> pd.DataFrame:
        """
        타입별 상세 테이블을 한 번에 조회(event_id ANY(:event_ids))
        반환 DF는 반드시 event_id 포함
        """
        if event_type == "logon":
            return pd.DataFrame([self._sa_obj_to_dict(log) for log in behavior_log_crud.get_logon_logs_by_event_ids(self.db, event_ids)])
        elif event_type == "http":
            return pd.DataFrame([self._sa_obj_to_dict(log) for log in behavior_log_crud.get_http_logs_by_event_ids(self.db, event_ids)])
        elif event_type == "email": 
            return pd.DataFrame([self._sa_obj_to_dict(log) for log in behavior_log_crud.get_email_logs_by_event_ids(self.db, event_ids)])
        elif event_type == "device":
            return pd.DataFrame([self._sa_obj_to_dict(log) for log in behavior_log_crud.get_device_logs_by_event_ids(self.db, event_ids)])
        elif event_type == "file":
            return pd.DataFrame([self._sa_obj_to_dict(log) for log in behavior_log_crud.get_file_logs_by_event_ids(self.db, event_ids)])

    def _sa_obj_to_dict(self, obj):
        """
        SQLAlchemy ORM 객체를 컬럼 기반 dict로 변환
        """
        mapper = sqla_inspect(obj).mapper
        data = {c.key: getattr(obj, c.key) for c in mapper.column_attrs}
        return data
    
    def _finalize(self, df: pd.DataFrame) -> pd.DataFrame:
        # 최종 표준 스키마만 남기고 정리
        rows = []
        for row in df.itertuples(index=False):
            url_or_fname = getattr(row, "url", None)
            if pd.isna(url_or_fname):
                url_or_fname = getattr(row, "filename", None)
              
            rows.append({
                "date": row.timestamp,
                "user": row.employee_id,
                "pc": row.pc_id,
                "activity": row.activity,
                "type": row.event_type,
                "to": getattr(row, "to", None),
                "cc": getattr(row, "cc", None),
                "bcc": getattr(row, "bcc", None),
                "from": getattr(row, "from_addr", None),
                "size": getattr(row, "size", None),
                "#att": getattr(row, "attachment", None),
                "url/fname": url_or_fname
            })
        return pd.DataFrame(rows, columns=TARGET_COLUMNS)