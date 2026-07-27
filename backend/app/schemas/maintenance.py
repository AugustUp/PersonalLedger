from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageQuery


class MaintenanceCategory(str, Enum):
    """通用维护台账的任务分类（覆盖会议之外的全部运维领域）。"""
    OA = "OA"
    EMAIL = "邮箱"
    TERMINAL_LICENSE = "终端正版化"
    TERMINAL_SECURITY = "终端安全软件"
    NETWORK = "网络维护"
    WIFI = "WIFI"
    ALARM = "告警维护"
    IP_BAN = "封禁IP"
    WIRELESS_NCECAMPUS = "ncecampus无线"
    WIRELESS_SHENLAN = "深澜无线"
    WIRELESS_AC_AP = "AC维护AP"


# 值 -> 中文标签（与枚举值一致，便于前端直接展示）
CATEGORY_LABELS: dict[str, str] = {m.value: m.value for m in MaintenanceCategory}

# 分类分组（前端下拉可按组展示）
CATEGORY_GROUPS: list[tuple[str, list[str]]] = [
    ("账号类", ["OA", "邮箱"]),
    ("终端类", ["终端正版化", "终端安全软件"]),
    ("网络类", ["网络维护", "WIFI", "告警维护", "封禁IP"]),
    ("无线类", ["ncecampus无线", "深澜无线", "AC维护AP"]),
]


class MaintenanceBase(BaseModel):
    category: MaintenanceCategory | None = None
    related_system: str | None = Field(None, max_length=100)
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
    category: MaintenanceCategory | None = None
    related_system: str | None = Field(None, max_length=100)
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
    related_system: str | None = None
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
    related_system: str | None = None
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
