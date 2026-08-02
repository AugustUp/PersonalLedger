"""IP/MAC ledger service with change history and Excel import (manual 10.2)."""
from datetime import date, datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import conflict, not_found
from app.models.department import Department
from app.models.network_asset import NetworkAsset, NetworkAssetHistory
from app.models.user import User
from app.schemas.network_asset import (
    ImportErrorItem,
    ImportPreview,
    NetworkAssetCreate,
    NetworkAssetQuery,
    NetworkAssetUpdate,
)
from app.services.import_session import drop, get, put
from app.services.department import resolve_department_id
from app.services.operation_log import log_operation
from app.utils.excel import cell_to_text, read_rows
from app.utils.mac import normalize_mac
from app.utils.query import apply_sort, paginate

EXPORT_HEADERS = {
    "id": "ID",
    "ip_address": "IP地址",
    "mac_address": "MAC地址",
    "user_name": "使用人",
    "department_name": "部门",
    "device_name": "设备名称",
    "device_type": "设备类型",
    "building": "楼栋",
    "room": "房间",
    "vlan": "VLAN",
    "switch_name": "交换机",
    "switch_port": "端口",
    "account_name": "认证账号",
    "status": "状态",
    "registered_at": "登记日期",
    "remark": "备注",
}
SORT_WHITELIST = {
    "ip_address": NetworkAsset.ip_address,
    "mac_address": NetworkAsset.mac_address,
    "user_name": NetworkAsset.user_name,
    "status": NetworkAsset.status,
    "updated_at": NetworkAsset.updated_at,
}

# Excel header (CN) -> model field
IMPORT_HEADER_MAP = {
    "IP地址": "ip_address", "IP": "ip_address", "ip_address": "ip_address",
    "MAC地址": "mac_address", "MAC": "mac_address", "mac_address": "mac_address",
    "使用人": "user_name", "用户": "user_name",
    "部门": "department_name",
    "设备名称": "device_name", "设备": "device_name",
    "设备类型": "device_type",
    "楼栋": "building", "楼宇": "building",
    "房间": "room",
    "VLAN": "vlan", "vlan": "vlan",
    "交换机": "switch_name", "接入交换机": "switch_name",
    "端口": "switch_port", "交换机端口": "switch_port",
    "认证账号": "account_name", "账号": "account_name",
    "状态": "status", "status": "status",
    "登记日期": "registered_at", "登记时间": "registered_at",
    "备注": "remark", "说明": "remark",
}
VALID_STATUS = {"active", "inactive", "replaced"}


def _department_id_by_name(db: Session, name: str | None):
    if not name:
        return None
    d = db.query(Department).filter(Department.name == name.strip()).first()
    if d is None:
        return False  # signal not found
    return d.id


def _parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) and not isinstance(value, datetime) else value.date()
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _base_query(db: Session):
    return db.query(NetworkAsset)


def query_assets(db: Session, q: NetworkAssetQuery):
    query = _base_query(db)
    if q.ip_address:
        query = query.filter(NetworkAsset.ip_address.like(f"%{q.ip_address}%"))
    if q.mac_address:
        query = query.filter(NetworkAsset.mac_address.like(f"%{q.mac_address}%"))
    if q.user_name:
        query = query.filter(NetworkAsset.user_name.like(f"%{q.user_name}%"))
    if q.department_id is not None:
        query = query.filter(NetworkAsset.department_id == q.department_id)
    if q.building:
        query = query.filter(NetworkAsset.building.like(f"%{q.building}%"))
    if q.room:
        query = query.filter(NetworkAsset.room.like(f"%{q.room}%"))
    if q.status:
        query = query.filter(NetworkAsset.status == q.status)
    if q.keyword:
        like = f"%{q.keyword}%"
        query = query.filter(
            or_(
                NetworkAsset.ip_address.like(like),
                NetworkAsset.mac_address.like(like),
                NetworkAsset.user_name.like(like),
                NetworkAsset.device_name.like(like),
                NetworkAsset.account_name.like(like),
            )
        )
    query = apply_sort(query, NetworkAsset, q.sort_by, q.sort_order, SORT_WHITELIST)
    items, total, pages = paginate(query, q.page, q.page_size)
    return _with_dept_name(db, items), total, pages


def _with_dept_name(db: Session, items):
    out = []
    for a in items:
        name = None
        if a.department_id:
            d = db.get(Department, a.department_id)
            name = d.name if d else None
        out.append({
            "id": a.id,
            "ip_address": a.ip_address,
            "mac_address": a.mac_address,
            "user_name": a.user_name,
            "department_id": a.department_id,
            "department_name": name,
            "device_name": a.device_name,
            "device_type": a.device_type,
            "building": a.building,
            "room": a.room,
            "status": a.status,
            "registered_at": a.registered_at,
            "updated_at": a.updated_at,
        })
    return out


def get_asset_or_404(db: Session, asset_id: int) -> NetworkAsset:
    a = db.get(NetworkAsset, asset_id)
    if a is None:
        raise not_found("资产不存在")
    return a


def create_asset(db: Session, data: NetworkAssetCreate, user_id: int, ip: str | None) -> NetworkAsset:
    fields = data.model_dump()
    fields["department_id"] = resolve_department_id(
        db, fields.get("department_id"), fields.pop("department_name", None)
    )
    if fields.get("mac_address"):
        fields["mac_address"] = normalize_mac(fields["mac_address"])
        dup = db.query(NetworkAsset).filter(
            NetworkAsset.mac_address == fields["mac_address"]).first()
        if dup:
            raise conflict("MAC 地址已被其他资产占用", {"mac": fields["mac_address"]})
    a = NetworkAsset(**fields)
    db.add(a)
    db.commit()
    db.refresh(a)
    log_operation(db, user_id=user_id, module="network_asset", action="create",
                  business_id=a.id, description="新建 IP/MAC 台账", request_ip=ip)
    db.commit()
    return a


