@echo off
REM LocalMind Web Server Control Script
REM This script starts the LocalMind web interface with multiple AI backends

echo ========================================
echo   LocalMind Web Server
echo   Multi-Backend AI Assistant
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
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

REM Quick status check
echo Checking system status...
python main.py status >nul 2>&1
if errorlevel 1 (
    echo Warning: Some backends may not be available
    echo.
)

echo.
echo ========================================
echo   Starting LocalMind Web Server
echo ========================================
echo.
echo Features:
echo   - Local AI models (Ollama)
echo   - API models (ChatGPT, Claude, Gemini, etc.)
echo   - Model management and downloads
echo   - Professional web interface
echo.
echo The web interface will be available at:
echo   - Local:    http://localhost:5000
echo   - Network:  http://YOUR_IP:5000
echo.
echo API Configuration:
echo   - Configure APIs: python main.py configure
echo   - Or visit: http://localhost:5000/configure
echo   - See API_CONFIGURATION.md for more info
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the web server
python main.py web --host 0.0.0.0 --port 5000

pause

