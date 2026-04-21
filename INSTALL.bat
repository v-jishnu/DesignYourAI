@echo off
REM Simple installation script for image dependencies

echo.
echo ========================================
echo Installing Image Dependencies
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run Python installation script
python install_image_deps.py

echo.
pause
