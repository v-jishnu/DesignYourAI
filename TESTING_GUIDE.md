# Testing Guide - What Works Now

## ⚠️ Important Discovery: GeeksforGeeks Won't Work

**The GeeksforGeeks quiz you provided uses JavaScript rendering**, which our current BeautifulSoup extractor cannot handle.

### Why It Won't Work:
- ✅ Our extractor: Static HTML with BeautifulSoup
- ❌ GeeksforGeeks: JavaScript-rendered content (JSON data loaded dynamically)
- ❌ Result: BeautifulSoup sees empty page before JavaScript runs

---

## ✅ What WILL Work Right Now

### 1. Static HTML MCQ Sites
**Examples of compatible sources:**
- Sanfoundry: `https://www.sanfoundry.com/machine-learning-questions-answers/`
- InterviewBit static pages
- Tutorial sites with visible MCQs in HTML
- Any page where "View Page Source" shows the questions

### 2. PDF Files
- MCQ question banks in PDF format
- Interview preparation PDFs
- Academic quiz documents

### 3. DOCX Files
- Word documents with MCQs
- Formatted question banks

---

## 🧪 Test the Current System

### Option 1: Test with Local Sample (Recommended First)

I've created a sample HTML file with 5 ML MCQs.

**Run this:**
```cmd
cd C:\DesignYourAI
test_sample_local.bat
```

**What it does:**
1. Extracts 5 MCQs from `data/raw/sample_mcqs.html`
2. Classifies them using Gemini AI:
   - Category: Conceptual/Mathematical/Application
   - Topic: AI/ML/Data Science/System Design
   - Difficulty: Easy/Medium/Hard
3. Checks for duplicates
4. Stores in Excel: `data/knowledge_base/mcq_knowledge_base.xlsx`

**Expected output:**
```
🚀 Starting ingestion workflow...
📄 Processing: data/raw/sample_mcqs.html
✅ Extracted 5 MCQs
✅ Classified 5 MCQs
✅ Stored 5 MCQs (0 duplicates)
📊 Progress: 5/800 (0.6%)
```

**Then check Excel:**
- Open `data\knowledge_base\mcq_knowledge_base.xlsx`
- You'll see 5 rows with all metadata filled in

---

### Option 2: Try Static MCQ Sources

**Sources that SHOULD work:**

**1. Sanfoundry (Static HTML):**
```cmd
cd C:\DesignYourAI
.venv\Scripts\activate.bat
python main.py --sources "https://www.sanfoundry.com/machine-learning-questions-answers/"
```

**2. InterviewBit (if static sections):**
```cmd
python main.py --sources "https://www.interviewbit.com/machine-learning-mcq/"
```

**3. Your own PDF/DOCX files:**
```cmd
python main.py --sources "path/to/your/mcq_file.pdf"
```

---

## 🔧 Setup Required

### 1. Ensure Gemini API Key is Set

```cmd
notepad .env
```

Add this line:
```
GEMINI_API_KEY=your-actual-key-here
```

Get key from: https://makersuite.google.com/app/apikey

### 2. Verify Virtual Environment

```cmd
cd C:\DesignYourAI
.venv\Scripts\activate.bat
```

You should see: `(venv) C:\DesignYourAI>`

---

## 📊 What You'll See

### Console Output:
```
🚀 Starting ingestion workflow...
📄 Processing: [your source]
✅ Extracted X MCQs
✅ Classified X MCQs
✅ Stored Y MCQs (Z duplicates)
📊 Progress: Y/800 (X.X%)
```

### Excel Output:
Open: `data\knowledge_base\mcq_knowledge_base.xlsx`

Columns you'll see:
- Question_ID
- Question_Text
- Option_A, Option_B, Option_C, Option_D
- Correct_Answer (if found in source)
- Explanation (if found in source)
- **Category** (AI-assigned: Conceptual/Mathematical/Application)
- **Topic** (AI-assigned: AI/ML/Data Science/System Design)
- **Difficulty** (AI-assigned: Easy/Medium/Hard)
- Source (URL or file path)
- Date_Added
- Used_Status (FALSE - for future LinkedIn posting)
- Image fields (empty for now, Day 4 will enable these)

---

## 🚫 What WON'T Work Yet

### JavaScript-Rendered Sites:
- ❌ GeeksforGeeks quizzes (needs Selenium)
- ❌ Dynamic quiz platforms
- ❌ Sites that load questions via AJAX

**Solution:** I can add Selenium/Playwright support (~1 day work)

### Q&A Format:
- ❌ Descriptive interview questions (Days 6-8 will add this)

**Solution:** Currently in implementation plan, coming soon

### Images:
- ❌ Image extraction not integrated yet (Day 4 will add this)

**Solution:** Code is ready, just needs integration

---

## 🎯 Recommended Testing Flow

### Step 1: Test Locally (5 minutes)
```cmd
test_sample_local.bat
```
**Verifies:** Extraction → Classification → Storage pipeline works

### Step 2: Test with Static Source (10 minutes)
Try Sanfoundry or another static HTML MCQ site
**Verifies:** Real-world web extraction works

### Step 3: Review Excel Output
Check classifications make sense
**Verifies:** AI classification quality

### Step 4: Test Deduplication
Run same source twice, verify count doesn't increase
**Verifies:** Duplicate detection works

---

## 🔄 Next Steps After Testing

**If test works:**
1. I continue implementation (Days 3-8)
2. You get:
   - Image support (Days 3-5)
   - Q&A to MCQ generation (Days 6-8)
   - JavaScript support (optional, +1 day)

**If you need JavaScript support urgently:**
- I can prioritize adding Selenium
- Takes ~1 day
- Then GeeksforGeeks will work

**If you have other static sources:**
- Current system will work great!
- Just provide the URLs/files
- I'll continue with planned features

---

## 💡 Finding Static MCQ Sources

**How to check if a source will work:**

1. Visit the page in browser
2. Right-click → "View Page Source"
3. Search for question text in source
4. If you see it → ✅ Will work
5. If you don't see it → ❌ JavaScript-rendered, won't work yet

**Good source characteristics:**
- Questions visible in HTML source
- Static pages (no "Load More" buttons)
- Direct text content (not loaded via API calls)

---

## 📞 Support

**If extraction fails:**
1. Check `.env` has `GEMINI_API_KEY`
2. Verify virtual environment is activated `(venv)`
3. Check source is static HTML (View Page Source test)
4. Share error message with me for debugging

**Ready to test?** Start with `test_sample_local.bat` to verify everything works!
