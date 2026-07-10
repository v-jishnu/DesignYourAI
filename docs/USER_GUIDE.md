# User Guide

## What is this system?

This is an MCQ (Multiple Choice Question) knowledge base generator built for Data Science, Machine Learning, and AI interview preparation. You feed it sources -- URLs, PDFs, or local files -- and it produces quality-validated MCQs in a structured Excel spreadsheet. The questions are classified by category, topic, and difficulty, validated against a 6-point quality checklist, and independently verified using an LLM judge.

There are three separate pipelines:

- **Ingestion pipeline** (`run_ingest.py`) -- extract, classify, deduplicate, and store MCQs from any source
- **Questions-only PDF pipeline** (`run_questions_pdf.py`) -- read a PDF containing only bare questions (no options), generate full MCQs with options, correct answers, explanations, and classifications via LLM
- **Evaluation + fix pipeline** (`run_eval.py`) -- independently re-judge an existing Excel KB to catch wrong answers, bad explanations, and degenerate options; optionally auto-fix and produce a clean final sheet

---

## Prerequisites

- **Python 3.10+** installed on your machine
- **An API key** from a supported LLM provider (free options available), OR **Ollama** installed locally
- **Git** (optional, for cloning)

### Getting an API key (2 minutes)

The recommended provider is **Google Gemini** -- it is completely free and requires no credit card.

1. Go to https://makersuite.google.com/app/apikey
2. Click "Get API Key"
3. Copy the key (starts with `AIza...`)

That is it. You are ready to install.

---

## Installation

```bash
# Clone the repo (or unzip if you received it as a zip)
git clone <repo-url>
cd DesignYourAI

# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt:
.venv\Scripts\activate.bat

# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (needed for JS-heavy websites)
playwright install chromium
```

### Configure your API key

Create a file called `.env` in the project root (or copy from `.env.template`):

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key-here
```

### Verify setup

```bash
python test_sample.py
```

If this prints "All tests passed" you are good to go.

---

## How the ingestion pipeline works

When you give the engine a source, it goes through a 6-step pipeline:

```
Source (URL / PDF / file)
    |
    v
[1] FETCH -- download the content (static HTML, browser render, or file read)
    |
    v
[2] DETECT SHAPE -- what kind of content is this?
    |
    +-- Already MCQ with answers? (has A/B/C/D options + answer key)
    |       --> extract and preserve the existing correct answers
    +-- MCQ questions without answers? (has options but no answer key)
    |       --> LLM reasons the correct answer using domain knowledge
    +-- Q&A pairs? (question + prose answer text)
    |       --> convert to MCQ: use answer as correct option, generate distractors
    +-- Prose? (article, tutorial, docs)
    |       --> generate new MCQs from the content
    |
    v
[3] CLASSIFY -- assign Category, Topic, and Difficulty
    |   Category:   Conceptual (50%) / Mathematical (25%) / Application (25%)
    |   Topic:      AI / ML / Data Science / System Design
    |   Difficulty: Easy / Medium / Hard
    |
    v
[4] DEDUPLICATE -- remove questions that are identical or very similar
    |   Uses hash matching (exact) + fuzzy matching (85% similarity threshold)
    |
    v
[5] QUALITY VALIDATE -- 6-point checklist
    |   1. Tests reasoning, not just recall
    |   2. Plausible distractors (wrong options look reasonable)
    |   3. Differentiates intermediate from beginner (difficulty + length)
    |   4. Logically sound and unambiguous
    |   5. Industry-level rigor (correct category/topic, clean grammar)
    |   6. Explanation is consistent with the declared correct answer
    |
    v
[6] STORE -- write to Excel with row-by-row fallback
        If one row fails (e.g. illegal characters), only that row
        is skipped. The rest of the batch is saved.
