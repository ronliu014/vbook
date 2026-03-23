# vbook 开发指南

> 版本: v0.1.0 | 最后更新: 2026-03-23 | 状态: MVP

本文档面向 vbook 的开发者和贡献者，介绍如何搭建开发环境、理解代码结构、扩展功能和提交贡献。

---

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [代码结构导览](#代码结构导览)
3. [核心抽象](#核心抽象)
4. [扩展指南](#扩展指南)
5. [编码规范](#编码规范)
6. [测试指南](#测试指南)
7. [提交规范](#提交规范)
8. [发布流程](#发布流程)

---

## 开发环境搭建

### 1. 克隆仓库

```bash
git clone https://github.com/ronliu014/vbook.git
cd vbook
```

### 2. 安装 uv

```bash
# Windows
pip install uv

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. 安装依赖

```bash
# 同步所有依赖（包括开发依赖）
uv sync

# 安装为可编辑模式
uv pip install -e .
```

### 4. 验证安装

```bash
# 运行测试
uv run pytest -v

# 检查代码覆盖率
uv run pytest --cov=src/vbook --cov-report=term-missing

# 验证 CLI
vbook --version
```

### 5. 安装系统依赖

```bash
# FFmpeg（必需）
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# 验证
ffmpeg -version
```

---

## 代码结构导览

### 项目结构

```
vbook/
├── src/vbook/           # 源代码
│   ├── cli/            # CLI 命令
│   ├── config/         # 配置管理
│   ├── pipeline/       # Pipeline 引擎
│   ├── backends/       # 后端抽象
│   ├── stages/         # 处理阶段
│   ├── output/         # 输出生成
│   └── utils/          # 工具函数
├── tests/              # 测试
├── docs/               # 文档
├── pyproject.toml      # 项目配置
└── README.md
```

### 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| `cli` | 命令行接口 | `main.py`, `process.py` |
| `config` | 配置加载和验证 | `schema.py`, `loader.py` |
| `pipeline` | 流程编排 | `engine.py`, `stage.py` |
| `backends` | 后端抽象 | `base.py`, `stt/`, `llm/` |
| `stages` | 处理逻辑 | `audio_extract.py`, etc. |
| `output` | 文档生成 | `markdown.py`, `templates/` |
| `utils` | 工具函数 | `path.py`, `retry.py` |

---

## 核心抽象

### 1. Stage（处理阶段）

**定义：** `src/vbook/pipeline/stage.py`

```python
class Stage(ABC):
    name: str  # 阶段名称

    @abstractmethod
    def run(self, context: dict) -> StageResult:
        """执行阶段逻辑，返回结果"""
        pass

    def can_skip(self, tracker) -> bool:
        """判断是否可以跳过（已完成）"""
        return tracker.is_complete(self.name)
```

**实现示例：**

```python
class MyStage(Stage):
    name = "my_stage"

    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def run(self, context: dict) -> StageResult:
        # 1. 从 context 获取输入
        input_data = context.get("previous_output")

        # 2. 执行处理逻辑
        result = self.process(input_data)

        # 3. 返回结果
        return StageResult(
            status=StageStatus.SUCCESS,
            output={"my_output": result},
        )
```

### 2. Backend（后端抽象）

**STT Backend 定义：** `src/vbook/backends/base.py`

```python
class STTBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptResult:
        """语音转文字"""
        pass
```

**实现示例：**

```python
class MySTTBackend(STTBackend):
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def transcribe(self, audio_path: str) -> TranscriptResult:
        # 调用 API
        response = requests.post(
            "https://api.example.com/transcribe",
            files={"audio": open(audio_path, "rb")},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

        # 解析响应
        data = response.json()
        segments = [
            TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
            )
            for seg in data["segments"]
        ]

        return TranscriptResult(
            segments=segments,
            language=data["language"],
        )
```

### 3. PipelineEngine（流程引擎）

**使用示例：**

```python
# 创建 stages
stages = [
    AudioExtractStage(video_path=video, cache_dir=cache),
    TranscribeStage(stt_backend=stt, cache_dir=cache),
    AnalyzeStage(llm_backend=llm, cache_dir=cache),
    GenerateStage(output_dir=output, cache_dir=cache),
]

# 创建引擎
engine = PipelineEngine(cache_dir=cache, max_retries=3)

# 执行
results = engine.run(stages, context={"video_path": str(video)})
```

---

## 扩展指南

### 扩展 1：添加新的 STT Backend

**场景：** 支持 Google Cloud Speech API

**步骤：**

1. **创建 Backend 类**

```python
# src/vbook/backends/stt/google_cloud.py
from google.cloud import speech_v1
from ..base import STTBackend, TranscriptResult, TranscriptSegment

class GoogleCloudSTTBackend(STTBackend):
    def __init__(self, credentials_path: str, language: str = "zh-CN"):
        self.client = speech_v1.SpeechClient.from_service_account_file(
            credentials_path
        )
        self.language = language

    def transcribe(self, audio_path: str) -> TranscriptResult:
        with open(audio_path, "rb") as f:
            audio = speech_v1.RecognitionAudio(content=f.read())

        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language,
            enable_word_time_offsets=True,
        )

        response = self.client.recognize(config=config, audio=audio)

        segments = []
        for result in response.results:
            for word in result.alternatives[0].words:
                segments.append(
                    TranscriptSegment(
                        start=word.start_time.total_seconds(),
                        end=word.end_time.total_seconds(),
                        text=word.word,
                    )
                )

        return TranscriptResult(segments=segments, language=self.language)
```

2. **添加配置 Schema**

```python
# src/vbook/config/schema.py
class BackendsConfig(BaseModel):
    # ... 现有字段 ...

    google_cloud: dict = Field(default_factory=lambda: {
        "credentials_path": "~/.gcloud/credentials.json",
        "language": "zh-CN",
    })
```

3. **在 process.py 中注册**

```python
# src/vbook/cli/process.py
from ..backends.stt.google_cloud import GoogleCloudSTTBackend

def _process_single(video_path, output, cfg, force):
    # ... 现有代码 ...

    if cfg.backends.stt == "google_cloud":
        stt = GoogleCloudSTTBackend(**cfg.backends.google_cloud)
    elif cfg.backends.stt == "whisper_remote":
        stt = WhisperRemoteBackend(**cfg.backends.whisper_remote)
    else:
        stt = WhisperSTTBackend(**cfg.backends.whisper_local)

    # ... 其余代码 ...
```

4. **编写测试**

```python
# tests/test_backends.py
def test_google_cloud_backend():
    with patch("google.cloud.speech_v1.SpeechClient") as MockClient:
        # Mock API 响应
        mock_response = MagicMock()
        # ... 设置 mock ...

        backend = GoogleCloudSTTBackend(
            credentials_path="/path/to/creds.json"
        )
        result = backend.transcribe("/tmp/audio.wav")

        assert isinstance(result, TranscriptResult)
        assert len(result.segments) > 0
```

5. **更新文档**

在 `docs/USER_GUIDE.md` 中添加使用说明。

### 扩展 2：添加新的输出格式

**场景：** 支持思维导图输出（XMind 格式）

**步骤：**

1. **创建生成器类**

```python
# src/vbook/output/mindmap.py
import xmind

class MindMapGenerator:
    def render(self, analysis: dict, output_path: str):
        workbook = xmind.load(output_path)
        sheet = workbook.getPrimarySheet()
        root = sheet.getRootTopic()
        root.setTitle(analysis["title"])

        for section in analysis["outline"]:
            topic = root.addSubTopic()
            topic.setTitle(section["title"])
            topic.setPlainNotes(section["summary"])

        xmind.save(workbook, output_path)
```

2. **创建新的 Stage**

```python
# src/vbook/stages/generate_mindmap.py
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..output.mindmap import MindMapGenerator

class GenerateMindMapStage(Stage):
    name = "generate_mindmap"

    def __init__(self, output_dir: Path, cache_dir: Path):
        self.output_dir = output_dir
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        analysis_path = context.get("analysis_path")
        analysis = json.loads(Path(analysis_path).read_text(encoding="utf-8"))

        mindmap_path = self.output_dir / "mindmap.xmind"
        gen = MindMapGenerator()
        gen.render(analysis, str(mindmap_path))

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"mindmap_path": str(mindmap_path)},
        )
```

3. **添加到 Pipeline**

```python
# src/vbook/cli/process.py
stages = [
    AudioExtractStage(...),
    TranscribeStage(...),
    AnalyzeStage(...),
    ScreenshotStage(...),
    GenerateStage(...),
    GenerateMindMapStage(...),  # 新增
]
```

4. **编写测试**

```python
# tests/test_output.py
def test_mindmap_generation(tmp_path):
    analysis = {
        "title": "测试",
        "outline": [{"title": "第一节", "summary": "内容"}],
    }
    gen = MindMapGenerator()
    output = tmp_path / "test.xmind"
    gen.render(analysis, str(output))

    assert output.exists()
```

### 扩展 3：添加新的 Pipeline Stage

**场景：** 添加视频摘要生成阶段

**步骤：**

1. **创建 Stage 类**

```python
# src/vbook/stages/summarize.py
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import LLMBackend

class SummarizeStage(Stage):
    name = "summarize"

    def __init__(self, llm_backend: LLMBackend, cache_dir: Path):
        self.llm_backend = llm_backend
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        transcript_path = context.get("transcript_path")
        transcript = json.loads(Path(transcript_path).read_text())

        prompt = "请用3-5句话总结以下内容的核心要点："
        summary = self.llm_backend.analyze(
            transcript["full_text"],
            prompt
        )

        summary_path = self.cache_dir / "summary.txt"
        summary_path.write_text(summary, encoding="utf-8")

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"summary": summary, "summary_path": str(summary_path)},
        )
```

2. **插入到 Pipeline**

```python
# src/vbook/cli/process.py
stages = [
    AudioExtractStage(...),
    TranscribeStage(...),
    SummarizeStage(llm_backend=llm, cache_dir=cache_dir),  # 新增
    AnalyzeStage(...),
    ScreenshotStage(...),
    GenerateStage(...),
]
```

3. **编写测试**

```python
# tests/test_stages.py
def test_summarize_stage(tmp_path):
    transcript_file = tmp_path / "transcript.json"
    transcript_file.write_text(json.dumps({
        "full_text": "这是一段很长的文本...",
        "segments": [],
    }))

    with patch("litellm.completion") as mock:
        mock.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="摘要内容"))]
        )

        backend = LiteLLMBackend(model="ollama/qwen2.5:14b")
        stage = SummarizeStage(llm_backend=backend, cache_dir=tmp_path)
        result = stage.run(context={"transcript_path": str(transcript_file)})

    assert result.status == StageStatus.SUCCESS
    assert "summary" in result.output
