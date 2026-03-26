# vbook 部署指南（Windows 服务器版）

> 版本: v0.1.0 | 最后更新: 2026-03-25 | 状态: MVP

本文档指导如何在 **Windows GPU 服务器**上部署 vbook 所需的模型服务。

---

## 部署架构

```
┌─────────────────────────────────────────────┐
│       Windows GPU 服务器（内网）               │
│                                             │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │  Ollama + Qwen  │  │  Whisper API     │  │
│  │  :7866         │  │  :7867           │  │
│  │  (LLM 分析)     │  │  (语音转录)       │  │
│  └─────────────────┘  └──────────────────┘  │
│           GPU                  GPU          │
└─────────────────────────────────────────────┘
          ▲                      ▲
          │      HTTP API        │
          └──────────┬───────────┘
                     │
┌─────────────────────────────────────────────┐
│        Windows 开发机                        │
│                                             │
│  vbook process video.mp4                    │
│  → 调用远程 Whisper API 转录                  │
│  → 调用远程 Ollama API 分析                   │
│  → 本地生成 Markdown                         │
└─────────────────────────────────────────────┘
```

---

## 前置条件

### 硬件要求

- **GPU**: NVIDIA GPU with CUDA support
  - Qwen 3.5 9B: 6GB+ VRAM
  - Whisper medium: 4GB+ VRAM
  - 推荐：RTX 3090 (24GB) 或更高
- **内存**: 16GB+ RAM
- **存储**: 50GB+ 可用空间（模型 + 缓存）
- **网络**: 千兆网卡

### 软件要求

- **操作系统**: Windows 10/11 或 Windows Server 2019+
- **NVIDIA 驱动**: 最新版（https://www.nvidia.com/Download/index.aspx）
- **CUDA Toolkit**: 11.8+ 或 12.x（https://developer.nvidia.com/cuda-downloads）
- **Python**: 3.11+（用于 Whisper API）

### 验证 GPU 环境

打开 PowerShell，运行：

```powershell
# 检查 NVIDIA 驱动
nvidia-smi

# 预期输出：显示 GPU 型号、驱动版本、CUDA 版本
```

如果 `nvidia-smi` 无输出或报错，需要先安装 NVIDIA 驱动。

---

## 服务 1：Ollama + Qwen（LLM 内容分析）

### 1.1 安装 Ollama

1. 访问 https://ollama.com/download/windows
2. 下载 `OllamaSetup.exe`
3. 双击运行安装程序
4. 安装完成后，Ollama 会自动作为后台服务启动

**验证安装（PowerShell）：**

```powershell
ollama --version
# 预期输出: ollama version 0.x.x
```

### 1.2 拉取 Qwen 模型

```powershell
# 拉取 Qwen 3.5 9B 模型（约 6GB，需要等待）
ollama pull qwen3.5:9b

# 验证模型已下载
ollama list

# 快速测试
ollama run qwen3.5:9b "你好，请用一句话介绍自己"
```

**模型选择建议：**

| 模型 | VRAM 需求 | 质量 | 适用场景 |
|------|----------|------|---------|
| `qwen3.5:4b` | ~3GB | 中等 | 内存不足时 |
| `qwen3.5:9b` | ~6GB | 推荐 | 默认选择 |
| `qwen3.5:35b` | ~24GB | 最佳 | 高端 GPU |

### 1.3 配置远程访问

**关键步骤：** Ollama 默认只监听 `127.0.0.1`，需要改为监听所有网卡以支持远程访问。

**方法 1：设置系统环境变量（推荐，永久生效）**

1. 打开 **系统属性** → **高级** → **环境变量**
2. 在 **系统变量** 中点击 **新建**
3. 变量名：`OLLAMA_HOST`
4. 变量值：`0.0.0.0:7866`
5. 点击 **确定** 保存
6. **重启 Ollama 服务**（任务栏右键 Ollama 图标 → Quit → 重新打开 Ollama）

或者用 PowerShell（以管理员身份运行）：

```powershell
# 设置系统环境变量
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:7866", "Machine")

# 重启 Ollama 服务
taskkill /f /im ollama.exe 2>$null
Start-Sleep -Seconds 2
Start-Process "ollama" "serve"
```

