# vbook 部署实操手册（RTX 4090 服务器）

> 最后更新: 2026-03-25 | 适用硬件: 双 RTX 4090 Windows 服务器

本文档是针对当前内网 GPU 服务器的**实操部署手册**，按步骤执行即可完成部署。

通用部署指南请参考 [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md)。

---

## 服务器硬件信息

| 项目 | 配置 |
|------|------|
| **GPU** | NVIDIA GeForce RTX 4090 × 2（使用 GPU 0） |
| **GPU VRAM** | 24GB（已用 ~5.1GB，可用 ~19GB） |
| **CPU** | 16 核 32 线程 @ 3.10GHz |
| **内存** | 107GB 可用 @ 2400MHz |
| **驱动** | 32.0.15.7652 |
| **操作系统** | Windows |

---

## 最佳模型配置

```
RTX 4090 GPU 0（24GB VRAM）
├── 已占用:           ~5.1GB
├── Ollama qwen3.5:9b:   ~6GB
├── Whisper medium:       ~2GB
├── 剩余:              ~10.9GB（余量充足）
└── 总计:              24GB
```

| 服务 | 模型 | VRAM | 端口 | 理由 |
|------|------|------|------|------|
| **Ollama** | qwen3.5:9b | ~6GB | 7866 | 原生多模态，性能优于 qwen2.5:14b，VRAM 占用更少 |
| **Whisper** | medium | ~2GB | 7867 | 中文 95%+ 准确率，速度快 |

> **升级说明：** Qwen 3.5 相比 2.5 架构全面升级，9b 模型内置视觉理解能力，256K 上下文窗口，201 种语言支持。如果转录质量不满意，Whisper 可升级到 `large-v3`（+2GB VRAM），VRAM 余量充足。

---

## 部署步骤

### 第 1 步：验证 GPU 环境（2 分钟）

打开 **PowerShell**：

```powershell
nvidia-smi
```

确认输出中能看到两块 RTX 4090，记住 GPU 0 的信息。

---

### 第 2 步：安装 Ollama（5 分钟）

1. 浏览器打开 https://ollama.com/download/windows
2. 下载 `OllamaSetup.exe`
3. 双击运行，按提示安装
4. 安装完成后验证：

```powershell
ollama --version
```

---

### 第 3 步：配置 Ollama 环境变量（2 分钟）

以**管理员身份**打开 PowerShell：

```powershell
# 监听所有网卡，使用自定义端口 7866
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:7866", "Machine")

# 强制使用 GPU 0
[System.Environment]::SetEnvironmentVariable("CUDA_VISIBLE_DEVICES", "0", "Machine")

# 自定义模型存储路径（可选，避免占用 C 盘空间）
[System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama\models", "Machine")
```

**使用 Ollama 管理脚本启动：**

将以下脚本保存为 `manage.ps1`（建议放在 `C:\scripts\` 目录下）：

```powershell
<#
.SYNOPSIS
Ollama One-Click Manager (GPU + Port + Custom Model Path)
#>

# ====================== 配置区（只改这里）======================
$GPU_ID = "0"
$OLLAMA_HOST = "0.0.0.0"
$OLLAMA_PORT = "7866"
$OLLAMA_MODELS_PATH = "D:\ollama\models"  # <-- 模型存储路径
# ==============================================================

# ====================== 自动设置窗口标题（新增）======================
$host.ui.RawUI.WindowTitle = "Ollama API Service | GPU:$GPU_ID | Port:$OLLAMA_PORT | Models:D:\ollama\models"

function Stop-OllamaCustom {
    Write-Host "`n[-] Stopping Ollama..." -ForegroundColor Red
    taskkill /F /IM ollama.exe 2>&1 | Out-Null
    taskkill /F /IM ollama-app.exe 2>&1 | Out-Null
    Write-Host "[OK] Ollama stopped"
    Start-Sleep -Milliseconds 1000
}

