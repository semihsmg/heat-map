@echo off

:: Build Keyboard Heat Map executable

echo Building Keyboard Heat Map...

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

:: Generate icon
echo Generating icon...
python "%~dp0icons.py"

:: Build the executable
pyinstaller --onefile --windowed --name "KeyboardHeatMap" --icon "%~dp0assets\icon.ico" --add-data "%~dp0assets;assets" "%~dp0main.pyw"

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete! Executable is in the 'dist' folder.
pause
