# 🆓 FREE API Setup Guide

## ✅ Your System Now Supports FREE APIs!

I've updated your MCQ ingestion system to support **FREE LLM providers**. You can now use:

1. **Google Gemini** (RECOMMENDED - Best free tier)
2. **Groq** (Very fast, free tier)
3. **Together.ai** (Free tier available)

No more paid APIs required! 🎉

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Get Your FREE API Key

#### Option A: Google Gemini (RECOMMENDED)

**Why Gemini?**
- ✅ **100% FREE** with generous limits
- ✅ 15 requests per minute
- ✅ 1,500 requests per day
- ✅ Fast and accurate
- ✅ No credit card required

**Get your key:**

1. Go to: **https://makersuite.google.com/app/apikey**
2. Click **"Get API Key"** or **"Create API Key"**
3. Select **"Create API key in new project"**
4. Copy your key (starts with `AIza...`)

**Example key:** `AIzaSyD...your-key-here...xyz123`

---

#### Option B: Groq (Alternative - Very Fast)

**Why Groq?**
- ✅ FREE tier available
- ✅ Extremely fast inference
- ✅ Good for rapid processing

**Get your key:**

1. Go to: **https://console.groq.com/**
2. Sign up for free account
3. Go to API Keys section
4. Create new API key
5. Copy your key

---

#### Option C: Together.ai (Alternative)

**Why Together.ai?**
- ✅ FREE credits on signup
- ✅ Multiple models available

**Get your key:**

1. Go to: **https://api.together.xyz/**
2. Sign up
3. Get API key from settings

---

### Step 2: Configure Your System

Edit the `.env` file:

```bash
notepad .env
```

**Add your API key:**

```bash
# For Gemini (RECOMMENDED)
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyD...your-key-here...xyz123

# OR for Groq
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key-here

# OR for Together.ai
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-key-here
```

---

### Step 3: Install Updated Dependencies

```bash
pip install google-generativeai openai
```

Or reinstall everything:

```bash
pip install -r requirements.txt
```

---

### Step 4: Test Your Setup

```bash
python test_sample.py
```

**Expected output:**

```
✅ Created 3 sample MCQs

🔍 Testing classification...
[ClassificationAgent] Using LLM provider: gemini (model: gemini-1.5-flash)

📊 Classification Results:
  MCQ 1:
    Question: What is the primary purpose of backpropagation in neural...
    Category: Conceptual
    Topic: ML
    Difficulty: Easy

✅ Successfully stored 3 MCQs
✅ ALL TESTS PASSED!
```

---

## 📖 Usage Examples

### Example 1: Single Link with Gemini

```bash
# Make sure .env has:
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=AIza...your-key...

# Run with single source
python main.py --sources "https://example.com/ai-mcqs"
```

**What happens:**

```
🚀 Starting ingestion workflow...
[ClassificationAgent] Using LLM provider: gemini (model: gemini-1.5-flash)

STEP 1: Extraction
✅ Extracted 40 MCQs from https://example.com/ai-mcqs

STEP 2: Classification
✅ Classified batch 1 (10 MCQs) with Gemini
✅ Classified batch 2 (10 MCQs) with Gemini
✅ Classified batch 3 (10 MCQs) with Gemini
✅ Classified batch 4 (10 MCQs) with Gemini

STEP 3: Deduplication
✅ Found 2 duplicates, 38 unique

STEP 4: Storage
✅ Stored 38 MCQs to Excel

======================================
RESULT:
✅ Extracted: 40 MCQs
✅ Stored: 38 MCQs
📊 Total: 38/800 (4.8%)
💰 Cost: $0 (FREE!)
======================================
```

---

### Example 2: Multiple Links (One at a Time)

```bash
# Link 1
python main.py --sources "https://site1.com/ai-questions"
# ✅ 30 MCQs added (Total: 30/800)

# Wait a minute, then Link 2
python main.py --sources "https://site2.com/ml-mcqs"
# ✅ 45 MCQs added (Total: 75/800)

# Link 3
python main.py --sources "https://site3.com/ds-interview"
# ✅ 50 MCQs added (Total: 125/800)

# Keep going until 800!
```

---

## 🎯 Provider Comparison

| Provider | Free Tier | Speed | Quality | Limits |
|----------|-----------|-------|---------|--------|
| **Gemini** | ✅ Yes | Fast | Excellent | 15/min, 1500/day |
| **Groq** | ✅ Yes | Very Fast | Good | Varies |
| **Together.ai** | ✅ Credits | Medium | Good | Credit-based |
| Claude | ❌ No | Fast | Excellent | Paid only |
| OpenAI | ❌ No | Medium | Excellent | Paid only |

