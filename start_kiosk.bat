@echo off
REM ICL Voice Assistant Kiosk Auto-Start Script
REM This script starts the kiosk and automatically restarts it if it crashes.

setlocal EnableDelayedExpansion

REM Configuration
set "VENV_PATH=%~dp0.venv\Scripts\python.exe"
set "SCRIPT_PATH=%~dp0scripts\launch_kiosk.py"
set "LOG_DIR=%~dp0logs"
set "MAX_RESTARTS=10"
set "RESTART_DELAY=5"
set "RESET_COUNTER_AFTER=3600"

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Log file with date
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "DATE=%%c%%a%%b"
set "LOG_FILE=%LOG_DIR%\autostart_%DATE%.log"

call :log "=== ICL Voice Assistant Auto-Start Script ==="
call :log "Python: %VENV_PATH%"
call :log "Script: %SCRIPT_PATH%"

set "RESTART_COUNT=0"
set "LAST_RESTART_TIME=0"

:main_loop
REM Check if we should reset the restart counter
for /f %%a in ('powershell -command "(Get-Date).ToFileTimeUtc()"') do set "CURRENT_TIME=%%a"

REM Calculate time since last restart (simplified check)
if %RESTART_COUNT% GEQ %MAX_RESTARTS% (
    call :log "ERROR: Maximum restart limit reached (%MAX_RESTARTS%)"
    call :log "Manual intervention required. Waiting 5 minutes before retry..."
    timeout /t 300 /nobreak >nul
    set "RESTART_COUNT=0"
)

call :log "Starting kiosk (attempt: !RESTART_COUNT!/%MAX_RESTARTS%)..."

REM Start the kiosk application
"%VENV_PATH%" "%SCRIPT_PATH%" 2>&1 | tee -a "%LOG_FILE%"
set "EXIT_CODE=%ERRORLEVEL%"

call :log "Kiosk exited with code: %EXIT_CODE%"

REM Check exit code
if %EXIT_CODE% EQU 0 (
    call :log "Clean exit. Stopping auto-restart."
    goto :end
)

if %EXIT_CODE% EQU 2 (
    call :log "Requested shutdown. Stopping auto-restart."
    goto :end
)

REM Increment restart counter
set /a RESTART_COUNT+=1
call :log "Crash detected. Restarting in %RESTART_DELAY% seconds..."
timeout /t %RESTART_DELAY% /nobreak >nul

goto :main_loop

:end
call :log "=== Auto-start script ended ==="
exit /b 0

:log
echo [%date% %time%] %~1
echo [%date% %time%] %~1 >> "%LOG_FILE%"
exit /b 0
