@echo off
REM Silver AI Employee - Complete System Startup
REM This script starts all 3 components in separate windows

echo ================================================
echo SILVER AI EMPLOYEE - SYSTEM STARTUP
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Starting 3 components...
echo.

REM Start Filesystem Watcher (Component 1)
echo [1/3] Starting Filesystem Watcher...
start "Silver - File Watcher" cmd /k "cd /d %~dp0 && python filesystem_watcher.py"
timeout /t 2 >nul

REM Start Simple Orchestrator (Component 2) - NO CLAUDE REQUIRED
echo [2/3] Starting Simple Orchestrator...
start "Silver - Orchestrator" cmd /k "cd /d %~dp0 && python orchestrator_simple.py"
timeout /t 2 >nul

REM Start Dashboard Updater (Component 3)
echo [3/3] Starting Dashboard Updater...
start "Silver - Dashboard" cmd /k "cd /d %~dp0 && python dashboard_updater.py --action status && timeout /t 5 && python dashboard_updater.py --action update"

echo.
echo ================================================
echo ALL COMPONENTS STARTED!
echo ================================================
echo.
echo You should see 3 new command windows:
echo   1. Silver - File Watcher  (Monitors Inbox)
echo   2. Silver - Orchestrator  (Processes tasks)
echo   3. Silver - Dashboard     (Shows status)
echo.
echo To test the system:
echo   1. Create a new .md or .txt file in the Inbox folder
echo   2. Watch it move to Needs_Action, then to Done
echo   3. Check Dashboard.md for updated metrics
echo.
echo To stop: Close all 3 command windows
echo ================================================
echo.
pause