function Start-OllamaCustom {
    Write-Host "`n[+] Starting Ollama..." -ForegroundColor Cyan
    Write-Host "    GPU: $GPU_ID"
    Write-Host "    Listen: $OLLAMA_HOST : $OLLAMA_PORT"
    Write-Host "    Model Path: $OLLAMA_MODELS_PATH`n"

    # 关键环境变量（只对当前脚本生效）
    $env:CUDA_VISIBLE_DEVICES = $GPU_ID
    $env:OLLAMA_HOST = "$OLLAMA_HOST`:$OLLAMA_PORT"
    $env:OLLAMA_MODELS = $OLLAMA_MODELS_PATH  # <-- 强制修改模型路径

    # 启动
    ollama serve
}

function Restart-OllamaCustom {
    Stop-OllamaCustom
    Start-OllamaCustom
}

# ====================== Menu ======================
Write-Host "==================== Ollama Manager ===================="
Write-Host "1 - Start (GPU $GPU_ID + Port $OLLAMA_PORT)"
Write-Host "2 - Stop"
Write-Host "3 - Restart"
Write-Host "========================================================="
$choice = Read-Host "Enter selection [1/2/3]"

switch ($choice) {
    1 { Start-OllamaCustom }
    2 { Stop-OllamaCustom }
    3 { Restart-OllamaCustom }
    default { Write-Host "Invalid option"; exit }
}
```

**启动方式：**

```powershell
# 右键 manage.ps1 → "使用 PowerShell 运行"
# 或在 PowerShell 中执行：
.\manage.ps1
```

---

### 第 4 步：拉取 Qwen 模型（10-30 分钟）

```powershell
# 拉取模型（约 6GB，取决于网速）
ollama pull qwen3.5:9b

# 验证
ollama list

# 测试
ollama run qwen3.5:9b "你好，请用一句话介绍Python语言"
```

看到中文回复即为成功。按 `/bye` 退出对话。

---

### 第 5 步：安装 Whisper API 依赖（10 分钟）

```powershell
# 创建虚拟环境
python -m venv D:\whisper
D:\whisper\Scripts\Activate.ps1

# 安装依赖
pip install faster-whisper uvicorn fastapi python-multipart
```

---

### 第 6 步：创建 Whisper API 服务（5 分钟）

创建文件 `D:\whisper\server.py`，内容如下：

```python
# 注意：这里不再设置 os.environ["CUDA_VISIBLE_DEVICES"]
# 全部由 manager.ps1 传入

import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from faster_whisper import WhisperModel

app = FastAPI(title="Whisper API for vbook")
model = WhisperModel("medium", device="cuda")
print("Whisper model loaded successfully")

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
        tmp.flush()
        tmp_path = tmp.name

    try:
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

        return {
            "language": info.language,
            "text": "\n".join(full_text_parts),
            "segments": segments,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)

@app.get("/health")
async def health():
    return {"status": "ok", "model": "medium", "device": "cuda"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7867)
```

创建文件 `D:\whisper\manager.ps1`，内容如下：

```powershell
<#
    Whisper API Service Manager (Single Window)
    GPU ID & Port managed here
#>

# ====================== 配置区（你只改这里）======================
$GPU_ID = "0"          # 改这里即可：0 / 1 / 2 等
$port = 7867           # 端口
$scriptPath = "D:\whisper\server.py"
$venvActivate = "D:\whisper\Scripts\Activate.ps1"
# ===============================================================

# 窗口标题自动显示 GPU + 端口
$host.ui.RawUI.WindowTitle = "Whisper API Service | GPU:$GPU_ID | Port:$port"

$env:PYTHONIOENCODING = "utf-8"
# 把 GPU 传入环境变量，给 Python 使用
$env:CUDA_VISIBLE_DEVICES = $GPU_ID

function Get-ServiceStatus {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    return $process -ne $null
}

