# Glossary Proofread Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Whisper hotwords injection + LLM post-transcription proofreading using a domain glossary file, improving professional terminology accuracy in transcripts.

**Architecture:** A YAML glossary file (`glossary/investment.yaml`) provides domain terms. The glossary is loaded via a new `processing.glossary` config field. Whisper backends receive hotwords to improve first-pass accuracy. A new `ProofreadStage` sits between `TranscribeStage` and `AnalyzeStage`, using LLM + glossary to correct remaining errors. Corrections are logged to `corrections.json` for human review.

**Tech Stack:** Python `logging`, `pyyaml` (already a dependency), `litellm` (existing LLM backend), faster-whisper hotwords API

---

### Task 1: Add `glossary` field to config schema

**Files:**
- Modify: `src/vbook/config/schema.py:12-15`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Add to `tests/test_config.py`:

```python
def test_config_glossary_field():
    from vbook.config.schema import VbookConfig
    cfg = VbookConfig()
    assert cfg.processing.glossary is None

def test_config_glossary_from_yaml(tmp_path):
    from vbook.config.loader import load_config
    config_file = tmp_path / "vbook.yaml"
    config_file.write_text("processing:\n  glossary: glossary/investment.yaml\n")
    cfg = load_config(config_path=config_file)
    assert cfg.processing.glossary == "glossary/investment.yaml"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py::test_config_glossary_field tests/test_config.py::test_config_glossary_from_yaml -v
```

Expected: FAIL — `ProcessingConfig` has no `glossary` attribute

**Step 3: Write minimal implementation**

In `src/vbook/config/schema.py`, add to `ProcessingConfig`:

```python
class ProcessingConfig(BaseModel):
    intermediate_dir: str = ".vbook_cache"
    keep_intermediate: bool = True
    max_retries: int = 3
    glossary: Optional[str] = None
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all PASSED

**Step 5: Commit**

```bash
git add src/vbook/config/schema.py tests/test_config.py
git commit -m "feat: add glossary config field to ProcessingConfig"
```

---

### Task 2: Create glossary loader utility

**Files:**
- Create: `src/vbook/utils/glossary.py`
- Create: `glossary/investment.yaml`
- Test: `tests/test_glossary.py`

**Step 1: Write the failing test**

```python
# tests/test_glossary.py
from pathlib import Path
from vbook.utils.glossary import load_glossary

def test_load_glossary(tmp_path):
    glossary_file = tmp_path / "test.yaml"
    glossary_file.write_text(
        "domain: 投资\nterms:\n  - term: PE比\n    description: 市盈率\n  - term: 底背离\n    description: 技术形态\n",
        encoding="utf-8",
    )
    glossary = load_glossary(str(glossary_file))
    assert glossary["domain"] == "投资"
    assert len(glossary["terms"]) == 2
    assert glossary["terms"][0]["term"] == "PE比"

def test_load_glossary_returns_none_for_missing():
    result = load_glossary("/nonexistent/path.yaml")
    assert result is None

def test_load_glossary_returns_none_for_none():
    result = load_glossary(None)
    assert result is None

def test_glossary_hotwords(tmp_path):
    from vbook.utils.glossary import extract_hotwords
    glossary_file = tmp_path / "test.yaml"
    glossary_file.write_text(
        "domain: 投资\nterms:\n  - term: PE比\n    description: 市盈率\n  - term: 满仓\n    description: 全部资金投入\n",
        encoding="utf-8",
    )
    glossary = load_glossary(str(glossary_file))
    hotwords = extract_hotwords(glossary)
    assert hotwords == ["PE比", "满仓"]

def test_extract_hotwords_none_glossary():
    from vbook.utils.glossary import extract_hotwords
    assert extract_hotwords(None) == []
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_glossary.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/vbook/utils/glossary.py
from pathlib import Path
from typing import Optional
import yaml
from .logger import get_logger

logger = get_logger(__name__)


def load_glossary(glossary_path: Optional[str]) -> Optional[dict]:
    if glossary_path is None:
        return None
    path = Path(glossary_path)
    if not path.exists():
        logger.warning("术语词表文件不存在: %s", glossary_path)
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    logger.info("加载术语词表: %s (%d 个术语)", data.get("domain", ""), len(data.get("terms", [])))
    return data