```

You do not need to manage any of these steps. They run automatically.

### How the engine handles PDFs with questions but no answer key

This is the most important routing decision in the pipeline. When the engine sees questions with options but no inline answer key (e.g., a university quiz PDF), it switches the LLM from "generation mode" to "reasoning mode":

- **Generation mode** (wrong): asks the LLM to write new MCQs from the content -- it ignores the existing questions and invents its own answers
- **Reasoning mode** (correct): tells the LLM to copy each question exactly, then use its domain knowledge to determine which option is genuinely correct

This distinction is why the engine can correctly answer "which layer in an ANN processes the input?" even when the PDF has no answer key -- the LLM knows the answer from training, and is explicitly asked to reason rather than author.

---

## Source reliability guide

Not all sources work equally well. Here is an honest breakdown based on real testing:

| Source type | Reliability | Typical yield | How it works | Examples |
|---|---|---|---|---|
| **GitHub repos** (Q&A markdown) | ~95% | High (50-300 per repo) | Parses Q&A headings directly, converts to MCQ | kojino/120-DS, youssefHosni/DS-Q&A, andrewekhalel/MLQuestions |
| **PDFs / DOCX** (local files) | ~95% | Depends on file | Extracts text, parses or generates | Any downloaded or exported file |
| **Technical blogs / Q&A sites** | ~75% | Medium (5-30 per page) | Renders with browser, generates MCQs from prose | GeeksforGeeks, Guru99, Wikipedia, company engineering blogs |
| **Structured quiz sites** | ~30% | Low (0-5 per page) | Tries to parse DOM for quiz markup | Simplilearn, InterviewBit free tier |
| **Bot-protected sites** (Cloudflare) | 0% | None | Blocked before content loads | Sanfoundry, some enterprise sites |
| **Login-gated sites** | 0% | None | Cannot authenticate | madinterview, LeetCode premium, Educative |

### What to do when a source does not work

1. Run `--dry-run` first to see if the engine can fetch content
2. If 0 words fetched or "blocked" message: the site is protected
3. **Workaround:** Open the page in your browser, press Ctrl+P, save as PDF, then use `--pdf`

This workaround works for any content you can see in your browser, including login-gated and bot-protected sites.

---

## Using `run_ingest.py` (primary ingestion CLI)

This is the main entry point. One command, one source, automatic routing.

### Ingest from a URL

```bash
# GitHub repo (highest reliability)
python run_ingest.py --url https://github.com/kojino/120-Data-Science-Interview-Questions

# Technical blog
python run_ingest.py --url https://www.geeksforgeeks.org/machine-learning/machine-learning-interview-questions/

# Wikipedia article
python run_ingest.py --url https://en.wikipedia.org/wiki/Gradient_descent
```

### Ingest from a PDF

```bash
python run_ingest.py --pdf data/raw/interview-prep.pdf
python run_ingest.py --pdf ~/Downloads/ml-questions.pdf
```

PDFs are handled with three extraction paths tried in order:
1. **Tabular format** -- if the PDF stores MCQs in a tab-separated table (Question | A | B | C | D | Correct), answers are read directly with no LLM call
2. **Regex parse** -- if the PDF has clear A) B) C) D) structure, a regex parser extracts questions before the LLM is involved
3. **LLM extraction** -- if neither of the above succeeds, the full text is sent to the LLM with the appropriate prompt (preserve answers / reason answers / generate, based on what was detected)

### Ingest from a local file
 
```bash
python run_ingest.py --file notes.md
python run_ingest.py --file interview-questions.txt
python run_ingest.py --file report.docx
```

Local files are handled depending on their formats:
1. **Plain Text / Markdown (`.md`, `.markdown`, `.txt`):** Routed to `MarkdownTxtExtractor`. If they contain structured questions with options (e.g. A) B) C) D)), the regex parser extracts them directly. If they contain prose/notes, the engine automatically runs LLM-based smart generation to extract clean MCQs.
2. **Word Documents (`.docx`):** Routed to `DOCXExtractor` which extracts text from paragraphs and tables, followed by regex or LLM cascade.
3. **XML/JSON Drafts (`.xml`, `.json`):** Routed to `StructuredFileExtractor` for static ingestion of human-vetted files.


### Batch mode (multiple sources at once)

Create a text file with one source per line:

```
# sources.txt
https://github.com/kojino/120-Data-Science-Interview-Questions
https://github.com/andrewekhalel/MLQuestions
data/raw/my-notes.pdf
```

Then run:

```bash
python run_ingest.py --batch sources.txt
```

Lines starting with `#` are treated as comments and skipped.

