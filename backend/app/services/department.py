"""Department service."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import conflict, duplicate, not_found
from app.models.department import Department
from app.models.maintenance import MaintenanceRecord
from app.models.network_asset import NetworkAsset
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.utils.query import apply_sort, paginate


def list_departments(db: Session, page: int, page_size: int, keyword: str | None = None):
    q = db.query(Department)
    if keyword:
        q = q.filter(Department.name.like(f"%{keyword}%"))
    q = apply_sort(q, Department, "id", "asc", {})
    items, total, pages = paginate(q, page, page_size)
    out = []
    for d in items:
        cnt = (
            db.query(func.count(User.id))
            .filter(User.department_id == d.id)
            .scalar()
            or 0
        )
        out.append(DepartmentOut.model_validate(d).model_copy(update={"user_count": cnt}))
    return out, total, pages


def create_department(db: Session, data: DepartmentCreate) -> Department:
    if db.query(Department).filter(Department.name == data.name).first():
        raise duplicate("部门名称已存在")
    d = Department(**data.model_dump())
    db.add(d)
    db.flush()
    return d


def resolve_department_id(
    db: Session,
    department_id: int | None = None,
    department_name: str | None = None,
) -> int | None:
    """台账表单"自由填写部门"用：按名称查找部门，不存在则自动创建。

    优先级：department_name（非空）> department_id。在 service 层直接落库，
    不经过 departments 路由权限，因此 operator 录入新部门也不受 403 限制。
    """
    name = (department_name or "").strip()
    if name:
        d = db.query(Department).filter(Department.name == name).first()
        if d is None:
            d = Department(name=name)
            db.add(d)
            db.flush()
        return d.id
    return department_id


def update_department(db: Session, dept_id: int, data: DepartmentUpdate) -> Department:
    d = db.get(Department, dept_id)
    if d is None:
        raise not_found("部门不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(d, field, value)
    db.flush()
    return d


def delete_department(db: Session, dept_id: int) -> None:
    d = db.get(Department, dept_id)
    if d is None:
        raise not_found("部门不存在")
    # 引用保护：被用户 / IP-MAC / 维护台账引用、或有子部门时禁止删除，
    # 避免产生悬空外键（SQLite 外键约束会直接报 500，这里给出友好提示）
    if db.query(Department).filter(Department.parent_id == d.id).first():
        raise conflict("该部门存在下级部门，无法删除")
    if db.query(User).filter(User.department_id == d.id, User.is_active.is_(True)).first():
        raise conflict("该部门下存在用户，无法删除")
    if db.query(NetworkAsset).filter(NetworkAsset.department_id == d.id).first():
        raise conflict("该部门被 IP/MAC 台账引用，无法删除")
    if db.query(MaintenanceRecord).filter(MaintenanceRecord.department_id == d.id).first():
        raise conflict("该部门被维护台账引用，无法删除")
    db.delete(d)
