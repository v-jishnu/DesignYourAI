@echo off
REM Test with local HTML file (demonstrates current capability)

echo ========================================
echo Testing MCQ Extraction - Local Sample
echo ========================================
echo.
echo Source: data\raw\sample_mcqs.html
echo MCQs: 5 sample Machine Learning questions
echo.
echo This demonstrates:
echo - HTML extraction
echo - AI classification (Gemini)
echo - Deduplication
echo - Excel storage
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run extraction on local file
python main.py --sources "data/raw/sample_mcqs.html"

echo.
echo ========================================
echo Complete!
echo ========================================
echo.
echo Results saved to:
echo data\knowledge_base\mcq_knowledge_base.xlsx
echo.
echo Open Excel to see:
echo - 5 MCQs extracted
echo - Category/Topic/Difficulty assigned by AI
echo - Source tracked
echo.

pause
