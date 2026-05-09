@echo off
REM AutoAttendance Web UI Launcher for Windows
REM Simple batch script to start the web interface

echo.
echo ========================================================================
echo   AutoAttendance Web UI Launcher
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

REM Install requirements if needed
echo Checking dependencies...
python -m pip install -q flask flask-cors 2>nul

REM Start the web UI
echo.
echo Starting AutoAttendance Web UI...
echo.
python run_web_ui.py

pause
