# Qwen Vision Adapter Design

## 目的

vBook 已经具备 `external-command` 视觉 backend。vBook core 可以写出
`vision/external/frames.json`，调用外部命令，再读取外部命令生成的
`vision/external/analysis.json`，最终归一化为 `VisualAnalysis[]`。

本设计新增一个仓库内置工具：

```text
tools/vision_qwen_adapter.py
```

该工具不作为新的 vBook core backend，而是作为 `external-command` 的 adapter。
它负责把 vBook frame 输入转换为 Qwen Vision Service 的 `POST /analyze-frame`
请求，再把服务响应转换为兼容 `manual-json` 的视觉分析 JSON。

目标是让 vBook 能在不绑定 Qwen 模型运行时、不引入模型 SDK、不改变 core backend
接口的前提下，接入外部团队正在搭建的 Qwen 视觉服务。

## 当前上下文

已经完成的能力：

- `placeholder` backend：生成确定性占位视觉分析。
- `manual-json` backend：读取人工或外部流程准备的视觉分析 JSON。
- `external-command` backend：写 `frames.json`，调用命令模板，读取
  `analysis.json`，并复用 `manual-json` 验证逻辑。
- `tools/vision_stub.py`：用于验证 `external-command` 契约的本地 smoke tool。
- `docs/90_reference/qwen-vision-service-requirements.md`：定义外部 Qwen 视觉服务的
  HTTP 契约。

本 adapter 是 `external-command` 和 Qwen Vision Service 之间的桥接层。

## 设计选择

采用方案 A：新增 `tools/vision_qwen_adapter.py`。

不新增：

```text
--vision-backend qwen-service
```

原因：

- Qwen 服务仍在外部项目中建设，vBook core 现在不应绑定具体 HTTP 服务实现。
- `external-command` 已经提供足够稳定的输入输出边界。
- adapter 可以独立测试、独立替换、独立传参。
- 后续如果 Qwen 服务稳定，再考虑是否把它提升为 first-class backend。

## CLI 用法

推荐通过 `external-command` 调用：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-qwen `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://127.0.0.1:8000/analyze-frame --timeout-seconds 120"
```

adapter 参数：

```text
--input             vBook 生成的 frames.json 路径，必填。
--output            adapter 要写出的 analysis.json 路径，必填。
--endpoint          Qwen 服务 POST /analyze-frame URL，必填。
--timeout-seconds   单帧 HTTP 请求超时，默认 120。
--prompt-profile    prompt profile，默认 vbook_visual_analysis_v1。
--token             可选 bearer token。
```

鉴权规则：

- 如果传入 `--token`，优先使用该值。
- 如果未传 `--token`，但存在环境变量 `VBOOK_QWEN_VISION_TOKEN`，使用环境变量。
- 如果存在 token，请求头加入：

```text
Authorization: Bearer <token>
```

## 输入契约

adapter 读取 `external-command` 写出的 frame input JSON：

```json
{
  "backend": "external-command",
  "frames": [
    {
      "frame_id": "frame-000001",
      "video_id": "lesson",
      "timestamp": 12.5,
      "image_path": "outputs/lesson/frames/selected/frame_000001.jpg",
      "width": 1280,
      "height": 720
    }
  ]
}
```

adapter 必须验证：

- 根节点必须是 object。
- `frames` 必须是 list。
- 每个 frame 必须是 object。
- `frame_id` 必须是非空 string。
- `image_path` 必须是非空 string。
- `image_path` 指向的文件必须存在。
- 图片后缀必须是 `.jpg`、`.jpeg` 或 `.png`。

MIME 推断规则：