### Dry run (preview without processing)

Use `--dry-run` to see what the engine would do without calling the LLM or writing to Excel:

```bash
python run_ingest.py --url https://some-site.com/questions --dry-run
```

Output looks like:

```
[1/1] https://some-site.com/questions
  [ok] fetched 3200 words
  -> shape: QA  (45 question markers)
```

This tells you:
- Whether the fetch succeeded
- How much content was found
- What shape was detected (MCQ / QA / PROSE)

**Always dry-run first** when trying a new source. It costs nothing and saves LLM tokens.

### Limit output

Cap the number of MCQs processed per source:

```bash
python run_ingest.py --url https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers --limit 20
```

Useful when:
- Testing a new source for the first time
- Conserving GPU / API usage
- Running a quick check before committing to a full batch

### Custom output path

```bash
python run_ingest.py --url https://... --output data/knowledge_base/custom_kb.xlsx
```

Default output: `data/knowledge_base/mcq_knowledge_base.xlsx`

### Intermediate XML & JSON Support (Decoupled Flow & Human-in-the-Loop Vetting)

If you have a complex PDF layout, dynamic website structure, or want to review/edit questions before they enter the final Excel database, you can use the decoupled structured XML/JSON pipeline.

#### Step 1: Dump raw/classified draft to an intermediate file
To extract and classify questions from a source without writing them to Excel or running deduplication, use the `--dump-draft` parameter with either a `.json` or `.xml` extension:
```bash
python run_ingest.py --pdf data/raw/messy_questions.pdf --dump-draft data/processed/draft.json
# or
python run_ingest.py --pdf data/raw/messy_questions.pdf --dump-draft data/processed/draft.xml
```

#### Step 2: Human-in-the-Loop Review (Optional)
Open the generated draft file in any editor. You can correct typos, update options, adjust the correct answer key, add company/metadata fields, or delete bad questions.

#### Step 3: Ingest the draft file into the main database
Pass the verified JSON or XML file directly to `--file` (which routes automatically to the static `StructuredFileExtractor`):
```bash
python run_ingest.py --file data/processed/draft.json
# or
python run_ingest.py --file data/processed/draft.xml
```

#### Structured File Schemas

##### JSON Schema
```json
[
  {
    "question_text": "Which optimization algorithm is commonly used to train neural networks by updating weights iteratively?",
    "option_a": "Stochastic Gradient Descent",
    "option_b": "K-Means Clustering",
    "option_c": "Principal Component Analysis",
    "option_d": "Decision Trees",
    "correct_answer": "A",
    "explanation": "Stochastic Gradient Descent is a popular optimization algorithm for neural networks.",
    "category": "Conceptual",
    "topic": "ML",
    "difficulty": "Easy",
    "company": "Google",
    "job_roles": "Machine Learning Engineer"
  }
]
```

##### XML Schema
```xml
<mcqs>
  <mcq>
    <question_text>Which optimization algorithm is commonly used to train neural networks by updating weights iteratively?</question_text>
    <option_a>Stochastic Gradient Descent</option_a>
    <option_b>K-Means Clustering</option_b>
    <option_c>Principal Component Analysis</option_c>
    <option_d>Decision Trees</option_d>
    <correct_answer>A</correct_answer>
    <explanation>Stochastic Gradient Descent is a popular optimization algorithm for neural networks.</explanation>
    <category>Conceptual</category>
    <topic>ML</topic>
    <difficulty>Easy</difficulty>
    <company>Google</company>
    <job_roles>Machine Learning Engineer</job_roles>
  </mcq>
</mcqs>
```

---

## Using `run_questions_pdf.py` (questions-only PDF)

