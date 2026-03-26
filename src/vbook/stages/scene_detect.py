import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..utils.scene_detector import detect_scene_changes
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SceneDetectStage(Stage):
    name = "scene_detect"

    def __init__(
        self,
        video_path: Path,
        cache_dir: Path,
        sample_interval: float = 5.0,
        threshold: float = 0.3,
    ):
        self.video_path = video_path
        self.cache_dir = cache_dir
        self.sample_interval = sample_interval
        self.threshold = threshold

    def run(self, context: dict) -> StageResult:
        logger.info("开始场景变化检测: interval=%.1fs threshold=%.2f", self.sample_interval, self.threshold)

        changes = detect_scene_changes(
            str(self.video_path),
            sample_interval=self.sample_interval,
            threshold=self.threshold,
        )

        scene_file = self.cache_dir / "scene_changes.json"
        scene_file.write_text(
            json.dumps({"timestamps": changes}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info("场景变化检测完成: %d 个变化点", len(changes))

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"scene_changes": changes},
        )
