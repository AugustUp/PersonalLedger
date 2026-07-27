from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ImportCommit, ImportErrorItem, ImportPreview, PageQuery


class NetworkAssetBase(BaseModel):
    ip_address: str | None = Field(None, max_length=45)
    mac_address: str | None = Field(None, max_length=17)
    user_name: str | None = Field(None, max_length=100)
    department_id: int | None = None
    device_name: str | None = Field(None, max_length=150)
    device_type: str | None = Field(None, max_length=50)
    building: str | None = Field(None, max_length=100)
    room: str | None = Field(None, max_length=100)
    vlan: str | None = Field(None, max_length=50)
    switch_name: str | None = Field(None, max_length=100)
    switch_port: str | None = Field(None, max_length=100)
    account_name: str | None = Field(None, max_length=100)
    status: str = Field("active", pattern="^(active|inactive|replaced)$")
    registered_at: date | None = None
    remark: str | None = None


class NetworkAssetCreate(NetworkAssetBase):
    pass


class NetworkAssetUpdate(BaseModel):
    ip_address: str | None = Field(None, max_length=45)
    mac_address: str | None = Field(None, max_length=17)
    user_name: str | None = Field(None, max_length=100)
    department_id: int | None = None
    device_name: str | None = Field(None, max_length=150)
    device_type: str | None = Field(None, max_length=50)
    building: str | None = Field(None, max_length=100)
    room: str | None = Field(None, max_length=100)
    vlan: str | None = Field(None, max_length=50)
    switch_name: str | None = Field(None, max_length=100)
    switch_port: str | None = Field(None, max_length=100)
    account_name: str | None = Field(None, max_length=100)
    status: str | None = Field(None, pattern="^(active|inactive|replaced)$")
    registered_at: date | None = None
    remark: str | None = None
    # required: every change must carry a reason (manual 10.2)
    change_reason: str = Field(..., min_length=1, max_length=300)


class NetworkAssetQuery(PageQuery):
    ip_address: str | None = None
    mac_address: str | None = None
    user_name: str | None = None
    department_id: int | None = None
    building: str | None = None
    room: str | None = None
    status: str | None = None
    keyword: str | None = None


class NetworkAssetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: str | None = None
    mac_address: str | None = None
    user_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    device_name: str | None = None
    device_type: str | None = None
    building: str | None = None
    room: str | None = None
    status: str
    registered_at: date | None = None
    updated_at: datetime | None = None


class NetworkAssetDetail(NetworkAssetListItem):
    vlan: str | None = None
    switch_name: str | None = None
    switch_port: str | None = None
    account_name: str | None = None
    remark: str | None = None
    version: int = 0


class NetworkAssetHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    field_name: str
    old_value: str | None = None
    new_value: str | None = None
    change_reason: str | None = None
    changed_by: int | None = None
    changed_at: datetime | None = None
