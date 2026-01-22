@echo off
REM ============================================================================
REM G-SignalX-M19-Trading-System - Environment Setup Script
REM ============================================================================
REM This script sets up the Python virtual environment and installs dependencies
REM ============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "LOGS_DIR=%SCRIPT_DIR%logs"

echo.
echo ============================================================================
echo G-SignalX-M19-Trading-System - Environment Setup
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo [2/5] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully
) else (
    echo [2/5] Virtual environment already exists, skipping...
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
if not exist "%VENV_ACTIVATE%" (
    echo [ERROR] Virtual environment activation script not found
    pause
    exit /b 1
)
call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing anyway...
) else (
    echo [OK] Pip upgraded successfully
)
echo.

REM Install requirements
echo [5/5] Installing dependencies from requirements.txt...
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo [ERROR] requirements.txt not found in project root
    pause
    exit /b 1
)
pip install -r "%SCRIPT_DIR%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully
echo.

REM Create logs directory if it doesn't exist
if not exist "%LOGS_DIR%" (
    echo [EXTRA] Creating logs directory...
    mkdir "%LOGS_DIR%"
    if errorlevel 1 (
        echo [WARNING] Failed to create logs directory
    ) else (
        echo [OK] Logs directory created successfully
    )
) else (
    echo [EXTRA] Logs directory already exists, skipping...
)
echo.

echo ============================================================================
echo Environment setup completed successfully!
echo ============================================================================
echo.
echo Next steps:
echo   1. Run start_enhanced_system.bat to start the enhanced trading system
echo   2. Run start_scouting_system.bat to start the scouting trading system
echo.
pause