**方法 2：临时启动（仅当前会话）**

```powershell
# 停止现有服务
taskkill /f /im ollama.exe 2>$null

# 设置环境变量并启动
$env:OLLAMA_HOST = "0.0.0.0:7866"
ollama serve
```

### 1.4 验证远程访问

**从 Windows 开发机测试（替换 `<SERVER_IP>` 为服务器实际 IP）：**

```powershell
# 测试 API 可访问性
curl http://<SERVER_IP>:7866/api/tags

# 测试生成功能
curl http://<SERVER_IP>:7866/api/generate -d '{"model":"qwen3.5:9b","prompt":"你好","stream":false}'
```

**或在浏览器中访问：** `http://<SERVER_IP>:7866/`，应显示 "Ollama is running"。

### 1.5 防火墙配置

**PowerShell（以管理员身份运行）：**

```powershell
# 添加入站规则允许 7866 端口
New-NetFirewallRule -DisplayName "Ollama API" -Direction Inbound -Protocol TCP -LocalPort 7866 -Action Allow

# 验证规则
Get-NetFirewallRule -DisplayName "Ollama API" | Format-Table
```

**或手动操作：**

1. 打开 **Windows Defender 防火墙** → **高级设置**
2. 点击 **入站规则** → **新建规则**
3. 选择 **端口** → 下一步
4. 选择 **TCP**，输入端口 `7866` → 下一步
5. 选择 **允许连接** → 下一步
6. 勾选 **域**、**专用**、**公用** → 下一步
7. 名称输入 `Ollama API` → 完成

### 1.6 设置 Ollama 开机自启

Ollama Windows 安装版默认会开机自启。如果需要手动管理：

```powershell
# 检查 Ollama 是否在运行
tasklist /fi "imagename eq ollama.exe"

# 手动启动
Start-Process "ollama" "serve"
```

---

## 服务 2：Whisper API（语音转录）

### 2.1 选择部署方式

#### 方式 1：Docker Desktop 部署（推荐，最简单）

**前置条件：** 安装 Docker Desktop for Windows

1. 下载：https://www.docker.com/products/docker-desktop/
2. 安装时勾选 **Use WSL 2 based engine**
3. 安装后重启电脑
4. 打开 Docker Desktop，进入 **Settings** → **Resources** → **WSL integration**，勾选启用

**安装 NVIDIA Container Toolkit（Docker GPU 支持）：**

```powershell
# 确保 Docker Desktop 已启动
docker --version

# 拉取并启动 Whisper API 服务
docker run -d `
  --name whisper-api `
  --gpus all `
  -p 7867:7867 `
  -e WHISPER__MODEL=medium `
  -e WHISPER__DEVICE=cuda `
  --restart unless-stopped `
  fedirz/faster-whisper-server

# 查看日志
docker logs -f whisper-api
```

**注意：** Windows Docker GPU 支持需要：
- Windows 11 或 Windows 10 21H2+
- NVIDIA 驱动 >= 510.06
- WSL 2 已启用

#### 方式 2：Python 虚拟环境部署

如果 Docker GPU 支持有问题，可以直接用 Python 部署。

**安装 Python 3.11+：**

1. 下载：https://www.python.org/downloads/
2. 安装时勾选 **Add to PATH**

**创建虚拟环境并安装：**

```powershell
# 创建虚拟环境
python -m venv D:\whisper
D:\whisper\Scripts\Activate.ps1

# 安装 faster-whisper-server
pip install faster-whisper-server

# 启动服务
faster-whisper-server --host 0.0.0.0 --port 7867 --model-size medium --device cuda
```

**如果 `faster-whisper-server` 安装失败，可以使用替代方案：**

```powershell
# 安装替代方案
pip install faster-whisper uvicorn fastapi python-multipart

# 创建简易 API 服务脚本
```

创建文件 `D:\whisper\server.py`：

```python
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from faster_whisper import WhisperModel

app = FastAPI()
model = WhisperModel("medium", device="cuda")

@app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model_name: str = Form("medium", alias="model"),
    language: str = Form("zh"),
    response_format: str = Form("verbose_json"),
):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    segments_gen, info = model.transcribe(tmp_path, language=language)
    segments = []
    full_text_parts = []
    for seg in segments_gen:
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        full_text_parts.append(seg.text.strip())

    Path(tmp_path).unlink(missing_ok=True)

    return {
        "language": info.language,
        "text": "\n".join(full_text_parts),
        "segments": segments,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7867)
