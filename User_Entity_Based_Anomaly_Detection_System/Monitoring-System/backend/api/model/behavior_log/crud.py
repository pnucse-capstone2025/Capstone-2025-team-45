
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from datetime import datetime
from model.behavior_log.models import Behavior_logs, Http_logs, Email_logs, Device_logs, Logon_logs, File_logs
from model.behavior_log.schemas import BehaviorLogCreate, HttpLogCreate, EmailLogCreate, DeviceLogCreate, LogonLogCreate, FileLogCreate
from typing import Optional , List, Tuple, Iterable

from sqlalchemy import extract
def create_behavior_log(db: Session, log_data: BehaviorLogCreate) -> Behavior_logs:
    # 1. 공통 로그 저장
    base_log = Behavior_logs(
        event_id = log_data.event_id,
        employee_id=log_data.employee_id,
        pc_id=log_data.pc_id,
        timestamp=log_data.timestamp,
        event_type=log_data.event_type
    )
    db.add(base_log)
    db.commit()
    db.refresh(base_log)

    # 2. event_type에 따라 세부 테이블 저장
    if log_data.event_type == "http":
        db.add(Http_logs(event_id=base_log.event_id, url=log_data.url))

    elif log_data.event_type == "email":
        db.add(Email_logs(
            event_id=base_log.event_id,
            to=log_data.to,
            cc=log_data.cc,
            bcc=log_data.bcc,
            from_addr=log_data.from_addr,
            size=log_data.size,
            attachment=log_data.attachment
        ))
    
    elif log_data.event_type == "device":
        db.add(Device_logs(event_id=base_log.event_id, activity=log_data.activity))

    elif log_data.event_type == "logon":
        db.add(Logon_logs(event_id=base_log.event_id, activity=log_data.activity))

    elif log_data.event_type == "file":
        db.add(File_logs(event_id=base_log.event_id, filename=log_data.filename))

    db.commit()
    return base_log

def get_all_behavior_logs(db: Session):
    return db.query(Behavior_logs).all()

def get_behavior_logs_by_event_id(db: Session, event_id: str) -> List[Behavior_logs]:
    return db.query(Behavior_logs).filter(Behavior_logs.event_id == event_id).all()

def get_behavior_logs_by_employee_id(db: Session, employee_id: str) -> List[Behavior_logs]:
    return db.query(Behavior_logs).filter(Behavior_logs.employee_id == employee_id).order_by(desc(Behavior_logs.timestamp)).all()

def get_behavior_logs_by_event_type(db: Session, event_type: str) -> List[Behavior_logs]:
    return db.query(Behavior_logs).filter(Behavior_logs.event_type == event_type).all()

def get_behavior_logs_by_period(db: Session, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Behavior_logs]:
    query = db.query(Behavior_logs)

    if start_time and end_time:
        query = query.filter(Behavior_logs.timestamp.between(start_time, end_time))
    elif start_time:
        query = query.filter(Behavior_logs.timestamp >= start_time)
    elif end_time:
        query = query.filter(Behavior_logs.timestamp <= end_time)
    
    return query.order_by(Behavior_logs.timestamp.desc()).all()

def get_logon_logs_by_event_ids(db: Session, event_ids: list[str]) -> list[Logon_logs]:
    return db.query(Logon_logs).filter(Logon_logs.event_id.in_(event_ids)).all()

def get_http_logs_by_event_ids(db: Session, event_ids: list[str]) -> list[Http_logs]:
    return db.query(Http_logs).filter(Http_logs.event_id.in_(event_ids)).all()

def get_email_logs_by_event_ids(db: Session, event_ids: list[str]) -> list[Email_logs]:
    return db.query(Email_logs).filter(Email_logs.event_id.in_(event_ids)).all()

def get_device_logs_by_event_ids(db: Session, event_ids: list[str]) -> list[Device_logs]:
    return db.query(Device_logs).filter(Device_logs.event_id.in_(event_ids)).all()

def get_file_logs_by_event_ids(db: Session, event_ids: list[str]) -> list[File_logs]:
    return db.query(File_logs).filter(File_logs.event_id.in_(event_ids)).all()

def get_monthly_event_type_counts(db: Session, tz: str = 'Asia/Seoul'):
    """
    월별 event_type별 로그 개수 집계
    반환: [{month: '2010-01', event_type: 'http', count: 123}, ...]
    """
    tz_ts   = func.timezone(tz, Behavior_logs.timestamp)
    month_s = func.to_char(tz_ts, 'YYYY-MM')

    result = (
        db.query(
            month_s.label('month'),
            Behavior_logs.event_type,
            func.count().label('count')
        )
        .group_by(month_s, Behavior_logs.event_type)
        .order_by(month_s)
        .all()
    )
    return [
        {'month': r.month, 'event_type': r.event_type, 'count': r.count}
        for r in result
    ]


def get_weekly_event_type_counts(db: Session, month: int, tz: str = 'Asia/Seoul'):
    """
    주차별 각 유형 로그 집계
    반환: (weeks:[1..N], counts:{logon:[...], email:[...], http:[...], device:[...], file:[...]})
    """
    tz_ts = func.timezone(tz, Behavior_logs.timestamp)

    latest_year_subq = (
        db.query(func.max(extract('year', tz_ts)))
        .filter(extract('month', tz_ts) == month)
        .scalar_subquery()
    )

    week_start = func.date_trunc('week', tz_ts)

    subq = (
        db.query(
            week_start.label('week_start'),
            Behavior_logs.event_type.label('event_type'),
            func.count().label('cnt'),
        )
        .filter(
            extract('month', tz_ts) == month,
            extract('year', tz_ts) == latest_year_subq,
            Behavior_logs.event_type.in_(('logon', 'email', 'http', 'device', 'file')),
        )
        .group_by('week_start', 'event_type')
        .subquery()
    )

    rows = (
        db.query(subq.c.week_start, subq.c.event_type, subq.c.cnt)
        .order_by(subq.c.week_start, subq.c.event_type)
        .all()
    )

    if not rows:
        return [], {t: [] for t in ['logon', 'email', 'http', 'device', 'file']}

    week_index_map, ordered = {}, []
    for r in rows:
        ws = r.week_start
        if ws not in week_index_map:
            week_index_map[ws] = len(ordered) + 1
            ordered.append(ws)

    maxw = len(ordered)
    event_types = ['logon', 'email', 'http', 'device', 'file']
    counts = {t: [0] * maxw for t in event_types}

    for r in rows:
        idx = week_index_map[r.week_start] - 1
        t = (r.event_type or '').lower()
        if t in counts:
            counts[t][idx] = int(r.cnt)

    weeks = list(range(1, maxw + 1))
    return weeks, counts