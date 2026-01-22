@echo off
REM ============================================================================
REM G-SignalX-M19-Trading-System - Enhanced System Launcher
REM ============================================================================
REM This script starts the Enhanced Trading System with 4 components:
REM   1. Web Interface (app.py)
REM   2. Enhanced Profit Monitor (run_enhanced_profit_monitor.py)
REM   3. MarketSession Trading Bot (MarketSessionTradingBot.py)
REM   4. Automation API Call Signal (run_gsignalx_automation_runner.py)
REM ============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

echo.
echo ============================================================================
echo G-SignalX-M19-Trading-System - Enhanced System Launcher
echo ============================================================================
echo.

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup_environment.bat first to create the environment.
    pause
    exit /b 1
)

REM Check if activation script exists
if not exist "%VENV_ACTIVATE%" (
    echo [ERROR] Virtual environment activation script not found!
    echo Please run setup_environment.bat first.
    pause
    exit /b 1
)

REM Function to start an application in a new terminal window
call :START_APP "Web Interface" "python src/web/app.py" "Web Interface - http://localhost:44444"
call :START_APP "Enhanced Profit Monitor" "python src/scripts/run_enhanced_profit_monitor.py" "Enhanced Profit Monitor"
call :START_APP "MarketSession Trading Bot" "python src/scripts/MarketSessionTradingBot.py" "MarketSession Trading Bot"
call :START_APP "Automation API Call Signal" "python src/scripts/run_gsignalx_automation_runner.py" "Automation API Call Signal"

echo.
echo ============================================================================
echo All applications are starting in separate terminal windows...
echo ============================================================================
echo.
echo Started Components:
echo   [1] Web Interface - http://localhost:44444
echo   [2] Enhanced Profit Monitor
echo   [3] MarketSession Trading Bot
echo   [4] Automation API Call Signal
echo.
echo Note: Each application runs in its own terminal window.
echo       Close individual terminals to stop specific applications.
echo       Close this window to keep all applications running.
echo.
pause
exit /b 0

REM ============================================================================
REM Function: START_APP
REM Description: Starts an application in a new terminal window with venv activated
REM Parameters:
REM   %1 - Application name (for display)
REM   %2 - Python command to run
REM   %3 - Window title
REM ============================================================================
:START_APP
set "APP_NAME=%~1"
set "PYTHON_CMD=%~2"
set "WINDOW_TITLE=%~3"

REM Create a temporary batch file for this application
set "TEMP_BAT=%TEMP%\gsignalx_%RANDOM%_%RANDOM%.bat"

(
    echo @echo off
    echo title %WINDOW_TITLE%
    echo cd /d "%SCRIPT_DIR%"
    echo call "%VENV_ACTIVATE%"
    echo if errorlevel 1 (
    echo     echo [ERROR] Failed to activate virtual environment
    echo     pause
    echo     exit /b 1
    echo ^)
    echo echo.
    echo echo ============================================================================
    echo echo %APP_NAME%
    echo echo ============================================================================
    echo echo.
    echo %PYTHON_CMD%
    echo if errorlevel 1 (
    echo     echo.
    echo     echo [ERROR] %APP_NAME% exited with an error
    echo     pause
    echo     exit /b 1
    echo ^)
    echo echo.
    echo echo [%APP_NAME%] Application terminated.
    echo pause
) > "%TEMP_BAT%"

REM Start the application in a new terminal window
start "G-SignalX: %WINDOW_TITLE%" cmd /k "%TEMP_BAT%"

REM Small delay to prevent window opening conflicts
timeout /t 1 /nobreak >nul

echo [OK] Started: %APP_NAME%
exit /b 0
