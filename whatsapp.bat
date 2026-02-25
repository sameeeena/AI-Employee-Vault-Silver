@echo off
REM Permanent WhatsApp Command with Task Tracking
REM Usage: whatsapp recipient_number "Message" [Project Name]
REM This sends WhatsApp AND creates task that flows: Inbox -> Needs_Action -> Done -> Dashboard

if "%1"=="" (
    echo ================================================
    echo WHATSAPP - Send with Task Tracking
    echo ================================================
    echo.
    echo Usage: whatsapp ^<number^> ^<message^> [project]
    echo.
    echo Example: whatsapp +923222208301 "Hello" "My Project"
    echo.
    echo This will:
    echo   1. Send the WhatsApp message
    echo   2. Create task in Inbox/
    echo   3. Task flows: Inbox -^> Needs_Action -^> Done
    echo   4. Dashboard updates automatically
    echo.
    exit /b 1
)

python "%~dp0whatsapp_auto.py" %*
