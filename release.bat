@echo off
setlocal enabledelayedexpansion

:: Check if version argument provided
if "%~1"=="" (
    echo Usage: release.bat ^<version^>
    echo Example: release.bat 0.4.0
    exit /b 1
)

set VERSION=%~1

:: Validate version format (basic check)
echo %VERSION% | findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo Invalid version format. Use semantic versioning: X.Y.Z
    exit /b 1
)

echo Releasing v%VERSION%...

:: Update version in main.pyw
powershell -Command "(Get-Content 'main.pyw') -replace '__version__ = \"[0-9]+\.[0-9]+\.[0-9]+\"', '__version__ = \"%VERSION%\"' | Set-Content 'main.pyw'"

if errorlevel 1 (
    echo Failed to update version in main.pyw
    exit /b 1
)

:: Stage and commit
git add main.pyw
git commit -m "Release v%VERSION%"

if errorlevel 1 (
    echo Failed to commit
    exit /b 1
)

:: Create tag
git tag v%VERSION%

if errorlevel 1 (
    echo Failed to create tag
    exit /b 1
)

echo.
echo Release v%VERSION% created successfully!
echo.
echo To publish, run:
echo   git push origin master
echo   git push origin v%VERSION%
