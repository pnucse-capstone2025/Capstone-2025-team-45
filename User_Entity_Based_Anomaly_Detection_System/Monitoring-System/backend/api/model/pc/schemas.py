from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from enum import Enum


class LogonState(str, Enum):
    ON = "logged_in"
    OFF = "logged_out"
    UNKNOWN = "unknown"


class PcsCreate(BaseModel):
    pc_id: str = Field(..., max_length=80)
    organization_id: UUID
    ip_address: str = Field(..., max_length=15)
    mac_address: str = Field(..., max_length=17)

class PcsRead(BaseModel):
    pc_id: str
    ip_address: str
    mac_address: str
    access_flag: bool
    present_user_id: Optional[str]
    current_state: LogonState

    class Config:
        orm_mode = True
