# vbook 项目设计文档

> 创建日期: 2026-03-20

## 1. 项目概述

**vbook** (video notebook) 是一个将视频内容转换为结构化知识文档的CLI工具。

### 核心功能

1. **音频提取与转录** - 从视频中提取音频，转换为带时间戳的文字序列
2. **内容分析与大纲生成** - 理解视频内容，生成知识大纲和思维导图结构
3. **视觉内容提取** - 智能提取关键画面截图，支持用户筛选
4. **文档生成** - 输出Markdown（含图片）、思维导图、PPT等多种格式

### 目标用户

- 需要整理在线课程/培训视频的学习者
- 需要归档会议/讲座内容的团队
- 需要将视频内容结构化的知识工作者

---

## 2. 需求分析

### 2.1 功能需求

| 模块 | 需求描述 | 优先级 |
|------|----------|--------|
| 视频输入 | 支持常见视频格式（mp4, mkv, avi等） | P0 |
| 批量处理 | 支持目录级批量处理，保持目录结构 | P0 |
| 语音转录 | 中视频（30分钟-2小时）支持，带时间戳 | P0 |
| 内容分析 | 自动生成知识大纲、关键词提取 | P0 |
| Markdown输出 | 图文并茂的Markdown文档 | P0 |
| 思维导图 | 输出思维导图数据结构 | P1 |
| PPT生成 | 自动生成演示文稿 | P2 |
| 视觉提取 | 场景检测、信息密度分析、用户筛选 | P1 |
| 断点续处理 | 支持从中断处继续处理 | P1 |
| 多语言支持 | 中文优先，预留英文支持 | P1 |

### 2.2 非功能需求

- **性能**: 1小时视频处理时间控制在视频时长的2-4倍内
- **可靠性**: 智能重试机制，失败不丢失进度
- **可扩展性**: 可插拔后端架构，支持替换STT/LLM引擎
- **易用性**: CLI命令简洁，进度可视化，错误信息清晰

### 2.3 约束条件

- 优先开发CLI版本，Web版后续考虑
- Python技术栈
- 支持本地开源方案部署（Whisper + Ollama/Qwen）
- 支持云端API作为备选

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    vbook CLI Application                     │
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
        │  Backend Store │  │ STT  │  │  LLM   │  │  Visual  │
        │   (后端注册表)   │  │Backend│ │Backend │  │ Backend  │
        └────────────────┘  └──┬───┘  └────┬───┘  └─────┬────┘
                              │           │             │
                    ┌─────────┴─────┬─────┴──────┬──────┴──────┐
                    │               │            │             │
              ┌─────▼──────┐ ┌─────▼─────┐ ┌───▼────┐ ┌──────▼─────┐
              │  Whisper   │ │  OpenAI   │ │ Ollama │ │ Screenshot │
              │  (本地)     │ │  (云端)    │ │ (本地)  │ │ Extraction │
              └────────────┘ └───────────┘ └────────┘ └────────────┘
```

### 3.2 模块化Pipeline

处理流程分为5个独立阶段：

```
Stage 1: AudioExtract     → 提取音频文件
Stage 2: Transcribe       → 语音转文字（带时间戳）
Stage 3: Analyze          → 内容分析，生成大纲
Stage 4: VisualExtract    → 提取关键画面截图
Stage 5: Generate         → 生成最终文档
```

每个阶段：
- 独立可测试
- 状态可追踪
- 支持断点续处理
- 失败可重试

### 3.3 可插拔Backend架构

```python
class STTBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptResult: ...

class LLMBackend(ABC):
    @abstractmethod
    def analyze(self, text: str, prompt: str) -> str: ...
    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str) -> str: ...

class VisualBackend(ABC):
    @abstractmethod
    def extract_keyframes(self, video_path: str, timestamps: list) -> list: ...
```

---

## 4. 目录结构设计

### 4.1 项目代码结构

```
vbook/
├── cli/                     # CLI命令层
│   ├── main.py              # Click应用入口
│   ├── process.py           # vbook process 命令
│   ├── status.py            # vbook status 命令
│   └── clean.py             # vbook clean 命令
│
├── config/                  # 配置管理
│   ├── schema.py            # Pydantic配置模型
│   ├── loader.py            # 配置加载（优先级合并）
│   └── defaults.py          # 默认配置值
│
├── pipeline/                # 处理流水线
│   ├── engine.py            # Pipeline编排引擎
│   ├── stage.py             # Stage基类定义
│   └── tracker.py           # 状态追踪和进度管理
│
├── backends/                # 可插拔后端
│   ├── base.py              # Backend抽象基类
│   ├── stt/                 # 语音识别后端
│   ├── llm/                 # LLM后端
│   └── visual/              # 视觉提取后端
│
├── stages/                  # Pipeline各阶段实现
│   ├── audio_extract.py
│   ├── transcribe.py
│   ├── analyze.py
│   ├── visual_extract.py
│   └── generate.py
│
├── output/                  # 输出格式化
│   ├── markdown.py
│   ├── mindmap.py
│   └── templates/
│
└── utils/                   # 工具函数
    ├── path.py
    ├── logger.py
    └── retry.py