**RECOMMENDATION: Use Gemini** (Best free option)

---

## 💡 Pro Tips

### 1. Rate Limit Management

Gemini allows 15 requests/minute. Each batch = 10 MCQs = 1 request.

**For 100 MCQs:**
- 10 batches = 10 requests
- Takes ~1-2 minutes
- ✅ Well within limits!

**For 800 MCQs:**
- 80 batches = 80 requests
- Spread across ~6 minutes
- ✅ No issues!

### 2. Switch Providers Anytime

Just edit `.env`:

```bash
# Switch from Gemini to Groq
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key
```

No code changes needed!

### 3. Daily Limits

Gemini: 1,500 requests/day = **15,000 MCQs/day**

More than enough for building your 800 MCQ knowledge base!

---

## 🔧 Troubleshooting

### "API key not found"

**Error:**
```
ValueError: API key for provider 'gemini' not found.
Please set GEMINI_API_KEY in .env file
```

**Solution:**
1. Open `.env`
2. Make sure `GEMINI_API_KEY=AIza...` is filled in
3. Save the file
4. Try again

---

### "google-generativeai not installed"

**Error:**
```
ImportError: google-generativeai package required
```

**Solution:**
```bash
pip install google-generativeai
```

---

### Rate Limit Exceeded

**Error:**
```
429 Resource has been exhausted
```

**Solution:**
- Wait 1 minute
- Process fewer sources at once
- Gemini: 15/min limit
- Just run again after waiting

---

### Classification Not Working

**Check:**
1. API key is correct (copy-paste carefully)
2. Internet connection is working
3. Provider is set correctly in `.env`

**Test:**
```bash
python test_sample.py
```

---

## 📊 Cost Comparison

### Before (Claude Only)

- 800 MCQs = ~$2-3
- 10,000 MCQs = ~$30-40
- **PAID API REQUIRED**

### After (Gemini FREE)

- 800 MCQs = **$0** ✅
- 10,000 MCQs = **$0** ✅
- **100% FREE!** 🎉

---

## ✅ Complete Workflow Example

### Scenario: Build 800 MCQ Knowledge Base for FREE

#### Day 1: Setup (5 minutes)

```bash
# 1. Get Gemini API key
# Visit: https://makersuite.google.com/app/apikey

# 2. Add to .env
notepad .env
# Add: GEMINI_API_KEY=AIza...your-key...

# 3. Test
python test_sample.py
# ✅ Should work!
```

#### Day 1-7: Collect MCQs (1-2 hours total)

```bash
# Find sources with MCQs
# Example sites:
# - GeeksforGeeks
# - InterviewBit
# - LeetCode discussions
# - Medium articles
# - GitHub repos

# Process one at a time
python main.py --sources "https://site1.com/mcqs"
# Wait for completion, check results

python main.py --sources "https://site2.com/more-mcqs"
# Repeat...

# Check progress
# Open: data/knowledge_base/mcq_knowledge_base.xlsx
```

#### After 800 MCQs: Done! 🎉

```
📊 Final Status:
✅ Total MCQs: 800
✅ Categories: Assigned
✅ Topics: Assigned
✅ Duplicates: Removed
💰 Total Cost: $0
```

---

## 🎓 FAQ

**Q: Is Gemini really free?**
A: Yes! 100% free with generous limits (1,500 requests/day).

**Q: How accurate is Gemini vs Claude?**
A: Very similar! Gemini 1.5 Flash is excellent for classification.

**Q: Can I use multiple providers?**
A: Yes! Just change `LLM_PROVIDER` in `.env`.

**Q: What if I hit rate limits?**
A: Just wait 1 minute and run again. Gemini: 15/min is plenty.

**Q: Can I process PDFs with Gemini?**
A: Yes! Extraction works the same. Only classification uses Gemini.

**Q: Do I need a credit card for Gemini?**
A: No! Completely free, no credit card required.

---

## 🚀 You're Ready!

Your system now supports **FREE APIs** with the **SAME QUALITY** as paid options!

**Next steps:**

1. ✅ Get your Gemini API key (5 minutes)
2. ✅ Add to `.env` file
3. ✅ Run `python test_sample.py`
4. ✅ Start processing your MCQ sources!

**Build your 800 MCQ knowledge base for $0! 🎉**

---

**Need help?** Check the main [USAGE.md](USAGE.md) guide or run `python test_sample.py` to verify setup.
