@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

REM ============================================================
REM Ops Ledger - stop backend + frontend [Windows 11]
REM Usage: double-click, or run scripts\stop.bat in cmd
REM Steps:
REM   1. kill processes recorded in run/*.pid
REM   2. fallback: kill uvicorn under managed python + kill by port
REM      (only real processes; ignores Windows ghost listeners)
REM   3. verify with curl (000 = no response = stopped)
REM ============================================================

set "PROJECT_DIR=%~dp0.."
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"
set "RUN_DIR=%PROJECT_DIR%\run"

echo [INFO] Stopping ops-ledger ...

REM 1) stop by pid file
for %%n in (backend frontend) do (
  if exist "%RUN_DIR%\%%n.pid" (
    set /p PID=<"%RUN_DIR%\%%n.pid"
    if defined PID (
      echo [INFO] stop %%n, pid=!PID!
      taskkill /F /T /PID !PID! 2>nul
    )
    del /f /q "%RUN_DIR%\%%n.pid" >nul 2>&1
  )
)

REM 2) fallback: kill uvicorn under managed python + by port
powershell -NoProfile -Command "$pyRoot=Join-Path $env:USERPROFILE '.workbuddy\binaries\python'; Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like ($pyRoot+'*') } | ForEach-Object { taskkill /F /T /PID $_.Id 2>$null }; foreach($port in @(8000,5173)){ Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { taskkill /F /T /PID $_.OwningProcess 2>$null } }"

timeout /t 2 >nul

REM 3) verify with PowerShell (no response = stopped)
powershell -NoProfile -Command "$bOk=$false; $fOk=$false; try { Invoke-WebRequest -Uri 'http://127.0.0.1:%BACKEND_PORT%/' -UseBasicParsing -TimeoutSec 2 | Out-Null; $bOk=$true } catch {} ; try { Invoke-WebRequest -Uri 'http://127.0.0.1:%FRONTEND_PORT%/' -UseBasicParsing -TimeoutSec 2 | Out-Null; $fOk=$true } catch {} ; if(-not $bOk -and -not $fOk){ Write-Output '[OK] Stopped. Ports %BACKEND_PORT% / %FRONTEND_PORT% are free.' } else { Write-Output ('[WARN] Still responding: backend='+$bOk+' frontend='+$fOk) }"
endlocal
