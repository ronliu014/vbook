# Qwen Vision Service 对接回复（致 vBook 项目组）

本文回复 `docs/qwen-vision-service-integration-request.md` 中的对接问卷，
供 vBook 侧开始联调前确认。除标注「待实测 / 待确认」的项外，其余均依据当前服务
实现（代码 + 配置）如实填写。

> 📌 之前问卷沟通中标记的两处契约偏差（缺字段校验返回码、`model.provider` 取值）
> 均已修复并与契约对齐，详见文末「契约对齐记录」。当前唯一待办是部署到
> `192.168.0.33` 后补充性能基线。

## 服务概况

- 服务实现：FastAPI + 本地 Ollama（视觉模型 `qwen3-vl:8b`）
- 部署机器：`192.168.0.33`
- 监听端口：`8866`（与 qwen3.6 文本服务的 7866 对应区分）
- 当前版本：单帧接口 `POST /analyze-frame` + `GET /health`，可信内网 HTTP，无认证

## 1. 服务地址

```text
Base URL:         http://192.168.0.33:8866
Analyze endpoint: http://192.168.0.33:8866/analyze-frame
Health endpoint:  http://192.168.0.33:8866/health
```

## 2. 网络访问方式

```text
Network:            LAN（可信内网）
Protocol:           http
Firewall/allowlist: 需在 192.168.0.33 上放行入站 TCP 8866
                    （部署脚本提供 New-NetFirewallRule 命令）
```

第一阶段在可信内网用 HTTP。若后续需暴露到不可信网络，我们再加 token 认证。

## 3. 认证方式

```text
Auth required:   否（当前版本无认证）
Token type:      —
Token expiration:—
How to obtain:   —
```

当前服务**不校验任何 token**，vBook adapter 无需传 `--token` 或设置
`VBOOK_QWEN_VISION_TOKEN`。如需启用认证请提出，我们按
`Authorization: Bearer <token>` 格式增加。

## 4. Health Check

支持 `GET /health`。模型已加载时返回 HTTP `200`：

```json
{
  "status": "ok",
  "model_loaded": true,
  "model": {
    "provider": "qwen",
    "name": "qwen3-vl:8b",
    "version": "service-defined"
  }
}
```

模型未就绪时返回 HTTP `503`：

```json
{
  "status": "unavailable",
  "model_loaded": false,
  "error": "<可读错误信息>"
}
```

> 注意：`model.provider` 为 `"qwen"`（与契约示例一致），`model.name` 为实际模型名
> `"qwen3-vl:8b"`，`version` 为 `"service-defined"`。

## 5. Analyze Frame 接口

支持 `POST /analyze-frame`，`Content-Type: application/json`。

确认支持：

- `image_mime_type = image/jpeg` ✅
- `image_mime_type = image/png` ✅
- `prompt_profile = vbook_visual_analysis_v1` ✅（唯一支持的 profile）

`image_path` 字段仅作 debug 透传，服务端**不会读取**该路径，vBook 与服务可在不同机器。
未知字段会被忽略。

## 6. 成功响应契约

完全符合契约的必填/可选字段。HTTP `200` 示例：

```json
{
  "request_id": "vbook-frame-000001",
  "frame_id": "frame-000001",
  "visual_type": "slide",
  "ocr_text": "课程标题\n短线选股条件",
  "vision_description": "一页讲解短线选股条件的课程幻灯片。",
  "structured_observations": {
    "topic": "短线选股",
    "key_points": ["均线多头排列", "成交量放大"],
    "visible_elements": ["标题", "项目符号"],
    "language": "zh-CN",
    "quality": { "readability": "high", "blur": "low" }
  },
  "confidence": 0.86,
  "model": { "provider": "qwen", "name": "qwen3-vl:8b", "version": "service-defined" },
  "usage": { "input_tokens": 0, "output_tokens": 0, "latency_ms": 1250 },
  "warnings": []
}
```

字段说明：