```

---

## 编码规范

### Python 代码风格

遵循 PEP 8，关键点：

```python
# 1. 类型提示（必需）
def process_video(video_path: Path, config: VbookConfig) -> dict:
    ...

# 2. Docstring（公共 API 必需）
def transcribe(self, audio_path: str) -> TranscriptResult:
    """
    将音频文件转换为文本。

    Args:
        audio_path: 音频文件路径

    Returns:
        TranscriptResult: 转录结果，包含分段和完整文本
    """
    ...

# 3. 命名规范
class MyClass:          # PascalCase
    def my_method(self): # snake_case
        my_variable = 1  # snake_case
        MY_CONSTANT = 2  # UPPER_SNAKE_CASE

# 4. 导入顺序
import os               # 标准库
import sys

import click            # 第三方库
import yaml

from .config import ... # 本地模块
```

### 错误处理

```python
# 好的做法
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise  # 或者返回错误结果

# 避免
try:
    result = risky_operation()
except:  # 不要捕获所有异常
    pass  # 不要静默失败
```

### 日志记录

```python
# 使用 Rich console 输出用户信息
from rich.console import Console
console = Console()

console.print("[green]处理完成[/green]")
console.print("[red]错误: 文件不存在[/red]")

# 避免使用 print()
print("这样不好")  # ❌
```

---

## 测试指南

### 测试结构

```
tests/
├── test_cli.py          # CLI 命令测试
├── test_config.py       # 配置系统测试
├── test_pipeline.py     # Pipeline 引擎测试
├── test_backends.py     # Backend 测试
├── test_stages.py       # Stage 测试
├── test_output.py       # 输出生成测试
└── conftest.py          # pytest 配置和 fixtures
```

### 编写测试

**单元测试示例：**

```python
# tests/test_my_feature.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

