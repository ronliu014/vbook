import json
from pathlib import Path
import ffmpeg as ffmpeg_lib
from ffmpeg import Error as FfmpegError
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        probe = ffmpeg_lib.probe(video_path)
        return float(probe["format"]["duration"])
    except Exception:
        return float("inf")


def _find_nearest_scene_change(timestamp: float, scene_changes: list[float], window: float) -> float | None:
    """Find the nearest scene change within ±window seconds of timestamp."""
    best = None
    best_dist = float("inf")
    for sc in scene_changes:
        dist = abs(sc - timestamp)
        if dist <= window and dist < best_dist:
            best = sc
            best_dist = dist
    return best


def _dedup_timestamps(timestamps: list[float], window: float) -> list[float]:
    """Remove timestamps that are within `window` seconds of each other, keeping the first."""
    if not timestamps:
        return []
    sorted_ts = sorted(timestamps)
    result = [sorted_ts[0]]
    for ts in sorted_ts[1:]:
        if ts - result[-1] >= window:
            result.append(ts)
    return result


class ScreenshotStage(Stage):
    name = "screenshot"

    def __init__(
        self,
        video_path: Path,
        cache_dir: Path,
        search_window: float = 10.0,
        dedup_window: float = 5.0,
    ):
        self.video_path = video_path
        self.cache_dir = cache_dir
        self.search_window = search_window
        self.dedup_window = dedup_window

    def run(self, context: dict) -> StageResult:
        analysis_path = context.get("analysis_path")
        analysis = json.loads(Path(analysis_path).read_text(encoding="utf-8"))

        scene_changes = context.get("scene_changes", [])
        visual_cues = analysis.get("visual_cues", [])

        screenshots_dir = self.cache_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        duration = _get_video_duration(str(self.video_path))

        # Collect all candidate timestamps
        candidates = []

        # 1. From visual_cues: snap to nearest scene change if possible
        for cue in visual_cues:
            ts = cue.get("timestamp", 0)
            snapped = _find_nearest_scene_change(ts, scene_changes, self.search_window)
            if snapped is not None:
                logger.debug("视觉线索 %.1fs → 场景变化 %.1fs", ts, snapped)
                candidates.append(snapped)
            else:
                logger.debug("视觉线索 %.1fs 无附近场景变化，直接使用", ts)
                candidates.append(ts)

        # 2. From outline key_timestamps: snap to nearest scene change
        for section in analysis.get("outline", []):
            for ts in section.get("key_timestamps", []):
                snapped = _find_nearest_scene_change(ts, scene_changes, self.search_window)
                candidates.append(snapped if snapped is not None else ts)

        # 3. Fallback: if no candidates at all, use first scene change or 0
        if not candidates:
            if scene_changes:
                candidates.append(scene_changes[0])
            else:
                candidates.append(0.0)

        # Dedup and filter
        final_timestamps = _dedup_timestamps(candidates, self.dedup_window)
        final_timestamps = [ts for ts in final_timestamps if ts < duration]

        logger.info("截图时间点: %d 个 (来自 %d 个候选)", len(final_timestamps), len(candidates))

        # Take screenshots
        screenshots_map = {}
        for i, ts in enumerate(final_timestamps):
            filename = f"frame_{i:03d}_{ts:.1f}s.jpg"
            output_path = screenshots_dir / filename
            try:
                (
                    ffmpeg_lib
                    .input(str(self.video_path), ss=ts)
                    .output(str(output_path), vframes=1, q=2)
                    .overwrite_output()
                    .run(quiet=True)
                )
                screenshots_map[str(i)] = [filename]
            except FfmpegError:
                logger.warning("截图失败: %.1fs", ts)
                continue

        return StageResult(
            status=StageStatus.SUCCESS,
            output={
                "screenshots_dir": str(screenshots_dir),
                "screenshots_map": screenshots_map,
            },
        )
