"""Account batch ledger service (manual 10.3).

Batch master + detail rows. Counts (total/success/failed/pending) and status are
always recomputed by the backend inside the same transaction.
"""
from datetime import date, datetime
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import conflict, duplicate, not_found
from app.models.account_batch import AccountBatch, AccountBatchItem
from app.schemas.account_batch import (
    AccountBatchCreate,
    AccountBatchItemQuery,
    AccountBatchQuery,
    AccountBatchUpdate,
    BatchItemResultUpdate,
)
from app.services.import_session import drop, get, put
from app.services.operation_log import log_operation
from app.schemas.common import ImportErrorItem
from app.utils.excel import cell_to_text, read_rows
from app.utils.number import commit_with_no
from app.utils.query import apply_sort, paginate

EXPORT_HEADERS = {
    "real_name": "姓名",
    "identity_no": "工号或学号",
    "department": "部门",
    "account_name": "账号名称",
    "account_type": "账号类型",
    "permission_type": "权限类型",
    "valid_until": "有效期",
    "result": "开通结果",
    "failure_reason": "失败原因",
    "processed_at": "处理时间",
    "remark": "备注",
}
ITEM_IMPORT_HEADER_MAP = {
    "姓名": "real_name", "名字": "real_name",
    "工号或学号": "identity_no", "工号": "identity_no", "学号": "identity_no",
    "部门": "department",
    "账号名称": "account_name", "账号": "account_name",
    "账号类型": "account_type",
    "权限类型": "permission_type",
    "有效期": "valid_until", "有效期限": "valid_until",
    "开通结果": "result", "结果": "result",
    "失败原因": "failure_reason", "原因": "failure_reason",
    "备注": "remark",
}
VALID_RESULT = {"pending", "success", "failed", "skipped"}
SORT_WHITELIST = {
    "application_date": AccountBatch.application_date,
    "status": AccountBatch.status,
    "created_at": AccountBatch.created_at,
}


def _base_query(db: Session):
    return db.query(AccountBatch).filter(AccountBatch.is_deleted.is_(False))


def query_batches(db: Session, q: AccountBatchQuery):
    query = _base_query(db)
    if q.batch_name:
        query = query.filter(AccountBatch.batch_name.like(f"%{q.batch_name}%"))
    if q.account_type:
        query = query.filter(AccountBatch.account_type == q.account_type)
    if q.status:
        query = query.filter(AccountBatch.status == q.status)
    if q.applicant:
        query = query.filter(AccountBatch.applicant.like(f"%{q.applicant}%"))
    if q.start_date:
        query = query.filter(AccountBatch.application_date >= q.start_date)
    if q.end_date:
        query = query.filter(AccountBatch.application_date <= q.end_date)
    query = apply_sort(query, AccountBatch, q.sort_by, q.sort_order, SORT_WHITELIST)
    items, total, pages = paginate(query, q.page, q.page_size)
    return items, total, pages


def get_batch_or_404(db: Session, batch_id: int) -> AccountBatch:
    b = _base_query(db).filter(AccountBatch.id == batch_id).first()
    if b is None:
        raise not_found("批次不存在")
    return b


def create_batch(db: Session, data: AccountBatchCreate, user_id: int, ip: str | None) -> AccountBatch:
    b = AccountBatch(created_by=user_id, **data.model_dump())
    db.add(b)
    commit_with_no(db, b, AccountBatch, "batch_no", "ACC")
    log_operation(db, user_id=user_id, module="account_batch", action="create",
                  business_id=b.id, description=f"新建账号批次 {b.batch_no}", request_ip=ip)
    db.commit()
    return b