Use this when you have a PDF that contains only bare questions -- no options, no answer key. The pipeline parses the questions out of the PDF, then calls the LLM once per question to generate four plausible options, pick the correct one, write an explanation, and assign a category, topic, and difficulty.

Questions that already have options in the PDF (A/B/C/D format) are automatically detected and skipped -- only bare questions are processed.

### Basic usage

```bash
python run_questions_pdf.py --pdf "path/to/your-questions.pdf"
```

Output: `your-questions_generated_kb.xlsx` saved alongside the PDF. Same column format as any other KB -- you can pass it directly to `run_eval.py --fix` for quality checking.

### Full options

```bash
# Specify a custom output path
python run_questions_pdf.py --pdf questions.pdf --output data/knowledge_base/my_kb.xlsx

# See each question as it is generated
python run_questions_pdf.py --pdf questions.pdf --verbose

# Increase concurrency for API providers (default is 2 for Ollama)
python run_questions_pdf.py --pdf questions.pdf --concurrency 6
```

### What the parser handles

| Content in PDF | Behaviour |
|---|---|
| Bare question ending with `?` | Extracted and sent to LLM for full MCQ generation |
| Multi-line question spanning a line break | Lines are joined into one question before processing |
| Question followed immediately by A) B) C) D) options | Detected as already-formed MCQ -- skipped |
| GFG / quiz-site blobs ("Question 1...AFitting...BFitting...") | Detected as inline MCQ format -- skipped |
| Navigation noise ("Tags:", "Last Updated", "View All Discussion") | Stripped before parsing |

### Recommended follow-up

After generating from a questions-only PDF, run the evaluation pipeline with `--fix` to catch any wrong answers the LLM may have generated:

```bash
python run_eval.py --excel "your-questions_generated_kb.xlsx" --fix --verbose
```

This produces a `_final.xlsx` with all errors corrected and unanswerable questions dropped.

---

## Using `run_eval.py` (post-generation evaluation)

After generating a knowledge base, run the evaluation pipeline to independently verify the quality of every MCQ. This is a separate feature -- it does not touch the generation code.

The evaluator uses an LLM judge (the same Ollama or API provider configured in `.env`) to re-examine each MCQ across four checks:

| Check | Question answered | How |
|---|---|---|
| **Answerability** | Are the 4 options well-formed and sufficient to answer the question? | LLM checks for degenerate options, near-duplicates, and whether exactly one is defensibly correct |
| **Blind answer pick** | Which option does the LLM independently believe is correct? | The stored `Correct_Answer` is hidden from the judge during this step -- it must reason from domain knowledge alone |
| **Answer match** | Does the stored `Correct_Answer` agree with the LLM's blind pick? | Direct comparison -- a mismatch here is the primary wrong-answer signal |
| **Explanation consistency** | Does the `Explanation` actually justify the marked correct option? | LLM checks whether the explanation's reasoning points at the stored answer, not a different option |

A row is marked **PASS** only if the options are answerable, the stored answer matches the blind pick, and the explanation is consistent. Each row also gets an `Eval_Verdict`, `Eval_LLM_Answer`, `Eval_Confidence`, and `Eval_Rationale` column in the output.

### Why the blind pick matters

If the judge were shown the stored answer, it would tend to agree with it (sycophancy). Hiding it forces genuine re-derivation. This is the same principle used in the ingestion pipeline's answer-verification prompt: the LLM is put in examiner mode, not author mode.

### Modes: evaluate only vs. evaluate + fix

The evaluator has two operating modes selected by whether you pass `--fix`:

**Evaluate only (default)** -- run checks and report findings. Produces `_eval.xlsx` with `Eval_*` columns so you can review failures manually.

**Evaluate + fix (`--fix`)** -- after evaluation, automatically patch every flagged row:

