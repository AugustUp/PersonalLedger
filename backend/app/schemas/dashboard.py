from pydantic import BaseModel


class DashboardSummary(BaseModel):
    meeting_total: int = 0
    meeting_pending: int = 0
    network_asset_total: int = 0
    network_asset_active: int = 0
    account_batch_total: int = 0
    account_batch_pending: int = 0
    maintenance_total: int = 0
    maintenance_pending: int = 0
    maintenance_by_category: dict[str, dict[str, int]] = {}
    user_total: int = 0
    # recent maintenance / meetings for quick view
    recent_maintenance: list[dict] = []
    recent_meetings: list[dict] = []
