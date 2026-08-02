"""SQLite 数据库备份脚本（复用后端 backup 服务，也可定时执行）。

用法：
    python scripts/backup_db.py                 # 备份到 <db同目录>/backups/
    python scripts/backup_db.py --keep 20       # 保留最近 20 份（默认 10）

恢复：停服后，用备份文件替换 data/ops_ledger.db 即可（先停 uvicorn）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.services.backup import backup_dir, db_path, run_backup  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="备份 SQLite 数据库")
    parser.add_argument("--keep", type=int, default=10, help="保留最近 N 份备份")
    args = parser.parse_args()
    name = run_backup(args.keep)
    size = os.path.getsize(os.path.join(backup_dir(), name))
    print(f"[OK] 已备份 {db_path()} -> {os.path.join(backup_dir(), name)} ({size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
