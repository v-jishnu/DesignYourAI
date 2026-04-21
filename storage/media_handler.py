"""
Media handler for extracting, optimizing, and storing images associated with MCQs.
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
import hashlib
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None

from utils.logger import get_logger

logger = get_logger(__name__)


class MediaHandler:
    """Handles image extraction, optimization, and storage for MCQs."""

    def __init__(self, images_dir: Path, manifest_path: Path,
                 optimize_for_web: bool = True,
                 max_width: int = 1200,
                 max_height: int = 1200,
                 quality: int = 85,
                 supported_formats: list = None):
        """
        Initialize MediaHandler.

        Args:
            images_dir: Root directory for image storage
            manifest_path: Path to manifest.json for tracking images
            optimize_for_web: Whether to optimize images for web/social media
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
            quality: JPEG quality (1-100)
            supported_formats: List of supported image formats
        """
        self.images_dir = images_dir
        self.manifest_path = manifest_path
        self.optimize_for_web = optimize_for_web
        self.max_width = max_width
        self.max_height = max_height
        self.quality = quality
        self.supported_formats = supported_formats or ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']

        # Ensure images directory exists
        self.images_dir.mkdir(exist_ok=True, parents=True)

        # Load or initialize manifest
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load image manifest from disk."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load manifest, starting fresh: {e}")
                return {}
        return {}

    def _save_manifest(self):
        """Save image manifest to disk."""
        try:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        # Remove special characters, replace spaces with hyphens
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text)
        return text[:50]  # Limit length

    def _get_source_slug(self, source: str) -> str:
        """Generate a slug from source URL or file path."""
        if source.startswith('http'):
            # Extract domain from URL
            parsed = urlparse(source)
            domain = parsed.netloc.replace('www.', '')
            return self._slugify(domain)
        else:
            # Use filename for local files
            return self._slugify(Path(source).stem)

    def _get_image_format(self, image_data: bytes, url: Optional[str] = None) -> str:
        """Detect image format from data or URL."""
        # Try to detect from data
        if image_data[:4] == b'\x89PNG':
            return 'png'
        elif image_data[:2] == b'\xff\xd8':
            return 'jpg'
        elif image_data[:3] == b'GIF':
            return 'gif'
        elif b'<svg' in image_data[:100].lower():
            return 'svg'
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return 'webp'

        # Try to detect from URL extension
        if url:
            ext = Path(urlparse(url).path).suffix.lower().lstrip('.')
            if ext in self.supported_formats:
                return ext

        # Default to jpg for optimization
        return 'jpg'

    async def save_image(self, image_data: bytes, question_id: str,
                        source: str, format: Optional[str] = None) -> str:
        """
        Save image to disk with organized structure.

        Args:
            image_data: Raw image bytes
            question_id: MCQ question ID
            source: Source URL or file path
            format: Image format (detected if not provided)

        Returns:
            Relative path to saved image (e.g., "data/images/source/qid.jpg")
        """
        try:
            # Detect format if not provided
            if not format:
                format = self._get_image_format(image_data)

            # Create source directory
            source_slug = self._get_source_slug(source)
            source_dir = self.images_dir / source_slug
            source_dir.mkdir(exist_ok=True, parents=True)

            # Generate filename
            filename = f"{question_id}.{format}"
            file_path = source_dir / filename

            # Save image
            with open(file_path, 'wb') as f:
                f.write(image_data)

            # Update manifest
            relative_path = str(file_path.relative_to(self.images_dir.parent))
            self.manifest[question_id] = {
                'path': relative_path,
                'source': source,
                'format': format,
                'size_bytes': len(image_data),
                'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self._save_manifest()

            logger.info(f"Saved image: {relative_path} ({len(image_data)} bytes)")
            return relative_path

        except Exception as e:
            logger.error(f"Failed to save image for {question_id}: {e}")
            raise

    async def extract_from_html(self, img_element, base_url: str) -> bytes:
        """
        Download image from HTML <img> tag.

        Args:
            img_element: BeautifulSoup img element
            base_url: Base URL for resolving relative URLs

        Returns:
            Image data as bytes
        """
        try:
            # Get image URL
            img_url = img_element.get('src') or img_element.get('data-src')
            if not img_url:
                raise ValueError("No src or data-src attribute found")

            # Handle data URLs
            if img_url.startswith('data:image'):
                # Extract base64 data
                import base64
                data_match = re.match(r'data:image/[^;]+;base64,(.+)', img_url)
                if data_match:
                    return base64.b64decode(data_match.group(1))
                else:
                    raise ValueError("Invalid data URL format")

            # Resolve relative URL
            full_url = urljoin(base_url, img_url)

            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.debug(f"Downloaded image from {full_url} ({len(image_data)} bytes)")
                        return image_data
                    else:
                        raise ValueError(f"HTTP {response.status} for {full_url}")

        except Exception as e:
            logger.error(f"Failed to extract image from HTML: {e}")
            raise

    def optimize_for_web(self, image_data: bytes,
                        max_width: Optional[int] = None,
                        max_height: Optional[int] = None,
                        quality: Optional[int] = None) -> bytes:
        """
        Optimize image for web/social media using Pillow.

        Args:
            image_data: Raw image bytes
            max_width: Maximum width (defaults to instance setting)
            max_height: Maximum height (defaults to instance setting)
            quality: JPEG quality (defaults to instance setting)

        Returns:
            Optimized image bytes
        """
        if not Image:
            logger.warning("Pillow not installed, returning original image")
            return image_data

        if not self.optimize_for_web:
            return image_data

        try:
            max_width = max_width or self.max_width
            max_height = max_height or self.max_height
            quality = quality or self.quality

            # Open image
            img = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background

            # Resize if too large
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to {img.width}x{img.height}")

            # Save to bytes with optimization
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            optimized_data = output.getvalue()

            logger.debug(f"Optimized image: {len(image_data)} -> {len(optimized_data)} bytes "
                        f"({100 * len(optimized_data) // len(image_data)}%)")

            return optimized_data

        except Exception as e:
            logger.warning(f"Failed to optimize image, returning original: {e}")
            return image_data

    def get_image_path(self, question_id: str) -> Optional[Path]:
        """
        Retrieve image path for a given question ID.

        Args:
            question_id: MCQ question ID

        Returns:
            Path object or None if not found
        """
        if question_id in self.manifest:
            path_str = self.manifest[question_id]['path']
            return Path(path_str)
        return None

    def verify_image_exists(self, image_path: str) -> bool:
        """
        Check if image file exists on disk.

        Args:
            image_path: Relative or absolute path to image

        Returns:
            True if file exists
        """
        path = Path(image_path)
        if not path.is_absolute():
            path = self.images_dir.parent / path
        return path.exists()

    def calculate_image_hash(self, image_path: str) -> Optional[str]:
        """
        Calculate perceptual hash for image deduplication.

        Args:
            image_path: Path to image file

        Returns:
            Perceptual hash as string, or None if failed
        """
        try:
            import imagehash
            path = Path(image_path)
            if not path.is_absolute():
                path = self.images_dir.parent / path

            if not path.exists():
                logger.warning(f"Image not found for hashing: {path}")
                return None

            img = Image.open(path)
            phash = str(imagehash.phash(img))
            return phash

        except ImportError:
            logger.warning("imagehash not installed, skipping image similarity")
            return None
        except Exception as e:
            logger.error(f"Failed to calculate image hash: {e}")
            return None

    def are_images_similar(self, hash1: str, hash2: str, threshold: int = 5) -> bool:
        """
        Compare perceptual hashes to detect similar images.

        Args:
            hash1: First image hash
            hash2: Second image hash
            threshold: Hamming distance threshold (lower = more similar)

        Returns:
            True if images are similar
        """
        try:
            import imagehash
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            distance = h1 - h2
            return distance <= threshold
        except Exception as e:
            logger.error(f"Failed to compare image hashes: {e}")
            return False
