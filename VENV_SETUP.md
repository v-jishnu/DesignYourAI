# Virtual Environment Setup

## ✅ Isolated Environment Created!

Your MCQ ingestion system now runs in an **isolated virtual environment** (`.venv`). This means:

- ✅ **No conflicts** with your other Python projects
- ✅ **No version issues** - dependencies are isolated
- ✅ **Clean setup** - only this project affected
- ✅ **Safe to experiment** - won't break other codebases

---

## 🚀 Quick Start (Windows)

### Option 1: Using Helper Script (Easiest)

```bash
# Just double-click or run:
activate.bat

# Or from command line:
.\activate.bat
```

This will:
1. Activate the virtual environment
2. Show you're ready to use the system
3. Display available commands

### Option 2: Manual Activation

```bash
# PowerShell
.venv\Scripts\Activate.ps1

# Command Prompt
.venv\Scripts\activate.bat
```

---

## 📋 Complete Usage Workflow

### 1. Activate Virtual Environment

```bash
# Run this EVERY TIME you open a new terminal
activate.bat

# You'll see (.venv) in your prompt:
(.venv) PS C:\DesignYourAI>
```

### 2. Use the System

```bash
# Test it
python test_sample.py

# Process MCQs
python main.py --sources "https://example.com/mcqs"
```

### 3. Deactivate When Done

```bash
deactivate

# Prompt returns to normal:
PS C:\DesignYourAI>
```

---

## 🔧 What's Installed (Isolated)

The `.venv` folder contains:

| Package | Version | Purpose |
|---------|---------|---------|
| google-generativeai | 0.3.2 | Gemini API (FREE) |
| openai | 1.10.0 | OpenAI/Groq/Together compatible |
| pandas | Latest | Excel operations |
| openpyxl | Latest | Excel read/write |
| beautifulsoup4 | Latest | Web scraping |
| aiohttp | Latest | Async HTTP |
| pdfplumber | Latest | PDF extraction |
| python-docx | Latest | DOCX parsing |
| tenacity | Latest | Retry logic |

**These are ONLY for this project!** Your other projects are unaffected.

---

## ✅ Verification

### Check Virtual Environment Status

```bash
# Are you in the venv?
where python

# Should show:
# C:\DesignYourAI\.venv\Scripts\python.exe

# If NOT activated, you'll see:
# C:\Users\...\AppData\Local\Programs\Python\python.exe
```

### Test Installation

```bash
# Activate first
activate.bat

# Then test
python test_sample.py

# Expected:
✅ Created 3 sample MCQs
🔍 Testing classification...
[ClassificationAgent] Using LLM provider: gemini
✅ ALL TESTS PASSED!
```

---

## 🎯 Daily Workflow

**Every time you work on this project:**

```bash
# 1. Open terminal in C:\DesignYourAI

# 2. Activate environment
activate.bat

# 3. Use the system
python main.py --sources "URL"

# 4. When done, deactivate
deactivate
```

---

## 💡 Pro Tips

### 1. Always Activate First

```bash
# WRONG (without activation)
PS C:\DesignYourAI> python test_sample.py
# Error: google-generativeai not found

# RIGHT (with activation)
PS C:\DesignYourAI> activate.bat
(.venv) PS C:\DesignYourAI> python test_sample.py
# ✅ Works!
```

### 2. Check If Activated

Look for `(.venv)` in your prompt:

```bash
# Activated:
(.venv) PS C:\DesignYourAI>

# Not activated:
PS C:\DesignYourAI>
```

### 3. VSCode Integration

If using VSCode:
1. Open folder: `C:\DesignYourAI`
2. VSCode will detect `.venv`
3. Select Python interpreter: `.venv\Scripts\python.exe`
4. Terminal will auto-activate!

### 4. Multiple Terminal Windows

Each new terminal needs activation:

```bash
# Terminal 1
activate.bat

# Terminal 2 (new window)
activate.bat  # Need to activate again
```

---

## 🔍 Troubleshooting

### "google-generativeai not found"

**Problem:** Virtual environment not activated

**Solution:**
```bash
activate.bat
python test_sample.py
```

### "Activate.ps1 cannot be loaded"

**Problem:** PowerShell execution policy

**Solution:**
```bash
# Use Command Prompt instead
cmd
activate.bat

# Or allow scripts in PowerShell (one-time):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "python not found"

**Problem:** Not in correct directory

**Solution:**
```bash
cd C:\DesignYourAI
activate.bat
```

### Want to Reinstall Dependencies

```bash
# Activate first
activate.bat

# Then reinstall
pip install --index-url https://pypi.org/simple -r requirements.txt --upgrade
```

---

## 📦 What's in `.venv` Folder?

```
.venv/
├── Scripts/
│   ├── python.exe          # Isolated Python
│   ├── pip.exe             # Isolated pip
│   ├── activate.bat        # Activation script
│   └── ...
├── Lib/
│   └── site-packages/      # All installed packages
│       ├── google/
│       ├── openai/
│       ├── pandas/
│       └── ...
└── pyvenv.cfg              # Config
```

**Size:** ~500 MB (all dependencies isolated here)

---

## 🗑️ Cleanup (If Needed)

### Remove Virtual Environment

```bash
# If you need to start fresh
rmdir /s .venv

# Then recreate
python -m venv .venv
activate.bat
pip install --index-url https://pypi.org/simple -r requirements.txt
```

### Keep Project, Remove Venv

The `.gitignore` already excludes `.venv`, so:
- Git won't track it
- Safe to delete and recreate anytime
- Won't affect your code

---

## ✅ Benefits Summary

| Aspect | Without Venv | With Venv (.venv) |
|--------|--------------|-------------------|
| **Isolation** | ❌ Global packages | ✅ Project-only |
| **Conflicts** | ❌ Version issues | ✅ No conflicts |
| **Other Projects** | ❌ Affected | ✅ Unaffected |
| **Clean Uninstall** | ❌ Hard to remove | ✅ Just delete folder |
| **Reproducible** | ❌ Hard to recreate | ✅ Easy with requirements.txt |

---

## 🎓 Understanding Virtual Environments

### What is `.venv`?

A **virtual environment** is an isolated Python environment where:
- Python packages are installed locally (in `.venv` folder)
- Doesn't affect your system Python
- Doesn't affect other projects

### Why Use It?

```
Your System:
├── Python (global)
│   └── pandas 1.5.0 (for Project A)
│
├── DesignYourAI/
│   └── .venv/
│       └── pandas 2.1.4 (isolated for this project)
│
└── OtherProject/
    └── .venv/
        └── pandas 1.3.0 (isolated for other project)
```

**Each project has its own dependencies!**

---

## 🚀 You're Ready!

Your environment is now:
- ✅ Isolated from other projects
- ✅ Ready to use with FREE Gemini API
- ✅ Safe to experiment
- ✅ Easy to manage

**Next steps:**

1. ✅ Run `activate.bat`
2. ✅ Add Gemini API key to `.env`
3. ✅ Run `python test_sample.py`
4. ✅ Start processing MCQs!

---

**Remember:** Always run `activate.bat` before using the system!

**Questions?** Check [FREE_API_SETUP.md](FREE_API_SETUP.md) for API setup.