def test_my_function():
    # Arrange
    input_data = "test"

    # Act
    result = my_function(input_data)

    # Assert
    assert result == "expected"

def test_with_mock(tmp_path):
    # 使用 tmp_path fixture 创建临时文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    # Mock 外部依赖
    with patch("module.external_call") as mock_call:
        mock_call.return_value = "mocked"
        result = function_using_external_call()

    assert result == "mocked"
    mock_call.assert_called_once()
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定文件
uv run pytest tests/test_stages.py

# 运行特定测试
uv run pytest tests/test_stages.py::test_audio_extract_success

# 显示详细输出
uv run pytest -v

# 生成覆盖率报告
uv run pytest --cov=src/vbook --cov-report=html

# 只运行失败的测试
uv run pytest --lf
```

### 测试覆盖率目标

- **整体覆盖率**: > 80%
- **核心模块**: > 90% (pipeline, backends, stages)
- **CLI 模块**: > 70%

---

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

**Type:**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 重构
- `perf`: 性能优化
- `chore`: 构建/工具相关

**示例：**

```
feat(backends): add Google Cloud STT backend

- Implement GoogleCloudSTTBackend class
- Add configuration schema
- Update process.py to support new backend
- Add tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

### Pull Request 流程

1. **Fork 仓库**
2. **创建功能分支**

