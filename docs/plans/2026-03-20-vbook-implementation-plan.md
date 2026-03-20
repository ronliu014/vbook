# vbook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that converts video content into structured knowledge documents (Markdown with images, mind maps).

**Architecture:** Single Python package with modular pipeline stages, pluggable backends for STT/LLM/Visual, config-driven with CLI > project config > global config priority.

**Tech Stack:** Python 3.11+, uv, Click, Pydantic, FFmpeg, faster-whisper, litellm, OpenCV, Rich, pytest

---

## Phase 1: 项目骨架和配置系统

### Task 1: 初始化项目结构

**Files:**
- Create: `pyproject.toml`
- Create: `src/vbook/__init__.py`
- Create: `src/vbook/cli/__init__.py`
- Create: `src/vbook/cli/main.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: 初始化 uv 项目**

```bash
cd E:/projects/my_app/vbook
uv init --name vbook --python 3.11
uv add click rich pydantic pyyaml
uv add --dev pytest pytest-cov
```

**Step 2: 创建 pyproject.toml 入口配置**

在 `pyproject.toml` 中添加：
```toml
[project.scripts]
vbook = "vbook.cli.main:cli"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 3: 创建 CLI 骨架**

```python
# src/vbook/cli/main.py
import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """vbook - 将视频转换为知识文档"""
    pass
```

**Step 4: 写测试验证 CLI 可运行**

```python
# tests/test_cli.py
from click.testing import CliRunner
from vbook.cli.main import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "vbook" in result.output

def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
```

**Step 5: 运行测试**

```bash
uv run pytest tests/test_cli.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git init
git add .
git commit -m "feat: initialize vbook project with CLI skeleton"
```

---

### Task 2: 配置系统

**Files:**
- Create: `src/vbook/config/__init__.py`
- Create: `src/vbook/config/schema.py`
- Create: `src/vbook/config/loader.py`
- Create: `src/vbook/config/defaults.py`
- Create: `tests/test_config.py`

**Step 1: 写失败测试**

```python
# tests/test_config.py
import pytest
from pathlib import Path
from vbook.config.loader import load_config

def test_load_default_config():
    config = load_config()
    assert config.processing.intermediate_dir == ".vbook_cache"
    assert config.output.structure == "mirror"

def test_config_from_yaml(tmp_path):
    config_file = tmp_path / "vbook.yaml"
    config_file.write_text("""
output:
  root: /tmp/output
  structure: mirror
backends:
  stt: whisper_local
  llm: ollama_qwen
""")
    config = load_config(config_path=config_file)
    assert str(config.output.root) == "/tmp/output"
    assert config.backends.stt == "whisper_local"

def test_cli_args_override_config(tmp_path):
    config_file = tmp_path / "vbook.yaml"
    config_file.write_text("backends:\n  stt: whisper_local\n")
    config = load_config(config_path=config_file, overrides={"backends.stt": "cloud_api"})
    assert config.backends.stt == "cloud_api"
```

**Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_config.py -v
```
Expected: FAIL with ImportError

**Step 3: 实现配置 Schema**

```python
# src/vbook/config/schema.py
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class SourceConfig(BaseModel):
    video_dirs: list[Path] = Field(default_factory=list)

class OutputConfig(BaseModel):
    root: Optional[Path] = None
    structure: str = "mirror"

class ProcessingConfig(BaseModel):
    intermediate_dir: str = ".vbook_cache"
    keep_intermediate: bool = True
    max_retries: int = 3

class BackendsConfig(BaseModel):
    stt: str = "whisper_local"
    llm: str = "ollama_qwen"
    whisper_local: dict = Field(default_factory=lambda: {"model": "medium", "device": "cpu"})
    ollama_qwen: dict = Field(default_factory=lambda: {"base_url": "http://localhost:11434", "model": "qwen2.5:14b"})

