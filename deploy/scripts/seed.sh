#!/usr/bin/env bash
# 初始化 / 重置管理员账号（默认 admin / admin123），详见 backend/scripts/seed.py
set -e
ROOT=/opt/ops-ledger
source "$ROOT/venv/bin/activate"
cd "$ROOT/backend"
python scripts/seed.py
echo "默认管理员: admin / admin123 （请登录后立即修改密码）"
