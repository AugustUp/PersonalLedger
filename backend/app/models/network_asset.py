from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import UniqueConstraint

from app.core.database import Base
from app.models.base import TimestampMixin


class NetworkAsset(Base, TimestampMixin):
    __tablename__ = "network_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(45), index=True, nullable=True)
    mac_address = Column(String(17), index=True, nullable=True)
    user_name = Column(String(100), index=True, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    device_name = Column(String(150), nullable=True)
    device_type = Column(String(50), nullable=True)
    building = Column(String(100), nullable=True)
    room = Column(String(100), nullable=True)
    vlan = Column(String(50), nullable=True)
    switch_name = Column(String(100), nullable=True)
    switch_port = Column(String(100), nullable=True)
    account_name = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="active")
    registered_at = Column(Date, nullable=True)
    remark = Column(Text, nullable=True)
    version = Column(Integer, default=0, nullable=False)


class NetworkAssetHistory(Base):
    __tablename__ = "network_asset_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(
        Integer, ForeignKey("network_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    field_name = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(String(300), nullable=True)
    changed_by = Column(Integer, nullable=True)
    changed_at = Column(DateTime, server_default=func.now(), nullable=False)
