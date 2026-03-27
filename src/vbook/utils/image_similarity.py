# src/vbook/utils/image_similarity.py
import cv2
import numpy as np
from pathlib import Path


def calculate_image_similarity(img_path1: Path, img_path2: Path) -> float:
    """Calculate similarity between two images using histogram comparison.

    Args:
        img_path1: Path to first image
        img_path2: Path to second image

    Returns:
        Similarity score between 0.0 (completely different) and 1.0 (identical)
    """
    img1 = cv2.imread(str(img_path1))
    img2 = cv2.imread(str(img_path2))

    if img1 is None or img2 is None:
        return 0.0

    # Convert to HSV for better color comparison
    hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

    # Calculate histograms
    hist1 = cv2.calcHist([hsv1], [0, 1], None, [50, 60], [0, 180, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1], None, [50, 60], [0, 180, 0, 256])

    # Normalize histograms
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    # Compare histograms using correlation
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return max(0.0, similarity)  # Ensure non-negative


def deduplicate_images(
    image_paths: list[Path],
    similarity_threshold: float = 0.95
) -> list[Path]:
    """Remove visually similar images from a list.

    Args:
        image_paths: List of image file paths
        similarity_threshold: Images with similarity above this are considered duplicates

    Returns:
        Filtered list of image paths with duplicates removed
    """
    if not image_paths:
        return []

    # Keep first image always
    result = [image_paths[0]]

    for img_path in image_paths[1:]:
        is_duplicate = False

        # Compare with all kept images
        for kept_img in result:
            similarity = calculate_image_similarity(img_path, kept_img)
            if similarity >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(img_path)

    return result