def update_batch(db: Session, batch_id: int, data: AccountBatchUpdate, user_id: int, ip: str | None) -> AccountBatch:
    b = get_batch_or_404(db, batch_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(b, field, value)
    db.commit()
    db.refresh(b)
    log_operation(db, user_id=user_id, module="account_batch", action="update",
                  business_id=b.id, description="修改账号批次", request_ip=ip)
    db.commit()
    return b


def delete_batch(db: Session, batch_id: int, user_id: int, ip: str | None) -> None:
    b = get_batch_or_404(db, batch_id)
    b.is_deleted = True
    b.deleted_at = datetime.now()
    b.deleted_by = user_id
    db.query(AccountBatchItem).filter(
        AccountBatchItem.batch_id == batch_id, AccountBatchItem.is_deleted.is_(False)
    ).update({AccountBatchItem.is_deleted: True})
    db.commit()
    log_operation(db, user_id=user_id, module="account_batch", action="delete",
                  business_id=b.id, description=f"作废账号批次 {b.batch_no}", request_ip=ip)
    db.commit()


def _recompute(db: Session, batch: AccountBatch) -> None:
    total = (
        db.query(func.count(AccountBatchItem.id))
        .filter(AccountBatchItem.batch_id == batch.id, AccountBatchItem.is_deleted.is_(False))
        .scalar()
        or 0
    )
    success = (
        db.query(func.count(AccountBatchItem.id))
        .filter(AccountBatchItem.batch_id == batch.id, AccountBatchItem.is_deleted.is_(False),
                AccountBatchItem.result == "success")
        .scalar()
        or 0
    )
    failed = (
        db.query(func.count(AccountBatchItem.id))
        .filter(AccountBatchItem.batch_id == batch.id, AccountBatchItem.is_deleted.is_(False),
                AccountBatchItem.result == "failed")
        .scalar()
        or 0
    )
    pending = total - success - failed
    batch.total_count = total
    batch.success_count = success
    batch.failed_count = failed
    batch.pending_count = pending
    if total == 0:
        batch.status = "draft"
    elif pending > 0 and (success + failed) == 0:
        batch.status = "pending"
    elif pending > 0:
        batch.status = "partial"
    else:
        batch.status = "completed"


def query_items(db: Session, batch_id: int, q: AccountBatchItemQuery):
    get_batch_or_404(db, batch_id)
    query = db.query(AccountBatchItem).filter(
        AccountBatchItem.batch_id == batch_id, AccountBatchItem.is_deleted.is_(False)
    )
    if q.result:
        query = query.filter(AccountBatchItem.result == q.result)
    if q.keyword:
        like = f"%{q.keyword}%"
        query = query.filter(
            or_(AccountBatchItem.account_name.like(like), AccountBatchItem.real_name.like(like))
        )
    query = apply_sort(query, AccountBatchItem, q.sort_by, q.sort_order, {})
    items, total, pages = paginate(query, q.page, q.page_size)
    return items, total, pages


def import_preview(db: Session, batch_id: int, file_path: str):
    get_batch_or_404(db, batch_id)
    _, rows = read_rows(file_path)
    errors = []
    valid = []
    sample = []
    existing_names = set(
        r[0]
        for r in db.query(AccountBatchItem.account_name).filter(
            AccountBatchItem.batch_id == batch_id, AccountBatchItem.is_deleted.is_(False)
        ).all()
        if r[0]
    )
    seen = set()
    for i, raw in enumerate(rows, start=2):
        fields, row_errors = _build_item_row(raw, i, seen, existing_names)
        if row_errors:
            errors.extend(row_errors)
            continue
        valid.append(fields)
        if len(sample) < 5:
            sample.append({k: (str(v) if isinstance(v, (date, datetime)) else v) for k, v in fields.items()})
    token = put({"business_type": "account_batch_items", "batch_id": batch_id, "valid": valid})
    return {
        "import_token": token,
        "total_rows": len(rows),
        "valid_rows": len(valid),
        "invalid_rows": len(errors),
        "errors": errors,
        "sample": sample,
    }


def _build_item_row(raw: dict, row_no: int, seen: set, existing_names: set):
    from datetime import datetime as _dt

    from app.schemas.common import ImportErrorItem

    errors = []
    fields: dict = {}
    for cn_header, value in raw.items():
        field = ITEM_IMPORT_HEADER_MAP.get(cn_header)
        if not field:
            continue
        text = cell_to_text(value)
        if field == "valid_until" and text:
            d = None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    d = _dt.strptime(text, fmt).date()
                    break
                except ValueError:
                    continue
            if d is None:
                errors.append(ImportErrorItem(row=row_no, field="valid_until",
                                              message=f"日期格式错误: {text}"))
            else:
                fields[field] = d
            continue
        if field == "result" and text:
            if text not in VALID_RESULT:
                errors.append(ImportErrorItem(row=row_no, field="result",
                                              message=f"未知结果: {text}"))
            else:
                fields[field] = text
            continue
        fields[field] = text or None
    # required checks
    if not fields.get("real_name"):
        errors.append(ImportErrorItem(
            row=row_no, field="real_name", message="姓名为空"))
    if not fields.get("identity_no"):
        errors.append(ImportErrorItem(
            row=row_no, field="identity_no", message="工号或学号为空"))
    if not fields.get("account_name"):
        errors.append(ImportErrorItem(
            row=row_no, field="account_name", message="账号名称为空"))
    else:
        name = fields["account_name"]
        if name in seen or name in existing_names:
            errors.append(ImportErrorItem(
                row=row_no, field="account_name", message="批次内账号重复"))
        else:
            seen.add(name)
    if fields.get("result") == "failed" and not fields.get("failure_reason"):
        errors.append(ImportErrorItem(
            row=row_no, field="failure_reason", message="失败原因必填"))
    if "result" not in fields:
        fields["result"] = "pending"
    return fields, errors


def import_commit(db: Session, batch_id: int, token: str, user_id: int, ip: str | None):
    session = get(token)
    if session is None or session.get("batch_id") != batch_id:
        raise not_found("导入会话已过期，请重新上传")
    valid = session["valid"]
    inserted = 0
    for fields in valid:
        db.add(AccountBatchItem(batch_id=batch_id, **fields))
        inserted += 1
    batch = get_batch_or_404(db, batch_id)
    db.flush()
    _recompute(db, batch)
    db.commit()
    drop(token)
    log_operation(db, user_id=user_id, module="account_batch", action="import",
                  business_id=batch.id,
                  description=f"导入名单 {inserted} 条 ({batch.batch_no})", request_ip=ip)
    db.commit()
    return {"inserted": inserted}


def batch_update_results(db: Session, batch_id: int, updates: list[BatchItemResultUpdate], user_id: int, ip: str | None):
    get_batch_or_404(db, batch_id)
    updated = 0
    for u in updates:
        item = db.get(AccountBatchItem, u.id)
        if item is None or item.batch_id != batch_id or item.is_deleted:
            continue
        item.result = u.result
        item.failure_reason = u.failure_reason
        item.processed_at = datetime.now()
        updated += 1
    batch = get_batch_or_404(db, batch_id)
    db.flush()
    _recompute(db, batch)
    db.commit()
    log_operation(db, user_id=user_id, module="account_batch", action="update_items",
                  business_id=batch.id, description=f"批量更新结果 {updated} 条", request_ip=ip)
    db.commit()
    return {"updated": updated}


def export_rows(db: Session, batch_id: int, which: str = "all") -> list[dict]:
    get_batch_or_404(db, batch_id)
    query = db.query(AccountBatchItem).filter(
        AccountBatchItem.batch_id == batch_id, AccountBatchItem.is_deleted.is_(False)
    )
    if which == "success":
        query = query.filter(AccountBatchItem.result == "success")
    elif which == "failed":
        query = query.filter(AccountBatchItem.result == "failed")
    elif which == "pending":
        query = query.filter(AccountBatchItem.result == "pending")
    items = query.order_by(AccountBatchItem.id.asc()).all()
    return [{k: getattr(it, k) for k in EXPORT_HEADERS} for it in items]
