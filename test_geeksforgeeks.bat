@echo off
REM Test GeeksforGeeks (JavaScript-rendered) extraction

echo ========================================
echo Testing JavaScript Site Extraction
echo ========================================
echo.
echo Source: GeeksforGeeks ML Quiz
echo URL: https://www.geeksforgeeks.org/quizzes/machine-learning-quiz-questions-and-answers/
echo.
echo This will test:
echo 1. Static extraction (should find nothing)
echo 2. Browser rendering with Playwright
echo 3. MCQ extraction from rendered HTML
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run extraction
python main.py --sources "https://www.geeksforgeeks.org/quizzes/machine-learning-quiz-questions-and-answers/"

echo.
echo ========================================
echo Extraction Complete!
echo ========================================
echo.
echo Check results:
echo - Console output above
echo - data\knowledge_base\mcq_knowledge_base.xlsx
echo.

pause
