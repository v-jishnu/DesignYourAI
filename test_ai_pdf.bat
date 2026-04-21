@echo off
REM Test AI MCQ PDF extraction

echo ========================================
echo Testing PDF MCQ Extraction
echo ========================================
echo.
echo Source: AI Unit 2 Questions PDF
echo URL: https://kumarsir34.wordpress.com/wp-content/uploads/2025/09/ai-417-unit-2-advanced-concepts-of-modeling-in-ai-questions-and-answers.pdf
echo.
echo This will:
echo 1. Download the PDF
echo 2. Extract MCQs using pdfplumber
echo 3. Classify with Gemini AI
echo 4. Remove duplicates
echo 5. Store in Excel
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run extraction
python main.py --sources "https://kumarsir34.wordpress.com/wp-content/uploads/2025/09/ai-417-unit-2-advanced-concepts-of-modeling-in-ai-questions-and-answers.pdf"

echo.
echo ========================================
echo Extraction Complete!
echo ========================================
echo.
echo Results saved to:
echo data\knowledge_base\mcq_knowledge_base.xlsx
echo.
echo Open Excel to see:
echo - Extracted MCQs
echo - AI classifications (Category/Topic/Difficulty)
echo - Source tracking
echo.

pause
