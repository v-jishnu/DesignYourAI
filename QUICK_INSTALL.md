# Quick Installation & Testing Guide

## Step 1: Install Browser Support (5 minutes)

```bash
cd C:\DesignYourAI
install_browser.bat
```

Wait for:
- ✅ Playwright package installed
- ✅ Chromium browser downloaded (~200MB)
- ✅ "Installation Complete!" message

---

## Step 2: Test JavaScript Extraction

### Option A: GeeksforGeeks (Automated Test)
```bash
test_geeksforgeeks.bat
```

### Option B: Manual Test
```bash
cd C:\DesignYourAI
.venv\Scripts\activate.bat
python main.py --sources "https://www.geeksforgeeks.org/quizzes/machine-learning-quiz-questions-and-answers/"
```

**Expected output:**
```
Extracting from URL: https://www.geeksforgeeks.org/...
Static extraction found nothing, trying browser rendering...
Extracted 15 MCQs from https://www.geeksforgeeks.org/...

======================================================================
INGESTION RESULTS
======================================================================

Extracted: 15 MCQs
Classified: 15 MCQs
Stored: 15 MCQs

Knowledge Base Status:
  - Total MCQs: 58
  - Target: 800
  - Progress: 58/800 (7.3%)
```

---

## Step 3: Verify in Excel

1. Open `data\knowledge_base\mcq_knowledge_base.xlsx`
2. Check last 15 rows
3. Verify Source column shows GeeksforGeeks URL
4. Verify Question_Text and Options populated

---

## Troubleshooting

### "Playwright not available"
```bash
cd C:\DesignYourAI
.venv\Scripts\activate.bat
pip install playwright
playwright install chromium
```

### "Browser timeout"
- Edit `config/settings.py`
- Increase `BROWSER_TIMEOUT` to `60000`

### Still 0 MCQs extracted
- Site might have bot protection
- Try a different source
- Check if site requires login

---

## What's Next?

**Phase 1 Complete!** ✅
- JavaScript sites now work

**Phase 2 (Next):**
- Q&A to MCQ generation
- Handle descriptive interview questions

**Phase 3 (After):**
- Complete image support
- Extract diagrams from PDFs

---

**Quick test:** `install_browser.bat` → `test_geeksforgeeks.bat` → Check Excel!
