# Image Support Implementation - Day 1 Complete ✅

## Status: Foundation Complete

**Date:** 2026-02-06

### Completed Tasks (Day 1)

#### 1. MCQ Schema Extended ✅
- **File:** `config/schemas.py`
- **Changes:**
  - Added 5 new image-related fields to MCQ dataclass:
    - `image_path: Optional[str]` - Local path to saved image
    - `image_url: Optional[str]` - Original source URL
    - `image_filename: Optional[str]` - Filename extracted from path
    - `has_image: bool` - Quick flag for filtering
    - `image_format: Optional[str]` - Format (jpg, png, etc.)
  - Updated `to_dict()` method to include all 4 image columns for Excel
  - Updated `from_dict()` method to parse image fields from Excel

#### 2. Settings Configuration Extended ✅
- **File:** `config/settings.py`
- **Changes:**
  - Added `IMAGES_DIR` path: `data/images/`
  - Added `IMAGE_MANIFEST_PATH`: `data/images/manifest.json`
  - Added image optimization settings:
    - `OPTIMIZE_FOR_WEB = True`
    - `IMAGE_MAX_WIDTH = 1200` (LinkedIn recommended)
    - `IMAGE_MAX_HEIGHT = 1200`
    - `IMAGE_QUALITY = 85` (JPEG quality)
  - Added `SUPPORTED_IMAGE_FORMATS` list
  - Updated `validate()` to create images directory

#### 3. MediaHandler Module Created ✅
- **File:** `storage/media_handler.py` (NEW - 345 lines)
- **Features Implemented:**
  - **Image Extraction:**
    - `extract_from_html()` - Download images from `<img>` tags
    - Handles data URLs (base64 embedded images)
    - Resolves relative URLs using base URL
    - Async image downloading with aiohttp

  - **Image Optimization:**
    - `optimize_for_web()` - Resize and compress for LinkedIn
    - Converts RGBA/LA to RGB (white background)
    - Thumbnail generation using Pillow LANCZOS resampling
    - JPEG compression with configurable quality
    - Logs optimization ratio

  - **Image Storage:**
    - `save_image()` - Organized storage: `data/images/{source_slug}/{question_id}.{format}`
    - Automatic source slug generation from URLs/file paths
    - Format detection from image data (PNG/JPG/GIF/SVG/WEBP)
    - Manifest tracking (metadata JSON)

  - **Image Deduplication:**
    - `calculate_image_hash()` - Perceptual hashing using imagehash
    - `are_images_similar()` - Compare hashes with configurable threshold
    - Hamming distance calculation

  - **Utilities:**
    - `get_image_path()` - Retrieve image path by question ID
    - `verify_image_exists()` - Check file existence
    - `_slugify()` - URL-safe slug generation
    - `_get_source_slug()` - Extract domain/filename from source
    - `_load_manifest()` / `_save_manifest()` - JSON persistence

#### 4. Excel Schema Updated ✅
- **File:** `storage/excel_handler.py`
- **Changes:**
  - Added 4 new columns to Excel headers:
    - `Image_Path`
    - `Image_URL`
    - `Has_Image`
    - `Image_Format`
  - Existing append/load logic automatically handles new columns

#### 5. Dependencies Added ✅
- **File:** `requirements.txt`
- **New Packages:**
  - `Pillow==10.1.0` - Image processing and optimization
  - `imagehash==4.3.1` - Perceptual hashing for visual deduplication

#### 6. Test Suite Created ✅
- **File:** `tests/test_image_support.py` (NEW)
- **Tests:**
  - `test_mcq_schema_with_images()` - Verify MCQ schema changes
  - `test_settings_has_image_config()` - Verify Settings configuration
  - `test_images_directory_created()` - Verify directory creation

---

## Next Steps (Day 2-3)

### Day 2: Web Extractor Enhancement
- **File to modify:** `extractors/web_extractor.py`
- **Tasks:**
  1. Inject MediaHandler into base_extractor
  2. Update `_parse_question_block()` to detect images within question blocks
  3. Download and optimize images
  4. Link images to MCQ objects
  5. **CRITICAL:** Return `None` (skip MCQ) if image extraction fails
  6. Test with real HTML containing images

