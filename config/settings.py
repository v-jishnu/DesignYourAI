"""
Central configuration for MCQ ingestion system.
"""

from pathlib import Path
from typing import Literal
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Central configuration class."""

    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    RAW_DIR = DATA_DIR / 'raw'
    PROCESSED_DIR = DATA_DIR / 'processed'
    KB_DIR = DATA_DIR / 'knowledge_base'
    IMAGES_DIR = DATA_DIR / 'images'
    LOG_DIR = BASE_DIR / 'logs'

    # Excel Configuration
    EXCEL_PATH = KB_DIR / 'mcq_knowledge_base.xlsx'
    EXCEL_SHEET_NAME = 'MCQs'

    # LLM Configuration
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')  # gemini, anthropic, openai, groq, together, qwen, deepseek, ollama

    # API Keys (one required based on provider)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
    QWEN_API_KEY = os.getenv('QWEN_API_KEY')
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', 'ollama')  # Ollama doesn't need a real key

    # Model configuration per provider
    LLM_MODELS = {
        'gemini': 'gemini-2.0-flash',  # FREE TIER
        'anthropic': 'claude-3-5-sonnet-20241022',
        'openai': 'gpt-3.5-turbo',
        'groq': 'llama-3.3-70b-versatile',  # FREE TIER (Groq)
        'together': 'mistralai/Mixtral-8x7B-Instruct-v0.1',  # FREE TIER
        'qwen': 'qwen-plus',  # FREE TIER (Alibaba Qwen)
        'deepseek': 'deepseek-chat',  # FREE TIER (DeepSeek)
        'ollama': 'qwen2.5:7b'  # LOCAL (free, unlimited)
    }

    # Base URLs for compatible APIs
    LLM_BASE_URLS = {
        'groq': 'https://api.groq.com/openai/v1',
        'together': 'https://api.together.xyz/v1',
        'qwen': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'deepseek': 'https://api.deepseek.com/v1',
        'ollama': 'http://localhost:11434/v1'
    }

    # Get appropriate API key and model
    @classmethod
    def get_llm_config(cls):
        """Get LLM configuration based on provider."""
        provider = cls.LLM_PROVIDER.lower()

        # Get API key for provider
        api_key_map = {
            'gemini': cls.GEMINI_API_KEY,
            'anthropic': cls.ANTHROPIC_API_KEY,
            'openai': cls.OPENAI_API_KEY,
            'groq': cls.GROQ_API_KEY,
            'together': cls.TOGETHER_API_KEY,
            'qwen': cls.QWEN_API_KEY,
            'deepseek': cls.DEEPSEEK_API_KEY,
            'ollama': cls.OLLAMA_API_KEY
        }

        api_key = api_key_map.get(provider)
        if not api_key:
            raise ValueError(
                f"API key for provider '{provider}' not found. "
                f"Please set {provider.upper()}_API_KEY in .env file"
            )

        return {
            'provider': provider,
            'api_key': api_key,
            'model': cls.LLM_MODELS.get(provider, 'gemini-1.5-flash'),
            'base_url': cls.LLM_BASE_URLS.get(provider)
        }

    # Classification Settings
    CLASSIFICATION_BATCH_SIZE = 10
    CATEGORIES = ['Conceptual', 'Mathematical', 'Application']
    TOPICS = ['AI', 'ML', 'Data Science', 'System Design']
    DIFFICULTY_LEVELS = ['Easy', 'Medium', 'Hard']

    # Deduplication Settings
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.85'))
    USE_SEMANTIC_SIMILARITY = False  # Enable for advanced semantic dedup

    # Quality Control Settings (MAANG-Level Standards)
    QUALITY_PASS_THRESHOLD = 0.90  # 90% of MCQs must pass quality check
    ENABLE_QUALITY_VALIDATION = True  # Set to False to disable quality filtering
    ENABLE_DISTRIBUTION_ENFORCEMENT = True  # Enforce 50/25/25 category split

    # Category Distribution (MANDATORY for MAANG-level quality)
    CATEGORY_DISTRIBUTION = {
        'Conceptual': 0.50,      # 50% - reasoning, trade-offs, failure cases
        'Mathematical': 0.25,    # 25% - quantitative intuition, not computation
        'Application': 0.25      # 25% - production scenarios, metric trade-offs
    }

    # Few-Shot Examples
    FEW_SHOT_COUNT = 3  # Number of examples to inject into prompts
    FEW_SHOT_ROTATION = True  # Rotate examples to prevent overfitting

    # Extraction Settings
    WEB_SCRAPER: Literal['beautifulsoup'] = 'beautifulsoup'
    PDF_PARSER: Literal['pypdf2', 'pdfplumber'] = 'pdfplumber'
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3

    # Browser Automation Settings (for JavaScript-rendered sites)
    BROWSER_ENABLED = True  # Enable Playwright browser automation
    BROWSER_TIMEOUT = 60000  # milliseconds (60 seconds)
    BROWSER_WAIT_UNTIL = 'domcontentloaded'  # Wait for DOM content loaded (faster than networkidle)
    BROWSER_HEADLESS = True  # Run browser in headless mode

    # Content-to-MCQ Generation Settings
    GENERATION_ENABLED = True  # Enable LLM-based MCQ generation from content
    GENERATION_NUM_QUESTIONS = 5  # Number of MCQs to generate per page
    GENERATION_MIN_CONTENT_LENGTH = 500  # Minimum content length in words to attempt generation
    GENERATION_MAX_CONTENT_LENGTH = 4000  # Maximum content length in chars to send to LLM

    # StrataScratch API Settings
    STRATASCRATCH_TOKEN = os.getenv('STRATASCRATCH_TOKEN')
    STRATASCRATCH_PAGE_SIZE = 50
    STRATASCRATCH_REQUEST_DELAY = 0.5  # seconds between API calls
    # Filter by job positions (IDs): 1=Data Engineer, 2=Data Scientist,
    # 4=Data Analyst, 5=ML Engineer, 11=AI Engineer
    STRATASCRATCH_JOB_POSITIONS = []  # Empty = all positions
    STRATASCRATCH_QUESTION_TYPES = []  # Empty = all types
    STRATASCRATCH_DIFFICULTIES = []  # Empty = all difficulties
    STRATASCRATCH_COMPANIES = []  # Empty = all companies

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Target
    MIN_MCQ_TARGET = 800

    # Image Settings
    SUPPORTED_IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']
    MAX_IMAGE_SIZE_MB = 5
    IMAGE_MANIFEST_PATH = IMAGES_DIR / 'manifest.json'

    # Image optimization for social media (LinkedIn target)
    OPTIMIZE_FOR_WEB = True
    IMAGE_MAX_WIDTH = 1200  # px (LinkedIn recommended)
    IMAGE_MAX_HEIGHT = 1200
    IMAGE_QUALITY = 85  # JPEG quality (balance size vs clarity)

    @classmethod
    def validate(cls):
        """Validate configuration and create necessary directories."""
        # Check API key for selected provider
        try:
            cls.get_llm_config()
        except ValueError as e:
            raise ValueError(str(e))

        # Create directories
        for directory in [cls.DATA_DIR, cls.RAW_DIR, cls.PROCESSED_DIR,
                         cls.KB_DIR, cls.IMAGES_DIR, cls.LOG_DIR]:
            directory.mkdir(exist_ok=True, parents=True)

        return True

    @classmethod
    def get_config(cls) -> dict:
        """Get configuration as dictionary for agents."""
        llm_config = cls.get_llm_config()

        return {
            'llm_provider': llm_config['provider'],
            'llm_api_key': llm_config['api_key'],
            'llm_model': llm_config['model'],
            'llm_base_url': llm_config.get('base_url'),
            'llm_config': llm_config,
            'classification_batch_size': cls.CLASSIFICATION_BATCH_SIZE,
            'similarity_threshold': cls.SIMILARITY_THRESHOLD,
            'excel_path': cls.EXCEL_PATH,
            'request_timeout': cls.REQUEST_TIMEOUT,
            'max_retries': cls.MAX_RETRIES,
            'log_level': cls.LOG_LEVEL,
            'categories': cls.CATEGORIES,
            'topics': cls.TOPICS,
            'difficulty_levels': cls.DIFFICULTY_LEVELS,
            'browser_enabled': cls.BROWSER_ENABLED,
            'browser_timeout': cls.BROWSER_TIMEOUT,
            'browser_wait_until': cls.BROWSER_WAIT_UNTIL,
            'browser_headless': cls.BROWSER_HEADLESS,
            'generation_enabled': cls.GENERATION_ENABLED,
            'generation_num_questions': cls.GENERATION_NUM_QUESTIONS,
            'generation_min_content_length': cls.GENERATION_MIN_CONTENT_LENGTH,
            'generation_max_content_length': cls.GENERATION_MAX_CONTENT_LENGTH,
            # Quality control settings
            'quality_pass_threshold': cls.QUALITY_PASS_THRESHOLD,
            'enable_quality_validation': cls.ENABLE_QUALITY_VALIDATION,
            'category_distribution': cls.CATEGORY_DISTRIBUTION,
            'few_shot_count': cls.FEW_SHOT_COUNT,
            'enable_distribution_enforcement': cls.ENABLE_DISTRIBUTION_ENFORCEMENT,
            # StrataScratch settings
            'stratascratch_token': cls.STRATASCRATCH_TOKEN,
            'stratascratch_page_size': cls.STRATASCRATCH_PAGE_SIZE,
            'stratascratch_request_delay': cls.STRATASCRATCH_REQUEST_DELAY,
            'stratascratch_job_positions': cls.STRATASCRATCH_JOB_POSITIONS,
            'stratascratch_question_types': cls.STRATASCRATCH_QUESTION_TYPES,
            'stratascratch_difficulties': cls.STRATASCRATCH_DIFFICULTIES,
            'stratascratch_companies': cls.STRATASCRATCH_COMPANIES,
        }


# Initialize and validate settings
try:
    settings = Settings()
    settings.validate()
except ValueError as e:
    # Don't fail on import if .env is not set up yet
    settings = Settings()
    print(f"Warning: {e}")