| Suffix | MIME |
| --- | --- |
| `.jpg` | `image/jpeg` |
| `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |

第一版不做图片重新编码、压缩、尺寸缩放或格式转换。

## Qwen 请求映射

对每个 frame，adapter 发送一个 HTTP request：

```text
POST <endpoint>
Content-Type: application/json
Accept: application/json
```

请求 body：

```json
{
  "request_id": "vbook-frame-000001",
  "frame_id": "frame-000001",
  "video_id": "lesson",
  "timestamp": 12.5,
  "image_base64": "<base64-encoded-image>",
  "image_mime_type": "image/jpeg",
  "image_path": "outputs/lesson/frames/selected/frame_000001.jpg",
  "prompt_profile": "vbook_visual_analysis_v1",
  "metadata": {}
}
```

字段来源：

- `frame_id` 来自 input frame。
- `video_id` 来自 input frame；缺失时传空字符串。
- `timestamp` 来自 input frame；缺失时传 `0.0`。
- `image_base64` 来自图片原始 bytes 的 base64 编码。
- `image_mime_type` 根据图片后缀推断。
- `image_path` 使用 input frame 的原始路径字符串，仅用于服务日志和调试。
- `prompt_profile` 来自 CLI 参数，默认 `vbook_visual_analysis_v1`。
- `metadata` 第一版传空 object，后续可以扩展课程名、课节名等上下文。

`request_id` 第一版使用确定性格式：

```text
vbook-<frame_id>
```

`frame_id` 按 input 中的原值拼接，除非不满足非空 string 的输入校验。

## Qwen 响应验证

服务成功响应必须是 JSON object，并包含：

```json
{
  "frame_id": "frame-000001",
  "visual_type": "slide",
  "ocr_text": "课程标题",
  "vision_description": "一页课程幻灯片。",
  "structured_observations": {
    "topic": "短线选股"
  },
  "confidence": 0.86
}
```

adapter 必须验证：

- HTTP status 必须是 2xx。
- body 必须是 JSON object。
- `frame_id` 必须等于请求 frame 的 `frame_id`。
- `visual_type` 必须是 `slide`、`kline_case` 或 `other`。
- `ocr_text` 必须存在；非 string 值转换为 string。
- `vision_description` 必须存在；非 string 值转换为 string。
- `structured_observations` 必须是 object。
- `confidence` 必须是 number 或 null。

如果响应包含 `model`、`usage`、`warnings` 等可选字段，adapter 第一版不提升为顶层
manual-json 字段。为了保留调试信息，adapter 将这些字段放入
`structured_observations.qwen_service`：

```json
{
  "qwen_service": {
    "request_id": "vbook-frame-000001",
    "model": {
      "provider": "qwen",
      "name": "qwen-vl"
    },
    "usage": {
      "latency_ms": 1250
    },
    "warnings": ["low readability"]
  }
}
```

如果原始 `structured_observations` 已经包含 `qwen_service`，adapter 使用
`qwen_service_response` 存放服务调试字段，避免覆盖模型输出。

## 输出契约

adapter 写出兼容 `manual-json` 的 output JSON：

```json
{
  "backend": "qwen-vision-service",
  "analyses": [
    {
      "frame_id": "frame-000001",
      "visual_type": "slide",
      "ocr_text": "课程标题",
      "vision_description": "一页课程幻灯片。",
      "structured_observations": {
        "topic": "短线选股",
        "qwen_service": {
          "request_id": "vbook-frame-000001"
        }
      },
      "confidence": 0.86
    }
  ]
}
```

输出路径规则：

- `--output` 的父目录不存在时自动创建。
- 写文件使用 UTF-8。
- JSON 使用 `ensure_ascii=False` 和 2 空格缩进，便于中文 OCR 和人工检查。

vBook core 后续会通过 `load_manual_visual_analysis(..., backend="external-command")`
再次验证该输出。因此 adapter 自己也做验证，但最终信任边界仍在 vBook core。

## 错误处理

adapter 是命令行工具。失败时：

- 返回 exit code `1`。
- 向 stderr 输出单行或短文本错误。
- 不写半成品 output；如果异常发生在写入前，保持 output 不存在。

需要覆盖的错误：

- input 文件不存在。
- input JSON 无法解析。
- input 根节点不是 object。
- 缺少 `frames` list。
- frame 不是 object。
- frame 缺少 `frame_id`。
- frame 缺少 `image_path`。
- 图片文件不存在。
- 图片后缀不支持。
- HTTP 请求超时。
- HTTP 连接失败。
- 服务返回非 2xx。
- 服务返回非 JSON。
- 服务返回 JSON 但不是 object。
- 服务响应 `frame_id` 不匹配。
- 服务响应 `visual_type` 不合法。
- 服务响应 `structured_observations` 不是 object。
- 服务响应 `confidence` 不是 number 或 null。

非 2xx 响应的错误信息优先提取：

```json
{
  "error": {
    "code": "invalid_request",
    "message": "image_base64 is required",
    "retryable": false
  }
}
```

stderr 示例：

```text
Qwen service returned HTTP 400 for frame-000001: invalid_request: image_base64 is required
```

如果服务错误 body 不是该格式，stderr 至少包含 HTTP status 和 frame_id。

## 实现边界

第一版使用 Python 标准库：

- `argparse`
- `base64`
- `json`
- `os`
- `sys`
- `urllib.request`
- `urllib.error`
- `pathlib.Path`

不新增 runtime dependency。这样工具可以在当前 `pyproject.toml` 不变的情况下运行。

为了便于单元测试和未来复用，脚本内部建议拆成小函数：

```python
def main(argv: list[str] | None = None) -> int: ...
def load_frame_input(input_path: Path) -> list[dict[str, object]]: ...
def build_qwen_request(frame: dict[str, object], prompt_profile: str) -> dict[str, object]: ...
def post_json(endpoint: str, payload: dict[str, object], token: str | None, timeout: float) -> dict[str, object]: ...
def normalize_response(frame_id: str, response: dict[str, object]) -> dict[str, object]: ...
def write_output(output_path: Path, analyses: list[dict[str, object]]) -> None: ...
```

这些函数是实现建议，不属于 vBook public API。

## 测试策略

不依赖真实 Qwen 服务。测试使用 Python 标准库启动本地 fake HTTP server。

新增测试文件：

```text
tests/test_tools/test_vision_qwen_adapter.py
```

核心测试：

1. 正常路径：
   - 临时目录创建 `.jpg` 图片。
   - 写入 `frames.json`。
   - fake server 返回合法 `slide` 响应。
   - 运行 `tools/vision_qwen_adapter.py`。
   - 断言 exit code 为 `0`。
   - 断言 output JSON backend 为 `qwen-vision-service`。
   - 断言 output 可被 `load_manual_visual_analysis(..., backend="external-command")`
     读取。

2. 请求内容：
   - fake server 捕获 request body。
   - 断言包含 `frame_id`、`image_base64`、`image_mime_type`、
     `prompt_profile`。
   - 断言 `.jpg` 映射为 `image/jpeg`。

3. 鉴权：
   - 使用 `--token` 或 `VBOOK_QWEN_VISION_TOKEN`。
   - fake server 断言 `Authorization: Bearer <token>`。

4. 服务错误：
   - fake server 返回 HTTP `400` 和标准 error body。
   - 断言 adapter exit code 为 `1`。
   - 断言 stderr 包含 error code、message 和 frame_id。

5. 响应不合法：
   - fake server 返回不同 `frame_id`。
   - 断言 adapter exit code 为 `1`。
   - 断言 stderr 包含 frame_id mismatch。

6. 本地输入错误：
   - 图片文件不存在。
   - 图片后缀不支持。
   - 缺少 `frames` list。

7. CLI build 集成 smoke：
   - fake server 返回合法响应。
   - 运行 `python -m vbook_client build --vision-backend external-command`
     并调用 adapter。
   - 断言 `vision/external/frames.json` 存在。
   - 断言 `vision/external/analysis.json` 存在。
   - 断言 `vision/analysis.json` 的 `backend` 为 `external-command`。
   - 断言 `manifest.json` 中 `stage_status.vision_analysis = done`。

完整验证命令：

```powershell
python -m unittest tests.test_tools.test_vision_qwen_adapter
python -m unittest discover
```

## 文档更新

实现完成后更新：

- `docs/60_operations/smoke-tests.md`：新增 Qwen adapter smoke 示例。
- `docs/00_project/status.md`：把 Qwen adapter 列为可用的真实服务接入桥。

如果测试命令或使用方式发生变化，同步更新相关 `README.md` 索引。

## 非目标

第一版不做：

- 新增 `qwen-service` core backend。
- 调用 OpenAI-compatible API。
- 批量 endpoint `POST /analyze-frames`。
- 并发请求。
- 自动重试。
- 断点续跑。
- 图片压缩、裁剪或格式转换。
- OCR bounding boxes 专门 schema。
- 真实 Qwen 服务的启动、部署或模型加载。
- 在 vBook 仓库中保存真实课程图片、视频或模型输出样本。

## 后续扩展

如果 adapter 和外部 Qwen 服务稳定，可以后续增加：

- `--metadata-json`：传入课程名、课节名、领域提示等上下文。
- `--max-frames`：限制 smoke run 的帧数量。
- `--continue-on-error`：单帧失败时写入 error observation 并继续。
- `--retry-count`：针对 `429`、`500`、`503`、`504` 做有限重试。
- `--parallelism`：服务吞吐稳定后增加并发。
- `qwen-service` first-class backend：当 HTTP 契约稳定并需要更短 CLI 时再评估。

## 验收口径

本设计完成实现后，视为 vBook 侧 Qwen adapter 第一阶段完成，当且仅当：

- `tools/vision_qwen_adapter.py` 可被 `external-command` 调用。
- adapter 能把本地 `.jpg` 或 `.png` frame 转成 Qwen `POST /analyze-frame` 请求。
- adapter 能把合法 Qwen 响应写成 manual-json 兼容 output。
- output 能通过 vBook 现有 `load_manual_visual_analysis()` 验证。
- fake HTTP server 测试覆盖正常路径、服务错误、响应校验失败、本地输入失败。
- `python -m unittest discover` 通过。
- smoke 文档说明如何用真实 Qwen 服务 endpoint 运行。