| Verdict | What the fixer does |
|---|---|
| **PASS** | Row kept unchanged |
| **WRONG_ANSWER** | `Correct_Answer` updated to the LLM's blind pick; `Explanation` rewritten to justify it |
| **BAD_EXPLANATION** | `Correct_Answer` kept; `Explanation` rewritten to actually justify the correct option |
| **NOT_ANSWERABLE** | Row dropped (options are unfixable -- the question itself is bad) |
| **INVALID_INPUT / ERROR** | Row kept unchanged |

The fix output is `<kb>_final.xlsx` -- no `Eval_*` columns, clean and ready to use.

### Basic usage

```bash
# Evaluate the default KB (data/knowledge_base/mcq_knowledge_base.xlsx)
python run_eval.py

# Evaluate a specific file
python run_eval.py --excel data/knowledge_base/mcq_knowledge_base.xlsx

# Evaluate AND auto-fix -- produces a clean _final.xlsx
python run_eval.py --excel my_kb.xlsx --fix

# Evaluate + fix with per-row progress
python run_eval.py --excel my_kb.xlsx --fix --verbose

# Quick spot-check: sample 10% of rows
python run_eval.py --sample 0.1

# Judge only the first 50 rows (useful for testing)
python run_eval.py --limit 50

# Verbose: print each verdict as it is judged
python run_eval.py --verbose

# Save outputs to a specific directory
python run_eval.py --output-dir reports/
```

### Concurrency

```bash
# Local Ollama (default: 2 concurrent calls to avoid OOM)
python run_eval.py

# Cloud API providers can handle more concurrent calls
python run_eval.py --concurrency 8
```

### Resumable runs

The evaluator writes each verdict to a `.jsonl` cache file as it completes. If a run is interrupted (Ctrl+C, power loss, rate limit), simply re-run the same command -- already-judged rows are skipped automatically.

```bash
# Interrupt then resume -- picks up where it left off
python run_eval.py --verbose

# Force a clean re-run ignoring the cache
python run_eval.py --no-cache
```

### Outputs

The evaluator produces outputs in the same directory as the Excel file (or `--output-dir` if specified):

| File | When | Description |
|---|---|---|
| `<kb>_eval.xlsx` | Always | Original KB columns + 7 `Eval_*` columns. Sort by `Eval_Verdict` to jump to failures. |
| `<kb>_eval.json` | Always | Machine-readable aggregate: pass rate, wrong-answer rate, verdict tallies, per-row results |
| `<kb>_eval_cache.jsonl` | Always | Resume cache -- one JSON line per judged row, keyed by Question_ID |
| `<kb>_final.xlsx` | `--fix` only | Clean KB with corrected answers and rewritten explanations. No `Eval_*` columns. Ready to use. |

### Reading the Eval_* columns

| Column | Values | Meaning |
|---|---|---|
| `Eval_Answerable` | PASS / FAIL | Are the 4 options well-formed and sufficient? |
| `Eval_LLM_Answer` | A / B / C / D | What the judge independently picked (blind) |
| `Eval_Answer_Match` | PASS / FAIL / N/A | Does stored answer == blind pick? N/A if no stored answer |
| `Eval_Explanation_Consistent` | PASS / FAIL / N/A | Does explanation justify the stored answer? N/A if no explanation |
| `Eval_Verdict` | PASS / WRONG_ANSWER / BAD_EXPLANATION / NOT_ANSWERABLE / INVALID_INPUT / ERROR | Overall verdict |
| `Eval_Confidence` | 0.0 -- 1.0 | Judge's self-reported confidence in its blind pick |
| `Eval_Rationale` | Text | One-sentence summary of the most important finding |

### Verdict meanings

| Verdict | Meaning | Action |
|---|---|---|
| **PASS** | All checks passed | No action needed |
| **WRONG_ANSWER** | Stored answer disagrees with LLM's blind pick | Review manually; the stored answer is likely wrong |
| **BAD_EXPLANATION** | Answer agrees, but explanation describes a different option | Fix the explanation to match the correct answer |
| **NOT_ANSWERABLE** | Options are degenerate, ambiguous, or no option is defensibly correct | Regenerate or delete the question |
| **INVALID_INPUT** | Row is missing required fields (options, question text) | Fix the KB row directly in Excel |
| **ERROR** | The judge call failed (LLM / parse error) | Re-run; these are skip candidates, not answer failures |

