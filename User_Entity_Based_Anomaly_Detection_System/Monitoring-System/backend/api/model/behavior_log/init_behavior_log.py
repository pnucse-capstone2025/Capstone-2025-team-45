
from pathlib import Path
import pandas as pd

from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime   
from joblib import Parallel, delayed

from model.database import engine, get_db, Base, SessionLocal

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

class BehaviorLogInserter:
    """
    행동 로그 seed data 초기화를 담당하는 클래스
    """
    def __init__(self, engine: engine, db: Annotated[Session, Depends(get_db)], organization_id: str, base_path: str = None):
        self.db = db
        self.engine = engine
        self.organization_id = organization_id
        self.base_path = base_path
        
        # 삽입을 원하는 기간 설정
        self.start_dt = datetime(2010,10,1,0,0,0)
        self.end_dt = datetime(2010,12,1,0,0,0)

    def _filter_date(self, df:pd.DataFrame, date_col:str = "date") -> pd.DataFrame:
        df["date_dt"] = pd.to_datetime(df[date_col], format="%m/%d/%Y %H:%M:%S")
        df = df[(df["date_dt"] >= self.start_dt) & (df["date_dt"] < self.end_dt)]
        return df.sort_values(by="date_dt")

    def init_behavior_log(self):
        """
        전체 행동 로그 삽입 시퀀스 실행 메서드 
        """
        print(f"행동 로그 데이터 삽입 기간: {self.start_dt} ~ {self.end_dt}")
        print("행동 로그 삽입: 1, 건너뛰기: 2, 전체 단계 진행: 3")
        progress = False
        choice = input()
        if choice == "2":
            return
        elif choice == "3":
            progress = True

        # 1. 로그온 로그
        if progress:
            self.insert_logon_log()
        else:
            print("로그온 로그 삽입: 2 건너뛰기: 1")
            if input() != "1":
                self.insert_logon_log()
        # 2. 디바이스 로그 데이터 삽입
        if progress:
            self.insert_device_log()
        else:
            print("디바이스 로그 삽입: 2 건너뛰기: 1")
            if input() != "1":
                self.insert_device_log()
        # 3. 파일 로그
        if progress:
            self.insert_file_log()
        else:
            print("파일 로그 삽입: 2 건너뛰기: 1")
            if input() != "1":
                self.insert_file_log()

        # 4. 이메일 로그
        if progress:
            self.insert_email_log()
        else:
            print("이메일 로그 삽입: 2 건너뛰기: 1")
            if input() != "1":
                self.insert_email_log()

        # 5. http 로그
        if progress:
            self.insert_http_log()
        else:
            print("http 로그 삽입: 2 건너뛰기: 1")
            if input() != "1":
                self.insert_http_log()


    def _ensure_pc(self, pc_id: str):
        if not pc_crud.get_pc_by_id(self.db, pc_id):
            pc_crud.create_pc(
                self.db,
                pc_schemas.PcsCreate(
                    pc_id=pc_id,
                    organization_id=self.organization_id,
                    ip_address="test",
                    mac_address="test",
                ),
            )

        
    def insert_logon_log(self):
        """
        로그온 로그 삽입 메서드 
        """
        try:
            logon_csv = (Path(self.base_path) / "logon.csv")
            ldf = pd.read_csv(logon_csv)
            ldf = self._filter_date(ldf, "date")
            print(ldf.head())
            
            row = ldf[ldf['id'] == "{L5X9-M9OC37KU-7681KHMN}"]
            print(row)
            
            itor = 0
            for row in ldf.itertuples(index = False):
                itor += 1
                print(f"type: logon, processing ittor: {itor}, processing date: {row.date_dt}")
                self._ensure_pc(row.pc)
                logon_log_data = behavior_logs_schemas.BehaviorLogCreate(
                    event_id=row.id,
                    employee_id=row.user,
                    pc_id=row.pc,
                    timestamp=row.date_dt,  
                    event_type="logon",
                    activity=row.activity,
                )
                behavior_log_crud.create_behavior_log(self.db, logon_log_data)
        except Exception as e:
            print(f"로그온 로그 삽입 중 오류 발생: {e}")
        return
        
    def insert_device_log(self):
        """
        디바이스 로그 삽입 메서드 
        """
        try:
            device_csv = (Path(self.base_path) / "device.csv")
            ddf = pd.read_csv(device_csv)
            ddf = self._filter_date(ddf, "date")
            print (ddf.head())
            itor = 0
            for row in ddf.itertuples(index = False):
                itor += 1
                print(f"type: device, processing ittor: {itor}, processing date: {row.date_dt}")
                self._ensure_pc(row.pc)
                device_log_data = behavior_logs_schemas.BehaviorLogCreate(
                    event_id=row.id,
                    employee_id=row.user,
                    pc_id=row.pc,
                    timestamp=row.date_dt,  
                    event_type="device",
                    activity=row.activity,
                )
                behavior_log_crud.create_behavior_log(self.db, device_log_data)
        except Exception as e:
            print(f"디바이스 로그 삽입 중 오류 발생: {e}")
        return
    
    def insert_http_log(self):
        """
        http 로그 삽입 메서드
        """
        try:    
            http_csv = (Path(self.base_path) / "http.csv")  
            itor = 0
            for chunk in pd.read_csv(http_csv, chunksize=10000):
                chunk = self._filter_date(chunk, "date")
                for row in chunk.itertuples(index = False):
                    itor += 1
                    print(f"type: http, processing ittor: {itor}, processing date: {row.date_dt}")
                    if behavior_log_crud.get_behavior_logs_by_event_id(self.db, row.id): 
                        continue
                    self._ensure_pc(row.pc)
                    http_log_data = behavior_logs_schemas.BehaviorLogCreate(
                        event_id=row.id,
                        employee_id=row.user,
                        pc_id=row.pc,
                        event_type="http",
                        timestamp=row.date_dt,
                        url=row.url,
                    )
                    behavior_log_crud.create_behavior_log(self.db, http_log_data)
        except Exception as e:
            print(f"HTTP 로그 삽입 중 오류 발생: {e}")
        return
    

    def insert_file_log(self):
        """
        파일 로그 삽입 메서드 
        """
        try:
            file_csv = (Path(self.base_path) / "file.csv")
            fdf = pd.read_csv(file_csv)
            fdf = self._filter_date(fdf, "date")    
            print(fdf.head())
            itor = 0
            for row in fdf.itertuples(index = False):
                itor += 1
                print(f"type: file, processing ittor: {itor}, processing date: {row.date_dt}")
                self._ensure_pc(row.pc)
                file_log_data = behavior_logs_schemas.BehaviorLogCreate(
                    event_id=row.id,
                    employee_id=row.user,
                    pc_id=row.pc,
                    timestamp=row.date_dt,  
                    event_type="file",
                    filename=row.filename,
                )
                behavior_log_crud.create_behavior_log(self.db, file_log_data)

        except Exception as e:
            print(f"파일 로그 삽입 중 오류 발생: {e}")
    
    def insert_email_log(self):
        """
        이메일 로그 삽입 메서드 
        """
        try: 
            email_csv = (Path(self.base_path) / "email.csv")    
            edf = pd.read_csv(email_csv)    
            edf = self._filter_date(edf, "date") 
            edf.rename(columns={"from": "from_addr"}, inplace=True)
            print(edf.head())
            itor = 0
            for row in edf.itertuples(index = False):
                itor += 1
                print(f"type: email, processing ittor: {itor}, processing date: {row.date_dt}")
                self._ensure_pc(row.pc)
                file_log_data = behavior_logs_schemas.BehaviorLogCreate(
                    event_id=row.id,
                    employee_id=row.user,
                    pc_id=row.pc,
                    timestamp=row.date_dt,  
                    event_type="email",
                    to = row.to,
                    cc = row.cc,
                    bcc = row.bcc,
                    from_addr = row.from_addr,
                    size = row.size,    
                    attachment = row.attachments,
                )
                behavior_log_crud.create_behavior_log(self.db, file_log_data)

        except Exception as e:
            print(f"이메일 로그 삽입 중 오류 발생: {e}")

# 수동 삽입 코드 
# base_path = (Path(__file__).resolve().parent.parent / "dataset" / "behavior_log" )
# loginserter = BehaviorLogInserter(engine, SessionLocal(), organization_id="d038bcfa-08aa-4c40-a3e8-0fd73dbd6436", base_path=base_path)

# loginserter.init_behavior_log()

