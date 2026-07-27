from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageQuery


class MaintenanceBase(BaseModel):
    category: str | None = Field(None, max_length=50)
    requester: str | None = Field(None, max_length=100)
    department_id: int | None = None
    contact_phone: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=200)
    problem_description: str | None = None
    handling_process: str | None = None
    fault_cause: str | None = None
    result: str | None = None
    status: str = Field(
        "pending", pattern="^(pending|processing|resolved|unresolved|closed)$"
    )
    handler: str | None = Field(None, max_length=100)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    remark: str | None = None


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    category: str | None = Field(None, max_length=50)
    requester: str | None = Field(None, max_length=100)
    department_id: int | None = None
    contact_phone: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=200)
    problem_description: str | None = None
    handling_process: str | None = None
    fault_cause: str | None = None
    result: str | None = None
    status: str | None = Field(
        None, pattern="^(pending|processing|resolved|unresolved|closed)$"
    )
    handler: str | None = Field(None, max_length=100)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    remark: str | None = None


class MaintenanceQuery(PageQuery):
    category: str | None = None
    status: str | None = None
    handler: str | None = None
    requester: str | None = None
    department_id: int | None = None
    keyword: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class MaintenanceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_no: str
    category: str | None = None
    requester: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    location: str | None = None
    status: str
    handler: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MaintenanceDetail(MaintenanceListItem):
    contact_phone: str | None = None
    problem_description: str | None = None
    handling_process: str | None = None
    fault_cause: str | None = None
    result: str | None = None
    remark: str | None = None
