"""Import all models so Base.metadata is fully populated and Alembic
autogenerate / create_all work from a single import."""
from app.models.account_batch import AccountBatch, AccountBatchItem
from app.models.attachment import Attachment
from app.models.department import Department
from app.models.maintenance import MaintenanceRecord
from app.models.meeting import MeetingRecord
from app.models.network_asset import NetworkAsset, NetworkAssetHistory
from app.models.operation_log import OperationLog
from app.models.system_config import SystemConfig
from app.models.user import User

__all__ = [
    "User",
    "Department",
    "MeetingRecord",
    "NetworkAsset",
    "NetworkAssetHistory",
    "AccountBatch",
    "AccountBatchItem",
    "MaintenanceRecord",
    "Attachment",
    "OperationLog",
    "SystemConfig",
]
