# Quick Start Guide - Test the System Now!

## ✅ Perfect! You Have a PDF Source

**Your PDF:** https://kumarsir34.wordpress.com/wp-content/uploads/2025/09/ai-417-unit-2-advanced-concepts-of-modeling-in-ai-questions-and-answers.pdf

This is **ideal** because:
- ✅ PDF extraction works great (no blocking)
- ✅ Your current system fully supports it
- ✅ Will demonstrate the complete pipeline

---

## 🚀 Test in 3 Steps (5 minutes)

### Step 1: Ensure API Key is Set

```cmd
cd C:\DesignYourAI
notepad .env
```

Make sure you have:
```
GEMINI_API_KEY=your-actual-api-key-here
```

Get free key from: https://makersuite.google.com/app/apikey

---

### Step 2: Run the Test

**Option A: Use the batch file (easiest)**
```cmd
cd C:\DesignYourAI
test_ai_pdf.bat
```

**Option B: Manual command**
```cmd
cd C:\DesignYourAI
.venv\Scripts\activate.bat
python main.py --sources "https://kumarsir34.wordpress.com/wp-content/uploads/2025/09/ai-417-unit-2-advanced-concepts-of-modeling-in-ai-questions-and-answers.pdf"
```

---

### Step 3: Check Results

**Console Output:**
```
🚀 Starting ingestion workflow...
📄 Processing: [PDF URL]
✅ Extracted X MCQs
✅ Classified X MCQs
✅ Stored Y MCQs (Z duplicates)
📊 Progress: Y/800 (X.X%)
```

**Excel Output:**
```cmd
# Open the file
data\knowledge_base\mcq_knowledge_base.xlsx
```

You'll see columns:
- Question_Text
- Option_A, Option_B, Option_C, Option_D
- Correct_Answer (if in PDF)
- Explanation (if in PDF)
- **Category** (AI-assigned: Conceptual/Mathematical/Application)
- **Topic** (AI-assigned: AI/ML/Data Science/System Design)
- **Difficulty** (AI-assigned: Easy/Medium/Hard)
- Source (PDF URL)
- Date_Added
- Used_Status (FALSE)
- Image fields (empty for now)

---

## 📊 What You'll See

### Expected Workflow:

1. **PDF Download** (~5 seconds)
   - System downloads the PDF
   - Saves to temporary location

2. **Text Extraction** (~10 seconds)
   - Extracts text using pdfplumber
   - Looks for MCQ patterns (Question, A) B) C) D))

3. **Classification** (~30 seconds)
   - Sends MCQs to Gemini AI in batches of 10
   - Gets category, topic, difficulty for each

4. **Deduplication** (~2 seconds)
   - Checks against existing knowledge base
   - Removes exact and fuzzy duplicates

5. **Storage** (~2 seconds)
   - Saves to Excel
   - Creates automatic backup

**Total Time:** ~1-2 minutes for typical PDF

---

## 🎯 Success Indicators

✅ **Console shows:** "✅ Stored X MCQs"
✅ **Excel file updated:** New rows added
✅ **Classifications present:** Category/Topic/Difficulty filled
✅ **No errors:** Clean execution

---

## 🔧 Troubleshooting

### "GEMINI_API_KEY not found"
**Fix:** Add your API key to `.env` file

### "No MCQs extracted"
**Possible reasons:**
- PDF format not recognized
- MCQs not in A) B) C) D) format
- PDF is image-based (needs OCR - not implemented yet)

**Solution:** Try the local sample test first:
```cmd
test_sample_local.bat
```

### "Module not found"
**Fix:** Ensure virtual environment is activated:
```cmd
.venv\Scripts\activate.bat
```
You should see: `(venv) C:\DesignYourAI>`

---

## 📝 After Testing

### If Successful:
You can process more sources:

**More PDFs:**
```cmd
python main.py --sources "path/to/another.pdf"
```

**Multiple sources at once:**
```cmd
python main.py --sources "url1.pdf" "url2.pdf" "local_file.pdf"
```

**Batch file:**
```cmd
# Create sources.txt with one URL/path per line
python main.py --batch sources.txt
```

### Progress Tracking:
```cmd
# Each run adds to the same Excel file
# Progress shown: X/800 (target)
```

---

## 🎉 Next Steps

**After verifying PDF extraction works:**

1. **Continue with more PDFs** to reach 800 MCQs
2. **I complete remaining features:**
   - Image support (Days 3-5)
   - Q&A to MCQ generation (Days 6-8)
3. **Add more source types** as needed

---

## 📞 Need Help?

**Common issues:**

| Issue | Solution |
|-------|----------|
| API key error | Add `GEMINI_API_KEY` to `.env` |
| Virtual env not activated | Run `.venv\Scripts\activate.bat` |
| No MCQs found | Check PDF format (try local sample) |
| Module not found | Run `pip install -r requirements.txt` |

---

## 🚀 Ready to Test?

**Run this now:**
```cmd
cd C:\DesignYourAI
test_ai_pdf.bat
```

Then check: `data\knowledge_base\mcq_knowledge_base.xlsx`

**This will prove the system works end-to-end!** 🎯