def extract_hotwords(glossary: Optional[dict]) -> list[str]:
    if glossary is None:
        return []
    return [t["term"] for t in glossary.get("terms", [])]
```

**Step 4: Create example glossary file**

```yaml
# glossary/investment.yaml
domain: 投资
terms:
  - term: PE比
    description: 市盈率，Price-to-Earnings Ratio
  - term: PB比
    description: 市净率，Price-to-Book Ratio
  - term: ROE
    description: 净资产收益率，Return on Equity
  - term: 底背离
    description: 价格创新低但指标未创新低的技术形态
  - term: 顶背离
    description: 价格创新高但指标未创新高的技术形态
  - term: 满仓
    description: 将全部资金投入持仓
  - term: 半仓
    description: 将一半资金投入持仓
  - term: 止损
    description: 设定亏损上限，达到后卖出以控制风险
  - term: 止盈
    description: 设定盈利目标，达到后卖出以锁定利润
  - term: 做多
    description: 买入资产，预期价格上涨后获利
  - term: 做空
    description: 借入资产卖出，预期价格下跌后买回获利
  - term: 均线
    description: 移动平均线，Moving Average
  - term: K线
    description: 蜡烛图，显示开盘价、收盘价、最高价、最低价
  - term: 涨停
    description: 股价达到当日最大涨幅限制
  - term: 跌停
    description: 股价达到当日最大跌幅限制
```

**Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_glossary.py -v
```

Expected: all PASSED

**Step 6: Commit**

```bash
git add src/vbook/utils/glossary.py tests/test_glossary.py glossary/investment.yaml
git commit -m "feat: add glossary loader utility and example investment glossary"
```

---

### Task 3: Inject hotwords into Whisper backends

**Files:**
- Modify: `src/vbook/backends/base.py:19-22`
- Modify: `src/vbook/backends/stt/whisper.py`
- Modify: `src/vbook/backends/stt/whisper_remote.py`
- Modify: `src/vbook/stages/transcribe.py`
- Test: `tests/test_stages.py`

**Step 1: Write the failing test**

Add to `tests/test_stages.py`:

```python
def test_whisper_backend_passes_hotwords():
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "PE比很高"

    with patch("vbook.backends.stt.whisper.WhisperModel") as MockModel:
        instance = MockModel.return_value
        instance.transcribe.return_value = ([mock_segment], MagicMock(language="zh"))

        backend = WhisperSTTBackend(model="small", device="cpu")
        result = backend.transcribe("/tmp/audio.wav", hotwords=["PE比", "满仓"])

    call_kwargs = instance.transcribe.call_args
    assert "hotwords" in call_kwargs.kwargs
    assert "PE比" in call_kwargs.kwargs["hotwords"]

def test_transcribe_stage_passes_hotwords(tmp_path):
    from vbook.stages.transcribe import TranscribeStage
    from vbook.backends.base import TranscriptResult, TranscriptSegment

    mock_backend = MagicMock()
    mock_backend.transcribe.return_value = TranscriptResult(
        segments=[TranscriptSegment(start=0, end=5, text="测试")],
        language="zh",
    )

    stage = TranscribeStage(stt_backend=mock_backend, cache_dir=tmp_path, hotwords=["PE比"])
    stage.run(context={"audio_path": "/tmp/audio.wav"})

    call_kwargs = mock_backend.transcribe.call_args
    assert call_kwargs.kwargs.get("hotwords") == ["PE比"]
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_stages.py::test_whisper_backend_passes_hotwords tests/test_stages.py::test_transcribe_stage_passes_hotwords -v
```

Expected: FAIL — `transcribe()` doesn't accept `hotwords`

**Step 3: Modify `base.py`**

```python
class STTBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, hotwords: list[str] | None = None) -> TranscriptResult:
        pass
```

**Step 4: Modify `whisper.py`**

```python
from faster_whisper import WhisperModel
from ..base import STTBackend, TranscriptResult, TranscriptSegment
from ...utils.logger import get_logger

logger = get_logger(__name__)

class WhisperSTTBackend(STTBackend):
    def __init__(self, model: str = "medium", device: str = "cpu"):
        self.model = WhisperModel(model, device=device)

    def transcribe(self, audio_path: str, hotwords: list[str] | None = None) -> TranscriptResult:
        kwargs = {"language": "zh"}
        if hotwords:
            kwargs["hotwords"] = " ".join(hotwords)
            logger.debug("Whisper hotwords: %s", kwargs["hotwords"])
        segments, info = self.model.transcribe(audio_path, **kwargs)
        return TranscriptResult(
            segments=[
                TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
                for s in segments
            ],
            language=info.language,
        )
```

