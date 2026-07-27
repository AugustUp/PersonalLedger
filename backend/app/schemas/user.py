from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    real_name: str = Field(..., min_length=1, max_length=50)
    role: str = Field("operator", pattern="^(admin|manager|operator)$")
    department_id: int | None = None
    is_active: bool = True


class UserCreate(UserBase):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    real_name: str | None = Field(None, max_length=50)
    role: str | None = Field(None, pattern="^(admin|manager|operator)$")
    department_id: int | None = None
    is_active: bool | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str
    role: str
    department_id: int | None = None
    department_name: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
