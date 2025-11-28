@echo off

:: Check for updates via git pull (silent unless updates found)
git --version >nul 2>&1
if not errorlevel 1 (
    cd /d "%~dp0"
    for /f "tokens=*" %%i in ('git pull --ff-only 2^>^&1') do set "GIT_OUTPUT=%%i"
    echo %GIT_OUTPUT% | findstr /i "Already up to date" >nul
    if errorlevel 1 (
        echo %GIT_OUTPUT% | findstr /i "error fatal" >nul
        if not errorlevel 1 (
            echo Update check failed, continuing with current version...
        ) else (
            echo Updated to latest version!
            timeout /t 2 >nul
        )
    )
)

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Check if required packages are installed
python -c "import pynput, pystray, PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

:: Run the app silently
start "" pythonw "%~dp0main.pyw"
