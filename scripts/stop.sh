#!/usr/bin/env bash
# ==============================================================================
# 运维智能台账系统 - 停止后端 + 前端
#
# 用法:
#   bash scripts/stop.sh
# 适用: Windows(Git Bash) / 统信UOS 等 Linux(bash)
#
# 行为:
#   1. 通过 run/*.pid 文件精确终止本脚本启动的进程
#   2. 兜底: 按端口终止（Windows 用 taskkill /T 杀进程树，
#      仅杀真实存在的进程，跳过 Windows 的"幽灵监听"残留）
#   3. 最终确认: 用 TCP 连接测试（curl）判断端口是否真的无服务响应，
#      避免被 Get-NetTCPConnection 的残留 LISTENING 条目误报
# ==============================================================================
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=5173
RUN_DIR="$PROJECT_DIR/run"
# 与 start.sh 保持一致的 venv 默认路径（用于按可执行路径精确杀 uvicorn）
export VENV_PYTHON="${VENV_PYTHON:-$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe}"

echo "==> 停止运维智能台账系统..."

# 1) 按 pid 文件停止
for name in backend frontend; do
  pidf="$RUN_DIR/$name.pid"
  if [ -f "$pidf" ]; then
    pid="$(cat "$pidf" 2>/dev/null || echo)"
    if [ -n "$pid" ]; then
      echo "    停止 $name (pid $pid)..."
      kill "$pid" 2>/dev/null || true
      OS="$(uname -s 2>/dev/null || echo Windows_NT)"
      case "$OS" in
        MINGW*|MSYS*|CYGWIN*|*NT*) taskkill.exe /F /T /PID "$pid" 2>/dev/null || true ;;
      esac
    fi
    rm -f "$pidf"
  fi
done

# 2) 兜底: 按端口/命令行停止
OS="$(uname -s 2>/dev/null || echo Windows_NT)"
case "$OS" in
  MINGW*|MSYS*|CYGWIN*|*NT*)
    powershell.exe -NoProfile -Command '
      # 杀掉托管 python 目录下的 uvicorn 后端进程（覆盖 venv 与裸 python 两种启动方式）
      # 注意：非管理员读不到命令行，故按可执行路径前缀匹配；本机仅该目录下的 python 跑后端
      $pyRoot = Join-Path $env:USERPROFILE ".workbuddy\binaries\python"
      Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$pyRoot*" } | ForEach-Object {
        taskkill.exe /F /T /PID $_.Id 2>$null | Out-Null
        Write-Output "    killed python pid $($_.Id)"
      }
      # 端口兜底：netstat 报告的所有 PID 都尝试杀（真实进程会被杀，幽灵 PID 杀不掉也无妨）
      foreach ($port in @(8000,5173)) {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
          taskkill.exe /F /T /PID $_.OwningProcess 2>$null | Out-Null
        }
      }
    ' || true
    ;;
  *)
    for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
      if command -v fuser >/dev/null 2>&1; then
        fuser -k "${port}/tcp" 2>/dev/null || true
      elif command -v lsof >/dev/null 2>&1; then
        pid="$(lsof -ti tcp:"$port" 2>/dev/null)"; [ -n "$pid" ] && kill $pid 2>/dev/null || true
      fi
    done
    ;;
esac

sleep 2

# 3) 最终确认: TCP 连接测试（curl）。端口无服务响应(000)即视为已停止。
#    不依赖 Get-NetTCPConnection，避免 Windows 幽灵监听(LISTENING 但进程已死)误报。
b_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/" 2>/dev/null)"
f_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$FRONTEND_PORT/" 2>/dev/null)"
if [ "$b_code" = "000" ] && [ "$f_code" = "000" ]; then
  echo "✅ 已停止，端口 $BACKEND_PORT / $FRONTEND_PORT 已无服务响应"
else
  echo "⚠️  仍有服务响应: 后端(HTTP $b_code) 前端(HTTP $f_code)"
  echo "    （可能是端口被其他程序占用，或杀进程不彻底，请手动检查）"
fi
