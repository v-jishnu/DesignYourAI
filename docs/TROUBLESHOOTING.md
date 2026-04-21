# Troubleshooting Guide

Common errors, what they mean, and how to fix them. Every error listed here was encountered during real development and testing.

---

## Table of Contents

1. [No API key found](#1-no-api-key-found)
2. [0 MCQs extracted from a URL](#2-0-mcqs-extracted-from-a-url)
3. ["You have been blocked" / Cloudflare](#3-you-have-been-blocked--cloudflare)
4. [429 Too Many Requests (rate limiting)](#4-429-too-many-requests-rate-limiting)
5. [402 Payment Required](#5-402-payment-required)
6. [UnicodeEncodeError on Windows](#6-unicodeencodeerror-on-windows)
7. [SSL Certificate Error](#7-ssl-certificate-error)
8. [Illegal XML character / Excel save error](#8-illegal-xml-character--excel-save-error)
9. [Column mismatch / NaN columns in Excel](#9-column-mismatch--nan-columns-in-excel)
10. [GPU running hot / slow performance](#10-gpu-running-hot--slow-performance)
11. [Playwright browser error](#11-playwright-browser-error)
12. [GitHub API 403 rate limit](#12-github-api-403-rate-limit)
13. ["0 pairs parsed, falling back to prose"](#13-0-pairs-parsed-falling-back-to-prose)
14. ["nan" strings appearing in Excel](#14-nan-strings-appearing-in-excel)

---

## 1. No API key found

**Error:**
```
Configuration Error: API key for provider 'gemini' not found.
Please set GEMINI_API_KEY in .env file
```

**What it means:**
The engine cannot find your LLM provider's API key. Either the `.env` file is missing, or the key name does not match the provider.

**Fix:**

1. Check that `.env` exists in the project root directory.
2. Check that the provider name and key name match:

```
# Correct -- provider and key must match
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...

# Wrong -- provider says "gemini" but only OPENAI key is set
LLM_PROVIDER=gemini
OPENAI_API_KEY=sk-...
```

3. If you copied from `.env.template`, make sure you replaced the placeholder with your actual key.
4. Make sure there are no spaces around the `=` sign.

---

## 2. 0 MCQs extracted from a URL

**Error:**
```
Extracted: 0
Classified: 0
Stored: 0
```

**What it means:**
The engine fetched the page but could not extract or generate any MCQs. Common causes:

- The site requires login (engine only handles public content)
- The site is heavily JS-rendered and Playwright could not find structured content
- The page has too little text (under 500 words after cleaning)
- The site blocks headless browsers (bot protection)

**Fix:**

1. Run `--dry-run` first to diagnose:
   ```bash
   python run_ingest.py --url https://the-url.com --dry-run
   ```
   Check the word count and shape detection result.

2. If the word count is very low (under 100): the site is probably blocking the scraper or requires login.

3. If shape is "prose" with 500+ words: the engine should have generated MCQs. Check the logs in `logs/` for error details.

4. **Workaround for blocked/gated sites:** Open the page in your browser, press Ctrl+P, save as PDF, then:
   ```bash
   python run_ingest.py --pdf downloaded-page.pdf
   ```

---

## 3. "You have been blocked" / Cloudflare

**Error (in logs or dry-run):**
```
Sorry, you have been blocked. You are unable to access [site].
This website is using a security service to protect itself from online attacks.
```

**What it means:**
The website uses Cloudflare or similar bot protection. Both the static fetcher and the headless browser are detected and blocked. This is a hard block with no in-engine workaround.

**Fix:**

There is no way to bypass this in the engine. Use the PDF export workaround:

1. Open the page in your normal browser (Chrome, Firefox, etc.)
2. Navigate to the page with the questions
3. Press Ctrl+P (or Cmd+P on Mac)
4. Choose "Save as PDF"
5. Run:
   ```bash
   python run_ingest.py --pdf saved-page.pdf
   ```

**Sites known to block:** Sanfoundry, some enterprise learning platforms.

---

## 4. 429 Too Many Requests (rate limiting)

**Error:**
```
Rate limited, waiting 60s (attempt 1/3)
```

**What it means:**
The LLM provider is throttling your requests. You have sent too many API calls in a short period. Free tiers have lower limits.

**Fix:**

- **Wait it out.** The engine automatically retries with exponential backoff (60s, then 120s).
- **Switch to a different free provider.** Edit `.env`:
  ```
  LLM_PROVIDER=groq
  GROQ_API_KEY=gsk_...
  ```
- **Use Ollama locally.** No rate limits, runs on your own GPU:
  ```
  LLM_PROVIDER=ollama
  ```
- **Use `--limit`** to process fewer items per run:
  ```bash
  python run_ingest.py --url https://... --limit 10
  ```

---

## 5. 402 Payment Required

**Error:**
```
Error: 402 Payment Required - Insufficient balance
```

**What it means:**
The selected provider (usually DeepSeek) has exhausted its free tier credits.

**Fix:**

Switch to a fully free provider. Edit `.env`:

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

Gemini has a generous free tier (1500 requests/day) that is sufficient for processing hundreds of MCQs.

---

## 6. UnicodeEncodeError on Windows

**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'
in position 2: character maps to <undefined>
```

**What it means:**
The Windows command prompt uses the cp1252 encoding by default, which cannot display certain Unicode characters (checkmarks, arrows, etc.).

**Fix (choose one):**

1. Set environment variable before running:
   ```bash
   set PYTHONIOENCODING=utf-8
   python run_ingest.py --url https://...
   ```

2. Switch the console to UTF-8 first:
   ```bash
   chcp 65001
   python run_ingest.py --url https://...
   ```

3. Use Windows Terminal (the modern one) instead of the old Command Prompt. Windows Terminal handles UTF-8 natively.

Note: This issue has been fixed in `run_ingest.py` (all Unicode symbols replaced with ASCII). If you see this error in `main.py` or other scripts, use one of the fixes above.

---

## 7. SSL Certificate Error

**Error:**
```
SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate
```

**What it means:**
Python cannot verify the SSL certificate of a website. Common on corporate networks with proxy servers, or when the `certifi` package is outdated.

**Fix:**

1. Update certifi:
   ```bash
   pip install --upgrade certifi
   ```

2. If on a corporate network with a custom CA certificate:
   ```bash
   set SSL_CERT_FILE=C:\path\to\corporate-ca-bundle.crt
   python run_ingest.py --url https://...
   ```

3. As a last resort (not recommended for production), you can disable SSL verification by setting:
   ```bash
   set PYTHONHTTPSVERIFY=0
   ```

---

## 8. Illegal XML character / Excel save error

**Error (in logs):**
```
openpyxl.utils.exceptions.IllegalCharacterError
```
or
```
Error saving batch, retrying row-by-row...
```

**What it means:**
One or more MCQs contain characters that are illegal in XML (which Excel uses internally). This commonly happens with LaTeX formulas that contain control characters (`\x00`-`\x08`, etc.).

**Fix:**

This is already handled automatically. The engine:

1. Sanitizes text by removing illegal XML characters before saving
2. If a batch save still fails, retries row-by-row
3. Only the problematic row is skipped; the rest of the batch is saved

**What you need to do:** Nothing. Check the logs to see which rows were skipped. The skipped MCQs contained characters that cannot be stored in Excel.

---

## 9. Column mismatch / NaN columns in Excel

**Error:**
```
Columns do not match. Old: 18, New: 20
```
or you see NaN values scattered across your Excel file.

**What it means:**
The knowledge base was created with an older schema (18 columns) and new MCQs are being added with the current schema (20 columns, which includes Company and Job_Roles). The mismatch causes columns to shift.

**Fix:**

This is already handled automatically. The engine aligns columns before concatenating old and new data.

If you still see NaN values from an old run:

1. Open the Excel file
2. Check for columns that are entirely NaN
3. Delete those columns (they are likely the old misaligned ones)
4. Save

Or, if you want a clean start:

1. Rename the old file: `mcq_knowledge_base.xlsx` -> `mcq_knowledge_base_backup.xlsx`
2. Run the engine again. It will create a fresh file with the correct schema.
3. Your old MCQs are preserved in the backup.

---

## 10. GPU running hot / slow performance

**What it means:**
If using Ollama with a local model, the GPU is under sustained load from generating MCQs. This is normal but can cause thermal throttling or system instability on laptops.

**Fix:**

- **Use `--limit`** to process fewer MCQs per run:
  ```bash
  python run_ingest.py --url https://... --limit 20
  ```

- **Take breaks.** After a large run (100+ MCQs), let the GPU cool for 5-10 minutes before starting the next one.

- **Switch to Gemini.** It is free and runs on Google's servers, so your GPU stays idle:
  ```
  LLM_PROVIDER=gemini
  GEMINI_API_KEY=AIza...
  ```

- **Monitor GPU temperature.** On Windows, use Task Manager (Performance tab > GPU) or `nvidia-smi` in the terminal. Stay below 85C for sustained periods.

---

## 11. Playwright browser error

**Error:**
```
playwright._impl._errors.Error: Browser closed unexpectedly
```
or
```
playwright._impl._errors.TimeoutError: Timeout 60000ms exceeded
```

**What it means:**
The headless browser crashed or took too long to load a page. Some sites are very heavy or have unusual JavaScript that causes timeouts.

**Fix:**

1. **Skip the URL.** Not every site works. Try a different source.

2. **Increase the timeout** in `config/settings.py`:
   ```python
   BROWSER_TIMEOUT = 120000  # 120 seconds instead of 60
   ```

3. **Check if Playwright is installed correctly:**
   ```bash
   playwright install chromium
   ```

4. **Use the PDF workaround** if you really need content from that specific page.

---

## 12. GitHub API 403 rate limit

**Error:**
```
GitHub API 403 for https://api.github.com/repos/.../contents/: rate limit exceeded
```

**What it means:**
The GitHub API allows 60 requests per hour for unauthenticated users. If you process many GitHub repos in a short period, you will hit this limit.

**Fix:**

- **Wait 60 minutes.** The rate limit resets every hour.

- **Use direct raw URLs** instead of repo root URLs. This bypasses the GitHub API entirely:
  ```bash
  # Instead of this (uses GitHub API to list files):
  python run_ingest.py --url https://github.com/kojino/120-Data-Science-Interview-Questions

  # Use this (fetches the raw file directly, no API):
  python run_ingest.py --url https://raw.githubusercontent.com/kojino/120-Data-Science-Interview-Questions/master/data-analysis.md
  ```

- **Space out your GitHub runs.** Process one repo, then move to a non-GitHub source, then come back.

---

## 13. "0 pairs parsed, falling back to prose"

**Log message:**
```
some-repo/.../README.md: generic parse weak (pairs=1, good=0%) -> prose generator
```

**What it means:**
The GitHub Markdown extractor tried to parse Q&A pairs from a markdown file but did not find enough structured questions. It is falling back to the prose generation path (extracting text and having the LLM generate MCQs from it).

**This is expected behavior, not an error.** It happens when:
- The file is a table of contents (links only, no Q&A content)
- The file uses an unusual formatting style the regex does not recognize
- The file is a README with project description, not questions

**Fix:**

No fix needed. The prose fallback still produces MCQs if the file has enough technical content (500+ words). If the file is truly a table of contents with no content, it will be skipped automatically.

---

## 14. "nan" strings appearing in Excel

**What it means:**
In older versions, reading the Excel file with `dtype=str` converted actual NaN (empty) values into the literal string `"nan"`. These strings would get re-saved as NaN on the next cycle, corrupting data over time.

**Fix:**

This has been permanently fixed in the codebase. The engine no longer reads with `dtype=str`.

If you have an old Excel file with `"nan"` strings:

1. Open in Excel
2. Use Find & Replace (Ctrl+H)
3. Find: `nan`
4. Replace with: (leave empty)
5. Click "Replace All"
6. Save

Or delete the file and regenerate from your sources.

---

## Still stuck?

If you encounter an error not listed here:

1. Check the log files in `logs/` for detailed error messages
2. Run with `--dry-run` to isolate whether the issue is with fetching, parsing, or generation
3. Try a different source to confirm the engine works (GitHub repos are the most reliable test)
4. Try a different LLM provider to rule out API issues
5. File an issue with the error message and the command you ran
