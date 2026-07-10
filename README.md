# MCQ Knowledge Ingestion & Categorization Agent

An intelligent automation system that extracts, classifies, and stores MCQ questions from multiple sources into a structured knowledge base.

## 🆓 NOW SUPPORTS FREE APIs!

**✅ Use Google Gemini (FREE)** - No credit card required!
**✅ Process 800 MCQs for $0**
**✅ Multiple provider support** - Switch anytime!

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** -- Complete beginner's guide to using the system
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** -- Common errors and fixes

## Features

- **Multi-source extraction**: Websites (HTML), PDFs, DOCX documents
- **🆓 FREE LLM classification**: Google Gemini (or Claude, OpenAI, Groq, Together.ai)
- **Intelligent deduplication**: Hash-based + fuzzy matching
- **Structured storage**: Excel-based knowledge base
- **Extensible architecture**: Multi-agent system design
- **One-at-a-time processing**: Simple sequential workflow

## Quick Start

### 1. Get FREE API Key (2 minutes)

**Recommended: Google Gemini (100% FREE)**

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Get API Key"
3. Copy your key (starts with `AIza...`)

### 2. Installation

```powershell
# IMPORTANT: Activate virtual environment first (isolates dependencies)
# PowerShell (use .\):
.\activate_venv.bat

# Command Prompt (no .\):
# activate_venv.bat

# Install dependencies (in isolated environment)
pip install --index-url https://pypi.org/simple -r requirements.txt

# Configure environment
notepad .env

# Add your FREE Gemini key:
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key-here
```

**📦 Virtual Environment:** This project uses `.venv` to isolate dependencies. See [VENV_SETUP.md](VENV_SETUP.md) for details.

**📖 Detailed setup:** See [FREE_API_SETUP.md](FREE_API_SETUP.md)

### 3. Test Setup

```powershell
# Make sure virtual environment is activated!
.\activate_venv.bat

# Then test
python test_sample.py
```

**Note:** PowerShell requires `.\` prefix. See [POWERSHELL_FIX.md](POWERSHELL_FIX.md) for details.

Expected: ✅ All tests passed with FREE Gemini API!

### 4. Usage (One Link at a Time)

```powershell
# Always activate first! (PowerShell requires .\ prefix)
.\activate_venv.bat

# Process ONE source at a time
python main.py --sources "https://example.com/mcqs"

# Then process next source
python main.py --sources "https://another-site.com/more-mcqs"

# Continue until you reach 800 MCQs!
```

**Simple workflow:** Each command processes one source completely (extract → classify → deduplicate → store)

### 5. Check Results

MCQs are stored in `data/knowledge_base/mcq_knowledge_base.xlsx` with the following schema:

- Question_ID, Question_Text
- Option_A, Option_B, Option_C, Option_D
- Correct_Answer (A/B/C/D or NULL)
- Explanation
- Category (Conceptual/Mathematical/Application)
- Topic (AI/ML/Data Science/System Design)
- Difficulty (Easy/Medium/Hard)
- Source, Date_Added, Used_Status

## Architecture

Multi-agent system with specialized agents:

```
IngestionAgent (Orchestrator)
├── ExtractionAgent → Web/PDF/DOCX extractors
├── ClassificationAgent → LLM classifier
├── DeduplicationAgent → Hash + fuzzy matching
└── StorageAgent → Excel handler
```

## Supported FREE APIs

| Provider | Free Tier | Get API Key |
|----------|-----------|-------------|
| **Gemini** (Recommended) | ✅ 1500/day | https://makersuite.google.com/app/apikey |
| **Groq** | ✅ Limited | https://console.groq.com/ |
| **Together.ai** | ✅ Credits | https://api.together.xyz/ |
| Claude | ❌ Paid | https://console.anthropic.com/ |
| OpenAI | ❌ Paid | https://platform.openai.com/ |

**💰 Cost: $0 with FREE providers!**

## Configuration

Edit `.env` to customize:

- Choose LLM provider (gemini, groq, together, anthropic, openai)
- Set API key for chosen provider
- Adjust similarity threshold (0.85 default)
- Set logging level

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## Drop-in Ingestion (`run_ingest.py`)

Ship-ready front door for feeding the engine a URL, PDF, or local file and
getting quality MCQs in the existing Excel schema. No source-specific wiring
required — the CLI routes to the right extractor automatically.

### Usage

```bash
# Public URL — any site. GitHub repos use the Q&A-aware extractor.
python run_ingest.py --url https://github.com/kojino/120-Data-Science-Interview-Questions

# Cap the number of MCQs processed per source
python run_ingest.py --url https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers --limit 50

# Local PDF (use this for login-gated content — export to PDF first)
python run_ingest.py --pdf data/raw/interview-prep.pdf

# Local .md / .txt / .docx
python run_ingest.py --file notes.md

# Decouple extraction: extract and save questions to a draft JSON/XML file (Human-in-the-Loop)
python run_ingest.py --pdf data/raw/interview-prep.pdf --dump-draft data/processed/draft.json

# Ingest intermediate XML/JSON files into the main database
python run_ingest.py --file data/processed/draft.json

# Batch file (one source per line, # comments allowed)
python run_ingest.py --batch sources.txt

# Preview only — fetch + detect shape, no LLM calls, no writes
python run_ingest.py --url https://some-blog.com/ml-qs --dry-run

# Override the output Excel path
python run_ingest.py --url https://... --output data/knowledge_base/custom.xlsx
```

### What it supports

| Input | Handler | Notes |
|---|---|---|
| GitHub repo / raw `.md` URL | `GitHubMarkdownExtractor` | Generic Q&A regex parse → QAConverter; weak parses fall back to prose generation |
| Generic public URL | `WebExtractor` | 3-tier cascade: static HTML → Playwright → LLM generation |
| `.pdf` file or URL | `PDFExtractor` | pdfplumber + LLM fallback |
| `.docx` file | `DOCXExtractor` | python-docx + LLM fallback |
| `.md` or `.txt` file | `MarkdownTxtExtractor` | Plain text parse + LLM fallback (excellent for clean, layout-free text extraction) |
| `.xml` or `.json` file | `StructuredFileExtractor` | Decoupled structured MCQ representation (useful for layout-heavy PDFs or review processes) |
| StrataScratch | `StrataScratchExtractor` | GraphQL API (still use `run_stratascratch.py` for full runs) |

### What it does NOT support

- **Login-gated content.** No OAuth, no cookie injection, no credential
  passthrough. If a site requires login, open the page in your browser,
  export to PDF, and pass that PDF via `--pdf`.
- **Arbitrary JS-heavy SPAs with weird DOMs.** Playwright handles most of
  these, but extraction quality varies. `--dry-run` is your friend.

### Output

All runs write into `data/knowledge_base/mcq_knowledge_base.xlsx` (unless
`--output` is passed) using the same 20-column schema the rest of the
pipeline uses: Question_ID, Question_Text, Option_A–D, Correct_Answer,
Explanation, Category, Topic, Difficulty, Source, Date_Added, Used_Status,
Company, Job_Roles, plus image fields.

Row-by-row fallback is preserved: a single malformed row (e.g. LaTeX with
illegal XML characters) no longer loses an entire batch.

## Future Extensions

- Google Sheets sync for cloud access
- Posting automation integration (LinkedIn, Twitter, Medium)
- Human-in-the-loop validation interface
- Advanced semantic deduplication with embeddings

## License

MIT
