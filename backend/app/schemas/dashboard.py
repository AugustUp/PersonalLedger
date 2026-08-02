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
    # 今日新增
    today_maintenance: int = 0
    today_meetings: int = 0
    today_assets: int = 0
    today_batches: int = 0
    # 待办清单（维护待处理/处理中，会议待调试）
    todo_maintenance: list[dict] = []
    todo_meetings: list[dict] = []
    # recent maintenance / meetings for quick view
    recent_maintenance: list[dict] = []
    recent_meetings: list[dict] = []
