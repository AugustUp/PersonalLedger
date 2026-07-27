from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.schemas.user import PasswordReset, UserCreate, UserOut, UserUpdate
from app.services.user import (
    create_user,
    list_users,
    reset_password,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])


def _ip(request: Request):
    return request.client.host if request.client else None


@router.get("", response_model=dict, dependencies=[Depends(RequirePermission("system:user_manage"))])
def list_users_endpoint(
    page: int = 1, page_size: int = 20, keyword: str | None = None,
    db: Session = Depends(get_db),
):
    items, total, pages = list_users(db, page, page_size, keyword)
    return ok({
        "items": [u.model_dump() for u in items],
        "page": page, "page_size": page_size, "total": total, "pages": pages,
    })


@router.post("", response_model=dict, dependencies=[Depends(RequirePermission("system:user_manage"))])
def create_user_endpoint(
    payload: UserCreate, request: Request, db: Session = Depends(get_db),
    operator: User = Depends(get_current_user),
):
    u = create_user(db, payload, operator.id)
    db.commit()
    return ok(UserOut.model_validate(u).model_dump(), message="创建成功")


@router.patch("/{user_id}", response_model=dict,
               dependencies=[Depends(RequirePermission("system:user_manage"))])
def update_user_endpoint(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    u = update_user(db, user_id, payload)
    db.commit()
    return ok(UserOut.model_validate(u).model_dump(), message="更新成功")


@router.post("/{user_id}/reset-password", response_model=dict,
              dependencies=[Depends(RequirePermission("system:user_manage"))])
def reset_password_endpoint(
    user_id: int, payload: PasswordReset, request: Request, db: Session = Depends(get_db),
    operator: User = Depends(get_current_user),
):
    reset_password(db, user_id, payload.new_password)
    db.commit()
    from app.services.operation_log import log_operation
    log_operation(db, user_id=operator.id, module="user", action="reset_password",
                  business_id=user_id, description=f"重置用户密码 {user_id}",
                  request_ip=_ip(request))
    db.commit()
    return ok(message="密码已重置")
