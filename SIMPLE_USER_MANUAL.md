# 📘 Simple User Manual - MCQ Ingestion System

## 🎯 What This Does

**Automatically extracts interview MCQs from websites/PDFs and organizes them into an Excel database.**

---

## 🚀 3-Step Setup (5 Minutes)

### Step 1: Get FREE API Key

Go to: **https://makersuite.google.com/app/apikey**

Click: **"Get API Key"**

Copy: `AIzaSyD...your-key...`

### Step 2: Configure

```bash
notepad .env
```

Add this:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyD...paste-your-key-here...
```

Save and close.

### Step 3: Test

```bash
python test_sample.py
```

Should say: ✅ ALL TESTS PASSED!

---

## 📖 How to Use (One Link at a Time)

### Basic Workflow

```
┌─────────────────────────────┐
│ 1. Find MCQ Source          │
│    (website with questions) │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 2. Run Command              │
│    python main.py           │
│    --sources "URL"          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 3. Wait 1-3 Minutes         │
│    System processes         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 4. Check Excel File         │
│    New MCQs added!          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 5. Repeat for Next Link    │
│    Until 800 MCQs           │
└─────────────────────────────┘
```

---

## 💻 Real Example

### Find a Source

Example: `https://www.geeksforgeeks.org/machine-learning-mcqs/`

### Run Command

```bash
python main.py --sources "https://www.geeksforgeeks.org/machine-learning-mcqs/"
```

### Watch Progress

```
🚀 Starting ingestion workflow...

[✓] STEP 1: Extraction
    → Fetching webpage...
    → Found 35 MCQs

[✓] STEP 2: Classification
    → Using Gemini API (FREE)
    → Classifying batch 1... Done
    → Classifying batch 2... Done
    → Classifying batch 3... Done
    → Classifying batch 4... Done

[✓] STEP 3: Deduplication
    → Checking against 0 existing MCQs
    → 2 duplicates found
    → 33 unique MCQs

[✓] STEP 4: Storage
    → Saving to Excel...
    → Created backup
    → Done!

========================================
✅ RESULT:
   Extracted: 35 MCQs
   Duplicates: 2
   Stored: 33 MCQs

📊 Progress: 33/800 (4.1%)
========================================
```

### Check Result

Open file: `data/knowledge_base/mcq_knowledge_base.xlsx`

You'll see 33 new rows with:
- Questions
- 4 Options each
- Category (Conceptual/Mathematical/Application)
- Topic (AI/ML/Data Science/System Design)
- Difficulty (Easy/Medium/Hard)

---

## 📝 What Each Step Does

### Step 1: Extraction

```
INPUT:  Website URL or PDF file
        ↓
ACTION: Scrapes/reads the page
        Finds question patterns
        Extracts question + 4 options
        ↓
OUTPUT: List of raw MCQs
```

**Example:**
```
Found on page:
"What is Machine Learning?
A) Programming
B) Learning from data
C) Hardware
D) Software"

Extracted as:
Question: "What is Machine Learning?"
Option A: "Programming"
Option B: "Learning from data"
Option C: "Hardware"
Option D: "Software"
```

---

### Step 2: Classification (AI Magic 🤖)

```
INPUT:  Raw MCQs
        ↓
ACTION: Sends to Gemini AI
        AI reads question
        Determines:
        - Is it Conceptual/Math/Application?
        - Is it AI/ML/DS/System Design?
        - Is it Easy/Medium/Hard?
        ↓
OUTPUT: MCQs with categories
```

**Example:**
```
Question: "What is Machine Learning?"

Gemini thinks:
→ Asks for definition → Conceptual
→ About ML → Topic: ML
→ Basic knowledge → Easy

Result:
Category: Conceptual
Topic: ML
Difficulty: Easy
```

---

### Step 3: Deduplication

```
INPUT:  Classified MCQs
        ↓
ACTION: Opens existing Excel file
        Compares new vs existing
        Removes exact duplicates
        Removes very similar ones
        ↓
OUTPUT: Only unique MCQs
```

**Example:**
```
New: "What is Machine Learning?"
Existing: "What is Machine Learning?"
→ DUPLICATE! Skip.

New: "What is ML?"
Existing: "What is Machine Learning?"
→ 90% similar! Skip.

New: "Explain Deep Learning"
Existing: Nothing similar
→ UNIQUE! Keep.
```

