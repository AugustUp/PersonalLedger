"""SQLite 数据库备份服务（供 /system/backup 接口与独立脚本共用）。"""
import os
import sqlite3
from datetime import datetime

from app.core.config import settings

BACKUP_PREFIX = "ops_ledger_backup_"


def db_path() -> str:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        raise ValueError(f"仅支持 SQLite 备份，当前 database_url: {url}")
    return os.path.abspath(url.replace("sqlite:///", "", 1))


def backup_dir() -> str:
    d = os.path.join(os.path.dirname(db_path()), "backups")
    os.makedirs(d, exist_ok=True)
    return d


def prune(keep: int = 10) -> None:
    files = sorted(
        f for f in os.listdir(backup_dir())
        if f.startswith(BACKUP_PREFIX) and f.endswith(".db")
    )
    for f in files[:-keep]:
        os.remove(os.path.join(backup_dir(), f))


def run_backup(keep: int = 10) -> str:
    src = db_path()
    if not os.path.exists(src):
        raise FileNotFoundError(f"数据库文件不存在: {src}")
    name = f"{BACKUP_PREFIX}{datetime.now():%Y%m%d_%H%M%S}.db"
    dst = os.path.join(backup_dir(), name)
    src_conn = sqlite3.connect(src)
    dst_conn = sqlite3.connect(dst)
    try:
        src_conn.backup(dst_conn)  # WAL 安全快照，可在服务运行中执行
    finally:
        dst_conn.close()
        src_conn.close()
    prune(keep)
    return name
