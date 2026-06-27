# Qwen Vision Service Requirements

## 1. 背景与目标

vBook 已支持 `external-command` 视觉 backend。vBook 会把待分析的视频帧写成
`frames.json`，再调用外部命令；外部命令负责生成兼容 `manual-json` 的
`analysis.json`，最终由 vBook 归一化为 `VisualAnalysis[]`。

下一步需要一个基于 Qwen-VL 或同类多模态模型的视觉服务。该服务由外部团队实现，
vBook 侧后续会提供 adapter 调用该服务。

本需求书定义外部 Qwen 视觉服务的 HTTP 契约、输入输出、错误处理、验收口径和非目标。

目标不是只做传统 OCR，而是为 vBook 提供一条单帧视觉理解接口，至少覆盖：

- 读取图片中的文字，填充 `ocr_text`。
- 判断画面类型，填充 `visual_type`。
- 描述画面内容，填充 `vision_description`。
- 提取结构化观察，填充 `structured_observations`。
- 返回模型置信度或质量估计，填充 `confidence`。

## 2. 总体设计

第一版服务提供单帧接口：

```text
POST /analyze-frame
```

推荐先做单帧接口，而不是批量接口。原因：

- 单帧失败更容易定位。
- vBook adapter 可以逐帧重试或记录失败。
- 不需要第一版就处理 batch 部分失败、队列、并发和超时聚合。
- 后续可以在单帧稳定后增加 `POST /analyze-frames`。

vBook 后续调用链：

```text
vBook build
  -> external-command backend
    -> tools/vision_qwen_adapter.py
      -> POST /analyze-frame
        -> Qwen Vision Service
```

服务不需要了解 vBook 全量 manifest、transcript、fusion 或 note。第一版只处理图片和
少量 frame metadata。

## 3. API Contract

### 3.1 Endpoint

```text
POST /analyze-frame
Content-Type: application/json
Accept: application/json
```

### 3.2 Request Body

```json
{
  "request_id": "run-20260627-001-frame-000001",
  "frame_id": "frame-000001",
  "video_id": "lesson",
  "timestamp": 12.5,
  "image_base64": "<base64-encoded-image>",
  "image_mime_type": "image/jpeg",
  "image_path": "outputs/lesson/frames/selected/frame_000001.jpg",
  "prompt_profile": "vbook_visual_analysis_v1",
  "metadata": {
    "course_title": "",
    "lesson_title": ""
  }
}
```

### 3.3 Required Request Fields

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `frame_id` | string | yes | Must be non-empty. Echo unchanged in response. |
| `image_base64` | string | yes | Base64 encoded JPEG or PNG bytes. |
| `image_mime_type` | string | yes | `image/jpeg` or `image/png`. |
| `prompt_profile` | string | yes | First supported value: `vbook_visual_analysis_v1`. |

### 3.4 Optional Request Fields

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | string | Echo in response when present. Used for logs. |
| `video_id` | string | Course/video grouping id. |
| `timestamp` | number | Seconds from source video start. |
| `image_path` | string | Debug-only path from vBook side. Service must not require local file access. |
| `metadata` | object | Optional context. Unknown keys must be ignored. |

The service must not require `image_path` to be readable, because vBook and service may run on different machines.

## 4. Success Response

### 4.1 HTTP Status

```text
200 OK
Content-Type: application/json
```

### 4.2 Response Body

```json
{
  "request_id": "run-20260627-001-frame-000001",
  "frame_id": "frame-000001",
  "visual_type": "slide",
  "ocr_text": "课程标题\n短线选股条件\n1. 均线多头排列\n2. 成交量放大",
  "vision_description": "一页讲解短线选股条件的幻灯片，包含标题、项目符号和一个K线截图。",
  "structured_observations": {
    "topic": "短线选股",
    "key_points": ["均线多头排列", "成交量放大"],
    "visible_elements": ["标题", "项目符号", "K线截图"],
    "language": "zh-CN",
    "quality": {
      "readability": "high",
      "blur": "low"
    }
  },
  "confidence": 0.86,
  "model": {
    "provider": "qwen",
    "name": "qwen-vl",
    "version": "service-defined"
  },
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "latency_ms": 1250
  }
}
```

### 4.3 Required Response Fields

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `frame_id` | string | yes | Must equal request `frame_id`. |
| `visual_type` | string | yes | One of `slide`, `kline_case`, `other`. |
| `ocr_text` | string | yes | Empty string allowed. |
| `vision_description` | string | yes | Empty string allowed only when model cannot describe the image. |
| `structured_observations` | object | yes | Empty object allowed. |
| `confidence` | number or null | yes | Use `0.0` to `1.0` when available, otherwise `null`. |

### 4.4 Optional Response Fields

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | string | Echo request id when present. |
| `model` | object | Model/provider debug info. |
| `usage` | object | Token/latency debug info. |
| `warnings` | list[string] | Non-fatal warnings, e.g. low image quality. |

The vBook adapter will preserve required fields in `analysis.json`. Optional fields may be stored inside
`structured_observations` by the adapter if useful.

## 5. Visual Type Rules

The service must choose exactly one `visual_type`.

### `slide`

Use for PPT, Keynote, document screenshots, teaching pages, whiteboard-like text pages, or UI pages where text/content layout is the primary information.

### `kline_case`

Use for stock chart / K-line / candlestick case images, especially when trading indicators, price movement, volume, or annotated chart regions are visible.

### `other`