```

### 4.2 用户数据目录结构

**配置文件示例 (`vbook.yaml`):**

```yaml
source:
  video_dirs:
    - /path/to/videos/course1
    - /path/to/videos/course2

output:
  root: /path/to/output
  structure: mirror  # 保持源目录结构

processing:
  intermediate_dir: .vbook_cache
  keep_intermediate: true

backends:
  stt: whisper_local
  llm: ollama_qwen

  whisper_local:
    model: large-v3
    device: cuda

  ollama_qwen:
    base_url: http://localhost:11434
    model: qwen2.5:14b
```

**文件布局示例:**

```
源视频:
/path/to/videos/course1/lesson1.mp4

输出:
/path/to/output/course1/lesson1/
├── .vbook_cache/           # 中间文件
│   ├── audio.wav
│   ├── transcript.json
│   ├── screenshots/
│   └── status.yaml
├── summary.md              # 最终输出
├── assets/                 # 图片资源
└── mindmap.json            # 思维导图
```

---

## 5. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 语言 | Python 3.11+ | 生态丰富，AI库支持好 |
| 包管理 | uv + pyproject.toml | 快速依赖管理 |
| CLI框架 | Click | 成熟稳定，支持子命令 |
| 配置管理 | Pydantic + PyYAML | 类型安全 |
| 音视频处理 | FFmpeg + ffmpeg-python | 行业标准 |
| 语音识别 | faster-whisper | 本地高效 |
| LLM集成 | litellm | 统一多种后端 |
| 视觉处理 | OpenCV + Pillow | 场景检测+图像处理 |
| 模板引擎 | Jinja2 | 文档生成 |
| 终端美化 | Rich | 进度条、日志 |
| 测试 | pytest + pytest-cov | 单元测试、覆盖率 |

---

## 6. CLI命令设计

```bash
# 初始化配置
vbook init --source /path/to/videos --output /path/to/output

# 处理单个视频
vbook process /path/to/videos/course1/lesson1.mp4

# 批量处理目录
vbook process /path/to/videos/course1 --recursive

# 处理所有配置的视频目录
vbook process --all

# 查看处理状态
vbook status /path/to/output/course1/lesson1

# 清理中间文件
vbook clean /path/to/output/course1/lesson1 --keep-final

# 查看版本
vbook version
```

---

## 7. 错误处理策略

### 7.1 智能重试

- 自动重试失败步骤（默认3次）
- 指数退避策略
- 记录重试日志

### 7.2 断点续处理

- 每个阶段完成后保存状态到 `status.yaml`
- 重启时检查状态，跳过已完成阶段
- 支持强制重新处理某个阶段

### 7.3 批量处理容错

- 单个视频失败不影响其他视频
- 最终生成处理报告（成功/失败列表）
- 失败视频可单独重新处理

---

## 8. 开发阶段规划

### Phase 1: 基础框架 (MVP)
- CLI骨架和配置系统
- Pipeline引擎和状态追踪
- 音频提取阶段
- Whisper本地转录
- 简单Markdown输出

### Phase 2: 内容分析
- LLM后端集成（Ollama/Qwen）
- 内容分析和大纲生成
- 思维导图输出

### Phase 3: 视觉提取
- 场景变化检测
- 信息密度分析
- 截图提取和筛选
- 图文整合输出

### Phase 4: 增强功能
- 批量处理优化
- PPT生成
- 多语言支持
- 性能优化

---

## 9. 开源方案部署指南

### 9.1 Whisper 本地部署

```bash
# 安装 faster-whisper
pip install faster-whisper

# 下载模型（首次运行自动下载）
# 模型存储在 ~/.cache/huggingface/hub/
```

**推荐模型:**
- `large-v3` - 最佳质量，需要GPU
- `medium` - 平衡选择
- `small` - 快速处理

### 9.2 Ollama + Qwen 部署

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动服务
ollama serve

# 拉取模型
ollama pull qwen2.5:14b

# 测试
ollama run qwen2.5:14b "你好"
```

### 9.3 FFmpeg 安装

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html 并添加到PATH
```

---

## 10. 验收标准

### MVP阶段验收

- [ ] 能够处理单个视频文件
- [ ] 生成带时间戳的转录文本
- [ ] 输出格式正确的Markdown文件
- [ ] CLI命令正常工作

### 完整版本验收

- [ ] 批量处理功能正常
- [ ] 断点续处理可用
- [ ] 图文并茂的输出质量
- [ ] 思维导图输出正确
- [ ] 错误处理和重试机制完善
- [ ] 文档完整（README、配置说明）