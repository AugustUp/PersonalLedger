"""FastAPI dependencies: current user resolution and permission enforcement."""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.core.exceptions import unauthorized
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise unauthorized("缺少访问令牌")
    try:
        payload = security.decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except Exception:
        raise unauthorized("令牌无效或已过期")
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized("用户不存在")
    if not user.is_active:
        raise unauthorized("账号已被停用")
    request.state.user = user
    return user


class RequirePermission:
    """Dependency factory that enforces one or more permission points.

    Usage:
        @router.get(..., dependencies=[Depends(RequirePermission("meeting:export"))])
    """

    def __init__(self, *permissions: str):
        self.permissions = permissions

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        from app.core.security import has_permission

        missing = [p for p in self.permissions if not has_permission(user, p)]
        if missing:
            from app.core.exceptions import forbidden

            raise forbidden(f"缺少权限: {', '.join(missing)}")
        return user