---

### Step 4: Storage

```
INPUT:  Unique MCQs
        ↓
ACTION: Validates format
        Appends to Excel
        Creates backup
        Updates count
        ↓
OUTPUT: Updated Excel file
```

---

## 🔄 Complete Workflow Example

### Goal: Get 100 MCQs

#### Link 1: AI Questions

```bash
python main.py --sources "https://site1.com/ai-mcqs"
```

Result: 30 MCQs added (Total: 30/100)

---

**Wait 2 minutes (optional)**

---

#### Link 2: ML Questions

```bash
python main.py --sources "https://site2.com/ml-interview"
```

Result: 35 MCQs added (Total: 65/100)

---

#### Link 3: Data Science

```bash
python main.py --sources "https://site3.com/ds-mcqs"
```

Result: 40 MCQs added (Total: 105/100)

---

**🎉 Done! You have 105 MCQs!**

---

## 📊 Understanding Results

After each run, you see:

```
✅ Extracted: 40 MCQs      ← Found on page
✅ Classified: 40 MCQs     ← AI categorized them
✅ Duplicates: 5           ← Removed repeats
✅ Stored: 35 MCQs         ← Added to Excel

📊 Total: 135/800 (16.9%)  ← Your progress
```

**Breakdown:**
- **Extracted:** How many MCQs found on the page
- **Classified:** All got categorized (same number)
- **Duplicates:** How many were already in database
- **Stored:** New unique ones added
- **Total:** Running total in your knowledge base

---

## 🎯 Tips

### Finding Good Sources

**✅ Good sources:**
- GeeksforGeeks MCQs
- InterviewBit questions
- Technical blogs with MCQs
- GitHub repos with questions
- PDF interview guides

**❌ Avoid:**
- Sites without clear A) B) C) D) format
- Paywalled content
- JavaScript-heavy dynamic sites

### Best Practices

**1. One link at a time**
```bash
# Good
python main.py --sources "link1"
# Wait for completion
python main.py --sources "link2"

# Bad (don't do this)
python main.py --sources "link1" "link2" "link3"
```

**2. Check results after each**
- Open Excel file
- Verify MCQs look correct
- Check categories assigned

**3. Keep a list**
```
sources_done.txt:
✅ https://site1.com/mcqs - 30 MCQs
✅ https://site2.com/more - 40 MCQs
⏳ https://site3.com/next - To do
```

---

## 🛠️ Troubleshooting

### "No MCQs extracted"

**Problem:** Found 0 MCQs on page

**Causes:**
- Page doesn't have MCQ format
- Questions not in A) B) C) D) pattern

**Solution:**
- Check page manually
- Look for clear MCQ structure
- Try different source

---

### "Classification failed"

**Problem:** API error

**Causes:**
- API key wrong
- No internet
- Rate limit hit

**Solution:**
```bash
# Check API key in .env
notepad .env

# Test connection
python test_sample.py

# Wait 1 minute if rate limited
```

---

### "Duplicate found"

**Problem:** All MCQs marked as duplicates

**This is good!** Means:
- You already have these MCQs
- Deduplication working correctly
- Try different source

---

## ❓ FAQ

**Q: How long does each link take?**
A: 1-3 minutes depending on number of MCQs

**Q: Can I stop mid-process?**
A: Yes! Press Ctrl+C. Already processed MCQs are saved.

**Q: Is my API key safe?**
A: Yes! Stored locally in `.env`, never uploaded.

**Q: Do I need internet?**
A: Yes, for:
- Fetching websites
- Calling Gemini API

**Q: Can I use PDFs?**
A: Yes!
```bash
python main.py --sources "data/raw/questions.pdf"
```

**Q: What if I hit daily limit?**
A: Gemini: 1,500 requests/day = 15,000 MCQs/day
You won't hit it for 800 MCQs!

---

## 🎉 You're Ready!

**Summary:**

1. ✅ Get Gemini API key (FREE)
2. ✅ Add to `.env` file
3. ✅ Run: `python test_sample.py`
4. ✅ Process one link at a time
5. ✅ Check Excel file
6. ✅ Repeat until 800 MCQs!

**Simple as that! 🚀**

---

**Need more help?**
- Detailed guide: [FREE_API_SETUP.md](FREE_API_SETUP.md)
- Full docs: [USAGE.md](USAGE.md)
- Run test: `python test_sample.py`
