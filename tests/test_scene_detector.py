import numpy as np
from unittest.mock import patch, MagicMock
from vbook.utils.scene_detector import detect_scene_changes


def test_detect_scene_changes_finds_transitions():
    """Mock cv2.VideoCapture to simulate scene changes."""
    # Create fake frames: 3 similar frames, then 1 very different frame
    frame_a = np.zeros((100, 100, 3), dtype=np.uint8)       # black
    frame_b = np.zeros((100, 100, 3), dtype=np.uint8) + 5   # near-black
    frame_c = np.ones((100, 100, 3), dtype=np.uint8) * 255  # white (scene change!)

    frames = [frame_a, frame_a.copy(), frame_b, frame_c]
    frame_idx = [0]

    mock_cap = MagicMock()
    mock_cap.get.return_value = 30.0  # fps
    mock_cap.isOpened.return_value = True

    def mock_read():
        if frame_idx[0] < len(frames):
            f = frames[frame_idx[0]]
            frame_idx[0] += 1
            return True, f
        return False, None

    mock_cap.read.side_effect = mock_read

    # Mock cv2 functions
    hist_call_count = [0]

    def mock_cvtColor(frame, code):
        return frame  # Just return the frame as-is

    def mock_calcHist(images, channels, mask, histSize, ranges):
        # Return different histograms for similar vs different frames
        hist_call_count[0] += 1
        if hist_call_count[0] <= 3:
            # First 3 frames: similar histograms
            return np.ones((50, 60), dtype=np.float32) * 0.5
        else:
            # 4th frame: very different histogram
            return np.ones((50, 60), dtype=np.float32) * 0.9

    def mock_normalize(src, dst):
        pass  # No-op

    def mock_compareHist(h1, h2, method):
        # Compare histograms - return high similarity for similar, low for different
        if np.allclose(h1, h2):
            return 0.95  # High similarity
        else:
            return 0.5   # Low similarity (triggers scene change)

    with patch("cv2.VideoCapture", return_value=mock_cap), \
         patch("cv2.cvtColor", side_effect=mock_cvtColor), \
         patch("cv2.calcHist", side_effect=mock_calcHist), \
         patch("cv2.normalize", side_effect=mock_normalize), \
         patch("cv2.compareHist", side_effect=mock_compareHist):
        changes = detect_scene_changes("fake.mp4", sample_interval=1/30, threshold=0.3)

    assert len(changes) >= 1
    # The scene change should be detected around the 4th frame
    mock_cap.release.assert_called_once()


def test_detect_scene_changes_empty_video():
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0
    mock_cap.read.return_value = (False, None)

    with patch("cv2.VideoCapture", return_value=mock_cap):
        changes = detect_scene_changes("empty.mp4")

    assert changes == []


def test_detect_scene_changes_unopenable_video():
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False

    with patch("cv2.VideoCapture", return_value=mock_cap):
        changes = detect_scene_changes("bad.mp4")

    assert changes == []
