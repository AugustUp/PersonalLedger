"""汇报中心数据汇总：按时间段返回四个台账的明细（供个人工作留底与写汇报）。

设计原则：返回精简的展示字段，任何登录用户可读（个人自用场景）。
"""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.account_batch import AccountBatch
from app.models.maintenance import MaintenanceRecord
from app.models.meeting import MeetingRecord
from app.models.network_asset import NetworkAsset


def _clamp(d: date | None, default: date) -> date:
    return d or default


def _summary(text: str | None, limit: int = 60) -> str | None:
    if not text:
        return None
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def summarize(
    db: Session,
    start: date | None,
    end: date | None,
) -> dict:
    """返回 {模块key: {total, items:[...]}}。按 created_at 落在 [start, end] 过滤。"""
    today = date.today()
    start = _clamp(start, date(1970, 1, 1))
    end = _clamp(end, today)
    s_begin = datetime.combine(start, datetime.min.time())
    s_end = datetime.combine(end, datetime.max.time())

    meetings = (
        db.query(MeetingRecord)
        .filter(MeetingRecord.is_deleted.is_(False), MeetingRecord.created_at >= s_begin, MeetingRecord.created_at <= s_end)
        .order_by(MeetingRecord.created_at.desc())
        .all()
    )
    maintenance = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.is_deleted.is_(False), MaintenanceRecord.created_at >= s_begin, MaintenanceRecord.created_at <= s_end)
        .order_by(MaintenanceRecord.created_at.desc())
        .all()
    )
    assets = (
        db.query(NetworkAsset)
        .filter(NetworkAsset.created_at >= s_begin, NetworkAsset.created_at <= s_end)
        .order_by(NetworkAsset.created_at.desc())
        .all()
    )
    batches = (
        db.query(AccountBatch)
        .filter(
            AccountBatch.created_at >= s_begin,
            AccountBatch.created_at <= s_end,
            AccountBatch.is_deleted.is_(False),
        )
        .order_by(AccountBatch.created_at.desc())
        .all()
    )

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "meetings": {
            "total": len(meetings),
            "items": [
                {
                    "record_no": m.record_no,
                    "title": m.meeting_name,
                    "status": m.status,
                    "occurred_at": (m.meeting_time or m.created_at).isoformat() if (m.meeting_time or m.created_at) else None,
                    "summary": _summary(m.result) or _summary(m.debug_content),
                }
                for m in meetings
            ],
        },
        "maintenance": {
            "total": len(maintenance),
            "items": [
                {
                    "record_no": m.record_no,
                    "title": f"{m.category or '通用'} · {m.requester or '未署名'}",
                    "status": m.status,
                    "occurred_at": m.created_at.isoformat() if m.created_at else None,
                    "summary": _summary(m.result) or _summary(m.problem_description),
                }
                for m in maintenance
            ],
        },
        "network_assets": {
            "total": len(assets),
            "items": [
                {
                    "record_no": f"{a.ip_address or '-'} / {a.mac_address or '-'}",
                    "title": a.device_name or a.user_name or "未命名终端",
                    "status": a.status,
                    "occurred_at": (a.registered_at or a.updated_at or a.created_at).isoformat()
                    if (a.registered_at or a.updated_at or a.created_at) else None,
                    "summary": _summary(a.remark),
                }
                for a in assets
            ],
        },
        "account_batches": {
            "total": len(batches),
            "items": [
                {
                    "record_no": b.batch_no,
                    "title": b.batch_name,
                    "status": b.status,
                    "occurred_at": (b.application_date or b.created_at).isoformat()
                    if (b.application_date or b.created_at) else None,
                    "summary": f"共 {b.total_count} 个（成功 {b.success_count} / 失败 {b.failed_count}）",
                }
                for b in batches
            ],
        },
    }
