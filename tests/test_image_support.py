"""
Tests for image support functionality.
"""

import pytest
from pathlib import Path
from config.schemas import MCQ
from config.settings import Settings


def test_mcq_schema_with_images():
    """Test MCQ schema includes image fields."""
    mcq = MCQ(
        question_text="Test question with image",
        option_a="Option A",
        option_b="Option B",
        option_c="Option C",
        option_d="Option D",
        source="test_source",
        image_path="data/images/test/q123.jpg",
        image_url="https://example.com/image.jpg",
        has_image=True,
        image_format="jpg"
    )

    # Verify fields exist
    assert mcq.image_path == "data/images/test/q123.jpg"
    assert mcq.image_url == "https://example.com/image.jpg"
    assert mcq.has_image == True
    assert mcq.image_format == "jpg"

    # Verify to_dict includes image fields
    mcq_dict = mcq.to_dict()
    assert 'Image_Path' in mcq_dict
    assert 'Image_URL' in mcq_dict
    assert 'Has_Image' in mcq_dict
    assert 'Image_Format' in mcq_dict
    assert mcq_dict['Image_Path'] == "data/images/test/q123.jpg"
    assert mcq_dict['Has_Image'] == True

    # Verify from_dict parses image fields
    mcq_restored = MCQ.from_dict(mcq_dict)
    assert mcq_restored.image_path == mcq.image_path
    assert mcq_restored.has_image == mcq.has_image
    assert mcq_restored.image_format == mcq.image_format

    print("✅ MCQ schema with image fields test passed")


def test_settings_has_image_config():
    """Test Settings includes image configuration."""
    settings = Settings()

    # Verify image paths exist
    assert hasattr(settings, 'IMAGES_DIR')
    assert hasattr(settings, 'IMAGE_MANIFEST_PATH')

    # Verify image optimization settings
    assert hasattr(settings, 'OPTIMIZE_FOR_WEB')
    assert hasattr(settings, 'IMAGE_MAX_WIDTH')
    assert hasattr(settings, 'IMAGE_MAX_HEIGHT')
    assert hasattr(settings, 'IMAGE_QUALITY')

    # Verify default values
    assert settings.IMAGE_MAX_WIDTH == 1200
    assert settings.IMAGE_MAX_HEIGHT == 1200
    assert settings.IMAGE_QUALITY == 85
    assert settings.OPTIMIZE_FOR_WEB == True

    print("✅ Settings image configuration test passed")


def test_images_directory_created():
    """Test that images directory is created during validation."""
    settings = Settings()
    settings.validate()

    # Check that images directory exists
    assert settings.IMAGES_DIR.exists()
    assert settings.IMAGES_DIR.is_dir()

    print("✅ Images directory creation test passed")


if __name__ == '__main__':
    test_mcq_schema_with_images()
    test_settings_has_image_config()
    test_images_directory_created()
    print("\n✅ ALL IMAGE SUPPORT FOUNDATION TESTS PASSED!")
