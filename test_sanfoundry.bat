@echo off
REM Test Sanfoundry AI Questions extraction

echo ========================================
echo Testing Sanfoundry AI MCQs
echo ========================================
echo.
echo Source: https://www.sanfoundry.com/artificial-intelligence-questions-answers/
echo.
echo Note: Some sites may block automated requests
echo If extraction fails, we'll try alternative sources
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run extraction
python main.py --sources "https://www.sanfoundry.com/artificial-intelligence-questions-answers/"

echo.
echo ========================================
echo Extraction Complete!
echo ========================================
echo.
echo Check results:
echo - Console output above
echo - data\knowledge_base\mcq_knowledge_base.xlsx
echo.
echo If no MCQs were extracted:
echo - Site may be blocking automated requests (403 error)
echo - Try the local sample test instead: test_sample_local.bat
echo.

pause
