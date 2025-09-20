# services/behavior_logs_service.py
from datetime import datetime
from typing import Optional
import time
from collections import OrderedDict
from urllib.parse import urlsplit

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, selectinload, load_only
from sqlalchemy.sql import exists

from model.behavior_log.models import (
    Behavior_logs, Http_logs, Email_logs, Device_logs, Logon_logs, File_logs
)
from model.employee.models import Employees
from model.team.models import Teams
from model.department.models import Departments
from model.pc.models import Pcs

# -------------------------------
# TTL 캐시 (OFFSET 모드일 때만 사용)
# -------------------------------
_PAGEIDS_CACHE = OrderedDict()
_PAGEIDS_TTL_SEC = 60
_PAGEIDS_MAX = 256

_TOTAL_CACHE = OrderedDict()
_TOTAL_TTL = 60

def _pget(key):
    now = time.time()
    v = _PAGEIDS_CACHE.get(key)
    if not v:
        return None
    ids, exp = v
    if exp < now:
        _PAGEIDS_CACHE.pop(key, None)
        return None
    _PAGEIDS_CACHE.move_to_end(key)
    return ids

def _pset(key, ids):
    exp = time.time() + _PAGEIDS_TTL_SEC
    _PAGEIDS_CACHE[key] = (tuple(ids), exp)
    if len(_PAGEIDS_CACHE) > _PAGEIDS_MAX:
        _PAGEIDS_CACHE.popitem(last=False)

def _tget(k):
    v = _TOTAL_CACHE.get(k)
    if not v:
        return None
    val, exp = v
    if exp < time.time():
        _TOTAL_CACHE.pop(k, None)
        return None
    _TOTAL_CACHE.move_to_end(k)
    return val

def _tset(k, val):
    _TOTAL_CACHE[k] = (int(val), time.time() + _TOTAL_TTL)
    if len(_TOTAL_CACHE) > 256:
        _TOTAL_CACHE.popitem(last=False)

def _canon_types(event_types: Optional[str]) -> str:
    if not event_types:
        return ""
    types = [t.strip() for t in event_types.split(",") if t.strip()]
    types = sorted(set(types))
    return ",".join(types)

def make_detail_bl(bl: Behavior_logs) -> str:
    et = bl.event_type or ""
    if et == "http" and bl.http_log:
        return f"HTTP • {bl.http_log.url}"
    if et == "email" and bl.email_log:
        att = bl.email_log.attachment or 0
        return f"EMAIL • {bl.email_log.from_addr} -> {bl.email_log.to} (att:{att})"
    if et == "device" and bl.device_log:
        return f"DEVICE • {bl.device_log.activity}"
    if et == "logon" and bl.logon_log:
        return f"LOGON • {bl.logon_log.activity}"
    if et == "file" and bl.file_log:
        return f"FILE • {bl.file_log.filename}"
    return f"{et.upper()} • event_id={bl.event_id}"

def _apply_common_filters(q, org_id, date_from, date_to, event_types):
    q = (q.join(Pcs, Pcs.pc_id == Behavior_logs.pc_id)
           .join(Employees, Employees.employee_id == Behavior_logs.employee_id)
           .join(Teams, Teams.team_id == Employees.team_id)
           .join(Departments, Departments.department_id == Teams.department_id)
           .filter(Pcs.organization_id == org_id))
    if date_from:
        try:
            q = q.filter(Behavior_logs.timestamp >= datetime.strptime(date_from, "%Y-%m-%d"))
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            q = q.filter(Behavior_logs.timestamp <= dt)
        except ValueError:
            pass
    if event_types:
        types = [t.strip() for t in event_types.split(",") if t.strip()]
        if types:
            q = q.filter(Behavior_logs.event_type.in_(types))
    return q

