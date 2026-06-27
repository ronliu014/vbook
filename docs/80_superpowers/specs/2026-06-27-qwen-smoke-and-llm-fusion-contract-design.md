# Qwen Smoke and LLM Fusion Contract Design

## 背景

vBook 侧已经完成 Qwen Vision Service adapter，并通过
`external-command` backend 调用外部 `POST /analyze-frame` 服务。Qwen 服务组已在
`docs/90_reference/integration-response.md` 中回复当前服务契约：

- Base URL: `http://192.168.0.33:8866`
- Analyze endpoint: `http://192.168.0.33:8866/analyze-frame`
- Health endpoint: `http://192.168.0.33:8866/health`
- 当前可信内网 HTTP，无认证。
- 唯一支持 prompt profile: `vbook_visual_analysis_v1`。
- 支持 JPEG / PNG。
- per-frame server timeout: 120 秒。
- recommended concurrency: 1。
- success response、error response、strict JSON 要求已与 vBook 契约对齐。
- 性能基线和部署后自测仍待实测。

同时，vBook 的知识融合已经推进到 deterministic evidence draft：能用 transcript、
视觉分析、OCR、图像描述、结构化观察和时间线关系生成可审计的 `KnowledgeSection[]`，
并支持保守的相邻 section merge。但它仍然不是最终 LLM 知识综合。

本阶段需要并行处理两个互不冲突的准备工作：

1. 把 Qwen 服务回复落地为 vBook 侧可执行的 smoke / 联调文档。
2. 定义 LLM-ready fusion contract，为未来模型综合做请求和响应 schema，但暂不调用模型。

## 目标

- 将 Qwen 服务组回复转化为 vBook 侧明确的联调口径和 smoke 命令。
- 保持 `tools/vision_qwen_adapter.py` 现有契约不变，除非测试证明必须修改。
- 明确真实服务上线前后的验收条件。
- 新增 LLM-ready fusion request artifact，用当前 evidence sections 作为输入。
- 新增 LLM fusion response parser / validator 的设计，但不接任何模型服务。
- 保持当前 deterministic evidence draft 作为默认用户输出路径。
- 所有新增 schema 都可通过 deterministic fixture 测试。

## 非目标

本阶段不做：

- 不调用 `192.168.0.33:8866`，除非用户明确说明服务已部署并要求 smoke。
- 不新增 OpenAI、Qwen、Ollama SDK 依赖。
- 不新增 `qwen-service` core backend。
- 不让 vBook core 直接依赖 Qwen 服务。
- 不把 LLM 输出作为默认 `note.md`。
- 不设计数据库或知识库检索。
- 不改变 `KnowledgeSection` dataclass。
- 不改变现有 `fusion/sections.json` schema。

## 方案选择

### 方案 A：先做真实 Qwen smoke，等服务上线后再继续

优点：

- 能尽快验证真实 OCR / 视觉描述质量。
- 可以暴露网络、防火墙、模型启动等真实问题。

缺点：

- 依赖 `192.168.0.33:8866` 已部署且可访问。
- 当前回复中性能基线仍待实测，今天不一定能完成。
- 会阻塞不依赖真实服务的 fusion contract 工作。

### 方案 B：先落文档和 LLM-ready contract，不调用真实服务

优点：

- 不依赖 Qwen 服务上线。
- 能把服务组回复变成可执行 smoke 说明。
- 能继续推进最终知识综合的接口基础。
- 不改变当前可运行 pipeline。

缺点：

- 不能证明真实服务已经可用。
- 不能验证真实模型输出质量。

### 方案 C：直接接入 LLM fusion

优点：

- 更接近最终智能笔记目标。

缺点：

- 需要模型服务、prompt、错误处理和质量评估同时落地，范围过大。
- 与当前“先稳定契约和 parser”的阶段不匹配。

## 决策

采用方案 B。

先完成：

- Qwen 服务回复落地文档。
- LLM-ready fusion request / response contract。
- deterministic parser / validator。

暂不调用真实 Qwen endpoint，也不调用任何 LLM。

## Qwen 服务回复落地设计

### 文档更新范围

更新 `docs/60_operations/smoke-tests.md`：

