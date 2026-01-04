@echo off
REM LocalMind Web Server Control Script (Advanced)
REM This script provides options for starting the web interface
REM Includes: AI Chat, Text-to-Video Generation, Real-time Updates

REM Change to project root directory (parent of scripts folder)
cd /d "%~dp0.."

:menu
cls
echo ========================================
echo   LocalMind Web Server Control
echo   Multi-Backend AI Assistant
echo ========================================
echo.
echo Select an option:
echo.
echo   1. Start web server (default: port 5000)
echo   2. Start web server (custom port)
echo   3. Start web server (local only - 127.0.0.1)
echo   4. Start web server (debug mode)
echo   5. Check system status
echo   6. List available models
echo   7. Check API key configuration
echo   8. Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto start_default
if "%choice%"=="2" goto start_custom
if "%choice%"=="3" goto start_local
if "%choice%"=="4" goto start_debug
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto list_models
if "%choice%"=="7" goto check_api_keys
if "%choice%"=="8" goto end
goto menu

:start_default
call venv\Scripts\activate.bat
echo Starting web server on port 5000...
python main.py web --host 0.0.0.0 --port 5000
pause
goto menu

:start_custom
set /p port="Enter port number (default 5000): "
if "%port%"=="" set port=5000
call venv\Scripts\activate.bat
echo Starting web server on port %port%...
python main.py web --host 0.0.0.0 --port %port%
pause
goto menu

:start_local
call venv\Scripts\activate.bat
echo Starting web server (local only)...
python main.py web --host 127.0.0.1 --port 5000
pause
goto menu

:start_debug
call venv\Scripts\activate.bat
echo Starting web server in debug mode...
python main.py web --host 0.0.0.0 --port 5000 --debug
pause
goto menu

:check_status
call venv\Scripts\activate.bat
echo.
echo Checking LocalMind status...
echo.
python main.py status
echo.
pause
goto menu

:list_models
call venv\Scripts\activate.bat
echo.
echo Listing available models...
echo.
python main.py models
echo.
pause
goto menu

:check_api_keys
echo.
echo Checking API key configuration...
echo.
if defined OPENAI_API_KEY (
    echo [OK] OPENAI_API_KEY is set - ChatGPT models available
) else (
    echo [ ] OPENAI_API_KEY not set - Set it to use ChatGPT models
)
if defined ANTHROPIC_API_KEY (
    echo [OK] ANTHROPIC_API_KEY is set - Claude models available
) else (
    echo [ ] ANTHROPIC_API_KEY not set - Set it to use Claude models
)
if defined GOOGLE_API_KEY (
    echo [OK] GOOGLE_API_KEY is set - Gemini models available
) else (
    echo [ ] GOOGLE_API_KEY not set - Set it to use Gemini models
)
if defined MISTRAL_AI_API_KEY (
    echo [OK] MISTRAL_AI_API_KEY is set - Mistral AI models available
) else (
    echo [ ] MISTRAL_AI_API_KEY not set - Set it to use Mistral AI models
)
if defined COHERE_API_KEY (
    echo [OK] COHERE_API_KEY is set - Cohere models available
) else (
    echo [ ] COHERE_API_KEY not set - Set it to use Cohere models
)
echo.
echo To set API keys:
echo   set OPENAI_API_KEY=your_key_here
echo   See API_MODELS.md for more information
echo.
pause
goto menu

:end
echo.
echo Goodbye!
exit /b 0