- `frame_id`：原样 echo 请求的 `frame_id`。
- `visual_type`：严格限定 `slide` / `kline_case` / `other` 之一（Pydantic 校验）。
- `confidence`：`0.0`–`1.0` 的 number，或 `null`。
- `request_id`：请求带则 echo；未带则服务生成一个（形如 `req-<毫秒时间戳>`）。
- `usage.input_tokens` / `output_tokens`：当前固定为 `0`（Ollama 未回传），`latency_ms` 为实际推理耗时。
- `structured_observations` 的内部结构由模型生成，上表字段为建议项，不保证每帧都齐全。

## 7. Strict JSON 要求

- 响应由 Pydantic 序列化为标准 JSON，不含注释、不含尾逗号。
- `confidence` 为 number 或 `null`，约束在 `0.0`–`1.0`，不会出现 `NaN`/`Infinity`。
- 模型若返回非 JSON 或畸形 JSON，服务会**兜底降级**为保守默认值
  （`visual_type=other`、`confidence=0.0`、`vision_description` 说明解析失败），
  仍返回结构合法的 200 响应，不会把畸形内容透传给 vBook。

## 8. 错误响应契约

业务错误返回契约规定的 JSON 结构：

```json
{
  "error": { "code": "invalid_request", "message": "...", "retryable": false },
  "request_id": "vbook-frame-000001"
}
```

支持的错误类型：

| HTTP | error.code | retryable | 触发条件 | 状态 |
| --- | --- | --- | --- | --- |
| 400 | `invalid_request` | false | **缺必填字段 / base64 或 mime 格式非法** | ✅ 符合契约（见说明①） |
| 400 | `unsupported_prompt_profile` | false | 未知 prompt_profile | ✅ 符合契约 |
| 413 | `image_too_large` | false | 解码后图片超过 10 MB | ✅ 符合契约 |
| 429 | `rate_limited` | true | 限流 | ✅ 已定义（当前未触发，无限流） |
| 500 | `model_error` | true | 模型调用异常 | ✅ 符合契约 |
| 503 | `service_unavailable` | true | 模型未加载/后端不可用 | ✅ 符合契约 |
| 504 | `timeout` | true | 推理超时（>120s） | ✅ 符合契约 |

## 9. 运行限制

```text
Supported prompt profiles:  vbook_visual_analysis_v1
Supported image MIME types: image/jpeg, image/png
Max decoded image size:     10 MB（超出返回 413 image_too_large）
Max image dimensions:       无显式上限（仅按字节大小限制）
Per-frame server timeout:   120 秒（超时返回 504）
Recommended client timeout: 120 秒（与 vBook adapter 默认一致）
Rate limit / QPS:           无限流；建议逐帧串行（与 adapter 默认一致）
Recommended concurrency:    1（单实例单 GPU；如需更高并发见文末扩展说明）
Model warmup time:          首次请求触发加载（约 21 秒），之后进入稳态
Measured latency (warm):    ~6.2 秒/帧（稳态；见下方实测说明）
```

**实测基线（2026-07-06，192.168.0.33）**

在目标机器（双 RTX 4090，`qwen3-vl:8b` 独占 GPU 1，与 qwen3.6 隔离互不抢显存）上，
用同一张内置测试幻灯片 `tests/fixtures/test_slide.png`（48 KB，1280x720）连续两次实测：

| 场景 | 端到端 | 模型推理 | visual_type | OCR | confidence |
| --- | --- | --- | --- | --- | --- |
| 冷启动（首帧，含模型加载） | 21365 ms | 21319 ms | `slide` | 109 字符 | 0.95 |
| **预热后（稳态）** | **6200 ms** | **6186 ms** | `slide` | 109 字符 | 0.95 |

> 说明：
> - **首帧慢是模型加载开销**，之后稳定在 ~6 秒/帧。vBook 批量处理时首帧偏慢属正常。
> - 结果稳定：两次 `visual_type`、OCR 长度、confidence 完全一致。
> - vBook 侧建议：客户端超时保持 120 秒（覆盖冷启动）；逐帧串行；估算批量总时长
>   按 ~6 秒/帧 + 首次一次性 ~21 秒（例如 100 帧约 11 分钟）。
> - 这仍是单张幻灯片的数据点；不同图片内容耗时会有差异，后续可积累平均/p95。