### Day 3: PDF & DOCX Extractors
- **Files to modify:**
  - `extractors/pdf_extractor.py`
  - `extractors/docx_extractor.py`
  - `extractors/base_extractor.py`
- **Tasks:**
  1. PDF: Extract embedded images using pdfplumber
  2. PDF: Map images to questions by position analysis
  3. DOCX: Parse inline images from document structure
  4. DOCX: Build paragraph-to-image mapping
  5. Test with sample PDF/DOCX files

### Day 4: Storage Integration
- **Files to modify:**
  - `agents/extraction_agent.py`
  - `storage/data_validator.py`
- **Tasks:**
  1. Initialize MediaHandler in extraction agent
  2. Pass MediaHandler to all extractors
  3. Update data validator to check image paths
  4. Test end-to-end: source → extraction → storage

### Day 5: Deduplication & Testing
- **File to modify:** `agents/deduplication_agent.py`
- **Tasks:**
  1. Integrate perceptual image hashing
  2. Compare visual similarity if both MCQs have images
  3. Keep first encountered (per requirement)
  4. Run end-to-end tests with real sources
  5. Verify Excel output includes images
  6. Test LinkedIn posting workflow

---

## Installation Instructions

### Install New Dependencies

**Using Command Prompt (Recommended):**
```cmd
cd C:\DesignYourAI
.venv\Scripts\activate.bat
pip install --index-url https://pypi.org/simple Pillow==10.1.0 imagehash==4.3.1
```

**Using PowerShell:**
```powershell
cd C:\DesignYourAI
.\venv\Scripts\activate.bat
pip install --index-url https://pypi.org/simple Pillow==10.1.0 imagehash==4.3.1
```

**Or Install All Requirements:**
```cmd
pip install --index-url https://pypi.org/simple -r requirements.txt
```

---

## Testing the Foundation

**Run the test suite:**
```cmd
# Activate virtual environment first
.venv\Scripts\activate.bat

# Run test
python tests\test_image_support.py
```

**Expected output:**
```
✅ MCQ schema with image fields test passed
✅ Settings image configuration test passed
✅ Images directory creation test passed

✅ ALL IMAGE SUPPORT FOUNDATION TESTS PASSED!
```

---

## Directory Structure

```
c:\DesignYourAI\
├── config/
│   ├── schemas.py              ✅ UPDATED (added image fields)
│   └── settings.py             ✅ UPDATED (added image config)
│
├── storage/
│   ├── excel_handler.py        ✅ UPDATED (added image columns)
│   └── media_handler.py        ✅ NEW (image operations)
│
├── data/
│   ├── images/                 ✅ NEW DIRECTORY
│   │   └── manifest.json       (will be created on first image save)
│   └── knowledge_base/
│       └── mcq_knowledge_base.xlsx
│
├── tests/
│   └── test_image_support.py   ✅ NEW (foundation tests)
│
└── requirements.txt            ✅ UPDATED (added Pillow, imagehash)
```

---

## Code Changes Summary

### New Files Created: 2
1. `storage/media_handler.py` - 345 lines
2. `tests/test_image_support.py` - 75 lines

### Files Modified: 4
1. `config/schemas.py` - Added 5 fields + updated to_dict/from_dict (~15 lines)
2. `config/settings.py` - Added image config (~20 lines)
3. `storage/excel_handler.py` - Added 4 Excel columns (~5 lines)
4. `requirements.txt` - Added 2 packages (~3 lines)

### Total New/Modified Code: ~463 lines

---