```bash
git checkout -b feature/my-feature
```

3. **开发和测试**

```bash
# 编写代码
# 运行测试
uv run pytest

# 检查覆盖率
uv run pytest --cov=src/vbook
```

4. **提交代码**

```bash
git add .
git commit -m "feat: add my feature"
```

5. **推送并创建 PR**

```bash
git push origin feature/my-feature
# 在 GitHub 上创建 Pull Request
```

6. **代码审查**
   - 等待维护者审查
   - 根据反馈修改
   - 合并到 main

---

## 发布流程

### 版本号规范

遵循 [Semantic Versioning](https://semver.org/)：

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的 Bug 修复

### 发布步骤

1. **更新版本号**

```bash
# pyproject.toml
version = "0.2.0"

# src/vbook/cli/main.py
@click.version_option(version="0.2.0")
```

2. **更新 CHANGELOG.md**

```markdown
## [0.2.0] - 2026-04-01

### Added
- 思维导图输出
- PPT 生成

### Changed
- 优化批量处理性能

### Fixed
- 修复配置合并 bug
```

3. **创建 Git Tag**

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

4. **发布到 PyPI**

```bash
uv build
uv publish
```

---

## 常见问题

### Q: 如何调试 Pipeline？

**A:** 使用 Python 调试器：

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()
```

### Q: 如何测试远程 Backend？

**A:** 使用 Mock：

```python
with patch("httpx.post") as mock_post:
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"result": "mocked"}
    )
    # 测试代码
```

### Q: 如何添加新的 CLI 命令？

**A:** 在 `cli/` 目录创建新文件，然后在 `main.py` 中注册：

```python
# cli/my_command.py
@click.command()
def my_command():
    """My command description"""
    pass

# cli/main.py
from .my_command import my_command
cli.add_command(my_command)
```

---

## 资源链接

- **GitHub**: https://github.com/ronliu014/vbook
- **Issues**: https://github.com/ronliu014/vbook/issues
- **文档**: [docs/](../docs/)
- **测试方案**: [TESTING.md](TESTING.md)
- **架构设计**: [ARCHITECTURE.md](ARCHITECTURE.md)