## 10. 日志

服务记录结构化 JSON 日志（`logs/app.log` / `error.log` / `performance.log`），
按要求包含 `request_id`、`frame_id`、HTTP status、model name、latency、error code，
**默认不记录** 完整 `image_base64`（仅记录大小）。

## 11. 服务组自测结果

| 自测项 | 状态 |
| --- | --- |
| `GET /health` 返回 `status=ok`、`model_loaded=true` | ✅ 实测通过（192.168.0.33） |
| clear slide → `visual_type=slide` + 非空 OCR | ✅ 实测通过（OCR 109 字符，confidence 0.95） |
| K-line → `visual_type=kline_case` 或 `other` | 待补测（有测试图 `test_kline.png`） |
| invalid request → 400 `invalid_request` 结构化错误 | ✅ 实测通过 + 单元测试 |
| unknown prompt profile → 400 `unsupported_prompt_profile` | ✅ 实测通过 + 单元测试 |

> 通过 `scripts/verify.ps1` 一键端到端验证：环境/Ollama/API/错误处理/真实图片分析
> 共 15 项检查全部通过（2026-07-06，目标机器双 4090）。K-line 场景待用
> `tests/fixtures/test_kline.png` 补测一次即可勾选。

## 契约对齐记录

### 偏差①：缺字段校验 → 已修复，现返回 400（✅ 已解决）

契约要求「缺 `image_base64`、非法 base64、不支持的 mime」返回
`400 invalid_request`。早期版本用 FastAPI 默认校验会返回 422，现已加异常处理器
统一转成契约结构：

```json
{
  "error": { "code": "invalid_request", "message": "image_mime_type: ...", "retryable": false },
  "request_id": "<若请求体可解析则 echo>"
}
```

- HTTP 状态码：`400`，`error.code = invalid_request`，`retryable = false`。
- 请求体可解析时会 echo `request_id`；请求体本身畸形（非法 JSON）时 `request_id` 为 `null`。
- 已有单元测试覆盖（缺字段、非法 mime、request_id echo），vBook 可按
  `400 + error.code` 统一解析所有客户端错误。

### 偏差②：`model.provider` → 已对齐为 `"qwen"`（✅ 已解决）

契约示例中 `model.provider = "qwen"`。早期版本返回 `"ollama"`（底层引擎名），
现已对齐为 `"qwen"`，与契约一致。`/health` 和 `/analyze-frame` 的 `model` 对象
现统一为：

```json
{ "provider": "qwen", "name": "qwen3-vl:8b", "version": "service-defined" }
```

### 待办：性能基线

`192.168.0.33` 部署后补充：模型 warmup 时间、平均/p95 延迟、各尺寸图片实测耗时。

## 回复模板（按问卷 §13 汇总）

```text
Service owner:        （请填）
Contact:              （请填）

Environment:          Windows Server, 双 RTX 4090, Ollama + FastAPI
Base URL:             http://192.168.0.33:8866
Analyze endpoint:     http://192.168.0.33:8866/analyze-frame
Health endpoint:      http://192.168.0.33:8866/health

Network:              LAN（可信内网）
Protocol:             http
Firewall / allowlist: 放行入站 TCP 8866

Auth required:        否
Token type:           —
Token expiration:     —
How to obtain token:  —

Supported prompt profiles:  vbook_visual_analysis_v1
Supported image MIME types: image/jpeg, image/png
Max decoded image size:     10 MB
Max image dimensions:       无显式上限

Per-frame server timeout:   120s
Recommended client timeout: 120s
Rate limit / QPS:           无限流
Recommended concurrency:    1

Model provider:             qwen
Model name:                 qwen3-vl:8b
Model version:              service-defined
Model warmup requirement:   待实测

Success response confirmed: 是
Error response confirmed:   是（缺字段已统一为 400 invalid_request）
Strict JSON confirmed:      是

Known limitations:          性能基线待部署后补充（详见「契约对齐记录」）
Deployment ETA:             （请填，部署到 192.168.0.33 的时间）
```