```

**启动服务：**

```powershell
cd D:\whisper
D:\whisper\Scripts\Activate.ps1
python server.py
```

### 2.2 验证远程访问

**从 Windows 开发机测试：**

```powershell
# 测试 API 文档页面（浏览器访问）
# http://<SERVER_IP>:7867/docs

# 测试转录功能（需要准备一个测试音频文件）
curl -X POST "http://<SERVER_IP>:7867/v1/audio/transcriptions" -F "file=@test_audio.wav" -F "model=medium" -F "language=zh"
```

### 2.3 防火墙配置

```powershell
# PowerShell（管理员）
New-NetFirewallRule -DisplayName "Whisper API" -Direction Inbound -Protocol TCP -LocalPort 7867 -Action Allow
```

### 2.4 设置 Whisper API 开机自启

**方式 1：使用 NSSM（Non-Sucking Service Manager）**

```powershell
# 下载 NSSM: https://nssm.cc/download
# 解压到 C:\nssm

# 安装为 Windows 服务
C:\nssm\nssm.exe install WhisperAPI "D:\whisper\Scripts\python.exe" "D:\whisper\server.py"

# 启动服务
C:\nssm\nssm.exe start WhisperAPI

# 查看服务状态
C:\nssm\nssm.exe status WhisperAPI
```

**方式 2：使用任务计划程序**

1. 打开 **任务计划程序**（`taskschd.msc`）
2. 点击 **创建基本任务**
3. 名称：`Whisper API Server`
4. 触发器：**计算机启动时**
5. 操作：**启动程序**
   - 程序：`D:\whisper\Scripts\python.exe`
   - 参数：`D:\whisper\server.py`
   - 起始目录：`D:\whisper`
6. 勾选 **使用最高权限运行**
7. 完成

**方式 3：Docker（如果使用 Docker 部署）**

Docker Desktop 中 `--restart unless-stopped` 已确保容器随 Docker 自动启动。只需确保 Docker Desktop 开机自启（默认已开启）。

---

## 配置 vbook 连接远程服务

部署完成后，在 Windows 开发机上配置 vbook。

### 1. 创建配置文件

```bash
cd E:/projects/my_app/vbook
vbook init --source ./test_videos --output ./test_output
```

### 2. 编辑 vbook.yaml

将 `<SERVER_IP>` 替换为 GPU 服务器的实际 IP 地址：

```yaml
source:
  video_dirs:
    - E:/projects/my_app/vbook/test_videos

output:
  root: E:/projects/my_app/vbook/test_output
  structure: mirror

processing:
  intermediate_dir: .vbook_cache
  keep_intermediate: true
  max_retries: 3

backends:
  stt: whisper_remote
  llm: ollama_qwen

  whisper_remote:
    base_url: http://<SERVER_IP>:7867
    model: medium
    language: zh

  ollama_qwen:
    base_url: http://<SERVER_IP>:7866
    model: qwen3.5:9b
```

### 3. 测试连接

```bash
# 测试 Ollama
curl http://<SERVER_IP>:7866/api/tags

# 测试 Whisper
curl http://<SERVER_IP>:7867/docs
```

---

## 部署检查清单

| 步骤 | 命令/操作 | 预期结果 |
|------|----------|---------|
| 1. GPU 驱动 | `nvidia-smi` | 显示 GPU 型号和 CUDA 版本 |
| 2. 安装 Ollama | `ollama --version` | 显示版本号 |
| 3. 拉取 Qwen | `ollama list` | 显示 qwen3.5:9b |
| 4. Ollama 远程访问 | 浏览器 `http://<IP>:7866/` | 显示 "Ollama is running" |
| 5. 安装 Whisper API | 浏览器 `http://<IP>:7867/docs` | 显示 API 文档 |
| 6. 防火墙 7866 | `curl http://<IP>:7866/api/tags` | 返回模型列表 |
| 7. 防火墙 7867 | `curl http://<IP>:7867/docs` | 返回 API 文档 |
| 8. vbook 配置 | 编辑 `vbook.yaml` | 填入服务器 IP |
| 9. 端到端测试 | `vbook process test.mp4` | 生成 summary.md |

