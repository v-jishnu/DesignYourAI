# Usage Guide - MCQ Ingestion Agent

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
# Edit .env and add your ANTHROPIC_API_KEY
notepad .env
```

### 2. Prepare Your Sources

Create a `sources.txt` file with your MCQ sources (one per line):

```
https://example.com/ai-mcqs
data/raw/ml_questions.pdf
data/raw/ds_interview.docx
```

### 3. Run Ingestion

```bash
# Process from batch file
python main.py --batch sources.txt

# Process single sources
python main.py --sources "https://example.com/mcqs" "data/raw/questions.pdf"

# Set custom target
python main.py --batch sources.txt --target 1000
```

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--sources` | One or more sources (URLs or files) | `--sources "url1" "file.pdf"` |
| `--batch` | File with sources (one per line) | `--batch sources.txt` |
| `--target` | Target number of MCQs (default: 800) | `--target 1000` |

## Output

MCQs are stored in `data/knowledge_base/mcq_knowledge_base.xlsx` with this schema:

| Column | Description |
|--------|-------------|
| Question_ID | Unique identifier (UUID) |
| Question_Text | Full question text |
| Option_A/B/C/D | Answer options |
| Correct_Answer | A/B/C/D or NULL |
| Explanation | Explanation if available |
| Category | Conceptual/Mathematical/Application |
| Topic | AI/ML/Data Science/System Design |
| Difficulty | Easy/Medium/Hard |
| Source | URL or file path |
| Date_Added | Timestamp |
| Used_Status | FALSE (for posting automation) |

## Example Workflow

```bash
# 1. Add your API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-your-key" > .env

# 2. Create sources file
cat > my_sources.txt << EOF
https://site1.com/ai-questions
data/raw/ml_book.pdf
data/raw/ds_notes.docx
EOF

# 3. Run ingestion
python main.py --batch my_sources.txt --target 800

# 4. Check results
# - View data/knowledge_base/mcq_knowledge_base.xlsx
# - Check logs in logs/app.log
```

## Tips

### Finding Good Sources

**Web Sources:**
- Interview preparation websites
- Educational platforms
- Technical blogs with MCQ sections
- **Note:** Only static HTML pages supported (no JavaScript rendering)

**PDF Sources:**
- Interview preparation PDFs
- Academic papers with practice questions
- Study guides

**DOCX Sources:**
- Personal notes
- Collected questions
- Course materials

### Improving Extraction Quality

1. **Structured sources work best:**
   - Clear question-option format
   - Consistent A) B) C) D) pattern
   - One MCQ per block

2. **For poor extractions:**
   - Check logs/app.log for errors
   - Manually verify source format
   - Consider preprocessing (clean PDFs, format DOCX)

### Avoiding Duplicates

The system automatically:
- Removes exact duplicates (hash-based)
- Removes similar questions (fuzzy matching at 85% threshold)
- Checks against existing knowledge base

## Troubleshooting

### "Configuration Error: LLM API key not found"
- Edit `.env` and add `ANTHROPIC_API_KEY=your-key`
- Get API key from https://console.anthropic.com/

### "No MCQs extracted"
- Check source format (must have clear question + 4 options)
- Verify file paths are correct
- Check logs/app.log for details

### "Classification failed"
- Check API key is valid
- Verify internet connection
- Check Anthropic API status

### "Import errors"
- Run: `pip install -r requirements.txt`
- Ensure Python 3.8+ is installed

## Cost Estimation

**Claude 3.5 Sonnet pricing:**
- ~$3 per 1000 MCQs classified
- Input: $3/million tokens
- Output: $15/million tokens

**For 800 MCQs:**
- Estimated cost: ~$2-3
- Batch size: 10 MCQs per API call
- Total API calls: ~80

## Next Steps

Once you have 800+ MCQs:

1. **Review quality:**
   - Open Excel file
   - Check classifications are accurate
   - Verify category distribution

2. **Prepare for posting automation:**
   - All MCQs have `Used_Status=FALSE`
   - Ready for LinkedIn/Twitter/Medium posting
   - Category rotation ensures variety

3. **Expand knowledge base:**
   - Add more sources over time
   - Run incrementally (duplicates auto-handled)
   - Track progress towards larger targets

## Advanced Usage

### Custom Configuration

Edit `config/settings.py` to customize:

```python
SIMILARITY_THRESHOLD = 0.90  # Stricter dedup
CLASSIFICATION_BATCH_SIZE = 20  # Larger batches
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Integration with Google Sheets

*Coming soon: Automatic sync to Google Sheets for cloud access*

### Posting Automation

*Coming soon: Automated posting to LinkedIn, Twitter, Medium*

---

**Need help?** Check logs/app.log or create an issue.
