"""Dashboard summary service (manual 8.5.5, 10.4)."""
from datetime import date, datetime

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.account_batch import AccountBatch
from app.models.maintenance import MaintenanceRecord
from app.models.meeting import MeetingRecord
from app.models.network_asset import NetworkAsset
from app.models.user import User
from app.schemas.dashboard import DashboardSummary


def get_summary(db: Session) -> DashboardSummary:
    today0 = datetime.combine(date.today(), datetime.min.time())

    meeting_total = db.query(func.count(MeetingRecord.id)).filter(
        MeetingRecord.is_deleted.is_(False)).scalar() or 0
    meeting_pending = db.query(func.count(MeetingRecord.id)).filter(
        MeetingRecord.is_deleted.is_(False), MeetingRecord.status == "pending").scalar() or 0
    net_total = db.query(func.count(NetworkAsset.id)).scalar() or 0
    net_active = db.query(func.count(NetworkAsset.id)).filter(
        NetworkAsset.status == "active").scalar() or 0
    batch_total = db.query(func.count(AccountBatch.id)).filter(
        AccountBatch.is_deleted.is_(False)).scalar() or 0
    batch_pending = db.query(func.count(AccountBatch.id)).filter(
        AccountBatch.is_deleted.is_(False), AccountBatch.status.in_(["draft", "pending", "processing"])).scalar() or 0
    maint_total = db.query(func.count(MaintenanceRecord.id)).filter(
        MaintenanceRecord.is_deleted.is_(False)).scalar() or 0
    maint_pending = db.query(func.count(MaintenanceRecord.id)).filter(
        MaintenanceRecord.is_deleted.is_(False), MaintenanceRecord.status.in_(["pending", "processing"])).scalar() or 0
    maint_by_cat: dict[str, dict[str, int]] = {}
    for cat, total, pending in db.query(
        MaintenanceRecord.category,
        func.count(MaintenanceRecord.id),
        func.coalesce(func.sum(case((MaintenanceRecord.status.in_(["pending", "processing"]), 1), else_=0)), 0),
    ).filter(MaintenanceRecord.is_deleted.is_(False)).group_by(MaintenanceRecord.category).all():
        maint_by_cat[cat or "未分类"] = {"total": total, "pending": int(pending)}
    user_total = db.query(func.count(User.id)).scalar() or 0

    # 今日新增
    today_maintenance = db.query(func.count(MaintenanceRecord.id)).filter(
        MaintenanceRecord.is_deleted.is_(False), MaintenanceRecord.created_at >= today0).scalar() or 0
    today_meetings = db.query(func.count(MeetingRecord.id)).filter(
        MeetingRecord.is_deleted.is_(False), MeetingRecord.created_at >= today0).scalar() or 0
    today_assets = db.query(func.count(NetworkAsset.id)).filter(
        NetworkAsset.created_at >= today0).scalar() or 0
    today_batches = db.query(func.count(AccountBatch.id)).filter(
        AccountBatch.is_deleted.is_(False), AccountBatch.created_at >= today0).scalar() or 0

    # 待办清单（维护：待处理/处理中；会议：待调试）
    todo_maintenance = [
        {"id": m.id, "record_no": m.record_no, "category": m.category,
         "requester": m.requester, "status": m.status, "location": m.location}
        for m in db.query(MaintenanceRecord).filter(
            MaintenanceRecord.is_deleted.is_(False),
            MaintenanceRecord.status.in_(["pending", "processing"]))
        .order_by(MaintenanceRecord.created_at.asc()).limit(20).all()
    ]
    todo_meetings = [
        {"id": m.id, "record_no": m.record_no, "meeting_name": m.meeting_name,
         "status": m.status,
         "meeting_time": m.meeting_time.isoformat() if m.meeting_time else None}
        for m in db.query(MeetingRecord).filter(
            MeetingRecord.is_deleted.is_(False), MeetingRecord.status == "pending")
        .order_by(MeetingRecord.meeting_time.asc()).limit(20).all()
    ]

    recent_maintenance = [
        {"id": m.id, "record_no": m.record_no, "category": m.category,
         "status": m.status, "requester": m.requester}
        for m in db.query(MaintenanceRecord).filter(MaintenanceRecord.is_deleted.is_(False))
        .order_by(MaintenanceRecord.created_at.desc()).limit(8).all()
    ]
    recent_meetings = [
        {"id": m.id, "record_no": m.record_no, "meeting_name": m.meeting_name,
         "status": m.status, "meeting_time": m.meeting_time.isoformat() if m.meeting_time else None}
        for m in db.query(MeetingRecord).filter(MeetingRecord.is_deleted.is_(False))
        .order_by(MeetingRecord.meeting_time.desc()).limit(8).all()
    ]
    return DashboardSummary(
        meeting_total=meeting_total, meeting_pending=meeting_pending,
        network_asset_total=net_total, network_asset_active=net_active,
        account_batch_total=batch_total, account_batch_pending=batch_pending,
        maintenance_total=maint_total, maintenance_pending=maint_pending,
        maintenance_by_category=maint_by_cat,
        user_total=user_total,
        today_maintenance=today_maintenance, today_meetings=today_meetings,
        today_assets=today_assets, today_batches=today_batches,
        todo_maintenance=todo_maintenance, todo_meetings=todo_meetings,
        recent_maintenance=recent_maintenance, recent_meetings=recent_meetings,
    )