def update_asset(db: Session, asset_id: int, data: NetworkAssetUpdate, user_id: int, ip: str | None) -> NetworkAsset:
    a = get_asset_or_404(db, asset_id)
    changes = data.model_dump(exclude_unset=True)
    reason = changes.pop("change_reason")
    # 自由填写部门：按名查找或自动创建后转 department_id
    if "department_name" in changes:
        changes["department_id"] = resolve_department_id(
            db, changes.get("department_id"), changes.pop("department_name")
        )
    # MAC conflict check (MAC is expected unique)
    new_mac = changes.get("mac_address")
    if new_mac:
        norm = normalize_mac(new_mac)
        dup = (
            db.query(NetworkAsset)
            .filter(NetworkAsset.mac_address == norm, NetworkAsset.id != a.id)
            .first()
        )
        if dup:
            raise conflict("MAC 地址已被其他资产占用", {"mac": norm})
    histories = []
    for field, value in changes.items():
        if field in ("mac_address",) and value:
            value = normalize_mac(value)
        old = getattr(a, field)
        if old != value:
            setattr(a, field, value)
            histories.append(
                NetworkAssetHistory(
                    asset_id=a.id, field_name=field,
                    old_value=str(old) if old is not None else "",
                    new_value=str(value) if value is not None else "",
                    change_reason=reason, changed_by=user_id,
                )
            )
    if histories:
        db.add_all(histories)
    db.commit()
    db.refresh(a)
    log_operation(db, user_id=user_id, module="network_asset", action="update",
                  business_id=a.id, description=f"修改 IP/MAC 台账，{len(histories)} 个字段变更", request_ip=ip)
    db.commit()
    return a


def list_histories(db: Session, asset_id: int):
    return (
        db.query(NetworkAssetHistory)
        .filter(NetworkAssetHistory.asset_id == asset_id)
        .order_by(NetworkAssetHistory.changed_at.desc())
        .all()
    )


# --------------------------------------------------------------------------
# Excel import
# --------------------------------------------------------------------------
def _build_asset_row(db: Session, raw: dict, row_no: int):
    """Validate and normalize one Excel row into a dict of model fields."""
    errors = []
    fields: dict = {}
    for cn_header, value in raw.items():
        field = IMPORT_HEADER_MAP.get(cn_header)
        if not field:
            continue
        text = cell_to_text(value)
        if field == "department_name":
            if text:
                did = _department_id_by_name(db, text)
                if did is False:
                    errors.append(ImportErrorItem(row=row_no, field="department_name",
                                                  message=f"部门不存在: {text}"))
                else:
                    fields["department_id"] = did
            continue
        if field == "mac_address" and text:
            try:
                fields[field] = normalize_mac(text)
            except ValueError:
                errors.append(ImportErrorItem(row=row_no, field="mac_address",
                                              message=f"非法 MAC: {text}"))
            continue
        if field == "registered_at" and text:
            d = _parse_date(text)
            if d is None:
                errors.append(ImportErrorItem(row=row_no, field="registered_at",
                                              message=f"日期格式错误: {text}"))
            else:
                fields[field] = d
            continue
        if field == "status" and text:
            if text not in VALID_STATUS:
                errors.append(ImportErrorItem(row=row_no, field="status",
                                              message=f"未知状态: {text}"))
            else:
                fields[field] = text
            continue
        fields[field] = text or None
    if "status" not in fields:
        fields["status"] = "active"
    return fields, errors


def import_preview(db: Session, file_path: str) -> ImportPreview:
    _, rows = read_rows(file_path)
    errors: list[ImportErrorItem] = []
    valid: list[dict] = []
    sample = []
    for i, raw in enumerate(rows, start=2):  # row 1 is header
        fields, row_errors = _build_asset_row(db, raw, i)
        if row_errors:
            errors.extend(row_errors)
            continue
        valid.append(fields)
        if len(sample) < 5:
            sample.append({k: (v if not isinstance(v, date) else str(v)) for k, v in fields.items()})
    token = put({"business_type": "network_assets", "valid": valid})
    return ImportPreview(
        import_token=token,
        total_rows=len(rows),
        valid_rows=len(valid),
        invalid_rows=len(errors),
        errors=errors,
        sample=sample,
    )


def import_commit(db: Session, token: str, strategy: str, user_id: int, ip: str | None):
    session = get(token)
    if session is None:
        raise not_found("导入会话已过期，请重新上传")
    valid: list[dict] = session["valid"]
    inserted = updated = skipped = 0
    for fields in valid:
        mac = fields.get("mac_address")
        existing = None
        if mac:
            existing = db.query(NetworkAsset).filter(NetworkAsset.mac_address == mac).first()
        if existing is None:
            db.add(NetworkAsset(**fields))
            inserted += 1
        elif strategy == "update":
            for k, v in fields.items():
                setattr(existing, k, v)
            updated += 1
        else:
            skipped += 1
    db.commit()
    drop(token)
    log_operation(db, user_id=user_id, module="network_asset", action="import",
                  description=f"IP/MAC 导入: 新增{inserted} 更新{updated} 跳过{skipped}", request_ip=ip)
    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


def export_rows(db: Session, q: NetworkAssetQuery) -> list[dict]:
    q.page_size = 100000
    items, _, _ = query_assets(db, q)
    rows = []
    for a in items:
        d = {k: a.get(k) for k in EXPORT_HEADERS}
        rows.append(d)
    return rows
