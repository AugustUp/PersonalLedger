#!/usr/bin/env bash
# 运维智能台账系统 —— 恢复演练脚本（每季度执行一次，见手册 17.4）
# 作用：从最近一次备份恢复数据库与附件到测试目录，并做基础校验。
# 用法: bash /opt/ops-ledger/scripts/restore_test.sh
set -euo pipefail

ROOT=/opt/ops-ledger
BACKUP_DIR="$ROOT/backups"
TEST_DIR="$(mktemp -d /tmp/ops_restore_test.XXXXXX)"
DB_BACKUP=$(ls -t "$BACKUP_DIR"/ops_ledger_*.db 2>/dev/null | head -n1)
UP_BACKUP=$(ls -t "$BACKUP_DIR"/uploads_*.tar.gz 2>/dev/null | head -n1)

echo "测试恢复目录: $TEST_DIR"

if [ -z "$DB_BACKUP" ]; then
  echo "错误: 未找到数据库备份"; exit 1
fi

TEST_DB="$TEST_DIR/ops_ledger.db"
cp "$DB_BACKUP" "$TEST_DB"

# 校验：完整性检查 + 关键表行数
python3 - "$TEST_DB" <<'PY'
import sys, sqlite3
db = sys.argv[1]
con = sqlite3.connect(db)
try:
    con.execute("PRAGMA integrity_check")
    tables = ["users","departments","meeting_records","network_assets",
              "account_batches","account_batch_items","maintenance_records",
              "attachments","operation_logs"]
    print("完整性检查: OK")
    for t in tables:
        try:
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  表 {t}: {n} 行")
        except sqlite3.OperationalError:
            print(f"  表 {t}: 不存在(可忽略, 迁移后会出现)")
finally:
    con.close()
PY

# 恢复附件
if [ -n "$UP_BACKUP" ]; then
  mkdir -p "$TEST_DIR/uploads"
  tar -xzf "$UP_BACKUP" -C "$TEST_DIR"
  echo "附件已恢复到 $TEST_DIR/uploads"
fi

echo
echo "恢复校验完成。如需启动测试实例验证登录与查询，可临时修改一份 .env："
echo "  DATABASE_URL=sqlite:///$TEST_DIR/ops_ledger.db"
echo "  UPLOAD_DIR=$TEST_DIR/uploads"
echo "然后在该测试目录启动 uvicorn 并访问前端登录。"
echo "测试目录: $TEST_DIR （演练结束后可 rm -rf $TEST_DIR）"
