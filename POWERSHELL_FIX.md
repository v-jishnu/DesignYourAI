# PowerShell Activation Fix

## ⚠️ Important: PowerShell Requires `.\` Prefix

If you're using **PowerShell** (which you likely are), you need to use `.\` before the script name.

## ✅ Correct Commands

### PowerShell (Windows default)

```powershell
# Use this:
.\activate_venv.bat

# NOT this:
activate.bat  ❌ Won't work in PowerShell!
```

### Command Prompt (if you prefer)

```cmd
# Use this:
activate_venv.bat

# Works without .\ prefix
```

## 🚀 Quick Start (PowerShell)

```powershell
# 1. Navigate to project
cd C:\DesignYourAI

# 2. Activate virtual environment
.\activate_venv.bat

# You'll see:
(.venv) PS C:\DesignYourAI>

# 3. Test
python test_sample.py

# 4. Use
python main.py --sources "URL"

# 5. Deactivate
deactivate
```

## 📋 Full Workflow Example

```powershell
PS C:\DesignYourAI> .\activate_venv.bat

========================================
Activating DesignYourAI Virtual Environment
========================================

✅ Virtual environment activated!
   You should see (.venv) in your prompt

(.venv) PS C:\DesignYourAI> python test_sample.py

✅ Created 3 sample MCQs
✅ ALL TESTS PASSED!

(.venv) PS C:\DesignYourAI> python main.py --sources "https://example.com/mcqs"

🚀 Starting ingestion workflow...
✅ Stored 35 MCQs

(.venv) PS C:\DesignYourAI> deactivate

PS C:\DesignYourAI>
```

## 💡 Why the `.\` Prefix?

PowerShell doesn't run scripts from the current directory by default for security reasons. The `.\` explicitly tells PowerShell "run this script from the current folder."

## Alternative: Use PowerShell's Native Activation

```powershell
# Direct activation (PowerShell native)
.\.venv\Scripts\Activate.ps1

# You'll see:
(.venv) PS C:\DesignYourAI>
```

## 🔧 If You Get Execution Policy Error

```powershell
# Error: "cannot be loaded because running scripts is disabled"

# Solution: Use .bat file instead
.\activate_venv.bat

# OR allow scripts (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## ✅ Verification

Check if activated:

```powershell
# Look for (.venv) prefix
(.venv) PS C:\DesignYourAI>  ✅ Activated!

PS C:\DesignYourAI>  ❌ Not activated

# Check Python location
where.exe python

# Should show:
C:\DesignYourAI\.venv\Scripts\python.exe  ✅ Correct!
```

## 📚 Documentation Note

**Important:** Wherever you see `activate.bat` in the documentation, use `.\activate_venv.bat` if you're in PowerShell.

## 🎯 Remember

| Shell | Command |
|-------|---------|
| **PowerShell** | `.\activate_venv.bat` |
| **Command Prompt** | `activate_venv.bat` |
| **PowerShell (native)** | `.\.venv\Scripts\Activate.ps1` |
| **Command Prompt (native)** | `.venv\Scripts\activate.bat` |

---

**TL;DR for PowerShell users:** Use `.\activate_venv.bat` not `activate.bat`
