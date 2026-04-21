"""
Web extractor for MCQ extraction from HTML pages.

Supports both static HTML (BeautifulSoup) and JavaScript-rendered sites (Playwright).
"""

from typing import List
import re

try:
    from bs4 import BeautifulSoup
    import aiohttp
except ImportError:
    BeautifulSoup = None
    aiohttp = None

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    async_playwright = None
    PlaywrightTimeout = None

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ
from utils.text_processor import extract_option_text, extract_correct_answer


class WebExtractor(BaseExtractor):
    """Extract MCQs from web pages using BeautifulSoup."""

    async def extract(self, source: str) -> List[MCQ]:
        """
        Extract MCQs from HTML page using multi-strategy approach:
        1. Static extraction (fast)
        2. Browser rendering (handles JS)
        3. Content generation (works on ANY content) - NEW

        Args:
            source: URL to scrape

        Returns:
            List of extracted/generated MCQs
        """
        if BeautifulSoup is None or aiohttp is None:
            self.log("beautifulsoup4 and aiohttp required. Install with: pip install beautifulsoup4 aiohttp lxml", 'error')
            return []

        self.log(f"Extracting from URL: {source}")

        try:
            # Try static extraction first (fast)
            mcqs = await self._extract_static(source)

            # If no MCQs found, try browser rendering (slower but handles JS)
            if len(mcqs) == 0 and self.config.get('browser_enabled', True):
                self.log("Static extraction found nothing, trying browser rendering...", 'info')
                mcqs = await self._extract_with_browser(source)

            # NEW: If still no MCQs, try content generation (works on ANY content)
            if len(mcqs) == 0 and self.config.get('generation_enabled', True) and self.llm_client:
                self.log("Extraction failed, generating MCQs from page content...", 'info')
                mcqs = await self._generate_from_page_content(source)

            self.log(f"Extracted/Generated {len(mcqs)} MCQs from {source}")
            return mcqs

        except Exception as e:
            self.log(f"Error extracting from {source}: {e}", 'error')
            return []

    async def _extract_static(self, source: str) -> List[MCQ]:
        """Extract using static HTML (fast, works for most sites)."""
        try:
            html = await self._fetch_html(source)
            soup = BeautifulSoup(html, 'lxml')

            mcqs = []

            # Strategy 1: Look for question divs/sections
            mcqs.extend(await self._extract_from_question_blocks(soup, source))

            # Strategy 2: Look for list-based MCQs
            if not mcqs:
                mcqs.extend(self._extract_from_lists(soup, source))

            return mcqs

        except Exception as e:
            self.log(f"Static extraction error: {e}", 'warning')
            return []

    async def _extract_with_browser(self, url: str) -> List[MCQ]:
        """Extract using Playwright browser automation (handles JavaScript)."""
        if async_playwright is None:
            self.log("Playwright not available. Install with: pip install playwright && playwright install chromium", 'warning')
            return []

        try:
            async with async_playwright() as p:
                # Launch headless browser
                browser = await p.chromium.launch(
                    headless=self.config.get('browser_headless', True)
                )
                page = await browser.new_page()

                # Navigate and wait for content
                timeout = self.config.get('browser_timeout', 30000)
                wait_until = self.config.get('browser_wait_until', 'networkidle')

                await page.goto(url, wait_until=wait_until, timeout=timeout)

                # Wait for common quiz containers
                try:
                    await page.wait_for_selector(
                        '.question, .mcq, .quiz-item, .quiz-question, [class*="question"]',
                        timeout=5000
                    )
                except Exception:
                    # Timeout is okay, content might load differently
                    pass

                # Get rendered HTML
                html_content = await page.content()
                await browser.close()

                # Parse with existing BeautifulSoup logic
                soup = BeautifulSoup(html_content, 'lxml')

                mcqs = []
                mcqs.extend(await self._extract_from_question_blocks(soup, url))
                if not mcqs:
                    mcqs.extend(self._extract_from_lists(soup, url))

                return mcqs

        except Exception as e:
            self.log(f"Browser extraction error: {e}", 'error')
            return []

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL."""
        timeout = self.config.get('request_timeout', 30)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                return await response.text()

    async def _extract_from_question_blocks(self, soup, source: str) -> List[MCQ]:
        """Extract MCQs from structured question blocks."""
        mcqs = []

        # Common class names for questions
        question_patterns = ['question', 'mcq', 'quiz', 'q-item', 'question-block']

        for pattern in question_patterns:
            blocks = soup.find_all(['div', 'section', 'article'], class_=re.compile(pattern, re.I))

            for block in blocks:
                mcq = await self._parse_question_block(block, source)
                if mcq:
                    mcqs.append(mcq)

        return mcqs

    async def _parse_question_block(self, block, source: str):
        """Parse a single question block."""
        # Extract question text
        question_elem = block.find(['h3', 'h4', 'p', 'div'], class_=re.compile(r'question|q-text', re.I))
        if not question_elem:
            # Try finding text with '?'
            text = block.get_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            question_text = next((l for l in lines if '?' in l), None)
            if not question_text:
                return None
        else:
            question_text = question_elem.get_text(strip=True)

        # Extract options
        option_elems = block.find_all(['li', 'div', 'p'], class_=re.compile(r'option|choice|answer', re.I))

        if len(option_elems) < 4:
            # Try finding by pattern
            text = block.get_text()
            options = re.findall(r'(?:^|\n)\s*[A-D][\)\.]\s*(.+?)(?=\n\s*[A-D][\)\.]|\n\n|\Z)', text, re.MULTILINE)
            if len(options) >= 4:
                mcq = self._create_mcq(
                    question_text=question_text,
                    option_a=options[0].strip(),
                    option_b=options[1].strip(),
                    option_c=options[2].strip(),
                    option_d=options[3].strip(),
                    source=source
                )
                # Check for image in question block
                if mcq and self.media_handler:
                    mcq = await self._process_image(block, mcq, source)
                return mcq
            return None

        options = [extract_option_text(elem.get_text(strip=True)) for elem in option_elems[:4]]

        if len(options) != 4:
            return None

        # Extract correct answer if present
        correct_elem = block.find(class_=re.compile(r'correct|answer-key', re.I))
        correct_answer = None
        if correct_elem:
            correct_answer = extract_correct_answer(correct_elem.get_text(strip=True))

        mcq = self._create_mcq(
            question_text=question_text,
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            source=source,
            correct_answer=correct_answer
        )

        # Check for image in question block (CRITICAL FOR VISUAL MCQs)
        if mcq and self.media_handler:
            mcq = await self._process_image(block, mcq, source)

        return mcq

    async def _process_image(self, block, mcq, source: str):
        """
        Process image within question block.

        Returns None if image extraction fails (skip MCQ per requirements).
        """
        img_elem = block.find('img')
        if img_elem:
            try:
                self.log(f"Found image for MCQ: {mcq.question_text[:50]}...")

                # Download image
                image_data = await self.media_handler.extract_from_html(img_elem, source)

                # Optimize for web/LinkedIn
                optimized_data = self.media_handler.optimize_for_web(image_data)

                # Save locally with JPEG format (LinkedIn-friendly)
                image_path = await self.media_handler.save_image(
                    optimized_data, mcq.question_id, source, 'jpg'
                )

                # Link to MCQ
                mcq.image_path = image_path
                mcq.image_url = img_elem.get('src')
                mcq.has_image = True
                mcq.image_format = 'jpg'

                self.log(f"Successfully extracted image: {image_path}")
                return mcq

            except Exception as e:
                # CRITICAL: Skip MCQ if image extraction fails
                self.log(f"Failed to extract image for MCQ, skipping entire MCQ: {e}", 'warning')
                return None  # Skip this MCQ entirely

        # No image found - MCQ is fine
        return mcq

    def _extract_from_lists(self, soup, source: str) -> List[MCQ]:
        """Extract MCQs from list structures."""
        mcqs = []

        # Find all ordered/unordered lists
        lists = soup.find_all(['ol', 'ul'])

        for lst in lists:
            items = lst.find_all('li')

            # Check if this looks like an MCQ (has question + 4 options pattern)
            text = lst.get_text()
            if '?' in text and len(items) >= 5:
                # Might be question + 4 options
                question = items[0].get_text(strip=True)
                if len(items) >= 5:
                    mcq = self._create_mcq(
                        question_text=question,
                        option_a=extract_option_text(items[1].get_text(strip=True)),
                        option_b=extract_option_text(items[2].get_text(strip=True)),
                        option_c=extract_option_text(items[3].get_text(strip=True)),
                        option_d=extract_option_text(items[4].get_text(strip=True)),
                        source=source
                    )
                    if mcq:
                        mcqs.append(mcq)

        return mcqs

    async def _generate_from_page_content(self, url: str) -> List[MCQ]:
        """
        Extract text content from page and generate MCQs using LLM.

        NEW METHOD - fallback when HTML parsing fails.
        Works with ANY web page that has educational content.

        Args:
            url: Page URL

        Returns:
            List of generated MCQs (typically 3-5)
        """
        try:
            # Get page content (use browser if available for JS sites)
            if self.config.get('browser_enabled', True) and async_playwright:
                content = await self._get_page_text_with_browser(url)
            else:
                html = await self._fetch_html(url)
                soup = BeautifulSoup(html, 'lxml')
                content = soup.get_text()

            # Clean content (remove nav, footer, ads, etc.)
            cleaned_content = self._clean_page_content(content)

            # Check minimum content length
            min_length = self.config.get('generation_min_content_length', 500)
            if len(cleaned_content.split()) < min_length:
                self.log(f"Content too short for generation ({len(cleaned_content.split())} words < {min_length})", 'warning')
                return []

            # Generate MCQs using ContentGenerator
            from generators.content_generator import ContentGenerator
            generator = ContentGenerator(self.llm_client, self.config)

            num_questions = self.config.get('generation_num_questions', 5)
            mcqs = await generator.generate_from_content(
                cleaned_content,
                url,
                num_questions=num_questions
            )

            self.log(f"Generated {len(mcqs)} MCQs from page content")
            return mcqs

        except Exception as e:
            self.log(f"Content generation error: {e}", 'error')
            return []

    async def _get_page_text_with_browser(self, url: str) -> str:
        """
        Get text content using browser (for JS sites).

        Args:
            url: Page URL

        Returns:
            Visible text content from page
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Navigate and wait for content
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                # Extract visible text only (excludes scripts, styles, etc.)
                content = await page.evaluate('''() => {
                    return document.body.innerText;
                }''')

                await browser.close()
                return content

        except Exception as e:
            self.log(f"Browser text extraction error: {e}", 'warning')
            # Fallback to static HTML
            html = await self._fetch_html(url)
            soup = BeautifulSoup(html, 'lxml')
            return soup.get_text()

    def _clean_page_content(self, content: str) -> str:
        """
        Clean page content for generation.

        Removes:
        - Navigation menus
        - Footers
        - Ads
        - Cookie banners
        - Social media links
        - Multiple whitespace

        Args:
            content: Raw page text

        Returns:
            Cleaned content suitable for MCQ generation
        """
        # Remove multiple whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove common boilerplate patterns
        patterns_to_remove = [
            r'Cookie Policy.*?Accept',
            r'Share on.*?Twitter',
            r'Follow us on.*?Instagram',
            r'Copyright.*?\d{4}',
            r'Subscribe to our newsletter',
            r'Sign in.*?Register',
            r'Click here to.*?',
            r'Read more.*?',
            r'Advertisement',
            r'Sponsored content'
        ]

        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        # Remove URLs
        content = re.sub(r'http[s]?://\S+', '', content)

        return content.strip()
