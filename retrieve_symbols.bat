@echo off
REM ============================================================================
REM G-SignalX-M19-Trading-System - Symbol Retrieval Script
REM ============================================================================
REM This script retrieves broker-supported symbols from MT5 and saves them
REM to mt5_symbols.msgpack (and optionally mt5_symbols.json) in the database
REM directory. If the file already exists, it will be replaced.
REM ============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "DATABASE_DIR=%SCRIPT_DIR%database"
set "MSGPACK_FILE=%DATABASE_DIR%\mt5_symbols.msgpack"

echo.
echo ============================================================================
echo G-SignalX-M19-Trading-System - Symbol Retrieval
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

REM Check if msgpack file exists and warn user
if exist "%MSGPACK_FILE%" (
    echo [WARNING] Existing mt5_symbols.msgpack file found!
    echo           It will be replaced with new broker symbols.
    echo.
    echo File location: %MSGPACK_FILE%
    echo.
    set /p CONFIRM="Do you want to continue? (Y/N): "
    if /i not "!CONFIRM!"=="Y" (
        echo.
        echo [INFO] Symbol retrieval cancelled by user.
        pause
        exit /b 0
    )
    echo.
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Check and install required dependencies
echo [1.5/3] Checking required dependencies...
python -c "import msgpack" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] msgpack module not found. Installing from requirements.txt...
    pip install msgpack
    if errorlevel 1 (
        echo [ERROR] Failed to install msgpack module
        echo         Please run: pip install msgpack
        pause
        exit /b 1
    )
    echo [OK] msgpack module installed
) else (
    echo [OK] Required dependencies found
)
echo.

REM Check if MT5 is running
echo [2/3] Checking MetaTrader 5 connection...
echo        Please ensure MetaTrader 5 terminal is running and logged in.
echo.

REM Change to database directory for script execution
cd /d "%DATABASE_DIR%"

REM Run the symbol retriever
echo [3/4] Retrieving symbols from MT5 broker...
echo        This may take a few moments...
echo.
python mt5_symbol_retriever.py
if errorlevel 1 (
    echo.
    echo [ERROR] Symbol retrieval failed!
    echo.
    echo         Please check:
    echo         1. MetaTrader 5 terminal is running
    echo         2. You are logged into your broker account
    echo         3. Python dependencies are installed
    echo            Run: pip install -r "%SCRIPT_DIR%requirements.txt"
    echo            Or run: setup_environment.bat
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Symbols retrieved and saved to msgpack file
echo.

REM Update database with new symbols using shared function
echo [4/4] Updating database with new symbols...
echo        This will sync the database with the retrieved symbols.
echo.
python setup_db.py update
if errorlevel 1 (
    echo.
    echo [WARNING] Database update failed, but symbols are saved in msgpack file.
    echo           You can update the database manually from the UI or run:
    echo           python "%DATABASE_DIR%\setup_db.py" update
    echo.
) else (
    echo.
    echo [OK] Database updated successfully!
    echo.
)

echo.
echo ============================================================================
echo Symbol retrieval and database update completed!
echo ============================================================================
echo.
echo The symbols have been:
echo   - Saved to: %MSGPACK_FILE%
echo   - Updated in: database\trading_sessions.db
echo.
echo The UI will now show the updated symbols automatically.
echo.
pause
exit /b 0
