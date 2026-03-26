import cv2
import numpy as np
from .logger import get_logger

logger = get_logger(__name__)


def detect_scene_changes(
    video_path: str,
    sample_interval: float = 5.0,
    threshold: float = 0.3,
) -> list[float]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning("无法打开视频: %s", video_path)
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_skip = max(1, int(fps * sample_interval))

    prev_hist = None
    changes = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_skip == 0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist, hist)

            if prev_hist is not None:
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if similarity < (1.0 - threshold):
                    timestamp = frame_count / fps
                    changes.append(round(timestamp, 2))
                    logger.debug("检测到场景变化: %.2fs (similarity=%.3f)", timestamp, similarity)

            prev_hist = hist

        frame_count += 1

    cap.release()
    logger.info("场景变化检测完成: 发现 %d 个变化点", len(changes))
    return changes
