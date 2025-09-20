import pandas as pd
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect as sqla_inspect
from fastapi import Depends
from datetime import datetime   

from model.security_manager import models as SecurityManager_models
from model.security_manager import crud as security_manager_crud
from model.security_manager import schemas as security_manager_schemas

from model.organization import models as Organization_models
from model.organization import crud as organization_crud
from model.organization import schemas as organization_schemas

from model.functional_unit import models as FunctionalUnit_models
from model.functional_unit import crud as functional_unit_crud

from model.department import models as Department_models    
from model.department import crud as department_crud

from model.team import models as Team_models
from model.team import crud as team_crud

from model.employee import models as Employee_models
from model.employee import crud as employee_crud

from model.pc import models as Pc_models
from model.pc import crud as pc_crud
from model.pc import schemas as pc_schemas

from model.router import models as Router_models
from model.router import crud as router_crud
from model.router import schemas as router_schemas

from model.behavior_log import models as BehaviorLog_models
from model.behavior_log import crud as behavior_log_crud
from model.behavior_log import schemas as behavior_logs_schemas
from model.behavior_log.init_behavior_log import BehaviorLogInserter
from model.database import engine, get_db, Base, SessionLocal

from model.behavior_log import crud as behavior_log_crud

class LogLoader:
    """
    로그 데이터 로드 클래스
    DB 로부터 특정 주차의 로그 데이터를 조회 및 병합, 저장 
    """
    def __init__(self, engine: engine, db: Session, start_date: datetime, end_date: datetime):
        self.engine = engine
        self.db = db
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            df =  self._load_logs(self.start_date, self.end_date)
            return df 
        except Exception as e:
            print(f"로그 로드 중 오류 발생: {e}")
            return None
        
    def _sa_obj_to_dict(self, obj):
        """
        SQLAlchemy ORM 객체를 컬럼 기반 dict로 변환
        """
        mapper = sqla_inspect(obj).mapper
        data = {c.key: getattr(obj, c.key) for c in mapper.column_attrs}
        return data

    def _load_logs(self, start_date: datetime, end_date: datetime):
        """
        주어진 날짜 범위에 해당하는 로그 데이터를 로드
        """
        orm = behavior_log_crud.get_behavior_logs_by_period(self.db, start_time=start_date, end_time=end_date)

        rows = [self._sa_obj_to_dict(o) for o in orm]
        return pd.DataFrame(rows)
    
    

        