**Step 5: Modify `whisper_remote.py`**

```python
import httpx
from ..base import STTBackend, TranscriptResult, TranscriptSegment
from ...utils.logger import get_logger

logger = get_logger(__name__)


class WhisperRemoteBackend(STTBackend):
    """远程 Whisper 后端，调用 faster-whisper-server 的 OpenAI 兼容 API。"""

    def __init__(
        self,
        base_url: str = "http://localhost:7867",
        model: str = "medium",
        language: str = "zh",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.language = language

    def transcribe(self, audio_path: str, hotwords: list[str] | None = None) -> TranscriptResult:
        if hotwords:
            logger.info("远程 Whisper 不支持 hotwords，已跳过（%d 个热词）", len(hotwords))
        url = f"{self.base_url}/v1/audio/transcriptions"

        with open(audio_path, "rb") as f:
            resp = httpx.post(
                url,
                files={"file": (audio_path, f, "audio/wav")},
                data={
                    "model": self.model,
                    "language": self.language,
                    "response_format": "verbose_json",
                },
                timeout=600.0,
            )
        resp.raise_for_status()

        data = resp.json()
        segments = [
            TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
            )
            for seg in data.get("segments", [])
        ]
        return TranscriptResult(
            segments=segments,
            language=data.get("language", self.language),
        )
```

**Step 6: Modify `transcribe.py`**

```python
import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import STTBackend

class TranscribeStage(Stage):
    name = "transcribe"

    def __init__(self, stt_backend: STTBackend, cache_dir: Path, hotwords: list[str] | None = None):
        self.stt_backend = stt_backend
        self.cache_dir = cache_dir
        self.hotwords = hotwords

    def run(self, context: dict) -> StageResult:
        audio_path = context.get("audio_path")
        if not audio_path:
            raise ValueError("audio_path not found in context")

        result = self.stt_backend.transcribe(audio_path, hotwords=self.hotwords)

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

**Step 7: Run test to verify it passes**

```bash
uv run pytest tests/test_stages.py -v
```

Expected: all PASSED (old + new)

**Step 8: Commit**

```bash
git add src/vbook/backends/base.py src/vbook/backends/stt/whisper.py src/vbook/backends/stt/whisper_remote.py src/vbook/stages/transcribe.py tests/test_stages.py
git commit -m "feat: inject hotwords into Whisper backends for better term recognition"
```

---

### Task 4: Create ProofreadStage

**Files:**
- Create: `src/vbook/stages/proofread.py`
- Modify: `src/vbook/output/prompts.py`
- Test: `tests/test_proofread.py`

**Step 1: Write the failing test**

```python
# tests/test_proofread.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from vbook.stages.proofread import ProofreadStage
from vbook.pipeline.stage import StageStatus
from vbook.backends.llm.litellm_backend import LiteLLMBackend


def test_proofread_corrects_terms(tmp_path):
    transcript = {
        "language": "zh",
        "segments": [
            {"start": 0, "end": 5, "text": "这个股票的屁衣比很高"},
            {"start": 5, "end": 10, "text": "建议满仓买入"},
        ],
        "full_text": "这个股票的屁衣比很高\n建议满仓买入",
    }
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")

    glossary = {
        "domain": "投资",
        "terms": [
            {"term": "PE比", "description": "市盈率"},
            {"term": "满仓", "description": "全部资金投入"},
        ],
    }

    llm_response = json.dumps({
        "segments": [{"index": 0, "text": "这个股票的PE比很高"}],
        "corrections": [{"index": 0, "original": "屁衣比", "corrected": "PE比", "reason": "术语误识别"}],
    })

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=llm_response))]
        )
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b")
        stage = ProofreadStage(llm_backend=backend, cache_dir=tmp_path, glossary=glossary)
        result = stage.run(context={"transcript_path": str(transcript_path)})

    assert result.status == StageStatus.SUCCESS

    # transcript.json should be updated
    updated = json.loads(transcript_path.read_text(encoding="utf-8"))
    assert updated["segments"][0]["text"] == "这个股票的PE比很高"
    assert updated["segments"][1]["text"] == "建议满仓买入"  # unchanged

    # corrections.json should exist
    corrections_path = tmp_path / "corrections.json"
    assert corrections_path.exists()
    corrections = json.loads(corrections_path.read_text(encoding="utf-8"))
    assert len(corrections) == 1
    assert corrections[0]["corrected"] == "PE比"


