@echo off
REM Silver AI Employee - Complete System Startup
REM This script starts all components in separate windows

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

echo Starting components...
echo.

REM Start Filesystem Watcher (Component 1)
echo [1/6] Starting Filesystem Watcher...
start "Silver - File Watcher" cmd /k "cd /d %~dp0 && python filesystem_watcher.py"
timeout /t 1 >nul

REM Start Gmail Watcher (Component 2)
echo [2/6] Starting Gmail Watcher...
start "Silver - Gmail Watcher" cmd /k "cd /d %~dp0 && python watchers\gmail_watcher.py"
timeout /t 1 >nul

REM Start Claude Reasoning Loop (Component 3)
echo [3/6] Starting Claude Reasoning Loop...
start "Silver - Claude Reasoning" cmd /k "cd /d %~dp0 && python claude_reasoning.py"
timeout /t 1 >nul

REM Start Task Scheduler (Component 4)
echo [4/6] Starting Task Scheduler...
start "Silver - Task Scheduler" cmd /k "cd /d %~dp0 && python scheduler.py"
timeout /t 1 >nul

REM Start Simple Orchestrator (Component 5)
echo [5/6] Starting Simple Orchestrator...
start "Silver - Orchestrator" cmd /k "cd /d %~dp0 && python orchestrator_simple.py"
timeout /t 1 >nul

REM Start Dashboard Updater (Component 6)
echo [6/6] Starting Dashboard Updater...
start "Silver - Dashboard" cmd /k "cd /d %~dp0 && python dashboard_updater.py --action status && timeout /t 5 && python dashboard_updater.py --action update"

echo.
echo ================================================
echo ALL COMPONENTS STARTED!
echo ================================================
echo.
echo You should see 6 new command windows:
echo   1. Silver - File Watcher     (Monitors Inbox)
echo   2. Silver - Gmail Watcher    (Monitors Gmail)
echo   3. Silver - Claude Reasoning (Creates Plan.md files)
echo   4. Silver - Task Scheduler   (Scheduled tasks)
echo   5. Silver - Orchestrator     (Processes tasks)
echo   6. Silver - Dashboard        (Shows status)
echo.
echo To test the system:
echo   1. Create a new .md or .txt file in the Inbox folder
echo   2. Watch it move to Needs_Action, then to Done
echo   3. Check Dashboard.md for updated metrics
echo   4. Check Plans/ folder for generated plans
echo.
echo To stop: Close all command windows
echo ================================================
echo.
pause
