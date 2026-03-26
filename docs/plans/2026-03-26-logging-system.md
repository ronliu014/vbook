# Logging System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a structured logging system using Python's standard `logging` module, with terminal output and dual-file persistence (per-video output dir + project-level `logs/`), and a `--verbose` flag for DEBUG level.

**Architecture:** A single `src/vbook/utils/logger.py` module exposes `get_logger(name)` and `setup_logging(output_dir, verbose)`. `setup_logging` is called once at CLI entry in `process.py`. All modules replace `console.print` with `logger.info/debug/error`. The `engine.py` and `retry.py` add structured log calls at key boundaries so failures are traceable without reading tracebacks.

**Tech Stack:** Python `logging`, `rich.logging.RichHandler` (already a dependency via rich)

---

### Task 1: Create `src/vbook/utils/logger.py`

**Files:**
- Create: `src/vbook/utils/logger.py`
- Test: `tests/test_logger.py`

**Step 1: Write the failing test**

```python
# tests/test_logger.py
import logging
from pathlib import Path
from vbook.utils.logger import get_logger, setup_logging

def test_get_logger_returns_logger():
    logger = get_logger("vbook.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "vbook.test"

def test_setup_logging_creates_log_file(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    setup_logging(output_dir=output_dir, verbose=False)

    log_file = output_dir / "vbook.log"
    logger = get_logger("vbook.test_file")
    logger.info("test message")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "test message" in content

def test_setup_logging_verbose_sets_debug_level(tmp_path):
    output_dir = tmp_path / "output2"
    output_dir.mkdir()
    setup_logging(output_dir=output_dir, verbose=True)

    root_logger = logging.getLogger("vbook")
    assert root_logger.level == logging.DEBUG

def test_setup_logging_creates_project_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output3"
    output_dir.mkdir()
    setup_logging(output_dir=output_dir, verbose=False)

    project_log = tmp_path / "logs" / "vbook.log"
    assert project_log.exists()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_logger.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'vbook.utils.logger'`

**Step 3: Write minimal implementation**

```python
# src/vbook/utils/logger.py
import logging
from pathlib import Path
from rich.logging import RichHandler

_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(output_dir: Path, verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger("vbook")
    root.setLevel(level)

    # 避免重复添加 handler（多次调用时）
    if root.handlers:
        root.handlers.clear()

    # 终端：rich 格式化
    rich_handler = RichHandler(
        level=level,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    root.addHandler(rich_handler)

    # 输出目录日志（详细，DEBUG 级别）
    output_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        output_dir / "vbook.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(file_handler)

    # 项目根 logs/ 汇总日志（INFO 级别）
    project_log_dir = Path.cwd() / "logs"
    project_log_dir.mkdir(exist_ok=True)
    summary_handler = logging.FileHandler(
        project_log_dir / "vbook.log", encoding="utf-8"
    )
    summary_handler.setLevel(logging.INFO)
    summary_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(summary_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_logger.py -v
```

Expected: 4 PASSED

**Step 5: Commit**

```bash
git add src/vbook/utils/logger.py tests/test_logger.py
git commit -m "feat: add logging utility with dual-file output and verbose flag"
```

---

### Task 2: Wire `setup_logging` into CLI entry point

**Files:**
- Modify: `src/vbook/cli/process.py`

**Step 1: Write the failing test**

```python
# tests/test_cli_process.py — add this test to existing file
def test_process_verbose_flag(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    with patch("vbook.cli.process.PipelineEngine") as MockEngine, \
         patch("vbook.cli.process.setup_logging") as mock_setup:
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video), "--verbose"])

    mock_setup.assert_called_once()
    call_kwargs = mock_setup.call_args
    assert call_kwargs.kwargs.get("verbose") is True or call_kwargs.args[1] is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_cli_process.py::test_process_verbose_flag -v
```

Expected: FAIL — `setup_logging` not imported or `--verbose` option missing

**Step 3: Modify `process.py`**

Add import at top (after existing imports):
```python
from vbook.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)
```

Add `--verbose` option to the `process` command:
```python
@click.option("--verbose", "-v", is_flag=True, help="显示详细日志（DEBUG 级别）")
def process(target, output, config, force, verbose):
    """处理视频文件或目录"""
    target_path = Path(target)
    cfg = load_config(config_path=Path(config) if config else None)
    # setup_logging 需要 output_dir，先用临时占位，在 _process_single 内调用
    ...
```

Because `output_dir` is resolved per-video inside `_process_single`, call `setup_logging` there:

In `_process_single`, add `verbose` parameter and call at top:
```python
def _process_single(video_path: Path, output: str, cfg, force: bool, verbose: bool = False):
    output_root = Path(output) if output else (cfg.output.root or video_path.parent / "vbook_output")
    source_root = video_path.parent
    output_dir = resolve_output_dir(video_path, source_root, output_root)
    cache_dir = get_cache_dir(output_dir, cfg.processing.intermediate_dir)

    setup_logging(output_dir=output_dir, verbose=verbose)
    logger.info("开始处理: %s", video_path.name)
    ...
    engine.run(stages, context={"video_path": str(video_path)})
    logger.info("完成: %s", output_dir / "summary.md")
```

