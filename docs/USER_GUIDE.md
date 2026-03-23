# vbook 用户指南

> 版本: v0.1.0 | 最后更新: 2026-03-23 | 状态: MVP

本文档面向 vbook 的终端用户，介绍如何安装、配置和使用 vbook 将视频转换为知识文档。

---

## 目录

1. [系统要求](#系统要求)
2. [安装](#安装)
3. [快速开始](#快速开始)
4. [配置详解](#配置详解)
5. [CLI 命令参考](#cli-命令参考)
6. [使用示例](#使用示例)
7. [输出文件说明](#输出文件说明)
8. [常见问题](#常见问题)
9. [故障排查](#故障排查)

---

## 系统要求

### 开发机（运行 vbook 的机器）

- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.11 或更高版本
- **FFmpeg**: 用于音频提取（必须）
- **内存**: 8GB+ RAM
- **存储**: 10GB+ 可用空间
- **网络**: 能够访问内网 GPU 服务器（如果使用远程模型）

### GPU 服务器（运行模型服务）

详见 [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/ronliu014/vbook.git
cd vbook
```

### 2. 安装依赖

vbook 使用 `uv` 作为包管理器。

**安装 uv：**

```bash
# Windows (PowerShell)
pip install uv

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**安装 vbook 依赖：**

```bash
# 同步依赖
uv sync

# 安装到本地环境（可选，用于全局命令）
uv pip install -e .
```

### 3. 安装 FFmpeg

**Windows:**
```powershell
# 使用 Chocolatey
choco install ffmpeg

# 或手动下载：https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

**验证安装：**
```bash
ffmpeg -version
```

### 4. 验证 vbook 安装

```bash
vbook --version
# 输出: vbook, version 0.1.0

vbook --help
# 显示可用命令
```

---

## 快速开始

### 第一步：初始化配置

```bash
vbook init --source ./videos --output ./output
```

这会在当前目录创建 `vbook.yaml` 配置文件。

### 第二步：编辑配置

打开 `vbook.yaml`，配置远程服务地址（将 `<SERVER_IP>` 替换为实际 IP）：

```yaml
backends:
  stt: whisper_remote
  llm: ollama_qwen

  whisper_remote:
    base_url: http://<SERVER_IP>:8000
    model: medium
    language: zh

  ollama_qwen:
    base_url: http://<SERVER_IP>:11434
    model: qwen2.5:14b
```

### 第三步：处理视频

```bash
# 处理单个视频
vbook process video.mp4

# 处理目录中的所有视频
vbook process ./videos

# 指定输出目录
vbook process video.mp4 --output ./my_output
```

### 第四步：查看结果

```bash
# 查看生成的 Markdown 文档
cat output/video/summary.md

# 查看处理状态
vbook status output/video
```

---

## 配置详解

vbook 使用 YAML 格式的配置文件，支持三层配置优先级：

1. **全局配置**: `~/.vbook/config.yaml`（最低优先级）
2. **项目配置**: `./vbook.yaml`（中等优先级）
3. **CLI 参数**: 命令行参数（最高优先级）

### 完整配置示例

```yaml
# 视频源配置
source:
  video_dirs:
    - /path/to/videos/course1
    - /path/to/videos/course2

# 输出配置
output:
  root: /path/to/output        # 输出根目录
  structure: mirror            # 目录结构：mirror（镜像源目录）

# 处理配置
processing:
  intermediate_dir: .vbook_cache   # 中间文件目录名
  keep_intermediate: true          # 保留中间文件
  max_retries: 3                   # 失败重试次数

# 后端配置
backends:
  stt: whisper_remote          # STT 后端：whisper_local 或 whisper_remote
  llm: ollama_qwen             # LLM 后端：ollama_qwen

  # 本地 Whisper 配置（进程内运行）
  whisper_local:
    model: medium              # 模型：tiny, base, small, medium, large
    device: cpu                # 设备：cpu 或 cuda

  # 远程 Whisper 配置（HTTP API）
  whisper_remote:
    base_url: http://192.168.1.100:8000
    model: medium
    language: zh               # 语言：zh, en, ja, etc.

  # Ollama + Qwen 配置
  ollama_qwen:
    base_url: http://192.168.1.100:11434
    model: qwen2.5:14b         # 模型：qwen2.5:7b, qwen2.5:14b, qwen2.5:32b
```

### 配置字段说明

#### source（视频源）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `video_dirs` | list[str] | `[]` | 视频源目录列表 |

#### output（输出）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `root` | str | `None` | 输出根目录，为空时使用视频同级目录 |
| `structure` | str | `"mirror"` | 目录结构，当前仅支持 `mirror` |

#### processing（处理）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `intermediate_dir` | str | `".vbook_cache"` | 中间文件目录名 |
| `keep_intermediate` | bool | `true` | 是否保留中间文件（音频、转录、分析） |
| `max_retries` | int | `3` | 阶段失败时的最大重试次数 |

#### backends（后端）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stt` | str | `"whisper_local"` | STT 后端选择 |
| `llm` | str | `"ollama_qwen"` | LLM 后端选择 |
| `whisper_local` | dict | 见上 | 本地 Whisper 配置 |
| `whisper_remote` | dict | 见上 | 远程 Whisper 配置 |
| `ollama_qwen` | dict | 见上 | Ollama + Qwen 配置 |

---

## CLI 命令参考

### vbook init

初始化 vbook 配置文件。

**语法：**
```bash
vbook init --source <SOURCE_DIR> --output <OUTPUT_DIR> [--config <CONFIG_FILE>]
```

**参数：**
- `--source, -s`: 视频源目录（必需）
- `--output, -o`: 输出根目录（必需）
- `--config, -c`: 配置文件路径（默认：`vbook.yaml`）

**示例：**
```bash
# 创建默认配置
vbook init --source ./videos --output ./output

# 指定配置文件名
vbook init -s ./videos -o ./output -c my_config.yaml
```

### vbook process

处理视频文件或目录。

**语法：**
```bash
vbook process <TARGET> [--output <OUTPUT_DIR>] [--config <CONFIG_FILE>] [--force]
```

**参数：**
- `<TARGET>`: 视频文件或目录路径（必需）
- `--output, -o`: 输出目录（可选，覆盖配置文件）
- `--config, -c`: 配置文件路径（可选）
- `--force, -f`: 强制重新处理所有阶段（删除缓存）

**示例：**
```bash
# 处理单个视频
vbook process video.mp4

# 处理目录（递归查找 .mp4 和 .mkv）
vbook process ./videos

# 指定输出目录
vbook process video.mp4 --output ./my_output

# 使用自定义配置
vbook process video.mp4 --config prod_config.yaml

# 强制重新处理（忽略缓存）
vbook process video.mp4 --force
```

### vbook status

查看视频处理状态。

**语法：**
```bash
vbook status <OUTPUT_DIR>
```

**参数：**
- `<OUTPUT_DIR>`: 输出目录路径（必需）

**示例：**
```bash
vbook status output/video_name
```

**输出示例：**
```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ 阶段          ┃ 状态    ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ audio_extract │ success │
│ transcribe    │ success │
│ analyze       │ success │
│ generate      │ success │
└───────────────┴─────────┘
```

---

## 使用示例

### 示例 1：处理单个视频

```bash
# 1. 准备视频
mkdir -p test_videos
cp my_lecture.mp4 test_videos/

# 2. 初始化配置
vbook init --source test_videos --output test_output

# 3. 编辑 vbook.yaml，配置服务器地址

# 4. 处理视频
vbook process test_videos/my_lecture.mp4

# 5. 查看结果
cat test_output/my_lecture/summary.md
```

### 示例 2：批量处理目录

```bash
# 目录结构：
# videos/
#   ├── course1/
#   │   ├── lesson1.mp4
#   │   └── lesson2.mp4
#   └── course2/
#       └── lesson1.mp4

# 处理整个目录
vbook process videos --output output

# 输出结构（mirror）：
# output/
#   ├── course1/
#   │   ├── lesson1/
#   │   │   ├── summary.md
#   │   │   ├── assets/
#   │   │   └── .vbook_cache/
#   │   └── lesson2/
#   └── course2/
#       └── lesson1/
```

### 示例 3：断点续处理

```bash
# 首次处理（假设在 analyze 阶段失败）
vbook process video.mp4
# 错误: analyze stage failed

# 修复问题后，重新运行（自动跳过已完成的阶段）
vbook process video.mp4
# ✓ audio_extract (skipped)
# ✓ transcribe (skipped)
# ✓ analyze (running)
# ✓ generate (running)
```

### 示例 4：强制重新处理

```bash
# 删除缓存，重新处理所有阶段
vbook process video.mp4 --force
```

---

## 输出文件说明

处理完成后，每个视频会生成以下文件结构：

```
output/video_name/
├── summary.md              # 最终输出：Markdown 知识文档
├── assets/                 # 图片资源目录
│   └── *.jpg              # 视频截图（如果有）
└── .vbook_cache/          # 中间文件（可选保留）
    ├── audio.wav          # 提取的音频
    ├── transcript.json    # 转录结果（带时间戳）
    ├── analysis.json      # 内容分析结果
    ├── screenshots/       # 原始截图
    └── status.yaml        # 处理状态
```

### summary.md 格式

```markdown
# 视频标题

**关键词：** 关键词1, 关键词2, 关键词3

---

## 知识大纲

### 1. 章节标题

章节摘要内容...

![章节标题](assets/screenshot_1.jpg)

### 2. 另一个章节

...
```

### transcript.json 格式

```json
{
  "language": "zh",
  "full_text": "完整转录文本...",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "你好，欢迎来到本次课程"
    },
    {
      "start": 5.2,
      "end": 10.8,
      "text": "今天我们将学习..."
    }
  ]
}
```

### analysis.json 格式

```json
{
  "title": "Python 入门教程",
  "keywords": ["Python", "编程", "入门"],
  "outline": [
    {
      "title": "变量和数据类型",
      "summary": "介绍 Python 的基本数据类型...",
      "key_timestamps": [60.0, 120.5]
    }
  ]
}
```

---

## 常见问题

### Q1: 支持哪些视频格式？

**A:** 当前支持 `.mp4` 和 `.mkv` 格式。其他格式可以先用 FFmpeg 转换：

```bash
ffmpeg -i input.avi -c:v copy -c:a copy output.mp4
```

### Q2: 处理一个视频需要多长时间？

**A:** 取决于视频长度和服务器性能：

- **音频提取**: 几秒（本地 FFmpeg）
- **语音转录**: 约为视频时长的 10-20%（GPU Whisper）
- **内容分析**: 1-3 分钟（取决于转录文本长度）
- **截图提取**: 几秒
- **文档生成**: 几秒

**示例：** 1 小时视频，总处理时间约 8-15 分钟。

### Q3: 可以离线使用吗？

**A:** 部分可以。如果使用 `whisper_local` 和本地部署的 Ollama，可以完全离线。但首次运行需要联网下载模型。

### Q4: 转录准确率如何？

**A:** 取决于：
- 音频质量（清晰度、背景噪音）
- 说话人口音
- Whisper 模型大小（medium 通常足够）

中文普通话在清晰音频下准确率可达 95%+。

### Q5: 生成的大纲质量如何？

**A:** 取决于：
- LLM 模型质量（qwen2.5:14b 效果较好）
- 转录文本质量
- 视频内容结构化程度

建议使用 14B 或更大的模型以获得更好的分析质量。

### Q6: 可以自定义输出格式吗？

**A:** 可以。编辑 `src/vbook/output/templates/summary.md.j2` 模板文件，使用 Jinja2 语法自定义格式。

### Q7: 如何处理多语言视频？

**A:** 修改配置文件中的 `language` 参数：

```yaml
whisper_remote:
  language: en  # 英文
  # 或 ja（日语）、ko（韩语）等
```

### Q8: 中间文件占用空间大吗？

**A:** 取决于视频长度：
- 音频文件：约为视频大小的 10-20%
- 转录 JSON：几百 KB
- 分析 JSON：几十 KB
- 截图：每张约 100-500 KB

可以设置 `keep_intermediate: false` 自动清理。

---

## 故障排查

### 问题 1：`ModuleNotFoundError: No module named 'vbook'`

**原因：** vbook 未正确安装。

**解决：**
```bash
cd /path/to/vbook
uv sync
uv pip install -e .
```

### 问题 2：`ffmpeg: command not found`

**原因：** FFmpeg 未安装或不在 PATH 中。

**解决：**
```bash
# 验证安装
ffmpeg -version

# 如果未安装，参考"安装"章节
```

### 问题 3：`Connection refused` 或 `Failed to connect`

**原因：** 无法连接到远程服务（Whisper 或 Ollama）。

**解决：**
1. 检查服务器 IP 是否正确
2. 检查服务是否运行：`curl http://<IP>:11434/api/tags`
3. 检查防火墙是否放行端口
4. 检查网络连通性：`ping <SERVER_IP>`

### 问题 4：`TranscribeStage failed: HTTP 500`

**原因：** Whisper API 内部错误。

**解决：**
1. 查看 Whisper API 日志：`docker logs whisper-api`
2. 检查 GPU 是否可用：`nvidia-smi`（在服务器上）
3. 重启 Whisper 服务：`docker restart whisper-api`

### 问题 5：生成的大纲质量差

**原因：** 转录质量差或 LLM 模型太小。

**解决：**
1. 检查转录文本：`cat output/video/.vbook_cache/transcript.json`
2. 如果转录质量差，尝试更大的 Whisper 模型（large）
3. 如果转录正常，尝试更大的 LLM 模型（qwen2.5:32b）

### 问题 6：处理速度很慢

**原因：** 可能使用了 CPU 而非 GPU。

**解决：**
1. 确认服务器 GPU 可用：`nvidia-smi`
2. 检查 Whisper API 配置：`device: cuda`
3. 检查 Ollama 是否使用 GPU（Ollama 自动检测）

### 问题 7：`PermissionError` 或文件访问错误

**原因：** 权限不足或文件被占用。

**解决：**
```bash
# 检查文件权限
ls -la output/

# 确保有写权限
chmod -R u+w output/
```

### 问题 8：处理中断后无法继续

**原因：** 状态文件损坏。

**解决：**
```bash
# 删除状态文件，重新处理
rm output/video/.vbook_cache/status.yaml
vbook process video.mp4
```

---

## 获取帮助

- **GitHub Issues**: https://github.com/ronliu014/vbook/issues
- **文档**:
  - [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
  - [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计（待创建）
  - [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - 开发指南（待创建）

---

## 下一步

- 了解如何部署模型服务：[DEPLOYMENT.md](DEPLOYMENT.md)
- 了解如何扩展 vbook：[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)（待创建）
- 查看项目路线图：[PROJECT_PLAN.md](PROJECT_PLAN.md)（待创建）