---

## 故障排查

### Ollama 无法远程访问

**症状：** 浏览器或 curl 无法连接 `http://<IP>:7866`

**排查步骤：**

```powershell
# 1. 检查 Ollama 是否运行
tasklist /fi "imagename eq ollama.exe"

# 2. 检查监听地址
netstat -an | findstr "7866"
# 应显示 0.0.0.0:7866 而非 127.0.0.1:7866

# 3. 检查环境变量
echo %OLLAMA_HOST%
# 应显示 0.0.0.0:7866

# 4. 检查防火墙
Get-NetFirewallRule -DisplayName "Ollama API"
```

**解决方案：**

- 如果监听 `127.0.0.1`：重新设置 `OLLAMA_HOST` 环境变量并重启 Ollama
- 如果防火墙阻挡：添加防火墙规则
- 如果 Ollama 未运行：手动启动 `ollama serve`

### Whisper API 返回 500 错误

**症状：** POST 转录请求返回 HTTP 500

**排查步骤：**

```powershell
# 1. 查看 Docker 日志
docker logs whisper-api  # 仅 Docker 部署方式

# 2. 或查看 Python 控制台输出（如果用 Python 方式部署）

# 3. 检查 GPU 可用性
nvidia-smi
# 确认 GPU 未被占满
```

**常见原因：**
- GPU 内存不足：尝试使用更小的模型（`small`）
- CUDA 版本不兼容：更新 NVIDIA 驱动
- 模型首次下载：等待模型下载完成后重试

### Docker GPU 支持问题

**症状：** `docker run --gpus all` 失败

**排查步骤：**

```powershell
# 1. 检查 WSL 2
wsl --status

# 2. 检查 Docker Desktop 设置
# Settings → General → Use the WSL 2 based engine ✓

# 3. 测试 GPU
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**解决方案：**
- 安装或更新 WSL 2：`wsl --update`
- 确保 Docker Desktop 使用 WSL 2 引擎
- 如果 Docker GPU 始终有问题，改用 Python 虚拟环境方式部署 Whisper

### 网络连通性问题

**症状：** 开发机无法访问服务器

```powershell
# 1. 测试网络连通性
ping <SERVER_IP>

# 2. 测试端口
Test-NetConnection -ComputerName <SERVER_IP> -Port 7866
Test-NetConnection -ComputerName <SERVER_IP> -Port 7867
```

**解决方案：**
- 确认两台机器在同一网段
- 检查服务器防火墙
- 检查是否有网络安全策略阻挡

---

## 性能优化建议

### GPU 内存管理

```powershell
# 查看 GPU 使用情况
nvidia-smi

# 如果 GPU 内存紧张，可以同时使用两张 GPU（如果有）
# Ollama 自动使用可用 GPU
# Whisper 需要在启动时指定 device

# 或使用更小的模型
ollama pull qwen3.5:4b  # 替代 9b
# Whisper 使用 small 替代 medium
```

### 模型预热

首次调用会较慢（模型加载），可以预热：

```powershell
# Ollama 预热
curl http://localhost:7866/api/generate -d '{\"model\":\"qwen3.5:9b\",\"prompt\":\"test\",\"stream\":false}'

# Whisper 预热（准备一个短音频文件）
curl -X POST http://localhost:7867/v1/audio/transcriptions -F "file=@short_audio.wav" -F "model=medium"
```

### 网络优化

- 确保服务器和开发机在同一内网
- 使用千兆网络
- 考虑使用共享文件夹存放视频，避免大文件网络传输

---

## 参考链接

- **Ollama Windows**: https://ollama.com/download/windows
- **Docker Desktop**: https://www.docker.com/products/docker-desktop/
- **NVIDIA 驱动**: https://www.nvidia.com/Download/index.aspx
- **CUDA Toolkit**: https://developer.nvidia.com/cuda-downloads
- **faster-whisper-server**: https://github.com/fedirz/faster-whisper-server
- **NSSM**: https://nssm.cc

---

## 下一步

部署完成后，参考 [USER_GUIDE.md](USER_GUIDE.md) 了解如何使用 vbook 处理视频。