## Excel Schema (Updated)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Question_ID | String | UUID | `abc123-def456` |
| Question_Text | String | Full question | `Which classifiers lead to 0 training error?` |
| Option_A | String | Option A | `Decision tree depth=1` |
| Option_B | String | Option B | `SVM linear kernel` |
| Option_C | String | Option C | `Logistic regression` |
| Option_D | String | Option D | `Decision tree depth=2` |
| Correct_Answer | String | A/B/C/D or NULL | `D` |
| Explanation | String | Explanation if available | `Deep decision trees can overfit...` |
| Category | String | Conceptual/Mathematical/Application | `Application` |
| Topic | String | AI/ML/Data Science/System Design | `ML` |
| Difficulty | String | Easy/Medium/Hard | `Medium` |
| Source | String | URL or file path | `https://example.com/mcqs` |
| Date_Added | Date | Ingestion timestamp | `2026-02-06 12:00:00` |
| Used_Status | Boolean | Posted to LinkedIn? | `FALSE` |
| **Image_Path** | **String** | **Relative path** | **`data/images/example-site/abc123-def456.jpg`** |
| **Image_URL** | **String** | **Original URL** | **`https://example.com/images/scatter.png`** |
| **Has_Image** | **Boolean** | **Has image?** | **`TRUE`** |
| **Image_Format** | **String** | **Format** | **`jpg`** |

---

## Usage Example (After Full Implementation)

### Extracting MCQ with Image

```python
from extractors.web_extractor import WebExtractor
from storage.media_handler import MediaHandler
from config.settings import Settings

# Initialize
settings = Settings()
media_handler = MediaHandler(
    images_dir=settings.IMAGES_DIR,
    manifest_path=settings.IMAGE_MANIFEST_PATH,
    optimize_for_web=settings.OPTIMIZE_FOR_WEB,
    max_width=settings.IMAGE_MAX_WIDTH,
    max_height=settings.IMAGE_MAX_HEIGHT,
    quality=settings.IMAGE_QUALITY
)

extractor = WebExtractor(config={}, media_handler=media_handler)

# Extract from source with images
mcqs = await extractor.extract("https://example.com/visual-mcqs")

# MCQs with images will have:
for mcq in mcqs:
    if mcq.has_image:
        print(f"Question: {mcq.question_text}")
        print(f"Image: {mcq.image_path}")
        print(f"Format: {mcq.image_format}")
```

### LinkedIn Posting Workflow

```python
import pandas as pd
from pathlib import Path

# Load Excel
df = pd.read_excel("data/knowledge_base/mcq_knowledge_base.xlsx")

# Filter for MCQs with images
visual_mcqs = df[df['Has_Image'] == True]

# Get unused MCQ
unused = visual_mcqs[visual_mcqs['Used_Status'] == False].iloc[0]

# Post to LinkedIn
question = unused['Question_Text']
options = f"A) {unused['Option_A']}\nB) {unused['Option_B']}\nC) {unused['Option_C']}\nD) {unused['Option_D']}"
image_path = unused['Image_Path']

# Upload image + post text to LinkedIn
# ... (posting automation to be implemented later)

# Mark as used
df.loc[df['Question_ID'] == unused['Question_ID'], 'Used_Status'] = True
df.to_excel("data/knowledge_base/mcq_knowledge_base.xlsx", index=False)
```

---

## Critical Requirements Met

✅ **MCQ Schema Extended** - Image fields added to dataclass
✅ **Settings Configuration** - Image paths and optimization settings
✅ **MediaHandler Created** - Complete image operations module
✅ **Excel Schema Updated** - 4 new columns for images
✅ **Dependencies Added** - Pillow and imagehash
✅ **Tests Created** - Foundation verification tests

---

## Ready for Day 2

**Next:** Enhance web extractor to detect and extract images from HTML.

**What to expect:**
- Web extractor will download images within question blocks
- Images optimized for LinkedIn (1200x1200px max, 85% quality JPEG)
- MCQs with failed image extraction will be skipped (per requirement)
- Images saved to `data/images/{source}/{question_id}.jpg`

---

## Questions?

See:
- [README.md](README.md) - Full documentation
- [COMMAND_PROMPT_GUIDE.txt](COMMAND_PROMPT_GUIDE.txt) - Daily usage
- [Plan document](C:\Users\V. Jishnu\.claude\plans\buzzing-napping-lollipop.md) - Complete implementation plan

---

**Day 1 Complete! 🎉**

The foundation for image support is now in place. You can proceed to Day 2 when ready, or test the current implementation first.
