"""Meeting / 会议调试 ledger service (manual 10.1)."""
from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.meeting import MeetingRecord
from app.schemas.meeting import MeetingCreate, MeetingQuery, MeetingUpdate
from app.services.operation_log import log_operation
from app.utils.number import commit_with_no
from app.utils.query import apply_sort, paginate

EXPORT_HEADERS = {
    "record_no": "记录编号",
    "meeting_name": "会议名称",
    "meeting_time": "会议时间",
    "location": "地点",
    "contact_name": "联系人",
    "contact_phone": "联系电话",
    "technicians": "调试人员",
    "equipment": "设备清单",
    "debug_content": "调试内容",
    "problem_description": "发现问题",
    "handling_process": "处理过程",
    "result": "结果",
    "onsite_support": "现场保障",
    "status": "状态",
    "remark": "备注",
}
SORT_WHITELIST = {
    "meeting_time": MeetingRecord.meeting_time,
    "status": MeetingRecord.status,
    "created_at": MeetingRecord.created_at,
}


def _base_query(db: Session):
    return db.query(MeetingRecord).filter(MeetingRecord.is_deleted.is_(False))


def query_meetings(db: Session, q: MeetingQuery):
    query = _base_query(db)
    if q.keyword:
        like = f"%{q.keyword}%"
        query = query.filter(
            or_(
                MeetingRecord.meeting_name.like(like),
                MeetingRecord.contact_name.like(like),
                MeetingRecord.technicians.like(like),
                MeetingRecord.result.like(like),
            )
        )
    if q.status:
        query = query.filter(MeetingRecord.status == q.status)
    if q.location:
        query = query.filter(MeetingRecord.location.like(f"%{q.location}%"))
    if q.contact_name:
        query = query.filter(MeetingRecord.contact_name.like(f"%{q.contact_name}%"))
    if q.technicians:
        query = query.filter(MeetingRecord.technicians.like(f"%{q.technicians}%"))
    if q.start_date:
        query = query.filter(MeetingRecord.meeting_time >= q.start_date)
    if q.end_date:
        query = query.filter(MeetingRecord.meeting_time <= q.end_date)
    query = apply_sort(query, MeetingRecord, q.sort_by, q.sort_order, SORT_WHITELIST)
    items, total, pages = paginate(query, q.page, q.page_size)
    return items, total, pages


def get_meeting_or_404(db: Session, meeting_id: int) -> MeetingRecord:
    m = _base_query(db).filter(MeetingRecord.id == meeting_id).first()
    if m is None:
        raise not_found("会议记录不存在")
    return m


def create_meeting(db: Session, data: MeetingCreate, user_id: int, ip: str | None) -> MeetingRecord:
    m = MeetingRecord(created_by=user_id, **data.model_dump())
    db.add(m)
    commit_with_no(db, m, MeetingRecord, "record_no", "MTG")
    log_operation(db, user_id=user_id, module="meeting", action="create",
                  business_id=m.id, description=f"新建会议调试 {m.record_no}", request_ip=ip)
    db.commit()
    return m


def update_meeting(db: Session, meeting_id: int, data: MeetingUpdate, user_id: int, ip: str | None) -> MeetingRecord:
    m = get_meeting_or_404(db, meeting_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    log_operation(db, user_id=user_id, module="meeting", action="update",
                  business_id=m.id, description=f"修改会议调试 {m.record_no}", request_ip=ip)
    db.commit()
    return m


def delete_meeting(db: Session, meeting_id: int, user_id: int, ip: str | None) -> None:
    m = get_meeting_or_404(db, meeting_id)
    m.is_deleted = True
    m.deleted_at = _now()
    m.deleted_by = user_id
    db.commit()
    log_operation(db, user_id=user_id, module="meeting", action="delete",
                  business_id=m.id, description=f"删除会议调试 {m.record_no}", request_ip=ip)
    db.commit()


def restore_meeting(db: Session, meeting_id: int, user_id: int, ip: str | None) -> MeetingRecord:
    m = db.query(MeetingRecord).filter(
        MeetingRecord.id == meeting_id, MeetingRecord.is_deleted.is_(True)
    ).first()
    if m is None:
        raise not_found("会议记录不存在或未被删除")
    m.is_deleted = False
    m.deleted_at = None
    m.deleted_by = None
    db.commit()
    log_operation(db, user_id=user_id, module="meeting", action="restore",
                  business_id=m.id, description=f"恢复会议调试 {m.record_no}", request_ip=ip)
    db.commit()
    return m


def export_rows(db: Session, q: MeetingQuery) -> list[dict]:
    q.page_size = 100000
    items, _, _ = query_meetings(db, q)
    rows = []
    for m in items:
        d = {k: getattr(m, k) for k in EXPORT_HEADERS}
        d["onsite_support"] = "是" if m.onsite_support else "否"
        rows.append(d)
    return rows


def _now():
    from datetime import datetime
    return datetime.now()
