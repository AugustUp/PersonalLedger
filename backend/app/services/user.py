"""User management service."""
from sqlalchemy.orm import Session

from app.core import security
from app.core.exceptions import duplicate, not_found
from app.models.department import Department
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.department import resolve_department_id
from app.utils.query import apply_sort, paginate


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise not_found("用户不存在")
    return user


def _department_name(db: Session, dept_id: int | None) -> str | None:
    if dept_id is None:
        return None
    d = db.get(Department, dept_id)
    return d.name if d else None


def serialize_user(db: Session, user: User) -> dict:
    """序列化为 UserOut 并补上部门名（User 模型无 department_name 列）。"""
    return UserOut.model_validate(user).model_copy(
        update={"department_name": _department_name(db, user.department_id)}
    ).model_dump()


def list_users(db: Session, page: int, page_size: int, keyword: str | None = None):
    q = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter((User.username.like(like)) | (User.real_name.like(like)))
    q = apply_sort(q, User, "created_at", "desc", {})
    items, total, pages = paginate(q, page, page_size)
    out = [
        UserOut.model_validate(u).model_copy(
            update={"department_name": _department_name(db, u.department_id)}
        )
        for u in items
    ]
    return out, total, pages


def create_user(db: Session, data: UserCreate, operator_id: int) -> User:
    if db.query(User).filter(User.username == data.username).first():
        raise duplicate("用户名已存在")
    user = User(
        username=data.username,
        password_hash=security.hash_password(data.password),
        real_name=data.real_name,
        role=data.role,
        department_id=resolve_department_id(db, data.department_id, data.department_name),
        is_active=data.is_active,
    )
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    user = get_user_or_404(db, user_id)
    changes = data.model_dump(exclude_unset=True)
    # 自由填写部门：按名查找或自动创建后转 department_id
    if "department_name" in changes:
        name = changes.pop("department_name")
        changes["department_id"] = resolve_department_id(db, changes.get("department_id"), name)
    for field, value in changes.items():
        # department_id 允许显式置空（清掉部门），其余字段只在非空时更新
        if value is not None or field == "department_id":
            setattr(user, field, value)
    db.flush()
    return user


def reset_password(db: Session, user_id: int, new_password: str) -> User:
    user = get_user_or_404(db, user_id)
    user.password_hash = security.hash_password(new_password)
    db.flush()
    return user