### Understanding the pass rate metric

The console summary reports two rates:

- **Pass rate** -- PASS count divided by "answerable rows" (total judged, minus INVALID_INPUT and ERROR). This is the headline quality metric.
- **Wrong-answer rate** -- WRONG_ANSWER count divided by answerable rows. This is the specific metric for answer correctness.

INVALID_INPUT rows are deliberately excluded from both rates so they reflect answer quality, not data completeness.

### Using the evaluator with cloud APIs

The evaluator uses the same `LLM_PROVIDER` and API key as the ingestion pipeline. Switching providers requires no code change:

```
# .env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...

# Then run
python run_eval.py --concurrency 6
```

Groq is recommended for API-based evaluation runs -- it is fast, free-tier, and handles concurrent calls well.

---

## Using `main.py` (original CLI)

The original entry point. Works the same as `run_ingest.py` but accepts multiple sources and a target count:

```bash
# Single source
python main.py --sources "https://example.com/questions"

# Multiple sources
python main.py --sources "https://site1.com" "data/raw/file.pdf"

# Batch file
python main.py --batch sources.txt --target 1000
```

**When to use `main.py` vs `run_ingest.py`:**
- `run_ingest.py` has `--dry-run`, `--limit`, and `--output`. Use it for daily ingestion work.
- `main.py` has `--target` (sets a KB size goal). Use it when building towards a specific count.

Both use the same pipeline underneath. No difference in output quality.

---

## Using `run_stratascratch.py` (StrataScratch API)

A dedicated runner for StrataScratch's GraphQL API. This is separate because it uses an authenticated API, not web scraping.

**Setup:**

1. Get a StrataScratch auth token (from browser DevTools while logged in)
2. Add to `.env`:
   ```
   STRATASCRATCH_TOKEN=your-token-here
   ```

**Run:**

```bash
python run_stratascratch.py
```

This fetches Q&A pairs with metadata (company name, job roles, difficulty) and converts them to MCQs. Results include the `Company` and `Job_Roles` columns that other sources leave blank.

---

## Understanding the output

All ingestion output goes to an Excel file (default: `data/knowledge_base/mcq_knowledge_base.xlsx`).

### Column reference

| Column | Description | Example |
|---|---|---|
| Question_ID | Unique UUID | `a3b2c1d4-...` |
| Question_Text | The question | "Which regularization technique adds an L1 penalty...?" |
| Option_A | First option | "Ridge regression" |
| Option_B | Second option | "Lasso regression" |
| Option_C | Third option | "Elastic net" |
| Option_D | Fourth option | "Polynomial regression" |
| Correct_Answer | A, B, C, or D | "B" |
| Explanation | Why this answer is correct | "Lasso uses L1 penalty which..." |
| Category | Conceptual / Mathematical / Application | "Conceptual" |
| Topic | AI / ML / Data Science / System Design | "ML" |
| Difficulty | Easy / Medium / Hard | "Medium" |
| Source | Where this MCQ came from | "https://github.com/kojino/..." |
| Date_Added | When it was ingested | "2026-04-17 10:30:00" |
| Used_Status | Has it been posted to LinkedIn? | FALSE |
| Company | Company associated with question | "Google" (StrataScratch only) |
| Job_Roles | Relevant job roles | "Data Scientist" (StrataScratch only) |
| Image_Path | Local path to image if any | Usually blank |
| Image_URL | Source URL of image if any | Usually blank |
| Has_Image | Whether question has an image | FALSE |
| Image_Format | Image file format | Usually blank |

### What good output looks like

- All rows have Question_Text, all 4 options, Correct_Answer, and Explanation filled
- Correct_Answer is always one of A, B, C, D
- Category distribution is roughly 50% Conceptual / 25% Mathematical / 25% Application
- No duplicate questions (check Source column for variety)
- Difficulty is spread across Easy, Medium, Hard
- The Explanation mentions specific terms from the correct option (not a generic statement)

