@echo off
REM Install dependencies for DesignYourAI using public PyPI only
REM This script ensures we don't interfere with other projects

echo ========================================
echo Installing DesignYourAI Dependencies
echo ========================================
echo.
echo Using: Public PyPI (NOT CodeArtifact)
echo Environment: .venv (isolated)
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install using explicit public PyPI URL (bypasses global pip config)
pip install --index-url https://pypi.org/simple/ --no-cache-dir -r requirements.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo New packages installed:
echo - Pillow (image processing)
echo - imagehash (visual deduplication)
echo.
echo Note: Packages installed in .venv ONLY
echo Your other projects remain unaffected
echo.

pause
