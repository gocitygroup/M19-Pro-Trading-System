@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo.
echo ========================================
echo  Forex Profit Monitoring System
echo ========================================
echo.

REM Resolve script directory and move there
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

REM Prefer venv Python if available
set "PYTHON_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=%SCRIPT_DIR%\.venv\Scripts\python.exe"
    echo Activating virtual environment...
    call "%SCRIPT_DIR%\.venv\Scripts\activate.bat"
) else (
    echo Warning: Virtual environment not found. Using system Python.
    echo.
)

REM Check if Python is available
"%PYTHON_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    popd
    exit /b 1
)

echo Starting Forex Profit Monitoring System...
echo Using Python: %PYTHON_CMD%
echo.

REM Start Enhanced Profit Monitor
echo Starting Enhanced Profit Monitor...
start "Enhanced Profit Monitor" cmd /k "\"%PYTHON_CMD%\" src/scripts/run_enhanced_profit_monitor.py"

REM Wait a moment for the monitor to initialize
timeout /t 3 /nobreak >nul

REM Start Trading Bot
echo Starting Trading Bot...
start "Trading Bot" cmd /k "\"%PYTHON_CMD%\" src/scripts/MarketSessionTradingBot.py"

REM Start Web Interface
echo Starting Web Interface...
start "Web Interface" cmd /k "\"%PYTHON_CMD%\" src/web/app.py"

echo.
echo ========================================
echo  System Started Successfully!
echo ========================================
echo.
echo Web Interface: http://localhost:44444
echo.
echo Press any key to exit this window...
pause >nul

popd
endlocal
