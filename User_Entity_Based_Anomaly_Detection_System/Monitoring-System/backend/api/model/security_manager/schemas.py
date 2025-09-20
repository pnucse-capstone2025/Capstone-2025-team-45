from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    manager_id: str = Field(..., max_length=50)  # 사용자 지정 로그인 ID
    name: str = Field(..., max_length=50)
    email: EmailStr
    organization_id: UUID

    @validator('email')
    def email_lowercase(cls, v) -> str:
        return v.lower()

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_length(cls, v) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class User(UserBase):
    manager_uuid: UUID  # 내부 고유 식별자
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    class Config:
        orm_mode = True