- 将 Qwen adapter smoke endpoint 示例从 `127.0.0.1:8000` 更新为
  `http://192.168.0.33:8866/analyze-frame`。
- 明确当前服务无认证，不需要 `--token`。
- 保留 token 说明作为未来认证启用时的可选路径。
- 增加 `GET /health` 预检命令。
- 增加当前运行限制：
  - max decoded image size: 10 MB
  - timeout: 120s
  - concurrency: 1
  - prompt profile: `vbook_visual_analysis_v1`
- 明确“性能基线待部署后补充”。

更新 `docs/90_reference/qwen-vision-service-integration-request.md`：

- 增加“服务组已回复”的链接和当前状态说明。
- 保留原问卷内容作为历史和后续服务变更的模板。

新增或更新 progress 文档：

- 记录 Qwen 服务组已回复。
- 记录 vBook 侧 adapter 与回复契约匹配。
- 记录真实 smoke 尚未开始，原因是部署/性能基线待实测。

### 真实 smoke 阶段门槛

只有满足以下条件，才开始真实服务 smoke：

- 用户明确告知服务已部署到 `192.168.0.33:8866`。
- `GET /health` 可访问并返回 HTTP 200。
- 防火墙已放行 TCP 8866。
- 有可用于 smoke 的本地 video 和 transcript。

### 真实 smoke 命令

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-qwen `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120"
```

### 验收口径

真实 smoke 通过的最低标准：

- build command exit code 为 0。
- `vision/external/frames.json` 生成。
- `vision/external/analysis.json` 生成。
- `vision/analysis.json` 生成。
- `fusion/sections.json` 生成，intent 为 `fusion_sections_evidence`。
- `manifest.json` 中 vision analysis stage 为 done。
- `note.md` 生成。
- 至少一个 frame 的 `ocr_text` 或 `vision_description` 能反映图片内容。

## LLM-ready Fusion Contract 设计

### 当前输入基础

现有 fusion artifacts：

- `fusion/prompt.json`
  - intent: `fusion_prompt_snapshot`
  - 包含 video、transcript segments、visual analyses、timeline links。
- `fusion/sections.json`
  - intent: `fusion_sections_evidence`
  - 包含 deterministic evidence `KnowledgeSection[]`。

新的 LLM-ready contract 应该以 evidence sections 为主输入，而不是重新要求 LLM 理解所有原始视觉记录。

### 新 artifact：`fusion/llm_request.json`

建议新增 request builder：

```python
def build_llm_fusion_request(
    video: VideoAsset,
    evidence_sections: Sequence[KnowledgeSection],
) -> dict[str, Any]:
    ...
```

输出 schema：

```json
{
  "schema_version": "1",
  "intent": "llm_fusion_request",
  "task": "course_note_synthesis",
  "output_contract": {
    "schema_version": "1",
    "required_top_level_fields": [
      "title",
      "overview",
      "sections"
    ],
    "section_required_fields": [
      "title",
      "summary",
      "key_points",
      "source_timestamps",
      "image_refs",
      "tags"
    ]
  },
  "video": {
    "id": "lesson",
    "course_title": "Course",
    "lesson_title": "Lesson",
    "duration_seconds": 123.0
  },
  "instructions": [
    "Use only provided evidence.",
    "Preserve source_timestamps and image_refs.",
    "Do not invent facts not supported by evidence.",
    "Write concise Simplified Chinese notes unless evidence is clearly another language."
  ],
  "evidence_sections": [
    {
      "title": "短线选股",
      "summary": "讲解：...",
      "source_timestamps": [0.0, 14.0],
      "image_refs": ["outputs/lesson/frames/selected/frame_000001.jpg"],
      "key_points": ["均线多头排列"],
      "tags": ["evidence", "visual:slide", "has_ocr"]
    }
  ]
}
```

### 新 parser：LLM fusion response parser

建议新增模块：

```text
vbook_fusion/llm_contract.py
```

职责：

- 构建 `llm_request`。
- 校验 LLM response JSON。
- 将合法 response 转为 `KnowledgeSection[]`。
- 写 `fusion/llm_request.json`。
- 写 `fusion/llm_sections.json`。

本阶段不执行 prompt，也不调用模型。

