@echo off
REM ================================================
REM CLEANUP SCRIPT - Remove Unnecessary Files
REM ================================================
REM This will remove old/duplicate files and keep only core system files
REM ================================================

echo ================================================
echo CLEANING UP UNNECESSARY FILES
echo ================================================
echo.

echo This will remove:
echo - Old duplicate email scripts
echo - Old duplicate WhatsApp scripts
echo - Test files
echo - Old documentation
echo - LinkedIn files (if not using)
echo - Cache folders
echo.
echo Keeping only core system files!
echo.
pause

echo.
echo [1/6] Removing old email scripts...
del send_email.py 2>nul
del send_email_auto.py 2>nul
del send_email_cmd.py 2>nul
del send_email.bat 2>nul
echo Done!

echo.
echo [2/6] Removing old WhatsApp scripts...
del send_whatsapp.py 2>nul
del whatsapp_automation.py 2>nul
del whatsapp_demo.py 2>nul
del whatsapp_diagnostic.py 2>nul
del whatsapp_easy.py 2>nul
del whatsapp_quick.py 2>nul
del whatsapp_simple.py 2>nul
del whatsapp_web_send.py 2>nul
echo Done!

echo.
echo [3/6] Removing old orchestrator...
del orchestrator.py 2>nul
echo Done!

echo.
echo [4/6] Removing test files...
del test_email_live.bat 2>nul
del test_orchestrator.bat 2>nul
echo Done!

echo.
echo [5/6] Removing old documentation...
del EMAIL_AUTOMATION.md 2>nul
del EMAIL_COMMAND.md 2>nul
del EMAIL_COMPLETE.md 2>nul
del WHATSAPP_AUTOMATION.md 2>nul
del WHATSAPP_COMPLETE_SETUP.md 2>nul
del WHATSAPP_EASY_SETUP.md 2>nul
del WHATSAPP_QUICK_START.md 2>nul
del WHATSAPP_README.md 2>nul
del WHATSAPP_SETUP.md 2>nul
del QUICK_START.md 2>nul
del SYSTEM_WORKING.md 2>nul
del AUTOMATION_REQUIREMENTS.md 2>nul
del master_processing_flow.md 2>nul
del GMAIL_SIMPLE_SETUP.md 2>nul
del SETUP_GUIDE.md 2>nul
del LINKEDIN_SETUP_STATUS.md 2>nul
echo Done!

echo.
echo [6/6] Removing other old files...
del scheduler.py 2>nul
del send_promo_email.py 2>nul
del setup_gmail_auth.py 2>nul
del mcp_server.py 2>nul
del PyWhatKit_DB.txt 2>nul
del 0.9.54 2>nul
del add_to_path.bat 2>nul
echo Done!

echo.
echo Cleaning folders...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q watchers 2>nul
echo Done!

echo.
echo ================================================
echo CLEANUP COMPLETE!
echo ================================================
echo.
echo Core files kept:
echo - filesystem_watcher.py
echo - orchestrator_simple.py
echo - dashboard_updater.py
echo - email_send.py
echo - whatsapp_auto.py
echo - email.bat
echo - whatsapp.bat
echo - start_system.bat
echo - commnds.md
echo - AUTOMATION_COMPLETE.md
echo - EMAIL_FLOW_VERIFIED.md
echo - Dashboard.md
echo.
echo Folders kept:
echo - Inbox/
echo - Needs_Action/
echo - Done/
echo - logs/
echo - state/
echo - skills/
echo.
echo ================================================
pause
