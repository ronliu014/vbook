# Qwen Vision Service 对接需求与回复清单

## 目的

本文用于发给 Qwen Vision Service 项目组，确认服务部署信息、接口契约和联调条件。

完整服务契约见：

- `docs/90_reference/qwen-vision-service-requirements.md`

本文不是替代完整需求书，而是 vBook 侧开始真实联调前需要服务组回复的最小清单。

## vBook 侧当前状态

vBook 侧已经完成 adapter：

```text
tools/vision_qwen_adapter.py
```

调用链如下：

```text
vBook build
  -> --vision-backend external-command
    -> tools/vision_qwen_adapter.py
      -> POST /analyze-frame
        -> Qwen Vision Service
```

vBook 侧不会直接依赖 Qwen SDK，也不会访问服务机器上的本地图片路径。adapter 会把本地
frame 读成 base64 后放入 JSON request。

## 请 Qwen 服务组回复的信息

### 1. 服务地址

请提供：

```text
Base URL:
Analyze endpoint:
Health endpoint:
```

示例：

```text
Base URL: http://10.0.0.12:8000
Analyze endpoint: http://10.0.0.12:8000/analyze-frame
Health endpoint: http://10.0.0.12:8000/health
```

### 2. 网络访问方式

请说明 vBook 运行机器如何访问服务：

```text
Network:
  local only / LAN / VPN / public internet / other

Firewall or allowlist:
  none / required, details:

Protocol:
  http / https
```

第一阶段可以使用可信内网 HTTP。如果暴露到不可信网络，请使用 token auth 或其他访问控制。

### 3. 认证方式

请确认是否需要 token。

如果需要，请确认 header 格式是否为：

```text
Authorization: Bearer <token>
```

vBook adapter 支持两种 token 传入方式：

```powershell
python tools\vision_qwen_adapter.py ... --token "<token>"
```

或：

```powershell
$env:VBOOK_QWEN_VISION_TOKEN = "<token>"
```

请回复：

```text
Auth required:
Token type:
Token expiration:
How to obtain token:
```

### 4. Health Check

请确认是否支持：

```text
GET /health
```

期望成功响应：

```json
{
  "status": "ok",
  "model_loaded": true,
  "model": {
    "provider": "qwen",
    "name": "qwen-vl",
    "version": "service-defined"
  }
}
```

如果模型未加载完成，请返回 HTTP `503`，并给出可读错误信息。

### 5. Analyze Frame 接口

vBook adapter 会调用：

```text
POST /analyze-frame
Content-Type: application/json
Accept: application/json
```

请求体示例：

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

请确认服务至少支持：

- `image_mime_type = image/jpeg`
- `image_mime_type = image/png`
- `prompt_profile = vbook_visual_analysis_v1`

服务不能要求 `image_path` 在服务端可读。该字段只用于 debug。

### 6. 成功响应契约

成功响应必须是标准 JSON object。

必填字段：

| Field | Type | Rule |
| --- | --- | --- |
| `frame_id` | string | 必须原样等于 request `frame_id` |
| `visual_type` | string | 只能是 `slide`、`kline_case`、`other` |
| `ocr_text` | string | 可以是空字符串 |
| `vision_description` | string | 可以是空字符串，但建议 1-3 句简明描述 |
| `structured_observations` | object | 可以是空 object |
| `confidence` | number or null | number 必须在 `0.0` 到 `1.0` |

可选字段：

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | string | 建议 echo request id |
| `model` | object | 模型/provider debug 信息 |
| `usage` | object | token、latency 等 debug 信息 |
| `warnings` | list[string] | 非致命 warning |

示例：

```json
{
  "request_id": "vbook-frame-000001",
  "frame_id": "frame-000001",
  "visual_type": "slide",
  "ocr_text": "课程标题\n短线选股条件",
  "vision_description": "一页讲解短线选股条件的课程幻灯片。",
  "structured_observations": {
    "topic": "短线选股",
    "visible_elements": ["标题", "项目符号"],
    "language": "zh-CN"
  },
  "confidence": 0.86,
  "model": {
    "provider": "qwen",
    "name": "qwen-vl",
    "version": "service-defined"
  },
  "usage": {
    "latency_ms": 1250
  },
  "warnings": []
}
```

### 7. Strict JSON 要求

服务必须返回标准 JSON。

不要返回：

```text
NaN
Infinity
-Infinity
```

也不要返回会被解析为非有限数字的值，例如：

