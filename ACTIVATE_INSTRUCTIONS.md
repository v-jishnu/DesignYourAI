# How to Activate Virtual Environment

## PowerShell Users (Most Common)

```powershell
# Option 1: Use the activation script with .\
.\activate_venv.bat

# Option 2: Direct activation
.\.venv\Scripts\Activate.ps1
```

## Command Prompt Users

```cmd
# Option 1: Use the activation script
activate_venv.bat

# Option 2: Direct activation
.venv\Scripts\activate.bat
```

## Quick Reference

| Shell | Command |
|-------|---------|
| **PowerShell** | `.\activate_venv.bat` or `.\.venv\Scripts\Activate.ps1` |
| **Command Prompt** | `activate_venv.bat` or `.venv\Scripts\activate.bat` |

## Verify Activation

After activation, you should see:

```
(.venv) PS C:\DesignYourAI>
```

The `(.venv)` prefix means you're in the virtual environment!

## Common Issues

### PowerShell: "cannot be loaded because running scripts is disabled"

**Solution 1:** Use the `.bat` file instead:
```powershell
.\activate_venv.bat
```

**Solution 2:** Allow scripts (one-time):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### PowerShell: "The term 'activate.bat' is not recognized"

**Solution:** Add `.\` prefix:
```powershell
.\activate_venv.bat
```

## Daily Workflow

```powershell
# 1. Navigate to project
cd C:\DesignYourAI

# 2. Activate (PowerShell)
.\activate_venv.bat

# 3. Use the system
python test_sample.py
python main.py --sources "URL"

# 4. Deactivate when done
deactivate
```

## Files Available

- `activate_venv.bat` - Main activation script (use this!)
- `.venv\Scripts\activate.bat` - Direct activation (Command Prompt)
- `.venv\Scripts\Activate.ps1` - Direct activation (PowerShell)
