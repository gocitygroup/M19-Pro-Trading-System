@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Gocity Trader Trading Profit Monitoring - Full System
color 0E
echo.
echo =============================================
echo    GOCITY TRADER TRADING PROFIT MONITORING
echo =============================================
echo   Gocity Group with ALGORITHMIC TRADING INVESTMENT
echo.
echo 🏢 Managed by Gocity Managed Service s.r.l – VAT: 04886750274
echo ✉️ Contact: invest@gocitygroup.org ^| services@gocitygroup.org ^| info@gocitygroup.org
echo.
echo Starting Complete Trading System...
echo - Enhanced Profit Monitor (background)
echo - Trading Bot (session-aware execution)
echo - Web Interface (http://localhost:44444)
echo - Real-time monitoring and control
echo.
echo Press Ctrl+C to stop both components
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

REM Check if MetaTrader 5 is running
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if %errorlevel% neq 0 (
    echo WARNING: MetaTrader 5 may not be running
    echo Please ensure MT5 is started and logged in
    echo.
    pause
)

REM Start the full system
echo Starting both components...
echo Web interface will be available at:
echo - http://localhost:44444
echo - http://127.0.0.1:44444
echo.
echo Starting profit monitor, trading bot, and web interface...
"%PYTHON_CMD%" src/scripts/MarketSessionTradingBot.py
"%PYTHON_CMD%" launch.py both

echo.
echo Gocity Trader Full System stopped.
pause
popd
endlocal