def test_proofread_skips_without_glossary(tmp_path):
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text('{"segments": [], "full_text": "", "language": "zh"}', encoding="utf-8")

    backend = MagicMock()
    stage = ProofreadStage(llm_backend=backend, cache_dir=tmp_path, glossary=None)
    result = stage.run(context={"transcript_path": str(transcript_path)})

    assert result.status == StageStatus.SKIPPED
    backend.analyze.assert_not_called()


def test_proofread_no_corrections_needed(tmp_path):
    transcript = {
        "language": "zh",
        "segments": [{"start": 0, "end": 5, "text": "PE比很高"}],
        "full_text": "PE比很高",
    }
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")

    glossary = {"domain": "投资", "terms": [{"term": "PE比", "description": "市盈率"}]}

    llm_response = json.dumps({"segments": [], "corrections": []})

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=llm_response))]
        )
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b")
        stage = ProofreadStage(llm_backend=backend, cache_dir=tmp_path, glossary=glossary)
        result = stage.run(context={"transcript_path": str(transcript_path)})

    assert result.status == StageStatus.SUCCESS
    # No corrections file when nothing changed
    corrections = json.loads((tmp_path / "corrections.json").read_text(encoding="utf-8"))
    assert corrections == []
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_proofread.py -v
```

Expected: FAIL — `ModuleNotFoundError`

**Step 3: Add PROOFREAD_PROMPT to prompts.py**

Append to `src/vbook/output/prompts.py`:

```python
PROOFREAD_PROMPT = """你是专业的语音转录校对助手。以下是语音识别的转录文本，可能存在专业术语识别错误。

专业术语词表：
{glossary}

请逐段检查转录文本，修正专业术语错误。只修正明显的术语误识别，不要改变原文的表达方式和语序。

返回严格的JSON格式：
{{
  "segments": [{{"index": 段落序号, "text": "修正后的文本"}}],
  "corrections": [{{"index": 段落序号, "original": "原文片段", "corrected": "修正后", "reason": "原因"}}]
}}

只返回有修改的段落。未修改的段落不要包含在 segments 中。
只返回JSON，不要其他文字。"""
```

**Step 4: Create `src/vbook/stages/proofread.py`**

```python
# src/vbook/stages/proofread.py
import json
from pathlib import Path
from typing import Optional
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import LLMBackend
from ..output.prompts import PROOFREAD_PROMPT
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProofreadStage(Stage):
    name = "proofread"

    def __init__(self, llm_backend: LLMBackend, cache_dir: Path, glossary: Optional[dict] = None):
        self.llm_backend = llm_backend
        self.cache_dir = cache_dir
        self.glossary = glossary

    def run(self, context: dict) -> StageResult:
        if self.glossary is None:
            logger.info("未配置术语词表，跳过校对阶段")
            return StageResult(status=StageStatus.SKIPPED, output={})

        transcript_path = Path(context["transcript_path"])
        transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
        segments = transcript_data["segments"]

        glossary_text = "\n".join(
            f"- {t['term']}: {t['description']}" for t in self.glossary.get("terms", [])
        )
        prompt = PROOFREAD_PROMPT.format(glossary=glossary_text)

        segment_text = "\n".join(
            f"[{i}] {seg['text']}" for i, seg in enumerate(segments)
        )

        logger.info("开始校对转录文本（%d 段，%d 个术语）", len(segments), len(self.glossary.get("terms", [])))
        raw = self.llm_backend.analyze(segment_text, prompt)

        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        result = json.loads(raw)

        # Apply corrections to segments
        for corrected_seg in result.get("segments", []):
            idx = corrected_seg["index"]
            if 0 <= idx < len(segments):
                segments[idx]["text"] = corrected_seg["text"]

        # Update full_text
        transcript_data["full_text"] = "\n".join(seg["text"] for seg in segments)

        # Write updated transcript
        transcript_path.write_text(
            json.dumps(transcript_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Write corrections log
        corrections = result.get("corrections", [])
        corrections_path = self.cache_dir / "corrections.json"
        corrections_path.write_text(
            json.dumps(corrections, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if corrections:
            logger.info("校对完成，修正 %d 处术语", len(corrections))
            for c in corrections:
                logger.debug("  [%d] %s → %s (%s)", c["index"], c["original"], c["corrected"], c["reason"])
        else:
            logger.info("校对完成，无需修正")

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"transcript_path": str(transcript_path), "corrections_path": str(corrections_path)},
        )
```

**Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_proofread.py -v
```

Expected: all 3 PASSED

**Step 6: Commit**

```bash
git add src/vbook/stages/proofread.py src/vbook/output/prompts.py tests/test_proofread.py
git commit -m "feat: add ProofreadStage for LLM-based terminology correction"
```

---

### Task 5: Wire everything into the pipeline

**Files:**
- Modify: `src/vbook/cli/process.py`

**Step 1: Write the failing test**

Add to `tests/test_cli_process.py`:

```python
def test_process_loads_glossary_and_creates_proofread_stage(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    glossary_file = tmp_path / "glossary.yaml"
    glossary_file.write_text(
        "domain: 投资\nterms:\n  - term: PE比\n    description: 市盈率\n",
        encoding="utf-8",
    )

    config_file = tmp_path / "vbook.yaml"
    config_file.write_text(
        f"processing:\n  glossary: {glossary_file}\n",
        encoding="utf-8",
    )

    with patch("vbook.cli.process.PipelineEngine") as MockEngine, \
         patch("vbook.cli.process.setup_logging"):
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video), "-c", str(config_file)])

    # Verify ProofreadStage was included in stages
    call_args = MockEngine.return_value.run.call_args
    stages = call_args[0][0]
    stage_names = [s.name for s in stages]
    assert "proofread" in stage_names
    # proofread should be after transcribe and before analyze
    assert stage_names.index("proofread") == stage_names.index("transcribe") + 1
    assert stage_names.index("proofread") == stage_names.index("analyze") - 1
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_cli_process.py::test_process_loads_glossary_and_creates_proofread_stage -v
```

Expected: FAIL — `ProofreadStage` not imported or not in stages list

**Step 3: Modify `process.py`**

Add imports at top:

```python
from vbook.utils.glossary import load_glossary, extract_hotwords
from vbook.stages.proofread import ProofreadStage
```

In `_process_single`, after loading config and before building stages, add glossary loading:

```python
    # Load glossary
    glossary = load_glossary(cfg.processing.glossary)
    hotwords = extract_hotwords(glossary)
```

Update `TranscribeStage` construction to pass hotwords:

```python
    TranscribeStage(stt_backend=stt, cache_dir=cache_dir, hotwords=hotwords),
```

Insert `ProofreadStage` after `TranscribeStage` and before `AnalyzeStage`:

```python
    stages = [
        AudioExtractStage(video_path=video_path, cache_dir=cache_dir),
        TranscribeStage(stt_backend=stt, cache_dir=cache_dir, hotwords=hotwords),
        ProofreadStage(llm_backend=llm, cache_dir=cache_dir, glossary=glossary),
        AnalyzeStage(llm_backend=llm, cache_dir=cache_dir),
        ScreenshotStage(video_path=video_path, cache_dir=cache_dir),
        GenerateStage(output_dir=output_dir, cache_dir=cache_dir),
    ]
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_cli_process.py -v
```

Expected: all PASSED

**Step 5: Commit**

```bash
git add src/vbook/cli/process.py tests/test_cli_process.py
git commit -m "feat: wire glossary loading and ProofreadStage into pipeline"
```

---

### Task 6: Full regression

**Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: all PASSED

**Step 2: Smoke test CLI**

```bash
python src/vbook/cli/process.py --help
```

Expected: help output unchanged (glossary is config-driven, no new CLI flags)

**Step 3: Verify glossary file exists**

```bash
cat glossary/investment.yaml
```

Expected: YAML with domain and terms list
