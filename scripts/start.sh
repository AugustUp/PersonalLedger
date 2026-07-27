#!/usr/bin/env bash
# ==============================================================================
# 运维智能台账系统 - 本地一键启动（后端 + 前端）
#
# 用法:
#   bash scripts/start.sh
# 适用: Windows(Git Bash) / 统信UOS 等 Linux(bash)
#
# 行为:
#   1. 先调用 stop.sh 清理可能残留的旧实例（避免端口被占）
#   2. 后台启动后端 uvicorn (端口 8000)
#   3. 后台启动前端 vite dev (端口 5173)
#   4. 等待后端就绪后打印访问地址
#
# 说明: 所有可配置项集中在下方「可配置项」区域，按需修改。
# ==============================================================================
set -uo pipefail

# ============================== 可配置项 =====================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173
RUN_DIR="$PROJECT_DIR/run"
LOG_DIR="$PROJECT_DIR/logs"

# 后端 Python：Windows 开发机用 managed venv（依赖已装好）
VENV_PYTHON="${VENV_PYTHON:-$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe}"
# 统信UOS / 生产环境改用项目内 venv：
# VENV_PYTHON="${VENV_PYTHON:-$BACKEND_DIR/venv/bin/python}"

# 前端 Node：Windows 开发机把 managed node 加入 PATH（如已全局安装可删掉这段）
MANAGED_NODE="$HOME/.workbuddy/binaries/node/versions/22.22.2"
# ==============================================================================

mkdir -p "$RUN_DIR" "$LOG_DIR"

# 确保 managed node 在 PATH（仅当存在时）
if [ -d "$MANAGED_NODE" ]; then
  export PATH="$MANAGED_NODE:$PATH"
fi

# 解析后端 python
PY="$VENV_PYTHON"
if [ ! -x "$PY" ]; then
  echo "[WARN] 未找到 venv python: $PY"
  if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
    PY="$BACKEND_DIR/venv/bin/python"
  else
    echo "[INFO] 项目内无 venv，尝试创建并安装后端依赖..."
    python3 -m venv "$BACKEND_DIR/venv" >/dev/null 2>&1 \
      && "$BACKEND_DIR/venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt" >/dev/null 2>&1 \
      && PY="$BACKEND_DIR/venv/bin/python" \
      || { echo "[ERROR] 找不到可用的 Python，请先安装依赖或设置 VENV_PYTHON"; exit 1; }
  fi
fi

echo "==> 项目目录: $PROJECT_DIR"
echo "==> 后端 Python: $PY"

# 先停掉残留实例
if [ -f "$PROJECT_DIR/scripts/stop.sh" ]; then
  bash "$PROJECT_DIR/scripts/stop.sh" || true
fi

# 启动后端
echo "==> 启动后端 (uvicorn :$BACKEND_PORT) ..."
cd "$BACKEND_DIR"
nohup "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload \
  > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$RUN_DIR/backend.pid"

# 启动前端
echo "==> 启动前端 (vite :$FRONTEND_PORT) ..."
cd "$FRONTEND_DIR"
nohup npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" \
  > "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$RUN_DIR/frontend.pid"

# 等待后端就绪
echo "==> 等待后端就绪..."
READY=0
for i in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/api/v1/maintenance-records" 2>/dev/null)"
  if [ -n "$code" ] && [ "$code" != "000" ]; then
    echo "    后端已就绪 (${i}s, HTTP $code)"
    READY=1
    break
  fi
  sleep 1
done
[ "$READY" -eq 0 ] && echo "    [WARN] 后端未在 60s 内就绪，请查看 $LOG_DIR/backend.log"

echo ""
echo "✅ 启动完成:"
echo "   前端: http://localhost:$FRONTEND_PORT"
echo "   后端: http://localhost:$BACKEND_PORT"
echo "   后端日志: $LOG_DIR/backend.log"
echo "   前端日志: $LOG_DIR/frontend.log"
echo "   关闭:    bash scripts/stop.sh"
