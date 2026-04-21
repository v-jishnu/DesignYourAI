# 🚀 START HERE - Quick Setup

## ⚠️ PowerShell Execution Policy Issue Detected

Your PowerShell has script execution disabled (common security setting). Here are **3 easy solutions**:

---

## ✅ SOLUTION 1: Use Command Prompt (Easiest)

**Recommended if you're not familiar with PowerShell execution policies.**

### Steps:

1. **Open Command Prompt** (not PowerShell):
   - Press `Win + R`
   - Type: `cmd`
   - Press Enter

2. **Navigate to project:**
   ```cmd
   cd C:\DesignYourAI
   ```

3. **Activate virtual environment:**
   ```cmd
   .venv\Scripts\activate.bat
   ```

4. **You'll see:**
   ```cmd
   (venv) C:\DesignYourAI>
   ```

5. **Now use the system:**
   ```cmd
   python test_sample.py
   python main.py --sources "URL"
   ```

**Works perfectly in Command Prompt!**

---

## ✅ SOLUTION 2: Allow PowerShell Scripts (One-time)

**If you prefer PowerShell, enable scripts once:**

```powershell
# Run this ONCE (allows scripts for your user)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate normally:
.\.venv\Scripts\Activate.ps1

# You'll see:
(.venv) PS C:\DesignYourAI>
```

---

## ✅ SOLUTION 3: Bypass Policy (Per-session)

**Temporary bypass for current session only:**

```powershell
# Bypass policy for this session
powershell -ExecutionPolicy Bypass

# Then activate:
.\.venv\Scripts\Activate.ps1
```

---

## 🎯 Recommended: Use Command Prompt

**Why?** Simpler, no policy issues, works immediately.

### Complete Workflow (Command Prompt)

```cmd
REM 1. Open Command Prompt (Win+R, type cmd)

REM 2. Go to project
cd C:\DesignYourAI

REM 3. Activate
.venv\Scripts\activate.bat

REM You'll see: (venv) C:\DesignYourAI>

REM 4. Add API key (first time only)
notepad .env
REM Add: GEMINI_API_KEY=AIza...your-key...

REM 5. Test
python test_sample.py

REM 6. Process MCQs
python main.py --sources "https://example.com/mcqs"

REM 7. Deactivate when done
deactivate
```

---

## 📋 Quick Verification

### Check if Activated

**Look for the prefix:**

```
✅ Activated:
(venv) C:\DesignYourAI>          (Command Prompt)
(.venv) PS C:\DesignYourAI>      (PowerShell)

❌ Not activated:
C:\DesignYourAI>                 (Command Prompt)
PS C:\DesignYourAI>              (PowerShell)
```

### Check Python Location

```cmd
where python
```

**Should show:**
```
C:\DesignYourAI\.venv\Scripts\python.exe  ✅ Correct!
```

**Not this:**
```
C:\Users\...\AppData\Local\Programs\Python\...  ❌ Not activated
```

---

## 🎓 What Happened?

When you ran `.\activate_venv.bat` in PowerShell, it:
- ✅ Found the script
- ✅ Started running
- ❌ Couldn't fully activate due to execution policy

**Solution:** Use Command Prompt (cmd) instead - no restrictions!

---

## 📚 Next Steps

### Option A: Command Prompt (Recommended)

1. Open Command Prompt: `Win+R` → `cmd`
2. `cd C:\DesignYourAI`
3. `.venv\Scripts\activate.bat`
4. Add Gemini API key to `.env`
5. `python test_sample.py`

### Option B: PowerShell (if you prefer)

1. Allow scripts (one-time): `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
2. `.\.venv\Scripts\Activate.ps1`
3. Add Gemini API key to `.env`
4. `python test_sample.py`

---

## 🔧 Files for Your Reference

| File | Purpose |
|------|---------|
| **START_HERE.md** | This file - setup guide |
| **CHEAT_SHEET.txt** | Quick command reference |
| **POWERSHELL_FIX.md** | PowerShell execution policy details |
| **.env** | Add your GEMINI_API_KEY here |

---

## ✅ Summary

**Problem:** PowerShell execution policy blocks scripts

**Solution:** Use Command Prompt (`cmd`) - works perfectly!

**Alternative:** Enable PowerShell scripts (one-time command)

---

## 🎉 You're Almost There!

1. ✅ Virtual environment created
2. ✅ Dependencies installed
3. ⏳ Just need to activate properly (use cmd!)
4. ⏳ Add Gemini API key
5. ⏳ Test with `python test_sample.py`

**Use Command Prompt and you'll be running in 2 minutes!**

---

**Quick Start:** Open cmd → `cd C:\DesignYourAI` → `.venv\Scripts\activate.bat` → Done!
