from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class OrganizationCreate(BaseModel):
    organization_name: str = Field(..., max_length=50)
    authentication_code: str = Field(..., min_length=16, max_length=16)
    description: Optional[str] = None

class OrganizationRead(BaseModel):
    organization_id: UUID
    organization_name: str
    authentication_code: str
    description: Optional[str]

    class Config:
        orm_mode = True