```text
1e999
```

如果某个数值未知，请使用 `null` 或省略可选字段。

vBook adapter 会拒绝这些非标准或非有限数值，避免生成不兼容的 `analysis.json`。

### 8. 错误响应契约

非 2xx 响应建议返回 JSON：

```json
{
  "error": {
    "code": "invalid_request",
    "message": "image_base64 is required",
    "retryable": false
  },
  "request_id": "vbook-frame-000001"
}
```

建议支持的错误类型：

| HTTP Status | error.code | retryable | Condition |
| --- | --- | --- | --- |
| 400 | `invalid_request` | false | 缺字段、invalid JSON、invalid base64 |
| 400 | `unsupported_prompt_profile` | false | 不支持的 prompt profile |
| 413 | `image_too_large` | false | 图片超过限制 |
| 429 | `rate_limited` | true | 限流 |
| 500 | `model_error` | true | 模型调用异常 |
| 503 | `service_unavailable` | true | 服务暂不可用 |
| 504 | `timeout` | true | 推理超时 |

### 9. 运行限制

请回复以下限制，便于 vBook 侧设置 smoke 参数：

```text
Max decoded image size:
Max image dimensions:
Per-frame timeout:
Recommended client timeout:
Rate limit / QPS:
Recommended concurrency:
Model warmup time:
Expected average latency:
Expected p95 latency:
```

第一阶段 vBook adapter 默认逐帧串行请求，默认 timeout 是 120 秒。

### 10. 日志要求

请至少记录：

- `request_id`
- `frame_id`
- HTTP status
- model name/version
- latency
- error code

不要默认记录完整 `image_base64`。

### 11. 服务组自测建议

服务组部署后，建议先完成这些自测：

1. `GET /health` 返回 `status = ok`。
2. clear slide image 返回：
   - `visual_type = slide`
   - `ocr_text` 非空或包含主要可见标题
   - `vision_description` 非空
   - `structured_observations` 是 object
   - `confidence` 是 `0.0` 到 `1.0` 的 number 或 `null`
3. K-line image 返回：
   - `visual_type = kline_case`，或图像不清晰时返回 `other`
4. invalid request 返回 HTTP `400` 和结构化 error。
5. unknown prompt profile 返回 HTTP `400` 和 `unsupported_prompt_profile`。

### 12. vBook 侧联调命令

拿到服务 endpoint 后，vBook 侧会使用类似命令：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-qwen `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://127.0.0.1:8000/analyze-frame --timeout-seconds 120"
```

如果需要 token：

```powershell
$env:VBOOK_QWEN_VISION_TOKEN = "<token>"
```

期望产物：

- `outputs\lesson-qwen\vision\external\frames.json`
- `outputs\lesson-qwen\vision\external\analysis.json`
- `outputs\lesson-qwen\vision\analysis.json`
- `outputs\lesson-qwen\manifest.json`
- `outputs\lesson-qwen\note.md`

### 13. 请服务组按此模板回复

```text
Service owner:
Contact:

Environment:
Base URL:
Analyze endpoint:
Health endpoint:

Network:
Protocol:
Firewall / allowlist:

Auth required:
Token type:
Token expiration:
How to obtain token:

Supported prompt profiles:
Supported image MIME types:
Max decoded image size:
Max image dimensions:

Per-frame server timeout:
Recommended client timeout:
Rate limit / QPS:
Recommended concurrency:

Model provider:
Model name:
Model version:
Model warmup requirement:

Success response confirmed:
Error response confirmed:
Strict JSON confirmed:

Known limitations:
Sample request / response:
Deployment ETA:
```

## vBook 侧验收口径

vBook 侧认为服务可进入第一轮联调，当且仅当：

- `GET /health` 可访问。
- `POST /analyze-frame` 可访问。
- 返回 JSON 符合成功响应契约。
- 非 2xx 错误响应可读。
- 服务组提供 endpoint、认证方式、timeout、image limits。
- 至少有一个 slide image 自测通过。

vBook 侧认为第一轮 smoke 通过，当且仅当：

- vBook build 命令退出码为 0。
- `vision/external/frames.json` 生成。
- `vision/external/analysis.json` 生成。
- `vision/analysis.json` 生成。
- `manifest.json` 中 `vision_analysis` 为 done。
- `note.md` 生成。
- 至少一个 frame 的 `ocr_text` 或 `vision_description` 能反映图片内容。
