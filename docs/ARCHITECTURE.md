# vbook 技术架构

> 版本: v0.1.0 | 最后更新: 2026-03-23 | 状态: MVP

本文档描述 vbook 的技术架构设计、核心组件、数据流和关键设计决策。

---

## 目录

1. [系统架构](#系统架构)
2. [核心组件](#核心组件)
3. [数据流](#数据流)
4. [目录结构](#目录结构)
5. [设计模式](#设计模式)
6. [关键设计决策](#关键设计决策)
7. [扩展点](#扩展点)

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    vbook CLI Application                     │
│                     (Click Framework)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
        ┌───────▼────────┐         ┌────────▼────────┐
        │  Config Manager │         │  Pipeline Engine │
        │  (全局+项目配置)  │         │   (处理流程编排)   │
        └───────┬────────┘         └────────┬────────┘
                │                           │
                │              ┌────────────┴────────────┐
                │              │                         │
        ┌───────▼────────┐  ┌──▼───┐  ┌────▼───┐  ┌─────▼────┐
        │  Backend Store │  │ STT  │  │  LLM   │  │  Output  │
        │   (后端注册表)   │  │Backend│ │Backend │  │ Generator│
        └────────────────┘  └──┬───┘  └────┬───┘  └─────┬────┘
                              │           │             │
                    ┌─────────┴─────┬─────┴──────┬──────┴──────┐
                    │               │            │             │
              ┌─────▼──────┐ ┌─────▼─────┐ ┌───▼────┐ ┌──────▼─────┐
              │  Whisper   │ │  Whisper  │ │ Ollama │ │  Jinja2    │
              │  (本地)     │ │  (远程)    │ │ (LLM)  │ │ (模板)     │
              └────────────┘ └───────────┘ └────────┘ └────────────┘
```

### 分层架构

```
┌─────────────────────────────────────────┐
│         CLI Layer (命令行接口)            │  ← Click commands
├─────────────────────────────────────────┤
│      Application Layer (应用逻辑)         │  ← Pipeline orchestration
├─────────────────────────────────────────┤
│       Domain Layer (领域模型)             │  ← Stage, Backend abstractions
├─────────────────────────────────────────┤
│    Infrastructure Layer (基础设施)        │  ← Config, Utils, I/O
└─────────────────────────────────────────┘
```

---

## 核心组件

### 1. CLI 层（vbook.cli）

**职责：** 命令行接口，参数解析，用户交互

**组件：**

```python
cli/
├── main.py          # CLI 入口，命令注册
├── init_cmd.py      # vbook init 命令
├── process.py       # vbook process 命令
└── status.py        # vbook status 命令
```

**关键类：**
- `cli()` - Click group，主入口
- `process()` - 处理视频的主命令
- `init_cmd()` - 初始化配置
- `status()` - 查看处理状态

**设计要点：**
- 使用 Click 装饰器定义命令
- 参数验证在 CLI 层完成
- 错误信息用户友好（Rich 格式化）

### 2. 配置系统（vbook.config）

**职责：** 配置加载、验证、合并

**组件：**

```python
config/
├── schema.py        # Pydantic 配置模型
└── loader.py        # 配置加载器
```

**关键类：**
- `VbookConfig` - 根配置模型
- `BackendsConfig` - 后端配置
- `load_config()` - 配置加载函数

**配置优先级：**

```python
def load_config(config_path, overrides):
    data = {}

    # 1. 全局配置（最低优先级）
    if global_config.exists():
        data = yaml.load(global_config)

    # 2. 项目配置（中等优先级）
    if config_path.exists():
        data = deep_merge(data, yaml.load(config_path))

    # 3. CLI 覆盖（最高优先级）
    if overrides:
        data = apply_overrides(data, overrides)

    return VbookConfig(**data)  # Pydantic 验证
```

**设计要点：**
- 使用 Pydantic 进行类型验证
- 深度合并字典（不是简单覆盖）
- 支持 dot-notation 覆盖（`backends.stt`）

### 3. Pipeline 引擎（vbook.pipeline）

**职责：** 编排处理流程，管理状态，重试机制

**组件：**

```python
pipeline/
├── stage.py         # Stage 抽象基类
├── engine.py        # Pipeline 引擎
└── tracker.py       # 状态追踪器
```

**关键类：**

```python
class Stage(ABC):
    name: str

    @abstractmethod
    def run(self, context: dict) -> StageResult:
        """执行阶段逻辑"""
        pass

    def can_skip(self, tracker) -> bool:
        """是否可以跳过（已完成）"""
        return tracker.is_complete(self.name)

class PipelineEngine:
    def run(self, stages: list[Stage], context: dict):
        """按顺序执行所有阶段"""
        for stage in stages:
            if stage.can_skip(tracker):
                continue  # 跳过已完成

            result = with_retry(stage.run, max_retries=3)
            tracker.mark_complete(stage.name, result.output)
            context.update(result.output)  # 传递给下一阶段
```

**设计要点：**
- Stage 之间通过 `context` 字典传递数据
- 每个 Stage 独立可测试
- 状态持久化到 YAML 文件
- 支持断点续处理

### 4. Backend 抽象层（vbook.backends）

**职责：** 定义后端接口，实现具体后端

**组件：**

```python
backends/
├── base.py          # 抽象基类
├── stt/
│   ├── whisper.py         # 本地 Whisper
│   └── whisper_remote.py  # 远程 Whisper API
└── llm/
    └── litellm_backend.py # LiteLLM 后端
```

**接口设计：**

```python
class STTBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptResult:
        """语音转文字"""
        pass

class LLMBackend(ABC):
    @abstractmethod
    def analyze(self, text: str, prompt: str) -> str:
        """文本分析"""
        pass
```

**设计要点：**
- 使用抽象基类定义接口
- 返回统一的数据结构（`TranscriptResult`）
- 易于添加新后端（继承基类即可）

### 5. 处理阶段（vbook.stages）

**职责：** 实现具体的处理逻辑

**组件：**

```python
stages/
├── audio_extract.py   # 音频提取
├── transcribe.py      # 语音转录
├── analyze.py         # 内容分析
├── screenshot.py      # 截图提取
└── generate.py        # 文档生成
```

**阶段依赖关系：**

```
AudioExtractStage
    ↓ (audio_path)
TranscribeStage
    ↓ (transcript_path)
AnalyzeStage
    ↓ (analysis_path)
ScreenshotStage
    ↓ (screenshots_map)
GenerateStage
    ↓ (markdown_path)
```

**设计要点：**
- 每个阶段继承 `Stage` 基类
- 输入从 `context` 获取
- 输出写入 `context` 供下游使用
- 中间文件保存到 `cache_dir`

### 6. 输出生成（vbook.output）

**职责：** 生成最终文档

**组件：**

```python
output/
├── markdown.py      # Markdown 生成器
├── prompts.py       # LLM 提示词
└── templates/
    └── summary.md.j2  # Jinja2 模板
```

**设计要点：**
- 使用 Jinja2 模板引擎
- 模板与逻辑分离
- 易于自定义输出格式

---

## 数据流

### 完整数据流图

```
┌──────────────┐
│  video.mp4   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ AudioExtractStage                                         │
│ - 使用 FFmpeg 提取音频                                     │
│ - 输出: audio.wav (16kHz, mono, PCM)                      │
└──────┬───────────────────────────────────────────────────┘
       │ context["audio_path"] = "cache/audio.wav"
       ▼
┌──────────────────────────────────────────────────────────┐
│ TranscribeStage                                           │
│ - 调用 STTBackend.transcribe()                            │
│ - 输出: transcript.json (segments + full_text)            │
└──────┬───────────────────────────────────────────────────┘
       │ context["transcript_path"] = "cache/transcript.json"
       ▼
┌──────────────────────────────────────────────────────────┐
│ AnalyzeStage                                              │
│ - 调用 LLMBackend.analyze()                               │
│ - 输出: analysis.json (title, outline, keywords)          │
└──────┬───────────────────────────────────────────────────┘
       │ context["analysis_path"] = "cache/analysis.json"
       ▼
┌──────────────────────────────────────────────────────────┐
│ ScreenshotStage                                           │
│ - 根据 key_timestamps 提取视频帧                           │
│ - 输出: screenshots/*.jpg                                 │
└──────┬───────────────────────────────────────────────────┘
       │ context["screenshots_map"] = {"0": ["img1.jpg"], ...}
       ▼
┌──────────────────────────────────────────────────────────┐
│ GenerateStage                                             │
│ - 复制截图到 assets/                                       │
│ - 渲染 Jinja2 模板                                         │
│ - 输出: summary.md                                         │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│  summary.md  │
│  + assets/   │
└──────────────┘
```

### Context 数据结构

```python
context = {
    # 初始输入
    "video_path": "/path/to/video.mp4",

    # AudioExtractStage 输出
    "audio_path": "/path/to/cache/audio.wav",

    # TranscribeStage 输出
    "transcript_path": "/path/to/cache/transcript.json",
    "language": "zh",

    # AnalyzeStage 输出
    "analysis_path": "/path/to/cache/analysis.json",

    # ScreenshotStage 输出
    "screenshots_dir": "/path/to/cache/screenshots",
    "screenshots_map": {
        "0": ["section_0_frame_0.jpg", "section_0_frame_1.jpg"],
        "1": ["section_1_frame_0.jpg"],
    },

    # GenerateStage 输出
    "markdown_path": "/path/to/output/summary.md",
}
```

---

## 目录结构

### 代码结构

```
vbook/
├── src/vbook/
│   ├── __init__.py
│   ├── cli/              # CLI 命令
│   │   ├── main.py
│   │   ├── process.py
│   │   ├── init_cmd.py
│   │   └── status.py
│   ├── config/           # 配置管理
│   │   ├── schema.py
│   │   └── loader.py
│   ├── pipeline/         # Pipeline 引擎
│   │   ├── stage.py
│   │   ├── engine.py
│   │   └── tracker.py
│   ├── backends/         # 后端抽象
│   │   ├── base.py
│   │   ├── stt/
│   │   │   ├── whisper.py
│   │   │   └── whisper_remote.py
│   │   └── llm/
│   │       └── litellm_backend.py
│   ├── stages/           # 处理阶段
│   │   ├── audio_extract.py
│   │   ├── transcribe.py
│   │   ├── analyze.py
│   │   ├── screenshot.py
│   │   └── generate.py
│   ├── output/           # 输出生成
│   │   ├── markdown.py
│   │   ├── prompts.py
│   │   └── templates/
│   │       └── summary.md.j2
│   └── utils/            # 工具函数
│       ├── path.py
│       └── retry.py
├── tests/                # 测试
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_pipeline.py
│   ├── test_stages.py
│   └── ...
├── docs/                 # 文档
├── pyproject.toml        # 项目配置
└── README.md
```

### 用户数据结构

```
output/
└── video_name/
    ├── summary.md              # 最终输出
    ├── assets/                 # 图片资源
    │   ├── section_0_frame_0.jpg
    │   └── section_0_frame_1.jpg
    └── .vbook_cache/          # 中间文件
        ├── audio.wav
        ├── transcript.json
        ├── analysis.json
        ├── screenshots/
        │   ├── section_0_frame_0.jpg
        │   └── section_0_frame_1.jpg
        └── status.yaml        # 处理状态
```

---

## 设计模式

### 1. 策略模式（Strategy Pattern）

**应用：** Backend 选择

```python
# 配置驱动的策略选择
if cfg.backends.stt == "whisper_local":
    stt = WhisperSTTBackend(**cfg.backends.whisper_local)
elif cfg.backends.stt == "whisper_remote":
    stt = WhisperRemoteBackend(**cfg.backends.whisper_remote)

# 统一接口调用
result = stt.transcribe(audio_path)
```

**优势：**
- 运行时切换实现
- 易于添加新策略
- 配置驱动

### 2. 模板方法模式（Template Method Pattern）

**应用：** Stage 基类

```python
class Stage(ABC):
    def execute(self, context, tracker):
        # 模板方法
        if self.can_skip(tracker):
            return self.load_cached_result(tracker)

        result = self.run(context)  # 子类实现
        tracker.mark_complete(self.name, result.output)
        return result

    @abstractmethod
    def run(self, context):
        """子类必须实现"""
        pass
```

### 3. 责任链模式（Chain of Responsibility）

**应用：** Pipeline 阶段链

```python
stages = [
    AudioExtractStage(...),
    TranscribeStage(...),
    AnalyzeStage(...),
    ScreenshotStage(...),
    GenerateStage(...),
]

# 依次执行，context 在链中传递
for stage in stages:
    stage.run(context)
```

### 4. 工厂模式（Factory Pattern）

**应用：** Backend 创建（隐式）

```python
def create_stt_backend(config):
    if config.stt == "whisper_local":
        return WhisperSTTBackend(**config.whisper_local)
    elif config.stt == "whisper_remote":
        return WhisperRemoteBackend(**config.whisper_remote)
    else:
        raise ValueError(f"Unknown STT backend: {config.stt}")
```

---

## 关键设计决策

### ADR-001: 使用 Python 而非 Go/Rust

**决策：** 选择 Python 3.11+ 作为实现语言

**理由：**
- AI/ML 生态丰富（Whisper, LiteLLM, etc.）
- 开发效率高，适合快速迭代
- 社区支持好，第三方库多

**权衡：**
- 性能不如 Go/Rust，但对 I/O 密集型任务影响不大
- 部署需要 Python 环境，但 uv 简化了依赖管理

### ADR-002: Stage-based Pipeline 而非 DAG

**决策：** 使用线性 Stage 链而非 DAG（有向无环图）

**理由：**
- 当前需求是线性流程，无需复杂的依赖关系
- 实现简单，易于理解和维护
- 性能足够（阶段间无并行需求）

**权衡：**
- 无法并行执行独立阶段
- 未来如需并行可重构为 DAG

### ADR-003: 配置优先级合并而非覆盖

**决策：** 使用深度合并而非简单覆盖

**理由：**
- 允许部分覆盖（只改需要的字段）
- 更符合用户直觉
- 支持多环境配置

**实现：**
```python
def deep_merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and key in base:
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base
```

### ADR-004: YAML 状态文件而非 SQLite

**决策：** 使用 YAML 文件存储处理状态

**理由：**
- 简单，无需数据库依赖
- 人类可读，便于调试
- 单视频处理，数据量小

**权衡：**
- 不支持复杂查询
- 并发写入需要加锁（当前无并发需求）

### ADR-005: Jinja2 模板而非硬编码

**决策：** 使用 Jinja2 模板生成 Markdown

**理由：**
- 模板与逻辑分离
- 用户可自定义模板
- 易于支持多种输出格式

**示例：**
```jinja2
# {{ analysis.title }}

{% for section in analysis.outline %}
### {{ loop.index }}. {{ section.title }}
{{ section.summary }}
{% endfor %}
```

---

## 扩展点

### 1. 添加新的 STT Backend

```python
# 1. 继承 STTBackend
class GoogleCloudSTTBackend(STTBackend):
    def transcribe(self, audio_path: str) -> TranscriptResult:
        # 调用 Google Cloud Speech API
        ...

# 2. 在 process.py 中注册
if cfg.backends.stt == "google_cloud":
    stt = GoogleCloudSTTBackend(**cfg.backends.google_cloud)

# 3. 在 schema.py 中添加配置
class BackendsConfig(BaseModel):
    google_cloud: dict = Field(default_factory=lambda: {
        "credentials_path": "~/.gcloud/credentials.json",
        "language": "zh-CN",
    })
```

### 2. 添加新的输出格式

```python
# 1. 创建新的生成器
class MindMapGenerator:
    def render(self, analysis: dict) -> str:
        # 生成思维导图格式
        ...

# 2. 创建新的 Stage
class GenerateMindMapStage(Stage):
    name = "generate_mindmap"

    def run(self, context: dict) -> StageResult:
        gen = MindMapGenerator()
        mindmap = gen.render(analysis)
        ...

# 3. 在 Pipeline 中添加
stages.append(GenerateMindMapStage(...))
```

### 3. 添加新的 Pipeline Stage

```python
# 1. 继承 Stage
class SummaryStage(Stage):
    name = "summary"

    def run(self, context: dict) -> StageResult:
        # 生成摘要
        ...

# 2. 插入到 Pipeline
stages = [
    ...,
    AnalyzeStage(...),
    SummaryStage(...),  # 新增
    ScreenshotStage(...),
    ...
]
```

---

## 性能考虑

### 瓶颈分析

| 阶段 | 耗时占比 | 瓶颈 | 优化方向 |
|------|---------|------|---------|
| AudioExtract | ~5% | I/O | 已优化（FFmpeg 高效） |
| Transcribe | ~60% | GPU 计算 | 使用 GPU，选择合适模型大小 |
| Analyze | ~30% | LLM 推理 | 使用 GPU，选择合适模型 |
| Screenshot | ~3% | I/O | 已优化 |
| Generate | ~2% | I/O | 已优化 |

### 优化策略

1. **GPU 加速** - Whisper 和 LLM 都支持 GPU
2. **模型选择** - 根据需求选择合适大小的模型
3. **批量处理** - 未来可并行处理多个视频
4. **缓存** - 断点续处理避免重复计算

---

## 安全考虑

### 1. 输入验证

- 文件路径验证（防止路径遍历）
- 视频格式验证（仅支持 mp4/mkv）
- 配置文件验证（Pydantic）

### 2. 资源限制

- 视频大小限制（建议 < 5GB）
- 处理超时（可配置）
- 磁盘空间检查（未来）

### 3. 敏感信息

- 不记录视频内容到日志
- 配置文件不包含密钥（使用环境变量）
- 中间文件可选清理

---

## 测试策略

### 测试金字塔

```
        ┌─────────┐
        │  E2E    │  ← 少量端到端测试
        ├─────────┤
        │ 集成测试 │  ← 中等数量集成测试
        ├─────────┤
        │ 单元测试 │  ← 大量单元测试
        └─────────┘
```

### 测试覆盖

- **单元测试** - 每个模块独立测试（Mock 依赖）
- **集成测试** - Pipeline 跨模块测试
- **E2E 测试** - 完整视频处理流程（手动）

---

## 下一步

- 了解如何扩展 vbook：[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- 了解测试方案：[TESTING.md](TESTING.md)
- 了解项目规划：[PROJECT_PLAN.md](PROJECT_PLAN.md)
