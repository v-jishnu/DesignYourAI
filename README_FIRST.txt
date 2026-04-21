================================================================================
                    📖 READ THIS FIRST 📖
================================================================================

YOUR SYSTEM IS READY! Just need 3 simple steps:

================================================================================
STEP 1: Open Command Prompt (Not PowerShell!)
================================================================================

Press: Win + R
Type: cmd
Press: Enter

Why cmd? PowerShell has execution policy restrictions. Command Prompt works
immediately without any configuration!

================================================================================
STEP 2: Activate Virtual Environment
================================================================================

In Command Prompt:

   cd C:\DesignYourAI
   .venv\Scripts\activate.bat

You'll see: (venv) C:\DesignYourAI>

The (venv) prefix means you're in the isolated environment!

================================================================================
STEP 3: Add Your FREE Gemini API Key
================================================================================

   notepad .env

Add this line:
   GEMINI_API_KEY=AIza...paste-your-key-here...

Get your FREE key: https://makersuite.google.com/app/apikey
(No credit card required!)

Save and close.

================================================================================
STEP 4: Test It Works
================================================================================

   python test_sample.py

Expected output:
   ✅ Created 3 sample MCQs
   ✅ ALL TESTS PASSED!

If this works, you're ready! 🎉

================================================================================
STEP 5: Process Your First MCQ Source
================================================================================

   python main.py --sources "https://example.com/your-mcq-source"

Wait 1-3 minutes. It will:
   1. Extract MCQs from the website
   2. Classify them with FREE Gemini AI
   3. Remove duplicates
   4. Store in Excel

Check results: data\knowledge_base\mcq_knowledge_base.xlsx

================================================================================
REPEAT FOR MORE SOURCES
================================================================================

Just run the same command with different URLs:

   python main.py --sources "https://another-site.com/mcqs"
   python main.py --sources "https://yet-another-site.com/questions"

Keep going until you have 800 MCQs!

================================================================================
WHEN DONE
================================================================================

   deactivate

This exits the virtual environment.

================================================================================
NEXT TIME YOU USE IT
================================================================================

1. Open Command Prompt
2. cd C:\DesignYourAI
3. .venv\Scripts\activate.bat
4. python main.py --sources "URL"
5. deactivate

================================================================================
IMPORTANT NOTES
================================================================================

✅ Always activate before using (.venv\Scripts\activate.bat)
✅ Use Command Prompt (cmd), not PowerShell (simpler)
✅ Look for (venv) prefix in your prompt
✅ Process one URL at a time (simple and clean)
✅ 100% FREE with Gemini API
✅ Isolated environment won't affect other projects

================================================================================
HELP FILES
================================================================================

COMMAND_PROMPT_GUIDE.txt  - Complete Command Prompt guide
START_HERE.md             - Detailed setup instructions
CHEAT_SHEET.txt           - Quick command reference
FREE_API_SETUP.md         - Get Gemini API key guide

================================================================================
VISUAL WORKFLOW
================================================================================

┌─────────────────────────┐
│ Win+R → cmd → Enter     │  Open Command Prompt
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ cd C:\DesignYourAI      │  Navigate
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ .venv\Scripts\          │  Activate
│ activate.bat            │  See: (venv) prefix
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ notepad .env            │  Add API key (first time)
│ Add GEMINI_API_KEY      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ python test_sample.py   │  Test system
│ ✅ Tests pass!          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ python main.py          │  Process MCQs
│ --sources "URL"         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Check Excel file        │  Verify results
│ 33/800 MCQs stored!     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Repeat with next URL    │  Until 800 MCQs
└─────────────────────────┘

================================================================================
YOU'RE READY! 🚀
================================================================================

Total time: 5 minutes
Total cost: $0 (FREE Gemini API)
Complexity: Minimal

Start now:
1. Win+R → cmd
2. cd C:\DesignYourAI
3. .venv\Scripts\activate.bat
4. Add GEMINI_API_KEY to .env
5. python test_sample.py

Happy ingesting!

================================================================================