function Start-Service {
    if (Get-ServiceStatus) {
        Write-Host "Service is already running." -ForegroundColor Yellow
        return
    }

    Write-Host "Starting Whisper API Service..." -ForegroundColor Cyan
    Write-Host "Using GPU: $GPU_ID | Port: $port" -ForegroundColor Green
    
    # 当前窗口激活环境 + 启动服务（不新开窗口）
    & $venvActivate
    python $scriptPath
}

function Stop-Service {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if (-not $process) {
        Write-Host "Service is not running." -ForegroundColor Yellow
        return
    }
    taskkill /pid $process.OwningProcess /F > $null 2>&1
    Write-Host "Service stopped successfully." -ForegroundColor Green
}

function Restart-Service {
    Write-Host "Restarting service..." -ForegroundColor Cyan
    Stop-Service
    Start-Sleep -Milliseconds 500
    Start-Service
}

Clear-Host
Write-Host "===== Whisper API Service Manager ====="
Write-Host "1. Start Service"
Write-Host "2. Stop Service"
Write-Host "3. Restart Service"
Write-Host "4. Check Status"
Write-Host "========================================"
$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    1 { Start-Service }
    2 { Stop-Service }
    3 { Restart-Service }
    4 {
        if (Get-ServiceStatus) {
            Write-Host "Service Status: Running" -ForegroundColor Green
        } else {
            Write-Host "Service Status: Stopped" -ForegroundColor Gray
        }
        Read-Host "`nPress Enter to exit"
    }
    default {
        Write-Host "Invalid input." -ForegroundColor Red
        Read-Host "`nPress Enter to exit"
    }
}
```

**启动服务：**

```powershell
D:\whisper\Scripts\Activate.ps1
python D:\whisper\manager.ps1
```

首次启动会自动下载 Whisper medium 模型（~1.5GB），等待出现：

```
INFO:     Uvicorn running on http://0.0.0.0:7867
```

即表示启动成功。

---

### 第 7 步：防火墙放行（2 分钟）

以**管理员身份**打开 PowerShell：

```powershell
New-NetFirewallRule -DisplayName "Ollama API" -Direction Inbound -Protocol TCP -LocalPort 7866 -Action Allow
New-NetFirewallRule -DisplayName "Whisper API" -Direction Inbound -Protocol TCP -LocalPort 7867 -Action Allow
```

---

### 第 8 步：本地验证（2 分钟）

在**服务器上**打开新的 PowerShell 窗口：

```powershell
# 验证 Ollama
curl http://localhost:7866/api/tags

# 验证 Whisper API
curl http://localhost:7867/health

# 验证 GPU 使用情况
nvidia-smi
```

`nvidia-smi` 输出中应看到 GPU 0 的显存占用增加（Ollama ~6GB + Whisper ~2GB）。

---

### 第 9 步：远程验证（5 分钟）

从 **Windows 开发机** 上测试（替换 `<SERVER_IP>` 为服务器实际 IP）：

```powershell
# 测试 Ollama
curl http://<SERVER_IP>:7866/api/tags

# 测试 Whisper API
curl http://<SERVER_IP>:7867/health

# 浏览器测试
# http://<SERVER_IP>:7866/        → 显示 "Ollama is running"
# http://<SERVER_IP>:7867/docs     → 显示 API 文档
```

---

### 第 10 步：设置开机自启（5 分钟）

#### Ollama

推荐使用任务计划程序配合 `manage.ps1` 脚本实现开机自启：

1. 打开 `taskschd.msc`
2. 创建基本任务 → 名称 `Ollama Serve`
3. 触发器：计算机启动时
4. 操作：启动程序
   - 程序：`powershell.exe`
   - 参数：`-ExecutionPolicy Bypass -WindowStyle Hidden -File "D:\ollama\manage.ps1"`
5. 勾选 **使用最高权限运行**

> **注意：** 如果使用任务计划程序，需要修改脚本去掉末尾的交互式菜单，直接调用 `Start-Ollama-Background`。

#### Whisper API

**方式 1：NSSM 服务（推荐）**

1. 下载 NSSM: https://nssm.cc/download
2. 解压到 `C:\nssm\`

```powershell
# 安装为 Windows 服务
C:\nssm\nssm.exe install WhisperAPI "D:\whisper\Scripts\python.exe" "D:\whisper\server.py"

