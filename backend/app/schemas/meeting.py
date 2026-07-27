from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageQuery


class MeetingBase(BaseModel):
    meeting_name: str = Field(..., min_length=1, max_length=200)
    meeting_time: datetime | None = None
    location: str | None = Field(None, max_length=200)
    contact_name: str | None = Field(None, max_length=100)
    contact_phone: str | None = Field(None, max_length=50)
    technicians: str | None = Field(None, max_length=300)
    equipment: str | None = None
    debug_content: str | None = None
    problem_description: str | None = None
    handling_process: str | None = None
    result: str | None = None
    onsite_support: bool = False
    status: str = Field("pending", pattern="^(pending|debugged|supporting|completed|cancelled)$")
    remark: str | None = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    meeting_name: str | None = Field(None, max_length=200)
    meeting_time: datetime | None = None
    location: str | None = Field(None, max_length=200)
    contact_name: str | None = Field(None, max_length=100)
    contact_phone: str | None = Field(None, max_length=50)
    technicians: str | None = Field(None, max_length=300)
    equipment: str | None = None
    debug_content: str | None = None
    problem_description: str | None = None
    handling_process: str | None = None
    result: str | None = None
    onsite_support: bool | None = None
    status: str | None = Field(None, pattern="^(pending|debugged|supporting|completed|cancelled)$")
    remark: str | None = None


class MeetingQuery(PageQuery):
    keyword: str | None = None
    status: str | None = None
    location: str | None = None
    contact_name: str | None = None
    technicians: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class MeetingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_no: str
    meeting_name: str
    meeting_time: datetime | None = None
    location: str | None = None
    contact_name: str | None = None
    technicians: str | None = None
    status: str
    onsite_support: bool
    created_by: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MeetingDetail(MeetingListItem):
    contact_phone: str | None = None
    equipment: str | None = None
    debug_content: str | None = None
    problem_description: str | None = None
    handling_process: str | None = None
    result: str | None = None
    remark: str | None = None
