# vbook 部署指南

> 版本: v0.1.0 | 最后更新: 2026-03-23 | 状态: MVP

本文档指导如何在内网 GPU 服务器上部署 vbook 所需的模型服务。

---

## 部署架构

```
┌─────────────────────────────────────────────┐
│           GPU 服务器（内网）                    │
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

## 服务 1：Ollama + Qwen（LLM 内容分析）

### 1.1 安装 Ollama

**在 Linux 服务器上执行：**

```bash
# 下载并安装
curl -fsSL https://ollama.com/install.sh | sh

# 验证安装
ollama --version
```

### 1.2 拉取 Qwen 模型

```bash
# 拉取 Qwen 3.5 9B 模型（约 9GB，需要等待）
ollama pull qwen3.5:9b

# 验证模型已下载
ollama list

# 快速测试
ollama run qwen3.5:9b "你好，请用一句话介绍自己"
```

**模型选择建议：**
- `qwen3.5:9b` - 推荐，质量好（需要 ~6GB VRAM）
- `qwen3.5:4b` - 备选，内存不足时使用（需要 ~3GB VRAM）
- `qwen3.5:35b` - 最佳质量（需要 ~22GB VRAM）

### 1.3 配置为网络服务

**关键步骤：** Ollama 默认只监听 `127.0.0.1`，需要改为监听所有网卡以支持远程访问。

**方式 1：使用 systemd 服务（推荐）**

```bash
# 编辑 systemd 服务配置
sudo systemctl edit ollama

# 在打开的编辑器中添加以下内容：
[Service]
Environment="OLLAMA_HOST=0.0.0.0:7866"

# 保存并退出，然后重启服务
sudo systemctl restart ollama

# 验证服务状态
sudo systemctl status ollama
```

**方式 2：手动启动（临时测试）**

```bash
# 停止现有服务
sudo systemctl stop ollama

# 手动启动并监听所有网卡
OLLAMA_HOST=0.0.0.0:7866 ollama serve
```

### 1.4 验证远程访问

**从 Windows 开发机测试（替换 `<SERVER_IP>` 为服务器实际 IP）：**

```bash
# 测试 API 可访问性
curl http://<SERVER_IP>:7866/api/tags

# 测试生成功能
curl http://<SERVER_IP>:7866/api/generate -d '{
  "model": "qwen3.5:9b",
  "prompt": "你好",
  "stream": false
}'
```

**预期结果：** 返回 JSON 格式的响应，包含模型列表或生成的文本。

### 1.5 防火墙配置

如果无法访问，需要开放端口：

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 7866/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=7866/tcp
sudo firewall-cmd --reload
```

---

## 服务 2：Whisper API（语音转录）

### 2.1 选择部署方式

推荐使用 `faster-whisper-server`，它提供 OpenAI 兼容的 API 接口。

**方式 1：Docker 部署（推荐，最简单）**

```bash
# 拉取镜像
docker pull fedirz/faster-whisper-server:latest

# 启动服务
docker run -d \
  --name whisper-api \
  --gpus all \
  -p 7867:7867 \
  -e WHISPER__MODEL=medium \
  -e WHISPER__DEVICE=cuda \
  --restart unless-stopped \
  fedirz/faster-whisper-server

# 查看日志
docker logs -f whisper-api
```

**方式 2：Python 虚拟环境部署**

```bash
# 创建虚拟环境
python3 -m venv /opt/whisper-api
source /opt/whisper-api/bin/activate

# 安装（需要 CUDA 环境）
pip install faster-whisper-server

# 启动服务
faster-whisper-server \
  --host 0.0.0.0 \
  --port 7867 \
  --model-size medium \
  --device cuda
```

### 2.2 验证远程访问

**从 Windows 开发机测试：**

```bash
# 测试 API 文档页面
curl http://<SERVER_IP>:7867/docs

# 测试转录功能（需要准备一个测试音频文件）
curl -X POST http://<SERVER_IP>:7867/v1/audio/transcriptions \
  -F "file=@test_audio.wav" \
  -F "model=medium" \
  -F "language=zh"
```

**预期结果：** 返回包含转录文本和时间戳的 JSON。

### 2.3 配置为系统服务（可选）

**创建 systemd 服务文件：**

```bash
sudo nano /etc/systemd/system/whisper-api.service
```

**内容：**

```ini
[Unit]
Description=Whisper API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/whisper-api
ExecStart=/opt/whisper-api/bin/faster-whisper-server --host 0.0.0.0 --port 7867 --model-size medium --device cuda
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启用服务：**

```bash
sudo systemctl daemon-reload
sudo systemctl enable whisper-api
sudo systemctl start whisper-api
sudo systemctl status whisper-api
```

### 2.4 防火墙配置

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 7867/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=7867/tcp
sudo firewall-cmd --reload
```

---

## 服务 3：FFmpeg（音频提取）

vbook 使用 FFmpeg 从视频中提取音频，需要在**开发机**上安装。

### Windows 安装

**方式 1：使用 Chocolatey（推荐）**

```powershell
# 以管理员身份运行 PowerShell
choco install ffmpeg
```

