import os
import pandas as pd 
from datetime import datetime
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from pathlib import Path

from core.config import settings
from model.database import engine, get_db, Base

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

from model.anomaly_detection_history import models as AnomalyDetectionHistory_models
from model.anomaly_detection_history import crud as anomaly_detection_history_crud  

from model.blocking_history import models as BlockingHistory_models 
from .util import getuserlist, ym_to_date

def init_database(engine: engine, db: Annotated[Session, Depends(get_db)]):
    """
    조직 정보, 직원, PC, 라우터 정보를 데이터베이스에 초기화합니다. 
    """
    Base.metadata.create_all(bind=engine)
    print("데이터 베이스 초기화를 건너 뛰려면 1을 입력하세요.")
    if input() == "1": 
        return
    
    #create all tables
    # 2. 기본 조직 존재 여부 확인
    organization = organization_crud.get_organization_by_name(db, settings.ADMIN_COMPANY_NAME)
    if not organization:
        organization = organization_crud.create_organization(db, organization_schemas.OrganizationCreate(
            organization_name=settings.ADMIN_COMPANY_NAME,
            authentication_code=settings.ADMIN_AUTH_CODE,
            description=settings.ADMIN_ORGANIZATION_DESCRIPTION
        ))
    
    additional_organization = organization_crud.get_organization_by_name(db, settings.ADDITIONAL_ORGANIZATIONS_NAME)
    if not additional_organization:
        additional_organization = organization_crud.create_organization(db, organization_schemas.OrganizationCreate(
            organization_name=settings.ADDITIONAL_ORGANIZATIONS_NAME,
            authentication_code=settings.ADDITIONAL_ORGANIZATIONS_AUTH_CODE,
            description=settings.ADDITIONAL_ORGANIZATIONS_DESCRIPTION
        ))

    # 3. 관리자 유저 존재 여부 확인
    admin_user = security_manager_crud.get_security_manager_by_name(db, settings.ADMIN_USERNAME)
    if not admin_user:
        admin_user = security_manager_schemas.UserCreate(
            manager_id=settings.ADMIN_USERID,
            name=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            organization_id=organization.organization_id  
        )
        security_manager_crud.create_security_manager(db, admin_user)

    # 4. 조직 및 직원 데이터 삽입
    df = getuserlist()  
    df = df.fillna("")
    # 4-0. 결측치 대처를 위해, "Unassigned" 값으로 대체
    unassigned_functional_unit = functional_unit_crud.get_or_create_functional_unit(
        db, functional_unit_name="Unassigned", organization_id=organization.organization_id
    )

    unassigned_department = department_crud.get_or_create_department(
        db, department_name="Unassigned", functional_unit_id=unassigned_functional_unit.functional_unit_id
    )

    unassigned_team = team_crud.get_or_create_team(
        db, team_name="Unassigned", department_id=unassigned_department.department_id
    )

    for _, row in df.iloc[0:].iterrows():
        if not row["employee_name"]:
            break

        try:
            # 1. 기능 단위
            if row["functional_unit"] and " - " in row["functional_unit"]:
                functional_unit_name = row["functional_unit"].split(" - ")[1]
                functional_unit = functional_unit_crud.get_or_create_functional_unit(
                    db, functional_unit_name=functional_unit_name,
                    organization_id=organization.organization_id
                )
            else:
                functional_unit = unassigned_functional_unit

            # 2. 부서
            if row["department"] and " - " in row["department"]:
                department_name = row["department"].split(" - ")[1]
                department = department_crud.get_or_create_department(
                    db, department_name=department_name,
                    functional_unit_id=functional_unit.functional_unit_id
                )
            else:
                department = unassigned_department

            # 3. 팀
            if row["team"] and " - " in row["team"]:
                team_name = row["team"].split(" - ")[1]
                team = team_crud.get_or_create_team(
                    db, team_name=team_name,
                    department_id=department.department_id
                )
            else:
                team = unassigned_team
    
            # 4. 직원
            wstart_date = ym_to_date(row.get("wstart"))
            wend_date = ym_to_date(row.get("wend"))
            employee = employee_crud.get_or_create_employee(
                db,
                employee_id=row['user_id'],
                employee_name=row['employee_name'],
                email=row['email'],
                role=row['role'],
                team_id=team.team_id,
                wstart=wstart_date,
                wend=wend_date,
                supervisor=row['supervisor'],
                anomaly_flag=False
            )
        except Exception as e:
            print(f"Error creating employee: {e}")
            continue
    
    # 5. PC 데이터 삽입
    try:
        pc_data = pc_schemas.PcsCreate(
            pc_id="PC-6672",
            organization_id=organization.organization_id,
            ip_address="192.168.100.113",
            mac_address="08:00:27:70:e5:f5",
        )
        pc_crud.create_pc(db, pc_data)
        pc_data = pc_schemas.PcsCreate(
            pc_id="PC-6673",
            organization_id=organization.organization_id,
            ip_address="192.168.100.235",
            mac_address="08:00:27:9e:c1:c5",
        )
        pc_crud.create_pc(db, pc_data)

    except Exception as e:
        print(f"Error creating PC: {e}")

    # 6. 라우터 데이터 삽입
    try:
        router_data = router_schemas.RouterCreate(
            organization_id=organization.organization_id,
            control_ip="192.168.56.2",
        )
        router_crud.create_router(db, router_data)
    except Exception as e:
        print(f"Error creating Router: {e}")

    # 7. 행동 로그 데이터 삽입
    
    try:
        base_path = Path(__file__).resolve().parent/"dataset"/"behavior_log"
        behavior_log_inserter = BehaviorLogInserter(engine, db, organization_id=organization.organization_id, base_path=base_path)
        behavior_log_inserter.init_behavior_log()
    except Exception as e:
        print(f"Error creating Behavior Logs: {e}")

    # 8. 사용자 주 PC/공유 PC 정보 저장
    print("Database initialized successfully.")