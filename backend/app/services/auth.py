"""Authentication service."""
from sqlalchemy.orm import Session

from app.core import security
from app.core.exceptions import unauthorized
from app.models.user import User
from app.schemas.auth import UserMe
from app.services.operation_log import log_operation


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None or not security.verify_password(password, user.password_hash):
        raise unauthorized("用户名或密码错误")
    if not user.is_active:
        raise unauthorized("账号已被停用")
    return user


def build_me(user: User, department_name: str | None, permissions: list[str]) -> UserMe:
    return UserMe(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        role=user.role,
        department_id=user.department_id,
        department_name=department_name,
        permissions=permissions,
    )
