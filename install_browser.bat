@echo off
REM Install Playwright and browser binary

echo ========================================
echo Installing Playwright Browser Support
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install Playwright
echo Installing playwright package...
pip install playwright==1.40.0

echo.
echo Installing Chromium browser binary...
echo This may take a few minutes (~200MB download)...
playwright install chromium

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Browser automation is now ready.
echo You can now extract MCQs from JavaScript-rendered sites!
echo.

pause
