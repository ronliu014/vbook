# vbook

将视频转换为知识文档的CLI工具。

## 功能

- 从视频中提取音频
- 使用Whisper进行语音转录（带时间戳）
- 使用LLM分析内容并生成知识大纲
- 生成Markdown格式的知识文档

## 安装

```bash
# 克隆仓库
git clone <repo>
cd vbook

# 安装依赖
uv sync

# 安装到本地环境
uv pip install -e .

# 验证安装
vbook --version
```

## 快速开始

### 1. 初始化配置

```bash
vbook init --source ./videos --output ./output
```

这会创建一个 `vbook.yaml` 配置文件。

### 2. 处理视频

```bash
# 处理单个视频
vbook process video.mp4 --output ./output

# 处理目录中的所有视频
vbook process ./videos --output ./output
```

### 3. 查看处理状态

```bash
vbook status ./output/video_name
```

## 配置

编辑 `vbook.yaml` 来自定义处理流程：

```yaml
source:
  video_dirs:
    - /path/to/videos

output:
  root: /path/to/output
  structure: mirror

processing:
  intermediate_dir: .vbook_cache
  keep_intermediate: true
  max_retries: 3

backends:
  stt: whisper_local
  llm: ollama_qwen
  whisper_local:
    model: medium
    device: cpu
  ollama_qwen:
    base_url: http://localhost:11434
    model: qwen2.5:14b
```

## 系统要求

- Python 3.11+
- FFmpeg（用于音频提取）
- Ollama + Qwen模型（用于LLM分析）

## 开发

```bash
# 运行测试
uv run pytest -v

# 运行测试并生成覆盖率报告
uv run pytest --cov=src/vbook --cov-report=term-missing
```