class VbookConfig(BaseModel):
    source: SourceConfig = Field(default_factory=SourceConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    backends: BackendsConfig = Field(default_factory=BackendsConfig)
```

**Step 4: 实现配置加载器**

```python
# src/vbook/config/loader.py
from pathlib import Path
from typing import Optional
import yaml
from .schema import VbookConfig

def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(
    config_path: Optional[Path] = None,
    overrides: Optional[dict] = None,
) -> VbookConfig:
    data = {}

    # 全局配置
    global_config = Path.home() / ".vbook" / "config.yaml"
    if global_config.exists():
        data = yaml.safe_load(global_config.read_text()) or {}

    # 项目配置
    if config_path and config_path.exists():
        project_data = yaml.safe_load(config_path.read_text()) or {}
        data = _deep_merge(data, project_data)

    # CLI 参数覆盖（dot-notation: "backends.stt" -> {"backends": {"stt": ...}}）
    if overrides:
        for key, value in overrides.items():
            parts = key.split(".")
            d = data
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value

    return VbookConfig(**data)
```

**Step 5: 运行测试，确认通过**

```bash
uv run pytest tests/test_config.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add src/vbook/config/ tests/test_config.py
git commit -m "feat: add config system with Pydantic schema and YAML loader"
```

---

### Task 3: 路径映射工具

**Files:**
- Create: `src/vbook/utils/__init__.py`
- Create: `src/vbook/utils/path.py`
- Create: `tests/test_utils_path.py`

**Step 1: 写失败测试**

```python
# tests/test_utils_path.py
from pathlib import Path
from vbook.utils.path import resolve_output_dir, get_cache_dir

def test_mirror_structure():
    source_root = Path("/videos")
    output_root = Path("/output")
    video = Path("/videos/course1/lesson1.mp4")
    result = resolve_output_dir(video, source_root, output_root, structure="mirror")
    assert result == Path("/output/course1/lesson1")

def test_mirror_nested():
    source_root = Path("/videos")
    output_root = Path("/output")
    video = Path("/videos/course1/section2/lesson3.mp4")
    result = resolve_output_dir(video, source_root, output_root, structure="mirror")
    assert result == Path("/output/course1/section2/lesson3")

def test_get_cache_dir():
    output_dir = Path("/output/course1/lesson1")
    cache = get_cache_dir(output_dir, ".vbook_cache")
    assert cache == Path("/output/course1/lesson1/.vbook_cache")
```

**Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_utils_path.py -v
```

**Step 3: 实现路径工具**

```python
# src/vbook/utils/path.py
from pathlib import Path

def resolve_output_dir(
    video_path: Path,
    source_root: Path,
    output_root: Path,
    structure: str = "mirror",
) -> Path:
    relative = video_path.relative_to(source_root)
    stem_path = relative.parent / relative.stem
    return output_root / stem_path

def get_cache_dir(output_dir: Path, cache_dir_name: str = ".vbook_cache") -> Path:
    return output_dir / cache_dir_name
```

**Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_utils_path.py -v
```

**Step 5: Commit**

```bash
git add src/vbook/utils/ tests/test_utils_path.py
git commit -m "feat: add path mapping utility for mirror directory structure"
```

---

## Phase 2: Pipeline 引擎

### Task 4: Stage 基类和状态追踪

**Files:**
- Create: `src/vbook/pipeline/__init__.py`
- Create: `src/vbook/pipeline/stage.py`
- Create: `src/vbook/pipeline/tracker.py`
- Create: `tests/test_pipeline.py`

**Step 1: 写失败测试**

```python
# tests/test_pipeline.py
import pytest
from pathlib import Path
from vbook.pipeline.stage import Stage, StageResult, StageStatus
from vbook.pipeline.tracker import ProcessingTracker

def test_stage_result_success():
    result = StageResult(status=StageStatus.SUCCESS, output={"key": "value"})
    assert result.status == StageStatus.SUCCESS
    assert result.output["key"] == "value"

def test_tracker_save_and_load(tmp_path):
    tracker = ProcessingTracker(tmp_path / ".vbook_cache")
    tracker.mark_complete("audio_extract", {"audio_path": "/tmp/audio.wav"})

    tracker2 = ProcessingTracker(tmp_path / ".vbook_cache")
    assert tracker2.is_complete("audio_extract")
    assert tracker2.get_output("audio_extract")["audio_path"] == "/tmp/audio.wav"

def test_tracker_incomplete_stage(tmp_path):
    tracker = ProcessingTracker(tmp_path / ".vbook_cache")
    assert not tracker.is_complete("audio_extract")
    assert tracker.get_output("audio_extract") is None
```

**Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_pipeline.py -v
```

**Step 3: 实现 Stage 基类**

```python
# src/vbook/pipeline/stage.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageResult:
    status: StageStatus
    output: dict = field(default_factory=dict)
    error: Optional[str] = None

class Stage(ABC):
    name: str

    @abstractmethod
    def run(self, context: dict) -> StageResult:
        pass

    def can_skip(self, tracker) -> bool:
        return tracker.is_complete(self.name)
```

**Step 4: 实现状态追踪器**

```python
# src/vbook/pipeline/tracker.py
from pathlib import Path
from typing import Any, Optional
import yaml

class ProcessingTracker:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.status_file = cache_dir / "status.yaml"
        self._data = self._load()

    def _load(self) -> dict:
        if self.status_file.exists():
            return yaml.safe_load(self.status_file.read_text()) or {}
        return {}

    def _save(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(yaml.dump(self._data))

    def mark_complete(self, stage_name: str, output: dict):
        self._data[stage_name] = {"status": "success", "output": output}
        self._save()

    def mark_failed(self, stage_name: str, error: str):
        self._data[stage_name] = {"status": "failed", "error": error}
        self._save()

    def is_complete(self, stage_name: str) -> bool:
        return self._data.get(stage_name, {}).get("status") == "success"

    def get_output(self, stage_name: str) -> Optional[dict]:
        entry = self._data.get(stage_name, {})
        if entry.get("status") == "success":
            return entry.get("output")
        return None
```

**Step 5: 运行测试，确认通过**

```bash
uv run pytest tests/test_pipeline.py -v
```

**Step 6: Commit**

```bash
git add src/vbook/pipeline/ tests/test_pipeline.py
git commit -m "feat: add pipeline stage base class and processing tracker"
```

---

### Task 5: Pipeline 引擎（编排 + 重试）

**Files:**
- Create: `src/vbook/pipeline/engine.py`
- Create: `src/vbook/utils/retry.py`
- Modify: `tests/test_pipeline.py`

**Step 1: 补充测试**

```python
# 追加到 tests/test_pipeline.py
from vbook.pipeline.engine import PipelineEngine

class MockStage(Stage):
    name = "mock_stage"
    call_count = 0

    def run(self, context: dict) -> StageResult:
        self.call_count += 1
        return StageResult(status=StageStatus.SUCCESS, output={"done": True})

class FailThenSucceedStage(Stage):
    name = "flaky_stage"
    call_count = 0

    def run(self, context: dict) -> StageResult:
        self.call_count += 1
        if self.call_count < 3:
            raise RuntimeError("Transient error")
        return StageResult(status=StageStatus.SUCCESS, output={"done": True})

def test_engine_runs_stages(tmp_path):
    stage = MockStage()
    engine = PipelineEngine(cache_dir=tmp_path / ".vbook_cache", max_retries=1)
    results = engine.run([stage], context={})
    assert results["mock_stage"].status == StageStatus.SUCCESS

def test_engine_skips_completed(tmp_path):
    cache_dir = tmp_path / ".vbook_cache"
    tracker = ProcessingTracker(cache_dir)
    tracker.mark_complete("mock_stage", {"done": True})

    stage = MockStage()
    engine = PipelineEngine(cache_dir=cache_dir, max_retries=1)
    engine.run([stage], context={})
    assert stage.call_count == 0

def test_engine_retries_on_failure(tmp_path):
    stage = FailThenSucceedStage()
    engine = PipelineEngine(cache_dir=tmp_path / ".vbook_cache", max_retries=3)
    results = engine.run([stage], context={})
    assert results["flaky_stage"].status == StageStatus.SUCCESS
    assert stage.call_count == 3
```

**Step 2: 实现重试工具**

```python
# src/vbook/utils/retry.py
import time
from typing import Callable, TypeVar

T = TypeVar("T")

def with_retry(fn: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0) -> T:
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error
```

**Step 3: 实现 Pipeline 引擎**

```python
# src/vbook/pipeline/engine.py
from pathlib import Path
from typing import Any
from rich.progress import Progress, SpinnerColumn, TextColumn
from .stage import Stage, StageResult, StageStatus
from .tracker import ProcessingTracker
from ..utils.retry import with_retry

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
                    results[stage.name] = StageResult(
                        status=StageStatus.SKIPPED,
                        output=tracker.get_output(stage.name) or {},
                    )
                    continue

                task = progress.add_task(f"[cyan]{stage.name}...", total=None)
                try:
                    result = with_retry(
                        lambda s=stage: s.run(context),
                        max_retries=self.max_retries,
                    )
                    tracker.mark_complete(stage.name, result.output)
                    context.update(result.output)
                    results[stage.name] = result
                except Exception as e:
                    tracker.mark_failed(stage.name, str(e))
                    results[stage.name] = StageResult(
                        status=StageStatus.FAILED, error=str(e)
                    )
                    raise
                finally:
                    progress.remove_task(task)

        return results
```

**Step 4: 运行测试**

```bash
uv run pytest tests/test_pipeline.py -v
```

**Step 5: Commit**

```bash
git add src/vbook/pipeline/engine.py src/vbook/utils/retry.py tests/test_pipeline.py
git commit -m "feat: add pipeline engine with retry and skip-completed logic"
```

---

## Phase 3: Backend 抽象层

### Task 6: Backend 抽象基类

**Files:**
- Create: `src/vbook/backends/__init__.py`
- Create: `src/vbook/backends/base.py`
- Create: `tests/test_backends.py`

**Step 1: 写测试**

```python
# tests/test_backends.py
from vbook.backends.base import STTBackend, LLMBackend, TranscriptResult, TranscriptSegment

def test_transcript_result_to_text():
    result = TranscriptResult(segments=[
        TranscriptSegment(start=0.0, end=5.0, text="你好世界"),
        TranscriptSegment(start=5.0, end=10.0, text="这是测试"),
    ])
    assert "你好世界" in result.full_text
    assert "这是测试" in result.full_text

def test_transcript_result_segments():
    result = TranscriptResult(segments=[
        TranscriptSegment(start=0.0, end=5.0, text="Hello"),
    ])
    assert result.segments[0].start == 0.0
    assert result.segments[0].text == "Hello"
```

**Step 2: 实现抽象基类**

```python
# src/vbook/backends/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

@dataclass
class TranscriptResult:
    segments: list[TranscriptSegment] = field(default_factory=list)
    language: str = "zh"

    @property
    def full_text(self) -> str:
        return "\n".join(seg.text for seg in self.segments)

class STTBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptResult:
        pass

class LLMBackend(ABC):
    @abstractmethod
    def analyze(self, text: str, prompt: str) -> str:
        pass

    def analyze_image(self, image_path: str, prompt: str) -> str:
        raise NotImplementedError("This backend does not support image analysis")
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_backends.py -v
```

**Step 4: Commit**

```bash
git add src/vbook/backends/ tests/test_backends.py
git commit -m "feat: add STT and LLM backend abstract base classes"
```

---

## Phase 4: 核心处理阶段

### Task 7: Stage 1 - 音频提取

**Files:**
- Create: `src/vbook/stages/__init__.py`
- Create: `src/vbook/stages/audio_extract.py`
- Create: `tests/test_stages.py`

**Step 1: 安装依赖**

```bash
uv add ffmpeg-python
```

**Step 2: 写失败测试**

```python
# tests/test_stages.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from vbook.stages.audio_extract import AudioExtractStage
from vbook.pipeline.stage import StageStatus

def test_audio_extract_success(tmp_path):
    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake video content")
    output_dir = tmp_path / ".vbook_cache"

    with patch("ffmpeg.input") as mock_input:
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.audio.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = AudioExtractStage(video_path=video_file, cache_dir=output_dir)
        result = stage.run(context={})

    assert result.status == StageStatus.SUCCESS
    assert "audio_path" in result.output

def test_audio_extract_sets_correct_path(tmp_path):
    video_file = tmp_path / "lesson1.mp4"
    video_file.write_bytes(b"fake")
    cache_dir = tmp_path / ".vbook_cache"

    with patch("ffmpeg.input") as mock_input:
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.audio.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = AudioExtractStage(video_path=video_file, cache_dir=cache_dir)
        result = stage.run(context={})

    assert result.output["audio_path"].endswith("audio.wav")
```

**Step 3: 实现音频提取阶段**

```python
# src/vbook/stages/audio_extract.py
from pathlib import Path
import ffmpeg
from ..pipeline.stage import Stage, StageResult, StageStatus

class AudioExtractStage(Stage):
    name = "audio_extract"

    def __init__(self, video_path: Path, cache_dir: Path):
        self.video_path = video_path
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.cache_dir / "audio.wav"

        (
            ffmpeg
            .input(str(self.video_path))
            .audio
            .output(str(audio_path), acodec="pcm_s16le", ar=16000, ac=1)
            .overwrite_output()
            .run(quiet=True)
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"audio_path": str(audio_path)},
        )
```

**Step 4: 运行测试**

```bash
uv run pytest tests/test_stages.py -v
```

**Step 5: Commit**

```bash
git add src/vbook/stages/ tests/test_stages.py
git commit -m "feat: add audio extraction stage using ffmpeg"
```

---

### Task 8: Stage 2 - Whisper 语音转录

**Files:**
- Create: `src/vbook/backends/stt/__init__.py`
- Create: `src/vbook/backends/stt/whisper.py`
- Create: `src/vbook/stages/transcribe.py`
- Modify: `tests/test_stages.py`

**Step 1: 安装依赖**

```bash
uv add faster-whisper
```

**Step 2: 写 Whisper Backend 测试**

```python
# 追加到 tests/test_stages.py
from unittest.mock import patch, MagicMock
from vbook.backends.stt.whisper import WhisperSTTBackend
from vbook.backends.base import TranscriptResult

def test_whisper_backend_returns_transcript():
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "  你好世界  "

    with patch("faster_whisper.WhisperModel") as MockModel:
        instance = MockModel.return_value
        instance.transcribe.return_value = ([mock_segment], MagicMock(language="zh"))

        backend = WhisperSTTBackend(model="small", device="cpu")
        result = backend.transcribe("/tmp/audio.wav")

    assert isinstance(result, TranscriptResult)
    assert result.segments[0].text == "你好世界"
    assert result.language == "zh"
```

**Step 3: 实现 Whisper Backend**

```python
# src/vbook/backends/stt/whisper.py
from faster_whisper import WhisperModel
from ..base import STTBackend, TranscriptResult, TranscriptSegment

class WhisperSTTBackend(STTBackend):
    def __init__(self, model: str = "medium", device: str = "cpu"):
        self.model = WhisperModel(model, device=device)

    def transcribe(self, audio_path: str) -> TranscriptResult:
        segments, info = self.model.transcribe(audio_path, language="zh")
        return TranscriptResult(
            segments=[
                TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
                for s in segments
            ],
            language=info.language,
        )
```

**Step 4: 实现转录阶段**

```python
# src/vbook/stages/transcribe.py
import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import STTBackend

class TranscribeStage(Stage):
    name = "transcribe"

    def __init__(self, stt_backend: STTBackend, cache_dir: Path):
        self.stt_backend = stt_backend
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        audio_path = context.get("audio_path")
        if not audio_path:
            raise ValueError("audio_path not found in context")

        result = self.stt_backend.transcribe(audio_path)

        transcript_path = self.cache_dir / "transcript.json"
        transcript_data = {
            "language": result.language,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in result.segments
            ],
            "full_text": result.full_text,
        }
        transcript_path.write_text(
            json.dumps(transcript_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"transcript_path": str(transcript_path), "language": result.language},
        )
```

**Step 5: 运行测试**

```bash
uv run pytest tests/test_stages.py -v
```

**Step 6: Commit**

```bash
git add src/vbook/backends/stt/ src/vbook/stages/transcribe.py tests/test_stages.py
git commit -m "feat: add Whisper STT backend and transcribe stage"
```

---

### Task 9: Stage 3 - LLM 内容分析

**Files:**
- Create: `src/vbook/backends/llm/__init__.py`
- Create: `src/vbook/backends/llm/litellm_backend.py`
- Create: `src/vbook/stages/analyze.py`
- Create: `src/vbook/output/prompts.py`

**Step 1: 安装依赖**

```bash
uv add litellm
```

**Step 2: 写测试**

```python
# 追加到 tests/test_stages.py
from vbook.backends.llm.litellm_backend import LiteLLMBackend
from vbook.stages.analyze import AnalyzeStage
import json

def test_llm_backend_analyze():
    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"outline": []}'))]
        )
        backend = LiteLLMBackend(model="ollama/qwen2.5:14b", base_url="http://localhost:11434")
        result = backend.analyze("some text", "generate outline")
    assert result == '{"outline": []}'

def test_analyze_stage_outputs_json(tmp_path):
    transcript_file = tmp_path / "transcript.json"
    transcript_file.write_text(
        json.dumps({"full_text": "这是测试内容", "segments": [], "language": "zh"}),
        encoding="utf-8"
    )

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                "title": "测试视频",
                "outline": [{"title": "第一节", "summary": "内容", "key_timestamps": [0]}],
                "keywords": ["测试"],
            })))]
        )
        backend = LiteLLMBackend(model="ollama/qwen2.5:14b")
        stage = AnalyzeStage(llm_backend=backend, cache_dir=tmp_path)
        result = stage.run(context={"transcript_path": str(transcript_file)})

    assert result.status == StageStatus.SUCCESS
    assert "analysis_path" in result.output
```

**Step 3: 实现 LiteLLM Backend**

```python
# src/vbook/backends/llm/litellm_backend.py
import litellm
from ..base import LLMBackend

class LiteLLMBackend(LLMBackend):
    def __init__(self, model: str, base_url: str = None):
        self.model = model
        self.base_url = base_url

    def analyze(self, text: str, prompt: str) -> str:
        kwargs = {"model": self.model, "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]}
        if self.base_url:
            kwargs["api_base"] = self.base_url
        response = litellm.completion(**kwargs)
        return response.choices[0].message.content
```

**Step 4: 实现分析阶段（含Prompt）**

```python
# src/vbook/output/prompts.py
ANALYZE_PROMPT = """你是一个专业的视频内容分析助手。
请分析以下视频转录文本，提取知识大纲。

请返回严格的JSON格式，结构如下：
{
  "title": "视频主题标题",
  "outline": [
    {
      "title": "章节标题",
      "summary": "章节摘要",
      "key_timestamps": [开始时间(秒)]
    }
  ],
  "keywords": ["关键词1", "关键词2"]
}

只返回JSON，不要其他文字。"""
```

```python
# src/vbook/stages/analyze.py
import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import LLMBackend
from ..output.prompts import ANALYZE_PROMPT

class AnalyzeStage(Stage):
    name = "analyze"

    def __init__(self, llm_backend: LLMBackend, cache_dir: Path):
        self.llm_backend = llm_backend
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        transcript_path = context.get("transcript_path")
        transcript_data = json.loads(Path(transcript_path).read_text(encoding="utf-8"))

        raw = self.llm_backend.analyze(transcript_data["full_text"], ANALYZE_PROMPT)

        # 提取JSON（防止LLM返回markdown代码块）
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        analysis = json.loads(raw)
        analysis_path = self.cache_dir / "analysis.json"
        analysis_path.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"analysis_path": str(analysis_path)},
        )
```

**Step 5: 运行测试**

```bash
uv run pytest tests/test_stages.py -v
```

**Step 6: Commit**

```bash
git add src/vbook/backends/llm/ src/vbook/stages/analyze.py src/vbook/output/prompts.py
git commit -m "feat: add LiteLLM backend and content analysis stage"
```

---

### Task 10: Stage 5 - Markdown 生成

**Files:**
- Create: `src/vbook/output/__init__.py`
- Create: `src/vbook/output/markdown.py`
- Create: `src/vbook/output/templates/summary.md.j2`
- Create: `src/vbook/stages/generate.py`
- Create: `tests/test_output.py`

**Step 1: 安装依赖**

```bash
uv add jinja2
```

**Step 2: 写测试**

```python
# tests/test_output.py
import json
from pathlib import Path
from vbook.output.markdown import MarkdownGenerator
from vbook.stages.generate import GenerateStage
from vbook.pipeline.stage import StageStatus

def test_markdown_generation(tmp_path):
    analysis = {
        "title": "Python入门教程",
        "outline": [
            {"title": "变量和类型", "summary": "介绍Python基本数据类型", "key_timestamps": [60]},
        ],
        "keywords": ["Python", "变量"],
    }

    gen = MarkdownGenerator()
    md = gen.render(analysis, assets_dir=Path("assets"))

    assert "# Python入门教程" in md
    assert "变量和类型" in md
    assert "Python" in md

def test_generate_stage_creates_file(tmp_path):
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "title": "测试视频",
        "outline": [{"title": "第一节", "summary": "摘要", "key_timestamps": [0]}],
        "keywords": ["测试"],
    }), encoding="utf-8")

    output_dir = tmp_path / "output"
    stage = GenerateStage(output_dir=output_dir, cache_dir=tmp_path)
    result = stage.run(context={"analysis_path": str(analysis_file)})

    assert result.status == StageStatus.SUCCESS
    assert Path(result.output["markdown_path"]).exists()
```

**Step 3: 创建 Jinja2 模板**

```jinja2
{# src/vbook/output/templates/summary.md.j2 #}
# {{ analysis.title }}

**关键词：** {{ analysis.keywords | join(", ") }}

---

## 知识大纲

{% for section in analysis.outline %}
### {{ loop.index }}. {{ section.title }}

{{ section.summary }}

{% if section.screenshots %}
{% for shot in section.screenshots %}
![{{ section.title }}]({{ assets_dir }}/{{ shot }})
{% endfor %}
{% endif %}

{% endfor %}
```

**Step 4: 实现 Markdown 生成器**

```python
# src/vbook/output/markdown.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class MarkdownGenerator:
    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def render(self, analysis: dict, assets_dir: Path = Path("assets")) -> str:
        template = self.env.get_template("summary.md.j2")
        return template.render(analysis=analysis, assets_dir=assets_dir)
```

**Step 5: 实现生成阶段**

```python
# src/vbook/stages/generate.py
import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..output.markdown import MarkdownGenerator

class GenerateStage(Stage):
    name = "generate"

    def __init__(self, output_dir: Path, cache_dir: Path):
        self.output_dir = output_dir
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        analysis_path = context.get("analysis_path")
        analysis = json.loads(Path(analysis_path).read_text(encoding="utf-8"))

        self.output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        gen = MarkdownGenerator()
        md_content = gen.render(analysis, assets_dir=Path("assets"))

        md_path = self.output_dir / "summary.md"
        md_path.write_text(md_content, encoding="utf-8")

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"markdown_path": str(md_path)},
        )
```

**Step 6: 运行测试**

```bash
uv run pytest tests/test_output.py -v
```

**Step 7: Commit**

```bash
git add src/vbook/output/ src/vbook/stages/generate.py tests/test_output.py
git commit -m "feat: add Markdown generation stage with Jinja2 template"
```

---

## Phase 5: CLI 命令集成

### Task 11: `vbook process` 命令

**Files:**
- Modify: `src/vbook/cli/main.py`
- Create: `src/vbook/cli/process.py`
- Create: `tests/test_cli_process.py`

**Step 1: 写测试**

```python
# tests/test_cli_process.py
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from vbook.cli.main import cli

def test_process_single_video(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    with patch("vbook.cli.process.PipelineEngine") as MockEngine:
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video), "--output", str(tmp_path)])

    assert result.exit_code == 0

def test_process_missing_video():
    runner = CliRunner()
    result = runner.invoke(cli, ["process", "/nonexistent/video.mp4"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or result.exit_code == 2
```

**Step 2: 实现 process 命令**

```python
# src/vbook/cli/process.py
from pathlib import Path
import click
from rich.console import Console
from ..config.loader import load_config
from ..pipeline.engine import PipelineEngine
from ..utils.path import resolve_output_dir, get_cache_dir
from ..backends.stt.whisper import WhisperSTTBackend
from ..backends.llm.litellm_backend import LiteLLMBackend
from ..stages.audio_extract import AudioExtractStage
from ..stages.transcribe import TranscribeStage
from ..stages.analyze import AnalyzeStage
from ..stages.generate import GenerateStage

console = Console()

@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="输出目录")
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
@click.option("--force", "-f", is_flag=True, help="强制重新处理所有阶段")
def process(target, output, config, force):
    """处理视频文件或目录"""
    target_path = Path(target)
    cfg = load_config(config_path=Path(config) if config else None)

    if target_path.is_file():
        _process_single(target_path, output, cfg, force)
    elif target_path.is_dir():
        videos = list(target_path.rglob("*.mp4")) + list(target_path.rglob("*.mkv"))
        console.print(f"[cyan]找到 {len(videos)} 个视频文件[/cyan]")
        for video in videos:
            _process_single(video, output, cfg, force)
    else:
        raise click.ClickException(f"Target not found: {target}")

def _process_single(video_path: Path, output: str, cfg, force: bool):
    output_root = Path(output) if output else (cfg.output.root or video_path.parent / "vbook_output")
    source_root = video_path.parent
    output_dir = resolve_output_dir(video_path, source_root, output_root)
    cache_dir = get_cache_dir(output_dir, cfg.processing.intermediate_dir)

    if force and cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)

    stt = WhisperSTTBackend(**cfg.backends.whisper_local)
    llm = LiteLLMBackend(
        model=f"ollama/{cfg.backends.ollama_qwen['model']}",
        base_url=cfg.backends.ollama_qwen.get("base_url"),
    )

    stages = [
        AudioExtractStage(video_path=video_path, cache_dir=cache_dir),
        TranscribeStage(stt_backend=stt, cache_dir=cache_dir),
        AnalyzeStage(llm_backend=llm, cache_dir=cache_dir),
        GenerateStage(output_dir=output_dir, cache_dir=cache_dir),
    ]

    engine = PipelineEngine(cache_dir=cache_dir, max_retries=cfg.processing.max_retries)
    console.print(f"[green]处理: {video_path.name}[/green]")
    engine.run(stages, context={"video_path": str(video_path)})
    console.print(f"[green]完成: {output_dir / 'summary.md'}[/green]")
```

**Step 3: 注册命令到 CLI**

```python
# src/vbook/cli/main.py (更新)
import click
from rich.console import Console
from .process import process

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """vbook - 将视频转换为知识文档"""
    pass

cli.add_command(process)
```

**Step 4: 运行测试**

```bash
uv run pytest tests/test_cli_process.py -v
```

**Step 5: 端到端手动测试**

```bash
# 安装到开发环境
uv pip install -e .

# 测试帮助
vbook --help
vbook process --help
```

**Step 6: Commit**

```bash
git add src/vbook/cli/ tests/test_cli_process.py
git commit -m "feat: add vbook process CLI command with full pipeline integration"
```

---

## Phase 6: 完善工具命令

### Task 12: `vbook init` 和 `vbook status` 命令

**Files:**
- Create: `src/vbook/cli/init_cmd.py`
- Create: `src/vbook/cli/status.py`
- Modify: `src/vbook/cli/main.py`

**Step 1: 实现 init 命令**

```python
# src/vbook/cli/init_cmd.py
from pathlib import Path
import click
import yaml
from rich.console import Console

console = Console()

@click.command("init")
@click.option("--source", "-s", required=True, type=click.Path(), help="视频源目录")
@click.option("--output", "-o", required=True, type=click.Path(), help="输出根目录")
@click.option("--config", "-c", default="vbook.yaml", help="配置文件路径")
def init_cmd(source, output, config):
    """初始化 vbook 配置文件"""
    config_data = {
        "source": {"video_dirs": [str(Path(source).resolve())]},
        "output": {"root": str(Path(output).resolve()), "structure": "mirror"},
        "processing": {"intermediate_dir": ".vbook_cache", "keep_intermediate": True},
        "backends": {
            "stt": "whisper_local",
            "llm": "ollama_qwen",
            "whisper_local": {"model": "medium", "device": "cpu"},
            "ollama_qwen": {"base_url": "http://localhost:11434", "model": "qwen2.5:14b"},
        },
    }
    config_path = Path(config)
    config_path.write_text(yaml.dump(config_data, allow_unicode=True), encoding="utf-8")
    console.print(f"[green]配置已写入: {config_path}[/green]")
    console.print(f"[yellow]请修改配置后运行: vbook process --all[/yellow]")
```

**Step 2: 实现 status 命令**

```python
# src/vbook/cli/status.py
from pathlib import Path
import click
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

@click.command()
@click.argument("output_dir", type=click.Path(exists=True))
def status(output_dir):
    """查看视频处理状态"""
    cache_dir = Path(output_dir) / ".vbook_cache"
    status_file = cache_dir / "status.yaml"

    if not status_file.exists():
        console.print("[yellow]未找到处理状态[/yellow]")
        return

    data = yaml.safe_load(status_file.read_text())
    table = Table(title="处理状态")
    table.add_column("阶段", style="cyan")
    table.add_column("状态", style="green")

    for stage, info in data.items():
        status_str = info.get("status", "unknown")
        color = "green" if status_str == "success" else "red"
        table.add_row(stage, f"[{color}]{status_str}[/{color}]")

    console.print(table)
```

**Step 3: 注册命令**

```python
# 更新 src/vbook/cli/main.py
from .init_cmd import init_cmd
from .status import status

cli.add_command(init_cmd)
cli.add_command(status)
```

**Step 4: 运行所有测试**

```bash
uv run pytest -v --cov=src/vbook --cov-report=term-missing
```

**Step 5: Commit**

```bash
git add src/vbook/cli/
git commit -m "feat: add vbook init and status commands"
```

---

## Phase 7: MVP 验收测试

### Task 13: 完整端到端测试

**Step 1: 准备测试视频**

准备一个短视频文件（1-5分钟），用于真实测试：
```bash
# 如果没有视频，可以用 ffmpeg 生成测试视频
ffmpeg -f lavfi -i testsrc=duration=60:size=1280x720:rate=25 \
       -f lavfi -i sine=frequency=1000:duration=60 \
       -shortest test_video.mp4
```

**Step 2: 部署 Ollama + Qwen（服务器端）**

```bash
# 在服务器上安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动服务
ollama serve &

# 拉取模型
ollama pull qwen2.5:14b

# 测试
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:14b",
  "prompt": "你好",
  "stream": false
}'
```

**Step 3: 配置 vbook**

```bash
vbook init --source ./test_videos --output ./test_output
# 编辑 vbook.yaml 填入实际路径和服务器地址
```

**Step 4: 运行端到端测试**

```bash
vbook process test_video.mp4 --output ./test_output
```

**Step 5: 检验输出**

验证：
- [ ] `test_output/test_video/summary.md` 存在
- [ ] Markdown 包含标题、大纲、关键词
- [ ] `.vbook_cache/transcript.json` 包含带时间戳的文字
- [ ] `.vbook_cache/analysis.json` 包含结构化大纲
- [ ] 重新运行时跳过已完成阶段（断点续处理）

**Step 6: 最终 Commit**

```bash
git add .
git commit -m "docs: add README and finalize MVP implementation"
```

---

## 附：开发环境快速启动

```bash
# 1. 克隆并安装
git clone <repo>
cd vbook
uv sync

# 2. 安装系统依赖
# Ubuntu: sudo apt install ffmpeg
# macOS: brew install ffmpeg

# 3. 运行测试
uv run pytest -v

# 4. 安装到本地开发
uv pip install -e .

# 5. 验证安装
vbook --version
```
