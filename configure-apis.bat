@echo off
REM API Configuration Script for LocalMind
REM Helps configure API keys for all AI providers

echo ========================================
echo   LocalMind API Configuration
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then install dependencies: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please run this script from the LocalMind project directory.
    pause
    exit /b 1
)

echo Starting API configuration wizard...
echo.

REM Run the configuration script
python configure_apis.py

pause

