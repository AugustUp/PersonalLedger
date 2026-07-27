from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageQuery


class OperationLogQuery(PageQuery):
    module: str | None = None
    action: str | None = None
    user_id: int | None = None
    keyword: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class OperationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    module: str
    action: str
    business_id: int | None = None
    description: str | None = None
    request_ip: str | None = None
    created_at: datetime | None = None
