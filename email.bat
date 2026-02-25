@echo off
REM Permanent Email Command with Task Tracking
REM Usage: email recipient@example.com "Subject" "Message"
REM This sends email AND creates task that flows: Inbox -> Needs_Action -> Done -> Dashboard

if "%1"=="" (
    echo ================================================
    echo EMAIL - Send with Task Tracking
    echo ================================================
    echo.
    echo Usage: email ^<recipient^> ^<subject^> ^<message^>
    echo.
    echo Example: email john@gmail.com "Hello" "This is a test"
    echo.
    echo This will:
    echo   1. Create task in Inbox/ (immediate)
    echo   2. Send the email
    echo   3. Task flows: Inbox -^> Needs_Action -^> Done
    echo   4. Dashboard updates automatically
    echo.
    exit /b 1
)

python "%~dp0email_send.py" %*