### How to spot bad rows

- Explanation is empty or very short (under 10 words)
- Multiple options say the same thing or are near-identical
- Question is too vague ("What is ML?") or too specific ("What was the learning rate in paper X?")
- The explanation describes a different answer than the one marked correct
- `nan` appears as text in any cell (should not happen -- see Troubleshooting)

Run the evaluation pipeline on a completed KB to catch these automatically rather than checking by hand.

---

## LLM provider options

The engine supports multiple LLM providers. You can switch at any time by changing `.env`. Both the ingestion and evaluation pipelines use the same provider.

| Provider | Cost | Speed | Quality | Setup |
|---|---|---|---|---|
| **Gemini** (recommended for ingestion) | Free | Fast | Good | `LLM_PROVIDER=gemini` + `GEMINI_API_KEY=...` |
| **Ollama** (local, recommended for eval) | Free | Depends on hardware | Good with 7B+ models | `LLM_PROVIDER=ollama` (no API key needed) |
| **Groq** (recommended for API-based eval) | Free tier | Very fast | Good | `LLM_PROVIDER=groq` + `GROQ_API_KEY=...` |
| **Together.ai** | Free credits | Fast | Good | `LLM_PROVIDER=together` + `TOGETHER_API_KEY=...` |
| **Qwen** | Free tier | Medium | Good | `LLM_PROVIDER=qwen` + `QWEN_API_KEY=...` |
| **DeepSeek** | Free tier | Medium | Good | `LLM_PROVIDER=deepseek` + `DEEPSEEK_API_KEY=...` |
| **OpenAI** | Paid | Fast | Very good | `LLM_PROVIDER=openai` + `OPENAI_API_KEY=...` |
| **Anthropic** | Paid | Fast | Very good | `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY=...` |

### Switching providers

Edit `.env`:

```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...your-key-here
```

No code changes needed. Restart the script.

### Using Ollama (local, free, unlimited)

Ollama runs a model on your own machine. No API key required, no rate limits, no usage costs.

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull qwen2.5:7b`
3. Start Ollama (it runs as a background service on most systems)
4. Set in `.env`:
   ```
   LLM_PROVIDER=ollama
   ```

Ollama works on CPU (slow but functional) and GPU (fast). The default model configured in this project is `qwen2.5:7b`. Other good options: `llama3.2:latest` (also pulled in the default install).

**For the evaluation pipeline specifically**, Ollama at concurrency 2 is the recommended local setup. A full 586-row populated KB takes approximately 30-40 minutes at this setting. To speed it up significantly, switch to Groq (free API, much faster):

```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

Then run: `python run_eval.py --concurrency 6`

---

## Recommended workflow

### Building a knowledge base from scratch

1. **Start with GitHub repos** -- highest reliability, most questions, fastest.
   ```bash
   python run_ingest.py --url https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers
   python run_ingest.py --url https://github.com/kojino/120-Data-Science-Interview-Questions
   python run_ingest.py --url https://github.com/andrewekhalel/MLQuestions
   ```

2. **Add PDFs you already have** -- course notes, exported prep docs, downloaded guides.
   ```bash
   # PDF with existing MCQs (has options + answer key) -- standard ingestion
   python run_ingest.py --pdf ~/Downloads/ml-interview-guide.pdf

   # PDF with only bare questions (no options) -- use the questions-only pipeline
   python run_questions_pdf.py --pdf ~/Downloads/questions-only.pdf --verbose
   ```

3. **Supplement with public URLs** -- GeeksforGeeks, Wikipedia, technical blogs.
   ```bash
   python run_ingest.py --url https://www.geeksforgeeks.org/machine-learning/machine-learning-interview-questions/
   ```

4. **Fill gaps with StrataScratch** (if you have a token).
   ```bash
   python run_stratascratch.py
   ```

