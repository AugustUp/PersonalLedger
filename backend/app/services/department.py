"""Department service."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import duplicate, not_found
from app.models.department import Department
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
    db.delete(d)