Use for lecturer face shots, blank frames, transition screens, low-information frames, or images that do not clearly fit `slide` or `kline_case`.

## 6. Prompt Behavior Requirements

The service owner may implement prompt engineering internally, but output must follow the JSON contract.

The model should be instructed to:

- Prefer Simplified Chinese in `ocr_text`, `vision_description`, and extracted semantic labels when the image is Chinese.
- Preserve important visible text as faithfully as possible in `ocr_text`.
- Keep `vision_description` concise, usually 1-3 sentences.
- Put structured facts in `structured_observations` rather than embedding everything in prose.
- Avoid inventing content that is not visible in the image.
- If the image is blurry or unreadable, say so in `structured_observations.quality` and reduce `confidence`.

Recommended prompt profile name:

```text
vbook_visual_analysis_v1
```

The service may reject unknown `prompt_profile` values with HTTP `400`.

## 7. Error Handling

### 7.1 Error Response Body

For non-2xx responses, return JSON:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "image_base64 is required",
    "retryable": false
  },
  "request_id": "run-20260627-001-frame-000001"
}
```

### 7.2 Error Codes

| HTTP Status | `error.code` | Retryable | Condition |
| --- | --- | --- | --- |
| 400 | `invalid_request` | false | Missing required field, invalid JSON, invalid base64, unsupported mime type. |
| 400 | `unsupported_prompt_profile` | false | Unknown `prompt_profile`. |
| 413 | `image_too_large` | false | Image exceeds configured size limit. |
| 429 | `rate_limited` | true | Service is throttling. |
| 500 | `model_error` | true | Model call failed unexpectedly. |
| 503 | `service_unavailable` | true | Model not loaded or backend temporarily unavailable. |
| 504 | `timeout` | true | Model call exceeded timeout. |

## 8. Operational Requirements

### 8.1 Transport

First version may run on HTTP inside trusted LAN:

```text
http://<host>:<port>/analyze-frame
```

If exposed outside a trusted network, add token authentication:

```text
Authorization: Bearer <token>
```

### 8.2 Timeouts

Recommended server-side timeout:

```text
single frame <= 120 seconds
```

The service should return HTTP `504` if model inference times out.

### 8.3 Image Limits

Recommended first-version limits:

- Supported formats: JPEG, PNG.
- Maximum decoded image size: 10 MB.
- Maximum image dimension: service-defined, but must report `image_too_large` when rejected.

### 8.4 Logging

Log at least:

- `request_id`
- `frame_id`
- response status
- model name/version
- latency
- error code when failed

Do not log full `image_base64` by default.

## 9. Health Check

Provide a lightweight endpoint:

```text
GET /health
```

Success response:

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

If the model is not ready, return HTTP `503`:

```json
{
  "status": "unavailable",
  "model_loaded": false,
  "error": "model is still loading"
}
```

## 10. Acceptance Tests

The service team should provide a small test script or curl examples for these cases.

### 10.1 Health Check

```text
GET /health
```

Expected:

- HTTP `200`.
- JSON contains `status = ok`.
- JSON contains `model_loaded = true`.

### 10.2 Valid Slide Image

Request:

- `POST /analyze-frame`
- image is a clear PPT/slide screenshot.

Expected:

- HTTP `200`.
- `visual_type = slide`.
- `ocr_text` contains visible title or major bullet text.
- `vision_description` is non-empty.
- `structured_observations` is object.
- `confidence` is number or null.

### 10.3 Valid K-line Case Image

Request:

- `POST /analyze-frame`
- image contains candlestick/K-line chart.

Expected:

- HTTP `200`.
- `visual_type = kline_case` or `other` if chart is too unclear.
- If `kline_case`, `structured_observations.visible_elements` or similar field mentions chart/K-line/candlestick/volume when visible.

### 10.4 Invalid Request

Request body misses `image_base64`.

Expected:

- HTTP `400`.
- `error.code = invalid_request`.
- `error.retryable = false`.

### 10.5 Unsupported Prompt Profile

Request uses:

```json
{"prompt_profile": "unknown_profile"}
```

Expected:

- HTTP `400`.
- `error.code = unsupported_prompt_profile`.

## 11. Example curl

PowerShell example with a prepared base64 text file:

```powershell
$body = @{
  request_id = "manual-test-frame-000001"
  frame_id = "frame-000001"
  video_id = "lesson"
  timestamp = 0.0
  image_base64 = Get-Content -Raw .\frame_000001.base64.txt
  image_mime_type = "image/jpeg"
  image_path = "frame_000001.jpg"
  prompt_profile = "vbook_visual_analysis_v1"
  metadata = @{
    course_title = ""
    lesson_title = ""
  }
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/analyze-frame" `
  -ContentType "application/json" `
  -Body $body
```

## 12. Non-Goals

First service version does not need to provide:

- Batch endpoint.
- Web UI.
- Job queue.
- Streaming response.
- vBook manifest parsing.
- Transcript/fusion/note generation.
- File path based image loading.
- Long-term image storage.
- Fine-grained OCR bounding boxes.

Fine-grained OCR boxes can be added later inside `structured_observations` if needed.

## 13. Delivery Checklist

The service is ready for vBook adapter integration when it provides:

- `GET /health`.
- `POST /analyze-frame`.
- JSON success response matching required fields.
- JSON error response matching required fields.
- At least one local slide image acceptance test.
- At least one invalid request test.
- Host, port, and optional token shared with the vBook adapter developer.