Remove the two `console.print` lines in `_process_single` (replaced by logger calls above).

Also pass `verbose` from `process()` to `_process_single()`:
```python
_process_single(target_path, output, cfg, force, verbose)
# and in the loop:
_process_single(video, output, cfg, force, verbose)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_cli_process.py -v
```

Expected: all PASSED

**Step 5: Commit**

```bash
git add src/vbook/cli/process.py tests/test_cli_process.py
git commit -m "feat: wire setup_logging into process CLI, add --verbose flag"
```

---

### Task 3: Add logging to `PipelineEngine` and `with_retry`

**Files:**
- Modify: `src/vbook/pipeline/engine.py`
- Modify: `src/vbook/utils/retry.py`

**Step 1: Write the failing test**

```python
# tests/test_pipeline.py — add these tests to existing file
import logging
from unittest.mock import MagicMock, patch

def test_engine_logs_stage_start_and_complete(tmp_path, caplog):
    from vbook.pipeline.engine import PipelineEngine
    from vbook.pipeline.stage import Stage, StageResult, StageStatus

    class FakeStage(Stage):
        name = "fake"
        def run(self, context):
            return StageResult(status=StageStatus.SUCCESS, output={})
        def can_skip(self, tracker):
            return False

    with caplog.at_level(logging.DEBUG, logger="vbook"):
        engine = PipelineEngine(cache_dir=tmp_path)
        engine.run([FakeStage()], context={})

    messages = [r.message for r in caplog.records]
    assert any("fake" in m for m in messages)

def test_retry_logs_on_failure(caplog):
    from vbook.utils.retry import with_retry

    attempts = []
    def flaky():
        attempts.append(1)
        if len(attempts) < 2:
            raise ValueError("transient error")
        return "ok"

    with caplog.at_level(logging.WARNING, logger="vbook"):
        result = with_retry(flaky, max_retries=3, base_delay=0)

    assert result == "ok"
    assert any("transient error" in r.message for r in caplog.records)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_pipeline.py -v -k "logs"
```

Expected: FAIL — no log records captured

**Step 3: Modify `engine.py`**

```python
# src/vbook/pipeline/engine.py
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
```

**Step 4: Modify `retry.py`**

```python
# src/vbook/utils/retry.py
import time
from typing import Callable, TypeVar
from .logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")

def with_retry(fn: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0) -> T:
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = base_delay * (2 ** attempt)
                logger.warning(
                    "第 %d/%d 次重试失败: %s，%.1fs 后重试",
                    attempt + 1, max_retries, e, wait
                )
                time.sleep(wait)
    raise last_error
```

**Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_pipeline.py -v
```

Expected: all PASSED

**Step 6: Commit**

```bash
git add src/vbook/pipeline/engine.py src/vbook/utils/retry.py tests/test_pipeline.py
git commit -m "feat: add structured logging to pipeline engine and retry utility"
```

---

### Task 4: Add logging to `LiteLLMBackend`

**Files:**
- Modify: `src/vbook/backends/llm/litellm_backend.py`

**Step 1: Write the failing test**

```python
# tests/test_backends.py — add to existing file
import logging
from unittest.mock import patch, MagicMock

def test_litellm_backend_logs_model_and_url(caplog):
    from vbook.backends.llm.litellm_backend import LiteLLMBackend

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"title": "test"}'

    with patch("litellm.completion", return_value=mock_response), \
         caplog.at_level(logging.DEBUG, logger="vbook"):
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b", base_url="http://localhost:7866")
        backend.analyze("some text", "some prompt")

    messages = [r.message for r in caplog.records]
    assert any("qwen3.5:9b" in m or "7866" in m for m in messages)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_backends.py::test_litellm_backend_logs_model_and_url -v
```

Expected: FAIL — no log records

**Step 3: Modify `litellm_backend.py`**

```python
# src/vbook/backends/llm/litellm_backend.py
import litellm
from ..base import LLMBackend
from ...utils.logger import get_logger

logger = get_logger(__name__)

class LiteLLMBackend(LLMBackend):
    def __init__(self, model: str, base_url: str = None):
        self.model = model
        self.base_url = base_url

    def analyze(self, text: str, prompt: str) -> str:
        logger.debug("调用 LLM: model=%s base_url=%s text_len=%d", self.model, self.base_url, len(text))
        kwargs = {"model": self.model, "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]}
        if self.base_url:
            kwargs["api_base"] = self.base_url
        response = litellm.completion(**kwargs)
        return response.choices[0].message.content
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_backends.py -v
```

Expected: all PASSED

**Step 5: Commit**

```bash
git add src/vbook/backends/llm/litellm_backend.py tests/test_backends.py
git commit -m "feat: add debug logging to LiteLLM backend"
```

---

### Task 5: Full regression

**Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: all PASSED, no warnings about missing handlers

**Step 2: Smoke test CLI**

```bash
python src/vbook/cli/process.py --help
```

Expected: `--verbose` option visible in help output

**Step 3: Verify log files created**

After a real or mock run, check:
- `<output_dir>/vbook.log` exists and contains DEBUG entries
- `logs/vbook.log` exists and contains INFO entries only
