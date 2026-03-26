import json
from pathlib import Path
import ffmpeg as ffmpeg_lib
from ffmpeg import Error as FfmpegError
from ..pipeline.stage import Stage, StageResult, StageStatus


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        probe = ffmpeg_lib.probe(video_path)
        return float(probe["format"]["duration"])
    except Exception:
        return float("inf")


class ScreenshotStage(Stage):
    name = "screenshot"

    def __init__(self, video_path: Path, cache_dir: Path):
        self.video_path = video_path
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        analysis_path = context.get("analysis_path")
        analysis = json.loads(Path(analysis_path).read_text(encoding="utf-8"))

        screenshots_dir = self.cache_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        duration = _get_video_duration(str(self.video_path))
        screenshots_map = {}

        for i, section in enumerate(analysis.get("outline", [])):
            timestamps = section.get("key_timestamps", [])
            if not timestamps:
                continue

            filenames = []
            for j, timestamp in enumerate(timestamps):
                if timestamp >= duration:
                    continue
                filename = f"section_{i}_frame_{j}.jpg"
                output_path = screenshots_dir / filename
                try:
                    (
                        ffmpeg_lib
                        .input(str(self.video_path), ss=timestamp)
                        .output(str(output_path), vframes=1, q=2)
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    filenames.append(filename)
                except FfmpegError:
                    continue

            if filenames:
                screenshots_map[str(i)] = filenames

        return StageResult(
            status=StageStatus.SUCCESS,
            output={
                "screenshots_dir": str(screenshots_dir),
                "screenshots_map": screenshots_map,
            },
        )