# 设置 GPU 环境变量
C:\nssm\nssm.exe set WhisperAPI AppEnvironmentExtra "CUDA_VISIBLE_DEVICES=0"

# 启动服务
C:\nssm\nssm.exe start WhisperAPI

# 验证
C:\nssm\nssm.exe status WhisperAPI
```

**方式 2：任务计划程序**

1. 打开 `taskschd.msc`
2. 创建基本任务 → 名称 `Whisper API`
3. 触发器：计算机启动时
4. 操作：启动程序
   - 程序：`D:\whisper\Scripts\python.exe`
   - 参数：`D:\whisper\server.py`
   - 起始目录：`D:\whisper`
5. 勾选 **使用最高权限运行**

---

## 部署检查清单

按顺序逐项确认：

- [ ] `nvidia-smi` 显示两块 RTX 4090
- [ ] `ollama --version` 显示版本号
- [ ] `OLLAMA_HOST` 环境变量设为 `0.0.0.0:7866`
- [ ] `CUDA_VISIBLE_DEVICES` 环境变量设为 `0`
- [ ] `ollama list` 显示 qwen3.5:9b
- [ ] `ollama run qwen3.5:9b "你好"` 返回中文回复
- [ ] `D:\whisper\server.py` 文件已创建
- [ ] Whisper API 启动成功（`http://localhost:7867/health` 返回 ok）
- [ ] 防火墙已放行 7866 和 7867 端口
- [ ] 从开发机可访问 `http://<SERVER_IP>:7866/`
- [ ] 从开发机可访问 `http://<SERVER_IP>:7867/health`
- [ ] 已设置开机自启

---

## 日常运维

### 查看服务状态

```powershell
# Ollama
tasklist /fi "imagename eq ollama.exe"

# Whisper API（如果用 NSSM）
C:\nssm\nssm.exe status WhisperAPI

# GPU 使用情况
nvidia-smi
```

### 重启服务

```powershell
# 重启 Ollama（使用管理脚本）
.\manage.ps1
# 选择 3（重启）

# 或手动重启
taskkill /f /im ollama.exe
Start-Sleep -Seconds 3
$env:CUDA_VISIBLE_DEVICES = "0"
$env:OLLAMA_HOST = "0.0.0.0:7866"
$env:OLLAMA_MODELS = "D:\ollama\models"
ollama serve

# 重启 Whisper API（如果用 NSSM）
C:\nssm\nssm.exe restart WhisperAPI
```

### 更新模型

```powershell
# 更新 Qwen 模型
ollama pull qwen3.5:9b

# 如需升级 Whisper 到 large-v3，修改 server.py 中：
# model = WhisperModel("large-v3", device="cuda")
# 然后重启 Whisper API
```

---

## 故障排查

| 问题 | 排查命令 | 解决方案 |
|------|---------|---------|
| Ollama 无法远程访问 | `netstat -an \| findstr 7866` | 确认显示 `0.0.0.0:7866`，否则重设 OLLAMA_HOST/OLLAMA_PORT |
| Whisper 启动失败 | 查看控制台错误 | 通常是 CUDA 版本问题，重装 faster-whisper |
| GPU 内存不足 | `nvidia-smi` | 关闭其他 GPU 程序，或换更小模型 |
| 远程连不上 | `Test-NetConnection <IP> -Port 7866` | 检查防火墙规则 |
| 模型下载慢 | - | 配置代理或使用镜像源 |

---

## 部署完成后

回到开发机，告诉我服务器 IP 地址，我会帮你：

1. 配置 `vbook.yaml`（指向服务器 IP，端口 7866）
2. 运行端到端测试
3. 验证输出质量