### LLM response schema

LLM response 必须是标准 JSON object：

```json
{
  "schema_version": "1",
  "title": "课程标题",
  "overview": "本节课讲解...",
  "sections": [
    {
      "title": "短线选股条件",
      "summary": "这一节说明...",
      "key_points": [
        "均线多头排列是条件之一"
      ],
      "source_timestamps": [0.0, 14.0],
      "image_refs": [
        "outputs/lesson/frames/selected/frame_000001.jpg"
      ],
      "tags": [
        "llm",
        "evidence",
        "visual:slide"
      ]
    }
  ]
}
```

### Parser 规则

校验规则：

- response 必须是 object。
- `schema_version` 必须是 `"1"`。
- `title` 必须是 string，可为空但必须存在。
- `overview` 必须是 string，可为空但必须存在。
- `sections` 必须是 list。
- 每个 section 必须包含：
  - `title`: string
  - `summary`: string
  - `key_points`: list[string]
  - `source_timestamps`: list[number]
  - `image_refs`: list[string]
  - `tags`: list[string]
- 所有 number 必须是有限数字。
- `source_timestamps` 至少保留 0 个，最多不强制，但必须全是有限数字。
- `image_refs` 和 `tags` 稳定去重。
- parser 自动给每个 section 增加 `llm` tag。
- parser 不允许 long-form Markdown response 直接进入 `KnowledgeSection[]`。

错误处理：

- parser fail-fast，抛出 `ValueError`。
- 错误信息包含字段路径，例如：
  - `sections[0].title must be a string`
  - `sections must be a list`
  - `source_timestamps[1] must be finite`

### 与现有 note 的关系

本阶段不让 `note.md` 默认使用 LLM sections。

后续可以新增显式 CLI flag：

```text
--fusion-mode evidence | llm-json
```

但这不是本阶段内容。本阶段只提供 request / parser / writer，供未来手动或外部命令产生 LLM response 后接入。

## 文件边界

### 本阶段文档改动

- `docs/60_operations/smoke-tests.md`
- `docs/90_reference/qwen-vision-service-integration-request.md`
- `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`
- `docs/80_superpowers/specs/2026-06-27-qwen-smoke-and-llm-fusion-contract-design.md`

### 后续实现改动

- 新增：`vbook_fusion/llm_contract.py`
- 新增：`tests/test_fusion/test_llm_contract.py`
- 可能新增 CLI 或 manifest wiring，但只有在单独计划确认后做。

## 测试策略

### Qwen 文档落地

文档改动通过人工 review 和 `git diff --check` 验证。

### LLM contract

使用 `unittest`：

- `build_llm_fusion_request()` 输出稳定 schema。
- request 包含 video metadata、instructions、output contract 和 evidence sections。
- parser 接受合法 response 并返回 `KnowledgeSection[]`。
- parser 给 section 添加 `llm` tag。
- parser 拒绝：
  - 非 object response
  - 缺 `sections`
  - section 字段类型错误
  - 非有限数字
  - `key_points` / `image_refs` / `tags` 中的非 string 值

最终验证：

```powershell
python -m unittest tests.test_fusion.test_llm_contract
python -m unittest discover
```

## 风险与控制

- 风险：把 Qwen 服务回复误写成“已联调通过”。
  - 控制：文档明确当前只是服务组回复，真实 smoke 仍待部署后执行。
- 风险：LLM contract 过早绑定具体模型。
  - 控制：只定义 provider-neutral JSON request/response，不出现模型 SDK。
- 风险：LLM 输出污染默认 note。
  - 控制：本阶段不改默认 `note.md` 路径。
- 风险：response parser 太宽松，后续吞掉坏输出。
  - 控制：fail-fast，字段路径明确，拒绝非 JSON 和非有限数字。

## 验收口径

设计完成后：

- Qwen 服务回复已纳入 vBook 侧联调文档。
- 文档明确当前 endpoint、无 token、timeout、concurrency、待实测项。
- LLM-ready fusion contract 明确 request 和 response schema。
- 后续实现计划可以直接按 TDD 新增 `vbook_fusion/llm_contract.py`。
- 不需要真实 Qwen 服务即可继续实现和测试。
