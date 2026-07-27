from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str | None = Field(None, max_length=50)
    parent_id: int | None = None
    remark: str | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    name: str | None = Field(None, min_length=1, max_length=100)


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None = None
    parent_id: int | None = None
    remark: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_count: int = 0
