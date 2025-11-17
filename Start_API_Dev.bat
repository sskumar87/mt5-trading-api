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

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Flask not found. Installing dependencies...
    pip install flask flask-cors flask-sqlalchemy gunicorn numpy pandas psycopg2-binary werkzeug email-validator
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if requirements.txt exists and install from it
if exist "requirements.txt" (
    echo Installing from requirements.txt...
    echo pip install -r requirements.txt
)

echo.
echo Dependencies ready!
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