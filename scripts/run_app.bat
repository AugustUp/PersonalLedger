@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

REM ============================================================
REM Ops Ledger - local startup (backend + frontend) [Windows 11]
REM Usage: double-click, or run scripts\run_app.bat in cmd
REM Config items are in the block below.
REM ============================================================

REM ---------------- CONFIG ----------------
set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"
set "RUN_DIR=%PROJECT_DIR%\run"
set "LOG_DIR=%PROJECT_DIR%\logs"
if defined VENV_PYTHON (set "PY=%VENV_PYTHON%") else (set "PY=%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe")
set "MANAGED_NODE=%USERPROFILE%\.workbuddy\binaries\node\versions\22.22.2"
REM ----------------------------------------

if not exist "%RUN_DIR%" mkdir "%RUN_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if exist "%MANAGED_NODE%" set "PATH=%MANAGED_NODE%;%PATH%"

echo [INFO] Project : %PROJECT_DIR%
echo [INFO] Backend : %PY%

REM stop any leftover instance (clean ports + stale uvicorn)
if exist "%RUN_DIR%\*.pid" del /f /q "%RUN_DIR%\*.pid" >nul 2>&1
powershell -NoProfile -Command "foreach($port in @(8000,5173)){ Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { taskkill /F /T /PID $_.OwningProcess 2>$null } }; $pyRoot=Join-Path $env:USERPROFILE '.workbuddy\binaries\python'; Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like ($pyRoot+'*') } | ForEach-Object { taskkill /F /T /PID $_.Id 2>$null }" 2>nul

REM ---------------- start backend ----------------
echo [INFO] Starting backend (uvicorn :%BACKEND_PORT%) ...
powershell -NoProfile -Command "$p=Start-Process -FilePath '%PY%' -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','%BACKEND_PORT%','--reload' -WorkingDirectory '%BACKEND_DIR%' -WindowStyle Hidden -PassThru; $p.Id" > "%RUN_DIR%\.bid.tmp"
set /p BID=<"%RUN_DIR%\.bid.tmp"
del /f /q "%RUN_DIR%\.bid.tmp" >nul 2>&1
if defined BID (echo !BID! > "%RUN_DIR%\backend.pid") else (echo [WARN] failed to capture backend PID)

REM ---------------- start frontend ----------------
echo [INFO] Starting frontend (vite :%FRONTEND_PORT%) ...
powershell -NoProfile -Command "$p=Start-Process -FilePath '%MANAGED_NODE%\node.exe' -ArgumentList 'node_modules\vite\bin\vite.js','--host','0.0.0.0','--port','%FRONTEND_PORT%' -WorkingDirectory '%FRONTEND_DIR%' -WindowStyle Hidden -PassThru; $p.Id" > "%RUN_DIR%\.fid.tmp"
set /p FID=<"%RUN_DIR%\.fid.tmp"
del /f /q "%RUN_DIR%\.fid.tmp" >nul 2>&1
if defined FID (echo !FID! > "%RUN_DIR%\frontend.pid") else (echo [WARN] failed to capture frontend PID)

REM ---------------- wait for backend (fixed 15s) ----------------
echo [INFO] Waiting for backend to start (up to 15s) ...
timeout /t 15 /nobreak >nul

echo.
echo [OK] Started:
echo     Frontend : http://localhost:%FRONTEND_PORT%
echo     Backend  : http://localhost:%BACKEND_PORT%
echo     Logs     : %LOG_DIR%\backend.log  %LOG_DIR%\frontend.log
echo     Stop     : scripts\stop.bat
endlocal
