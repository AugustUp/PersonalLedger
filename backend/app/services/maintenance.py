"""General maintenance ledger service (manual 10.4)."""
from datetime import datetime
from enum import Enum
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.maintenance import MaintenanceRecord
from app.schemas.maintenance import MaintenanceCreate, MaintenanceQuery, MaintenanceUpdate
from app.services.department import resolve_department_id
from app.services.operation_log import log_operation
from app.utils.number import commit_with_no
from app.utils.query import apply_sort, paginate

EXPORT_HEADERS = {
    "record_no": "事项编号",
    "category": "类别",
    "related_system": "关联系统/设备",
    "requester": "报修人",
    "department_name": "部门",
    "location": "地点",
    "contact_phone": "联系电话",
    "problem_description": "问题描述",
    "handling_process": "处理过程",
    "fault_cause": "故障原因",
    "result": "结果",
    "status": "状态",
    "handler": "经办人",
    "started_at": "开始时间",
    "finished_at": "完成时间",
    "remark": "备注",
}
SORT_WHITELIST = {
    "status": MaintenanceRecord.status,
    "category": MaintenanceRecord.category,
    "created_at": MaintenanceRecord.created_at,
}


def _base_query(db: Session):
    return db.query(MaintenanceRecord).filter(MaintenanceRecord.is_deleted.is_(False))


def _dept_name(db: Session, dept_id: int | None):
    from app.models.department import Department
    if not dept_id:
        return None
    d = db.get(Department, dept_id)
    return d.name if d else None


def query_maintenance(db: Session, q: MaintenanceQuery):
    query = _base_query(db)
    if q.keyword:
        like = f"%{q.keyword}%"
        query = query.filter(
            or_(
                MaintenanceRecord.requester.like(like),
                MaintenanceRecord.location.like(like),
                MaintenanceRecord.related_system.like(like),
                MaintenanceRecord.problem_description.like(like),
                MaintenanceRecord.result.like(like),
            )
        )
    if q.category:
        query = query.filter(MaintenanceRecord.category == q.category)
    if q.categories:
        query = query.filter(MaintenanceRecord.category.in_(q.categories))
    if q.related_system:
        query = query.filter(MaintenanceRecord.related_system.like(f"%{q.related_system}%"))
    if q.status:
        query = query.filter(MaintenanceRecord.status == q.status)
    if q.handler:
        query = query.filter(MaintenanceRecord.handler.like(f"%{q.handler}%"))
    if q.requester:
        query = query.filter(MaintenanceRecord.requester.like(f"%{q.requester}%"))
    if q.department_id is not None:
        query = query.filter(MaintenanceRecord.department_id == q.department_id)
    if q.start_date:
        query = query.filter(MaintenanceRecord.created_at >= q.start_date)
    if q.end_date:
        query = query.filter(MaintenanceRecord.created_at <= q.end_date)
    query = apply_sort(query, MaintenanceRecord, q.sort_by, q.sort_order, SORT_WHITELIST)
    items, total, pages = paginate(query, q.page, q.page_size)
    out = []
    for m in items:
        d = {
            "id": m.id,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
        for k in EXPORT_HEADERS:
            if k == "department_name":
                continue
            d[k] = getattr(m, k)
        d["department_name"] = _dept_name(db, m.department_id)
        out.append(d)
    return out, total, pages


def get_maintenance_or_404(db: Session, rec_id: int) -> MaintenanceRecord:
    m = _base_query(db).filter(MaintenanceRecord.id == rec_id).first()
    if m is None:
        raise not_found("维护记录不存在")
    return m


def _to_persist(payload: dict) -> dict:
    """将 Pydantic 模型 dump 出的枚举值转为字符串，便于写入 String 列。"""
    cat = payload.get("category")
    if isinstance(cat, Enum):
        payload["category"] = cat.value
    return payload


def create_maintenance(db: Session, data: MaintenanceCreate, user_id: int, ip: str | None) -> MaintenanceRecord:
    fields = _to_persist(data.model_dump())
    fields["department_id"] = resolve_department_id(
        db, fields.get("department_id"), fields.pop("department_name", None)
    )
    m = MaintenanceRecord(**fields)
    db.add(m)
    commit_with_no(db, m, MaintenanceRecord, "record_no", "OPS")
    log_operation(db, user_id=user_id, module="maintenance", action="create",
                  business_id=m.id, description=f"新建维护事项 {m.record_no}", request_ip=ip)
    db.commit()
    return m


def update_maintenance(db: Session, rec_id: int, data: MaintenanceUpdate, user_id: int, ip: str | None) -> MaintenanceRecord:
    m = get_maintenance_or_404(db, rec_id)
    fields = _to_persist(data.model_dump(exclude_unset=True))
    if "department_name" in fields:
        fields["department_id"] = resolve_department_id(
            db, fields.get("department_id"), fields.pop("department_name")
        )
    for field, value in fields.items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    log_operation(db, user_id=user_id, module="maintenance", action="update",
                  business_id=m.id, description=f"修改维护事项 {m.record_no}", request_ip=ip)
    db.commit()
    return m


def delete_maintenance(db: Session, rec_id: int, user_id: int, ip: str | None) -> None:
    m = get_maintenance_or_404(db, rec_id)
    m.is_deleted = True
    m.deleted_at = datetime.now()
    m.deleted_by = user_id
    db.commit()
    log_operation(db, user_id=user_id, module="maintenance", action="delete",
                  business_id=m.id, description=f"删除维护事项 {m.record_no}", request_ip=ip)
    db.commit()


def restore_maintenance(db: Session, rec_id: int, user_id: int, ip: str | None) -> MaintenanceRecord:
    m = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.id == rec_id, MaintenanceRecord.is_deleted.is_(True)
    ).first()
    if m is None:
        raise not_found("维护记录不存在或未被删除")
    m.is_deleted = False
    m.deleted_at = None
    m.deleted_by = None
    db.commit()
    log_operation(db, user_id=user_id, module="maintenance", action="restore",
                  business_id=m.id, description=f"恢复维护事项 {m.record_no}", request_ip=ip)
    db.commit()
    return m


def export_rows(db: Session, q: MaintenanceQuery) -> list[dict]:
    q.page_size = 100000
    items, _, _ = query_maintenance(db, q)
    return items
