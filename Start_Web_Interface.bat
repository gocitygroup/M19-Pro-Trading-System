@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Gocity Trader Trading Profit Monitoring - Web Interface
color 0B
echo.
echo =============================================
echo    GOCITY TRADER TRADING PROFIT MONITORING
echo =============================================
echo   Gocity Group with ALGORITHMIC TRADING INVESTMENT
echo.
echo 🏢 Managed by Gocity Managed Service s.r.l – VAT: 04886750274
echo ✉️ Contact: invest@gocitygroup.org ^| services@gocitygroup.org ^| info@gocitygroup.org
echo.
echo Starting Web Interface...
echo - Real-time dashboard at http://localhost:44444
echo - WebSocket communication
echo - Modern responsive interface
echo.
echo Press Ctrl+C to stop the web server
echo.

REM Change to script directory
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

REM Prefer venv Python if available
set "PYTHON_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=%SCRIPT_DIR%\.venv\Scripts\python.exe"
    echo Activating virtual environment...
    call "%SCRIPT_DIR%\.venv\Scripts\activate.bat"
)

REM Check if Python is installed
"%PYTHON_CMD%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    popd
    exit /b 1
)

REM Check if requirements are installed
"%PYTHON_CMD%" -c "import MetaTrader5, flask, flask_socketio" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required packages...
    "%PYTHON_CMD%" -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        popd
        exit /b 1
    )
)

REM Start the web interface
echo Web interface will be available at:
echo - http://localhost:44444
echo - http://127.0.0.1:44444
echo.
echo Starting server...
"%PYTHON_CMD%" launch.py web

echo.
echo Gocity Trader Web Interface stopped.
pause
popd
endlocal