@echo off
REM MT5 Trading API Development Server Startup Script
REM Based on IntelliJ Configuration

echo Starting MT5 Trading API Development Server...
echo.

REM Set environment variables
set PYTHONUNBUFFERED=1

REM Change to the project directory (adjust path as needed)
cd /d "C:\Users\shyam\PycharmProjects\mt5-trading-api"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    echo Current directory: %cd%
    pause
    exit /b 1
)

echo Project directory: %cd%
echo Python version:
python --version
echo.

REM Start the Flask development server
echo Starting Flask development server...
echo Server will be available at: http://127.0.0.1:5001
echo Press Ctrl+C to stop the server
echo.

python app.py

REM If we get here, the server stopped
echo.
echo Server stopped.
pause