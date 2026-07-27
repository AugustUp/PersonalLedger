from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ok
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
    user = authenticate(db, payload.username, payload.password)
    token = create_access_token(user.id, extra={"role": user.role})
    log_operation(db, user_id=user.id, module="auth", action="login",
                  description=f"{user.username} 登录", request_ip=_client_ip(request))
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
