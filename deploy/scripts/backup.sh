#!/usr/bin/env bash
# 运维智能台账系统 —— 每日备份脚本
# 用法: bash /opt/ops-ledger/scripts/backup.sh
# 建议加入 crontab: 0 2 * * * /opt/ops-ledger/scripts/backup.sh >> /opt/ops-ledger/logs/backup.log 2>&1
set -euo pipefail

ROOT=/opt/ops-ledger
DATA_DIR="$ROOT/data"
DB="$DATA_DIR/ops_ledger.db"
UPLOADS="$ROOT/uploads"
BACKUP_DIR="$ROOT/backups"
LOG_DIR="$ROOT/logs"
DATE=$(date +%F_%H%M%S)

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

echo "[$(date '+%F %T')] 开始备份..."

# 1) SQLite 在线备份（使用 backup API，不会长时间锁写）
if [ -f "$DB" ]; then
  python3 - "$DB" "$BACKUP_DIR/ops_ledger_$DATE.db" <<'PY'
import sys, sqlite3, os
src, dst = sys.argv[1], sys.argv[2]
if os.path.exists(dst):
    os.remove(dst)
con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
try:
    b = sqlite3.connect(dst)
    try:
        con.backup(b)
    finally:
        b.close()
finally:
    con.close()
print("db backup done")
PY
else
  echo "警告: 数据库文件不存在 $DB，跳过 DB 备份"
fi

# 2) 附件目录打包
if [ -d "$UPLOADS" ]; then
  tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$ROOT" uploads
  echo "uploads backup done"
fi

# 3) 保留策略：删除 30 天前的备份
find "$BACKUP_DIR" -name 'ops_ledger_*.db' -mtime +30 -delete
find "$BACKUP_DIR" -name 'uploads_*.tar.gz' -mtime +30 -delete

echo "[$(date '+%F %T')] 备份完成: $BACKUP_DIR"
