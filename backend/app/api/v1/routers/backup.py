"""数据库备份管理（参考开源后台的"备份管理"模块）。

权限：system:backup_manage（默认仅 admin）。备份文件存于 <数据库同目录>/backups/。
"""
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import not_found, ok
from app.models.user import User
from app.services import backup
from app.services.operation_log import log_operation

router = APIRouter(prefix="/system/backup", tags=["system"])


@router.get("", response_model=dict, dependencies=[Depends(RequirePermission("system:backup_manage"))])
def list_backups():
    items = []
    d = backup.backup_dir()
    if os.path.isdir(d):
        for f in sorted(os.listdir(d), reverse=True):
            if not (f.startswith(backup.BACKUP_PREFIX) and f.endswith(".db")):
                continue
            p = os.path.join(d, f)
            items.append({
                "filename": f,
                "size": os.path.getsize(p),
                "created_at": f[len(backup.BACKUP_PREFIX):].replace(".db", ""),
            })
    return ok(items)


@router.post("", response_model=dict, dependencies=[Depends(RequirePermission("system:backup_manage"))])
def create_backup(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not os.path.exists(backup.db_path()):
        raise not_found("数据库文件不存在，无法备份")
    name = backup.run_backup()
    log_operation(db, user_id=user.id, module="system", action="backup",
                  description=f"创建数据库备份 {name}")
    db.commit()
    p = os.path.join(backup.backup_dir(), name)
    return ok({"filename": name, "size": os.path.getsize(p)}, message="备份成功")
