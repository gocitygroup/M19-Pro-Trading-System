@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Gocity Trader Trading Profit Monitoring - Windows Setup
color 0C
echo.
echo =============================================
echo    GOCITY TRADER TRADING PROFIT MONITORING
echo =============================================
echo   Gocity Group with ALGORITHMIC TRADING INVESTMENT
echo.
echo 🏢 Managed by Gocity Managed Service s.r.l – VAT: 04886750274
echo ✉️ Contact: invest@gocitygroup.org ^| services@gocitygroup.org ^| info@gocitygroup.org
echo.
echo This script will set up the Gocity Trader Trading Profit Monitoring
echo on your Windows system.
echo.
echo Prerequisites:
echo - Python 3.8+ installed
echo - MetaTrader 5 installed
echo - Administrator privileges
echo.
pause

REM Change to script directory
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

echo.
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    popd
    exit /b 1
) else (
    echo SUCCESS: Python is installed
    python --version
)

echo.
echo [2/5] Checking MetaTrader 5...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    echo SUCCESS: MetaTrader 5 found
) else (
    echo WARNING: MetaTrader 5 not found in default location
    echo Please ensure MT5 is installed and accessible
)

echo.
echo [3/5] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Trying alternative method...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Could not install required packages
        pause
        popd
        exit /b 1
    )
)
echo SUCCESS: All dependencies installed

echo.
echo [4/5] Setting up directories...
if not exist "logs" mkdir logs
if not exist "commands" mkdir commands
if not exist "commands\errors" mkdir commands\errors
if not exist "data" mkdir data
echo SUCCESS: Directory structure created

echo.
echo [5/5] Creating desktop shortcuts...
set "DESKTOP=%USERPROFILE%\Desktop"

REM Create desktop shortcut for Enhanced Monitor
echo Creating Enhanced Monitor shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Gocity Trader - Enhanced Monitor.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%Start_Enhanced_Monitor.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = 'shell32.dll,277'; $Shortcut.Save()"

REM Create desktop shortcut for Web Interface
echo Creating Web Interface shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Gocity Trader - Web Interface.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%Start_Web_Interface.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = 'shell32.dll,14'; $Shortcut.Save()"

REM Create desktop shortcut for Full System
echo Creating Full System shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Gocity Trader - Full System.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%Start_Full_System.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = 'shell32.dll,238'; $Shortcut.Save()"

echo SUCCESS: Desktop shortcuts created

echo.
echo =========================================
echo    SETUP COMPLETED SUCCESSFULLY!
echo =========================================
echo.
echo Next steps:
echo 1. Configure MT5 connection in src\config\config.json
echo 2. Start MetaTrader 5 and log in to your account
echo 3. Use desktop shortcuts to start the application
echo.
echo Available shortcuts:
echo - Gocity Trader - Enhanced Monitor (Recommended)
echo - Gocity Trader - Web Interface (Web interface only)
echo - Gocity Trader - Full System (Both components)
echo.
echo For help, see:
echo - README.md (Main documentation)
echo - INSTALL_WINDOWS.md (Installation guide)
echo - DEPLOYMENT_GUIDE.md (Deployment information)
echo.
echo Press any key to open the configuration file...
pause

REM Open config file for editing
notepad src\config\config.json

echo.
echo Setup complete! You can now start the application.
pause 
popd
endlocal