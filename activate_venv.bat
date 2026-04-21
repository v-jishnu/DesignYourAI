@echo off
REM Activate virtual environment for DesignYourAI project
REM This script can be run from PowerShell or Command Prompt

echo.
echo ========================================
echo Activating DesignYourAI Virtual Environment
echo ========================================
echo.

REM Check if .venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Error: Virtual environment not found!
    echo.
    echo Please create it first:
    echo    python -m venv .venv
    echo.
    pause
    exit /b 1
)

REM Activate the virtual environment
call .venv\Scripts\activate.bat

echo.
echo ✅ Virtual environment activated!
echo    You should see (.venv) in your prompt
echo.
echo 📦 You can now run:
echo    python test_sample.py
echo    python main.py --sources "URL"
echo.
echo 🛑 To deactivate, type: deactivate
echo ========================================
echo.
