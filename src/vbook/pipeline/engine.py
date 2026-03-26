from pathlib import Path
from typing import Any
from rich.progress import Progress, SpinnerColumn, TextColumn
from .stage import Stage, StageResult, StageStatus
from .tracker import ProcessingTracker
from ..utils.retry import with_retry
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PipelineEngine:
    def __init__(self, cache_dir: Path, max_retries: int = 3):
        self.cache_dir = cache_dir
        self.max_retries = max_retries

    def run(self, stages: list[Stage], context: dict) -> dict[str, StageResult]:
        tracker = ProcessingTracker(self.cache_dir)
        results = {}

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            for stage in stages:
                if stage.can_skip(tracker):
                    logger.debug("跳过已完成阶段: %s", stage.name)
                    results[stage.name] = StageResult(
                        status=StageStatus.SKIPPED,
                        output=tracker.get_output(stage.name) or {},
                    )
                    continue

                task = progress.add_task(f"[cyan]{stage.name}...", total=None)
                logger.info("开始阶段: %s", stage.name)
                try:
                    result = with_retry(
                        lambda s=stage: s.run(context),
                        max_retries=self.max_retries,
                    )
                    tracker.mark_complete(stage.name, result.output)
                    context.update(result.output)
                    results[stage.name] = result
                    logger.info("完成阶段: %s", stage.name)
                except Exception as e:
                    tracker.mark_failed(stage.name, str(e))
                    results[stage.name] = StageResult(
                        status=StageStatus.FAILED, error=str(e)
                    )
                    logger.error("阶段失败: %s — %s", stage.name, e)
                    raise
                finally:
                    progress.remove_task(task)

        return results