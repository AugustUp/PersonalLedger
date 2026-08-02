"""台账定制：模块名称 / 维护分类 / 字段标签配置。

权限：system:config_manage（默认仅 admin）。GET 返回合并默认值的完整配置，
PUT 局部覆盖（缺省回退默认），保证数据安全（服务端校验 + 日志审计）。
"""
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.services.system_config import get_full_config, update_config

router = APIRouter(prefix="/customization", tags=["customization"])


class ConfigPayload(BaseModel):
    ledger_names: dict[str, Any] | None = None
    maintenance_categories: list[dict[str, Any]] | None = None
    field_meta: dict[str, Any] | None = None


def _ip(request: Request):
    return request.client.host if request.client else None


@router.get("/config", response_model=dict)
def get_config(db: Session = Depends(get_db)):
    """所有登录用户可读（前端各处渲染需要），仅写操作限 admin。"""
    return ok(get_full_config(db))


@router.put("/config", response_model=dict,
            dependencies=[Depends(RequirePermission("system:config_manage"))])
def put_config(payload: ConfigPayload, request: Request,
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    merged = update_config(db, payload.model_dump(exclude_none=True), user.id, _ip(request))
    return ok(merged, message="定制配置已保存")