5. **Run the evaluator with auto-fix** to catch and correct any wrong answers before using the KB.
   ```bash
   python run_eval.py --sample 0.2 --verbose   # quick 20% spot-check first
   python run_eval.py --fix --verbose           # full run with auto-fix
   ```

   This produces `mcq_knowledge_base_final.xlsx` -- a clean, ready-to-use sheet with wrong answers corrected and unanswerable questions dropped. The `_eval.xlsx` is also written alongside it if you want to review what was changed.

### Adding new sources to an existing KB

Same as above for steps 1-4. The deduplication step will automatically drop questions that are already in the KB (exact or 85% similar). After adding new sources, run the evaluator only on the new rows:

```bash
# --no-cache forces re-evaluation of everything including new rows
# Remove the old cache file first if you want only new rows evaluated
python run_eval.py --no-cache --limit 100
```

### Avoiding duplicates

The engine has built-in deduplication (exact hash match + 85% fuzzy similarity). You do not need to worry about running the same source twice -- duplicates are automatically dropped.

Questions from different sources that cover the same concept but are worded differently will both be kept. This is intentional -- different phrasings of the same concept are valuable for practice.

---

## Glossary

| Term | Meaning |
|---|---|
| **MCQ** | Multiple Choice Question -- a question with 4 options (A/B/C/D) and one correct answer |
| **Q&A** | Question and Answer pair -- a question followed by a text answer, no options |
| **Prose** | Plain text content like articles, tutorials, or documentation |
| **Shape detection** | The process of determining whether content is MCQ (with or without answers), Q&A, or prose |
| **Answer verification mode** | When the engine detects questions without an answer key, the LLM is asked to reason the correct answer using domain knowledge rather than generate from scratch |
| **Blind pick** | The evaluator's independent answer selection, made without seeing the stored correct answer |
| **Tier 1** | Static HTML extraction using BeautifulSoup (fastest, works on simple pages) |
| **Tier 2** | Browser-based extraction using Playwright (handles JavaScript-rendered sites) |
| **Tier 3** | LLM-based MCQ generation from prose content (works on anything with enough text) |
| **MAANG-level** | Quality standard modeled after Meta/Apple/Amazon/Netflix/Google interview prep |
| **Conceptual** | Questions about theory, trade-offs, comparisons, "why" and "when" |
| **Mathematical** | Questions involving formulas, probability, statistics, quantitative reasoning |
| **Application** | Questions about real-world scenarios, production systems, metric trade-offs |
| **Deduplication** | Removing identical or near-identical questions |
| **Fuzzy matching** | Detecting questions that are similar but not identical (85% threshold) |
| **Row-by-row fallback** | When saving fails on one row (e.g. illegal characters), the engine retries each row individually so only the bad row is lost, not the whole batch |
| **Dry run** | A preview run that fetches and analyzes content without calling the LLM or writing to Excel |
| **Knowledge base (KB)** | The Excel file containing all generated MCQs |
| **Eval cache** | A `.jsonl` file written by the evaluator so interrupted runs can resume without re-judging already-completed rows |
| **Answerable rows** | Rows the evaluator could actually judge -- excludes rows with missing fields (INVALID_INPUT) and rows where the LLM call failed (ERROR) |
| **Wrong-answer rate** | The fraction of answerable rows where the stored correct answer disagrees with the evaluator's blind pick. The primary quality metric for answer correctness. |
| **Questions-only PDF** | A PDF containing only question text with no options or answer key. Processed by `run_questions_pdf.py` which generates full MCQs via LLM. |
| **Auto-fix** | The `--fix` mode of `run_eval.py`. After evaluation, patches WRONG_ANSWER rows with corrected answers and rewritten explanations, and drops NOT_ANSWERABLE rows. Output is `_final.xlsx`. |
| **Final sheet** | The `<kb>_final.xlsx` output from `run_eval.py --fix`. Contains only original KB columns (no `Eval_*` columns), with all errors corrected. Ready to use without further processing. |
| **Bare question** | A question text with no associated options -- just the question ending with `?`. The questions-only PDF extractor identifies these and generates full MCQs from them. |
