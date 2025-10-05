@echo off
REM Launch Browser-Use WebUI
REM Windows batch script to start the browser-use WebUI interface

echo ============================================================
echo    Browser-Use WebUI Launcher
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Using system Python...
)

REM Check if browser-use-webui directory exists
if not exist "browser-use-webui" (
    echo.
    echo ERROR: browser-use-webui directory not found!
    echo Please ensure the browser-use-webui folder is present.
    echo.
    pause
    exit /b 1
)

REM Launch the WebUI
echo.
echo Starting Browser-Use WebUI...
echo.

python launch_browser_webui.py --ip 127.0.0.1 --port 7788 --theme Ocean

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start WebUI
    echo.
    pause
)
