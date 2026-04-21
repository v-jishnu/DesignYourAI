@echo off
REM Activate virtual environment for DesignYourAI project

echo ========================================
echo Activating DesignYourAI Virtual Environment
echo ========================================
echo.

call .venv\Scripts\activate.bat

echo.
echo ✅ Virtual environment activated!
echo.
echo 📦 You can now run:
echo    python test_sample.py
echo    python main.py --sources "URL"
echo.
echo 🛑 To deactivate, type: deactivate
echo.