**方式 2：手动安装**

1. 访问 https://ffmpeg.org/download.html#build-windows
2. 下载 Windows 构建版本（推荐 gyan.dev 或 BtbN）
3. 解压到 `C:\ffmpeg`
4. 添加 `C:\ffmpeg\bin` 到系统 PATH 环境变量
5. 重启终端，验证：`ffmpeg -version`

### Linux 安装（如果在服务器上运行 vbook）

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg

# 验证
ffmpeg -version
```

---

## 配置 vbook 连接远程服务

部署完成后，在 Windows 开发机上配置 vbook。

### 1. 创建配置文件

```bash
# 在项目目录下创建配置
cd E:/projects/my_app/vbook
vbook init --source ./test_videos --output ./test_output
```

### 2. 编辑 vbook.yaml

将 `<SERVER_IP>` 替换为你的服务器实际 IP 地址：

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
  stt: whisper_remote          # 使用远程 Whisper
  llm: ollama_qwen

  whisper_remote:
    base_url: http://<SERVER_IP>:7867   # 替换为服务器 IP
    model: medium
    language: zh

  ollama_qwen:
    base_url: http://<SERVER_IP>:7866  # 替换为服务器 IP
    model: qwen3.5:9b
```

### 3. 测试配置

```bash
# 准备一个短视频（1-3 分钟）用于测试
# 运行处理
vbook process test_video.mp4 --output ./test_output

# 查看输出
ls test_output/test_video/
cat test_output/test_video/summary.md
```

---

## 部署检查清单

| 步骤 | 命令 | 预期结果 |
|------|------|---------|
| 1. 安装 Ollama | `ollama --version` | 显示版本号 |
| 2. 拉取 Qwen | `ollama list` | 显示 qwen3.5:9b |
| 3. Ollama 监听 0.0.0.0 | `curl http://<IP>:7866/api/tags` | 返回模型列表 JSON |
| 4. 安装 Whisper API | `curl http://<IP>:7867/docs` | 返回 API 文档页 |
| 5. 测试转录 | POST `/v1/audio/transcriptions` | 返回转录文本 |
| 6. 防火墙放行 | 端口 7866, 7867 | 从 Windows 可访问 |
| 7. 安装 FFmpeg | `ffmpeg -version` | 显示版本信息 |
| 8. vbook 配置 | 编辑 `vbook.yaml` | 指向服务器 IP |
| 9. 端到端测试 | `vbook process test.mp4` | 生成 summary.md |

---

## 故障排查

### Ollama 无法远程访问

**症状：** `curl: (7) Failed to connect`

**解决方案：**
1. 检查 Ollama 是否监听 0.0.0.0：`sudo netstat -tlnp | grep 7866`
2. 检查防火墙：`sudo ufw status` 或 `sudo firewall-cmd --list-ports`
3. 检查服务状态：`sudo systemctl status ollama`

### Whisper API 返回 500 错误

**症状：** HTTP 500 Internal Server Error

**解决方案：**
1. 查看日志：`docker logs whisper-api` 或 `journalctl -u whisper-api -f`
2. 检查 GPU 可用性：`nvidia-smi`
3. 检查模型是否下载完成（首次运行会自动下载）

### vbook 转录失败

**症状：** `TranscribeStage` 失败

**解决方案：**
1. 验证 Whisper API 可访问：`curl http://<IP>:7867/docs`
2. 检查配置文件中的 `base_url` 是否正确
3. 查看 vbook 错误日志，确认具体错误信息

---

## 性能优化建议

### GPU 内存优化

如果 GPU 内存不足，可以：
- 使用更小的模型：`qwen3.5:4b` 或 `whisper small`
- 限制并发处理数量
- 调整 batch size（如果 API 支持）

### 网络优化

- 确保服务器和开发机在同一内网，避免跨网段
- 使用千兆网络，避免 100M 网络瓶颈
- 考虑使用 NFS/SMB 共享视频文件，避免大文件传输

### 模型预热

首次调用会较慢（模型加载），可以预热：

```bash
# Ollama 预热
curl http://<IP>:7866/api/generate -d '{"model":"qwen3.5:9b","prompt":"test"}'

# Whisper 预热
curl -X POST http://<IP>:7867/v1/audio/transcriptions \
  -F "file=@short_audio.wav" -F "model=medium"
```

---

## 硬件要求

### GPU 服务器最低配置

- **GPU**: NVIDIA GPU with CUDA support
  - Qwen 9B: 6GB+ VRAM
  - Whisper medium: 4GB+ VRAM
  - 建议：RTX 3090 (24GB) 或更高
- **内存**: 16GB+ RAM
- **存储**: 50GB+ 可用空间（模型 + 缓存）
- **网络**: 千兆网卡

### Windows 开发机最低配置

- **CPU**: 4 核心+
- **内存**: 8GB+ RAM
- **存储**: 10GB+ 可用空间
- **网络**: 千兆网卡

---

## 下一步

部署完成后，参考 [USER_GUIDE.md](USER_GUIDE.md) 了解如何使用 vbook 处理视频。
