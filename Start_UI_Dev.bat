@echo off
SETLOCAL

REM === SET YOUR PROJECT PATH ===
SET PROJECT_PATH=C:\Users\shyam\PycharmProjects\alert-ui-replit

REM === NAVIGATE TO PROJECT DIRECTORY ===
cd /d "%PROJECT_PATH%"
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to change directory to %PROJECT_PATH%.
    pause
    exit /b 1
)

echo =====================================================
echo 🚀 Starting Vite Development Server...
echo =====================================================

REM === START THE DEV SERVER ===

npm run dev

IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to start the Vite dev server. Check your npm setup.
    pause
    exit /b 1
)

echo =====================================================
echo ✅ Vite Dev Server started successfully!
echo =====================================================

ENDLOCAL
pause
