from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from typing import Optional
import re

EMAIL_SPLIT = re.compile(r"[;\s,]+")
BRACKETS    = re.compile(r"^[\{\[\(]+|[\}\]\)]+$")

def _normalize_recipients(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        raw = ";".join(str(v) for v in value if v)
    else:
        raw = str(value)
    raw = raw.strip()
    if not raw:
        return None
    raw = BRACKETS.sub("", raw)
    parts = [p.strip() for p in EMAIL_SPLIT.split(raw) if p and p.strip()]

    seen, uniq = set(), []
    for p in parts:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return ";".join(uniq) if uniq else None

class BehaviorLogCreate(BaseModel):
    event_id: str
    employee_id: str
    pc_id: str
    timestamp: datetime
    event_type: str = Field(..., max_length=10)

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def _normalize_email_extras(cls, values):
        for k in ("to", "cc", "bcc"):
            if k in values:
                values[k] = _normalize_recipients(values[k])
        if not values.get("cc"):
            values["cc"] = "NaN"
        if not values.get("bcc"):
            values["bcc"] = "NaN"
        return values

class BehaviorLogRead(BaseModel):
    event_id: str
    employee_id: str
    pc_id: str
    event_type: str
    timestamp: datetime

    class Config:
        orm_mode = True

class HttpLogCreate(BaseModel):
    url: str

class EmailLogCreate(BaseModel):
    to: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    from_addr: str
    size: int
    attachment: int

    @validator("to", "cc", "bcc", pre=True)
    def convert_to_semicolon_string(cls, v):
        return _normalize_recipients(v)

class DeviceLogCreate(BaseModel):
    activity: str

class LogonLogCreate(BaseModel):
    activity: str

class FileLogCreate(BaseModel):
    filename: str