def _host_of(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        return urlsplit(url).netloc
    except Exception:
        return None

# -------------------------------
# FACETS TTL 캐시 (org/날짜/타입/부서/팀 조합별)
# -------------------------------
_FACETS_CACHE = OrderedDict()
_FACETS_TTL = 60  # sec

def _fget(key):
    v = _FACETS_CACHE.get(key)
    if not v: return None
    val, exp = v
    if exp < time.time():
        _FACETS_CACHE.pop(key, None); return None
    _FACETS_CACHE.move_to_end(key)
    return val

def _fset(key, val):
    _FACETS_CACHE[key] = (val, time.time() + _FACETS_TTL)
    if len(_FACETS_CACHE) > 256:
        _FACETS_CACHE.popitem(last=False)

# -------------------------------
# Facets
# -------------------------------
def list_behavior_facets_for_org(
    db: Session, org_id,
    *, department: Optional[str] = None, team: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    event_types: Optional[str] = None,
):
    # --- 캐시 키
    fkey = (
        "facets", str(org_id),
        date_from or "", date_to or "",
        _canon_types(event_types),
        department or "", team or "",
    )
    cached = _fget(fkey)
    if cached is not None:
        return cached

    # --- 1단계: 조건(조직/기간/타입/PC)을 Behavior_logs에만 적용해서 employee_id 집합 축소
    ids_q = (
        db.query(Behavior_logs.employee_id)
          .filter(
              exists().where(and_(Pcs.pc_id == Behavior_logs.pc_id,
                                  Pcs.organization_id == org_id))
          )
          .filter(Behavior_logs.employee_id.isnot(None))
          .distinct()
    )
    if date_from:
        try:
            ids_q = ids_q.filter(Behavior_logs.timestamp >= datetime.strptime(date_from, "%Y-%m-%d"))
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            ids_q = ids_q.filter(Behavior_logs.timestamp <= dt)
        except ValueError:
            pass
    if event_types:
        types = [t.strip() for t in event_types.split(",") if t.strip()]
        if types:
            ids_q = ids_q.filter(Behavior_logs.event_type.in_(types))

    emp_ids_subq = ids_q.subquery()  # (employee_id)

    # --- 2단계: emp_ids_subq ↔ employees ↔ teams ↔ departments 로 이름만 DISTINCT
    # 부서
    dq = (
        db.query(Departments.department_name.label("name"))
          .join(Teams, Teams.department_id == Departments.department_id)
          .join(Employees, Employees.team_id == Teams.team_id)
          .filter(Employees.employee_id.in_(emp_ids_subq))
          .distinct()
          .order_by(Departments.department_name.asc())
    )
    departments = [r.name for r in dq.all() if r.name]

    # 팀 (선택된 부서가 있으면 그 범위로만)
    tq = (
        db.query(Teams.team_name.label("name"))
          .join(Employees, Employees.team_id == Teams.team_id)
          .join(Teams.department)   # to be able to filter by department_name
          .filter(Employees.employee_id.in_(emp_ids_subq))
    )
    if department:
        tq = tq.filter(Departments.department_name == department)
    teams = [r.name for r in tq.distinct().order_by(Teams.team_name.asc()).all() if r.name]

    # 직원 (선택된 부서/팀 범위 반영)
    eq = (
        db.query(Employees.employee_id.label("eid"))
          .join(Teams, Teams.team_id == Employees.team_id)
          .join(Teams.department)
          .filter(Employees.employee_id.in_(emp_ids_subq))
    )
    if department:
        eq = eq.filter(Departments.department_name == department)
    if team:
        eq = eq.filter(Teams.team_name == team)
    employees = [r.eid for r in eq.distinct().order_by(Employees.employee_id.asc()).all() if r.eid]

    out = {"departments": departments, "teams": teams, "employees": employees}
    _fset(fkey, out)
    return out

# -------------------------------
# 메인 목록 (커서 기반 + OFFSET 호환)
# -------------------------------
# services/behavior_logs_service.py

def list_behavior_logs_for_org(
    db: Session,
    org_id,
    *,
    offset: int = 0,
    limit: int = 50,
    department: Optional[str] = None,
    team: Optional[str] = None,
    user: Optional[str] = None,
    pc: Optional[str] = None,
    event_types: Optional[str] = None,
    sort_by: str = "time",          # "time" | "department" | "team" | "user"
    sort_order: str = "desc",       # "asc" | "desc"
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_total: bool = False,
    # 커서 파라미터(기존 유지; time 정렬에만 의미 있음)
    after_ts: Optional[str] = None,
    after_id: Optional[str] = None,
):
    # ---- (A) IDs with keyset or offset ----
    # 조직 제한
    id_q = (
        db.query(Behavior_logs.event_id, Behavior_logs.timestamp)
          .filter(
              exists().where(
                  and_(Pcs.pc_id == Behavior_logs.pc_id,
                       Pcs.organization_id == org_id)
              )
          )
    )

    # 기간/타입/PC
    if date_from:
        try:
            id_q = id_q.filter(Behavior_logs.timestamp >= datetime.strptime(date_from, "%Y-%m-%d"))
        except ValueError:
            pass
    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            id_q = id_q.filter(Behavior_logs.timestamp <= to_dt)
        except ValueError:
            pass
    if event_types:
        types = [t.strip() for t in event_types.split(",") if t.strip()]
        if types:
            id_q = id_q.filter(Behavior_logs.event_type.in_(types))
    if pc:
        id_q = id_q.filter(Behavior_logs.pc_id == pc)

    # 부서/팀/직원 필터 (exists 방식 유지)
    if department or team or user:
        emp_filters = [
            Employees.employee_id == Behavior_logs.employee_id,
            Teams.team_id == Employees.team_id,
            Departments.department_id == Teams.department_id,
        ]
        if department:
            emp_filters.append(Departments.department_name == department)
        if team:
            emp_filters.append(Teams.team_name == team)
        if user:
            emp_filters.append(Employees.employee_id == user)
        id_q = id_q.filter(exists().where(and_(*emp_filters)))

    # ---- 정렬 컬럼 결정 & 조인(정렬만을 위한 outerjoin) ----
    # desc/asc
    desc = (sort_order == "desc")

    # 정렬 컬럼
    if sort_by == "department":
        order_col = Departments.department_name
    elif sort_by == "team":
        order_col = Teams.team_name
    elif sort_by == "user":
        order_col = Employees.employee_id
    else:  # "time"
        order_col = Behavior_logs.timestamp

    # 정렬 컬럼이 직원/팀/부서라면 정렬에 필요한 조인만 추가
    if sort_by in ("department", "team", "user"):
        id_q = (
            id_q.outerjoin(Employees, Employees.employee_id == Behavior_logs.employee_id)
                 .outerjoin(Teams, Teams.team_id == Employees.team_id)
                 .outerjoin(Departments, Departments.department_id == Teams.department_id)
        )

    # 고정 보조키(event_id) 포함한 안정 정렬
    id_q = id_q.order_by(
        order_col.desc() if desc else order_col.asc(),
        Behavior_logs.event_id.desc() if desc else Behavior_logs.event_id.asc(),
    )

    # --- 커서 모드(시간 정렬에서만 의미 있게 유지), 그 외는 OFFSET 사용 ---
    use_cursor = (sort_by == "time") and bool(after_ts and after_id)
    has_more = False

    if use_cursor:
        try:
            ts_val = datetime.fromisoformat(after_ts.replace("Z", ""))
        except Exception:
            ts_val = None

        if ts_val is not None:
            if desc:
                id_q = id_q.filter(
                    or_(Behavior_logs.timestamp < ts_val,
                        and_(Behavior_logs.timestamp == ts_val,
                             Behavior_logs.event_id < after_id))
                )
            else:
                id_q = id_q.filter(
                    or_(Behavior_logs.timestamp > ts_val,
                        and_(Behavior_logs.timestamp == ts_val,
                             Behavior_logs.event_id > after_id))
                )

        rows = id_q.limit(limit + 1).all()
        has_more = len(rows) > limit
        page_pairs = rows[:limit]
        page_ids = [r[0] for r in page_pairs]
    else:
        # OFFSET 경로: 정렬 기준 포함해 캐시 키 분리
        canon_types = _canon_types(event_types)
        cache_key = (
            "pid", str(org_id), date_from or "", date_to or "",
            canon_types, pc or "", department or "", team or "", user or "",
            sort_by, ("desc" if desc else "asc"),
            str(offset), str(limit),
        )
        page_ids = list(_pget(cache_key) or ())
        if not page_ids:
            rows = id_q.limit(min(limit, 1000) + 1).offset(offset).all()
            has_more = len(rows) > limit
            page_ids = [r[0] for r in rows[:limit]]
            _pset(cache_key, page_ids)
        else:
            has_more = len(page_ids) >= limit
        page_pairs = None

    if not page_ids:
        out = {"items": [], "has_more": False, "next_cursor": None}
        if include_total:
            out["total"] = 0
        return out

    # ---- (B) 상세 로드 ----
    q = (
        db.query(Behavior_logs)
          .filter(Behavior_logs.event_id.in_(page_ids))
          .outerjoin(Employees, Employees.employee_id == Behavior_logs.employee_id)
          .outerjoin(Teams, Teams.team_id == Employees.team_id)
          .outerjoin(Departments, Departments.department_id == Teams.department_id)
          .options(
              load_only(
                  Behavior_logs.event_id, Behavior_logs.timestamp, Behavior_logs.event_type,
                  Behavior_logs.employee_id, Behavior_logs.pc_id,
              ),
              selectinload(Behavior_logs.http_log).load_only(Http_logs.event_id, Http_logs.url),
              selectinload(Behavior_logs.email_log).load_only(
                  Email_logs.event_id, Email_logs.from_addr, Email_logs.to, Email_logs.cc, Email_logs.bcc,
                  Email_logs.attachment, Email_logs.size
              ),
              selectinload(Behavior_logs.device_log).load_only(Device_logs.event_id, Device_logs.activity),
              selectinload(Behavior_logs.logon_log).load_only(Logon_logs.event_id, Logon_logs.activity),
              selectinload(Behavior_logs.file_log).load_only(File_logs.event_id, File_logs.filename),
              selectinload(Behavior_logs.employee).load_only(Employees.employee_id)
                  .selectinload(Employees.team).load_only(Teams.team_id, Teams.team_name)
                  .selectinload(Teams.department).load_only(Departments.department_id, Departments.department_name),
          )
    )

    # 부서/팀/직원 필터 한 번 더(정합성)
    if department:
        q = q.filter(Departments.department_name == department)
    if team:
        q = q.filter(Teams.team_name == team)
    if user:
        q = q.filter(Employees.employee_id == user)

    # 상세에서도 같은 정렬(안정화)
    if sort_by == "department":
        order2 = Departments.department_name
    elif sort_by == "team":
        order2 = Teams.team_name
    elif sort_by == "user":
        order2 = Employees.employee_id
    else:
        order2 = Behavior_logs.timestamp

    rows = q.order_by(
        order2.desc() if desc else order2.asc(),
        Behavior_logs.event_id.desc() if desc else Behavior_logs.event_id.asc(),
    ).all()

    items = []
    for bl in rows:
        emp = getattr(bl, "employee", None)
        team_obj = getattr(emp, "team", None) if emp else None
        dept_obj = getattr(team_obj, "department", None) if team_obj else None

        department_name = getattr(dept_obj, "department_name", None)
        team_name = getattr(team_obj, "team_name", None)
        user_display = bl.employee_id

        http = getattr(bl, "http_log", None)
        email = getattr(bl, "email_log", None)
        device = getattr(bl, "device_log", None)
        logon = getattr(bl, "logon_log", None)
        filel = getattr(bl, "file_log", None)
        url = http.url if http else None

        if bl.event_type == "http" and url:
            detail = f"HTTP • {url}"
        elif bl.event_type == "email" and email:
            att = email.attachment or 0
            detail = f"EMAIL • {email.from_addr} -> {email.to} (att:{att})"
        elif bl.event_type == "device" and device:
            detail = f"DEVICE • {device.activity}"
        elif bl.event_type == "logon" and logon:
            detail = f"LOGON • {logon.activity}"
        elif bl.event_type == "file" and filel:
            detail = f"FILE • {filel.filename}"
        else:
            detail = f"{(bl.event_type or '').upper()} • event_id={bl.event_id}"

        items.append({
            "id": bl.event_id,
            "timestamp": bl.timestamp.isoformat(),
            "event_type": bl.event_type,
            "department": department_name,
            "team": team_name,
            "user": user_display,
            "employee_id": bl.employee_id,
            "pc_id": bl.pc_id,
            "detail": detail,
            "url": url,
            "url_host": _host_of(url),
            "from_addr": (email.from_addr if email else None),
            "to": (email.to if email else None),
            "cc": (email.cc if email else None),
            "bcc": (email.bcc if email else None),
            "attachment": (email.attachment if email else None),
            "email_size": (email.size if email else None),
            "email_to_count": ((email.to.count(',') + 1) if (email and email.to) else 0),
            "filename_ext": ((filel.filename.rsplit('.', 1)[-1] if (filel and '.' in filel.filename) else None) if filel else None),
            "device_activity": (device.activity if device else None),
            "logon_activity": (logon.activity if logon else None),
            "filename": (filel.filename if filel else None),
        })

    out = {"items": items, "has_more": bool(has_more)}

    # next_cursor (time 정렬일 때만 유지)
    if use_cursor and page_pairs:
        out["next_cursor"] = {"after_ts": page_pairs[-1][1].isoformat(), "after_id": page_pairs[-1][0]}
    else:
        out["next_cursor"] = None

    # total
    if include_total:
        tkey = ("tot", str(org_id), date_from or "", date_to or "",
                _canon_types(event_types), pc or "", department or "", team or "", user or "")
        t = _tget(tkey)
        if t is None:
            count_q = (
                db.query(func.count(Behavior_logs.event_id))
                  .filter(
                      exists().where(and_(
                          Pcs.pc_id == Behavior_logs.pc_id,
                          Pcs.organization_id == org_id
                      ))
                  )
            )
            if date_from:
                try: count_q = count_q.filter(Behavior_logs.timestamp >= datetime.strptime(date_from, "%Y-%m-%d"))
                except ValueError: pass
            if date_to:
                try:
                    to_dt = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
                    count_q = count_q.filter(Behavior_logs.timestamp <= to_dt)
                except ValueError: pass
            if event_types:
                types = [t.strip() for t in event_types.split(",") if t.strip()]
                if types: count_q = count_q.filter(Behavior_logs.event_type.in_(types))
            if pc:
                count_q = count_q.filter(Behavior_logs.pc_id == pc)
            if department or team or user:
                emp_filters = [
                    Employees.employee_id == Behavior_logs.employee_id,
                    Teams.team_id == Employees.team_id,
                    Departments.department_id == Teams.department_id,
                ]
                if department:
                    emp_filters.append(Departments.department_name == department)
                if team:
                    emp_filters.append(Teams.team_name == team)
                if user:
                    emp_filters.append(Employees.employee_name == user)
                count_q = count_q.filter(exists().where(and_(*emp_filters)))
            t = count_q.scalar() or 0
            _tset(tkey, t)
        out["total"] = t

    return out
