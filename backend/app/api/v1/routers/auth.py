from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import BizError, ok, too_many_requests
from app.core.login_guard import is_locked, record_failure, reset
from app.core.security import create_access_token, user_permissions
from app.models.department import Department
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe
from app.services.auth import authenticate, build_me
from app.services.operation_log import log_operation

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/login", response_model=dict)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    locked, remain = is_locked(payload.username, ip)
    if locked:
        raise too_many_requests(f"登录失败次数过多，账号已锁定 {remain} 秒，请稍后再试")

    try:
        user = authenticate(db, payload.username, payload.password)
    except BizError as e:
        # 凭据错误/账号停用：记录失败次数 + 登录失败日志（防爆破 + 可审计）
        record_failure(payload.username, ip)
        u = db.query(User).filter(User.username == payload.username).first()
        log_operation(db, user_id=u.id if u else None, module="auth", action="login_failed",
                      description=f"{payload.username} 登录失败：{e.message}", request_ip=ip)
        db.commit()
        raise e

    reset(payload.username, ip)
    token = create_access_token(user.id, extra={"role": user.role})
    log_operation(db, user_id=user.id, module="auth", action="login",
                  description=f"{user.username} 登录", request_ip=ip)
    db.commit()
    return ok(TokenResponse(access_token=token, expires_in=480).model_dump())


@router.get("/me", response_model=dict)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dept_name = None
    if user.department_id:
        d = db.get(Department, user.department_id)
        dept_name = d.name if d else None
    return ok(build_me(user, dept_name, user_permissions(user.role)).model_dump())


@router.post("/logout", response_model=dict)
def logout(request: Request, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    log_operation(db, user_id=user.id, module="auth", action="logout",
                  description=f"{user.username} 退出", request_ip=_client_ip(request))
    db.commit()
    return ok(message="已退出")
