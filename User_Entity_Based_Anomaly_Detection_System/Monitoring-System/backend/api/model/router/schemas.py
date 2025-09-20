from pydantic import BaseModel, Field
from typing import Optional , List
from enum import Enum
from uuid import UUID



class RouterCreate(BaseModel):
    organization_id: UUID
    control_ip: str = Field(..., max_length=15)

class RouterUpdate(BaseModel):
    router_id: int
    organization_id: UUID
    state: str = None
    connected_mac_addresses: Optional[List[str]] = None


class RouterRead(BaseModel):
    router_id: int
    control_ip: str
    state: str

    class Config:
        orm_mode = True
