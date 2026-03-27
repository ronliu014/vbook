import pytest
from pathlib import Path
from PIL import Image
from vbook.utils.image_similarity import calculate_image_similarity, deduplicate_images


def test_calculate_image_similarity_identical(tmp_path):
    """Test similarity calculation for identical images."""
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(str(img_path))

    similarity = calculate_image_similarity(img_path, img_path)
    assert similarity == 1.0


def test_calculate_image_similarity_different(tmp_path):
    """Test similarity calculation for different images."""
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"

    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="blue")

    img1.save(str(img1_path))
    img2.save(str(img2_path))

    similarity = calculate_image_similarity(img1_path, img2_path)
    assert 0.0 <= similarity < 0.5  # Very different colors


def test_calculate_image_similarity_similar(tmp_path):
    """Test similarity calculation for similar images."""
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"

    # Create two similar images (same color, slightly different)
    img1 = Image.new("RGB", (100, 100), color=(200, 50, 50))
    img2 = Image.new("RGB", (100, 100), color=(210, 55, 55))

    img1.save(str(img1_path))
    img2.save(str(img2_path))

    similarity = calculate_image_similarity(img1_path, img2_path)
    assert 0.8 <= similarity <= 1.0  # Very similar


def test_deduplicate_images_removes_duplicates(tmp_path):
    """Test that deduplicate_images removes similar images."""
    # Create 3 images: 2 very similar (almost identical red), 1 different (blue)
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"
    img3_path = tmp_path / "img3.jpg"

    # Create two nearly identical images
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="red")
    # Add tiny variation to img2
    pixels = img2.load()
    pixels[0, 0] = (254, 0, 0)  # Slightly different pixel

    img3 = Image.new("RGB", (100, 100), color="blue")

    img1.save(str(img1_path))
    img2.save(str(img2_path))
    img3.save(str(img3_path))

    result = deduplicate_images([img1_path, img2_path, img3_path], similarity_threshold=0.95)

    # Should keep img1 and img3, remove img2 (nearly identical to img1)
    assert len(result) == 2
    assert img1_path in result
    assert img3_path in result


def test_deduplicate_images_empty_list():
    """Test deduplicate_images with empty list."""
    result = deduplicate_images([])
    assert result == []


def test_deduplicate_images_single_image(tmp_path):
    """Test deduplicate_images with single image."""
    img_path = tmp_path / "img.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(str(img_path))

    result = deduplicate_images([img_path])
    assert result == [img_path]
