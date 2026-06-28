# LLM Fusion Contract Samples Design

## 背景

vBook 已经支持 provider-neutral 的 LLM fusion external-command 流程：

```text
fusion/sections.json
  -> fusion/llm_request.json
  -> external LLM command
  -> fusion/llm_response.json
  -> parse_llm_fusion_response()
  -> fusion/llm_sections.json
  -> note.md
```

仓库也已经提供 `tools/llm_fusion_stub.py`，可以在没有真实 LLM 服务时跑通
`--llm-fusion-command` 闭环。但真实服务组后续交付时仍缺少一组固定的 contract 样例和本地
验收命令。现在 `docs/90_reference/README.md` 还列着 planned `sample-json.md`，但实际没有
可执行样例资产。

本阶段要补齐这个联调前置条件：让外部服务组可以拿到 sample request，生成 sample response，
再用 vBook 提供的 checker 自测是否符合当前 contract。

## 目标

- 新增 repo 内置 LLM fusion sample JSON 目录。
- 提供一个本地 contract checker，校验 sample 或服务组生成的 request/response 文件。
- 更新 LLM fusion command requirements，说明如何用样例和 checker 自测。
- 新增可转交给外部 LLM/Qwen 文本服务组的联调需求清单。
- 保持当前 `--llm-fusion-command`、request/response schema、parser 和 note export 行为不变。

## 非目标

本阶段不做：

- 不调用真实 Qwen 服务。
- 不新增 HTTP client。
- 不新增 OpenAI、Qwen、Ollama 或其他模型 SDK。
- 不改变 `vbook_fusion.llm_contract` 的 schema。
- 不改变 `tools/llm_fusion_stub.py` 输出规则。
- 不改变 `note.md` 模板。
- 不做模型质量评估。
- 不要求真实视频、图片或 transcript fixture。

## 方案选择

### 方案 A：样例 + contract checker + 转交清单

新增 sample JSON 文件、`tools/check_llm_fusion_contract.py` 和文档说明。

优点：

- 不依赖真实服务上线。
- 服务组可以独立自测 response 是否被 vBook 接受。
- vBook 侧可以用同一命令验收外部 command 的输出。
- 能修复 reference README 中 sample 文档缺口。

缺点：

- 只验证 contract，不评价模型输出质量。
- 只覆盖文件交接，不覆盖真实 HTTP 可用性。

### 方案 B：只写联调文档

只补外部服务组沟通清单，不新增样例和 checker。

优点：

- 改动少。

缺点：

- 后续仍靠人工判断 JSON 是否合规。
- 样例可能和 parser 逐渐漂移。

### 方案 C：先做 Qwen 视觉 smoke runner

新增一个真实视觉服务 health/analyze-frame smoke runner。

优点：

- Qwen 视觉服务上线后可以直接测 HTTP 连通性。

缺点：

- 当前服务尚未部署，无法完成端到端实测。
- 它解决的是视觉服务连通性，不解决 LLM fusion response contract 样例缺口。

## 决策

采用方案 A：样例 + contract checker + 转交清单。

原因：

- 这是当前不等待 Qwen 部署也能推进的最高价值工作。
- 它直接服务真实 LLM/Qwen 文本综合服务上线后的联调。
- 它把“能否被 vBook parser 接受”变成可重复命令，而不是口头约定。
- 它不改变现有 pipeline 行为，风险低。

## 文件结构

新增：

```text
docs/90_reference/samples/
  llm_fusion_request.valid.json
  llm_fusion_response.valid.json
  llm_fusion_response.invalid_markdown.txt
  llm_fusion_response.invalid_schema.json

tools/check_llm_fusion_contract.py
tests/test_tools/test_check_llm_fusion_contract.py
docs/90_reference/llm-fusion-service-integration-request.md
```

修改：

```text
docs/90_reference/README.md
docs/90_reference/llm-fusion-command-requirements.md
docs/00_project/status.md
```

## Sample Assets

### Valid Request

`docs/90_reference/samples/llm_fusion_request.valid.json` 表示服务组应支持读取的最小真实形态。

要求：

- 顶层是 JSON object。
- `schema_version` 为 `"1"`。
- `intent` 为 `"llm_fusion_request"`。
- `task` 为 `"course_note_synthesis"`。
- 包含 `output_contract`、`video`、`instructions` 和 `evidence_sections`。
- 至少包含两个 evidence sections：
  - 一个 slide 类 evidence，含 OCR/视觉标签和图片引用。
  - 一个 transcript 类 evidence，展示无图片或弱视觉证据的情况。
- 内容使用简体中文，贴近课程笔记场景。

### Valid Response

`docs/90_reference/samples/llm_fusion_response.valid.json` 表示服务组输出应满足的最小有效形态。

要求：

- 顶层是 JSON object。
- `schema_version` 为 `"1"`。
- 包含 `title`、`overview`、`sections`。
- `sections` 至少包含两个 section。
- 每个 section 包含：
  - `title`: string
  - `summary`: string
  - `key_points`: list[string]
  - `source_timestamps`: list[number]
  - `image_refs`: list[string]
  - `tags`: list[string]
- 至少一个 section 带 `final` tag。
- 保留 request 中的关键 `source_timestamps` 和 `image_refs`。

### Invalid Samples

`llm_fusion_response.invalid_markdown.txt` 表示模型常见错误：把 JSON 包在 Markdown code fence 或输出解释性文本。

`llm_fusion_response.invalid_schema.json` 表示结构是 JSON 但不符合 vBook response schema，例如缺少
`sections` 或 `source_timestamps` 含 bool。

这些无效样例用于 checker 测试和服务组排查，不用于正常 pipeline。

## Contract Checker

新增命令：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response docs\90_reference\samples\llm_fusion_response.valid.json
```

### 参数

| Argument | Required | Description |
| --- | --- | --- |
| `--request` | yes | vBook LLM fusion request JSON path。 |
| `--response` | yes | external command 或服务组生成的 response JSON path。 |

### Request Checks

checker 校验 request：

- 文件存在。
- 文件是 UTF-8 JSON。
- 顶层是 object。
- `schema_version == "1"`。
- `intent == "llm_fusion_request"`。
- `evidence_sections` 是 list。
- 每个 evidence section 是 object。
- 每个 evidence section 的核心字段类型符合当前 request contract：
  - `title`: string
  - `summary`: string
  - `key_points`: list[string]
  - `source_timestamps`: list[number]，bool 无效
  - `image_refs`: list[string]
  - `tags`: list[string]

### Response Checks

checker 校验 response：

- 文件存在。
- 文件是 UTF-8 JSON。
- 顶层是 object。
- 调用现有 `vbook_fusion.llm_contract.parse_llm_fusion_response()`。
- parser 返回至少 0 个 `KnowledgeSection`，数量不限。
- 输出 section count，方便服务组确认。

checker 不单独实现 response parser，避免 contract 逻辑复制。它只负责文件读取、request 校验和调用现有 parser。

### Exit Codes

成功：

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: <N>
```

返回 exit code `0`。

失败：

```text
ERROR: <reason>
```

返回 exit code `1`。

常见失败信息：

- `request file does not exist: <path>`
- `response file does not exist: <path>`
- `invalid request JSON: <json error>`
- `invalid response JSON: <json error>`
- `request JSON must be an object`
- `request schema_version must be '1'`
- `request intent must be 'llm_fusion_request'`
- `request evidence_sections must be a list`
- `request evidence_sections[0].source_timestamps[0] must be a number`
- `response sections[0].source_timestamps[0] must be a number`

## 外部服务组转交清单

新增 `docs/90_reference/llm-fusion-service-integration-request.md`，用于转交给 LLM/Qwen 文本综合服务组。

内容包括：

- vBook 当前 LLM fusion 文件交接流程。
- 服务组需要实现的命令行入口或 HTTP wrapper。
- vBook 提供的 sample request 路径。
- 服务组应回传 sample response 路径或内容。
- 自测命令：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response path\to\service-generated-response.json
```

- 需要服务组回复的信息：
  - command 路径和运行参数。
  - 是否需要 endpoint、model、token、timeout。
  - 支持的最大 evidence section 数。
  - 超时和失败时 stderr 格式。
  - 是否保证严格 JSON，不输出 Markdown fence。
  - 自测结果。

这份清单不替代 `llm-fusion-command-requirements.md`，而是面向沟通和回填的短表。

## 文档更新

### `docs/90_reference/README.md`

将 planned `sample-json.md` 调整为实际样例入口：

- 增加 `samples/` 目录说明。
- 增加 `llm-fusion-service-integration-request.md`。
- 移除或降级不再准确的 planned `sample-json.md`。

### `docs/90_reference/llm-fusion-command-requirements.md`

增加章节：

- `Sample Files`
- `Contract Checker`
- `External Team Self-Test`

说明样例路径、checker 命令、成功/失败输出和验收口径。

### `docs/00_project/status.md`

更新：

- What Works Now：增加 LLM fusion sample contract checker。
- What Is Still Placeholder or Partial：说明 checker 只验证 contract，不验证模型质量。
- Verification Snapshot：实现后按实际 full suite 测试数更新。

## 测试策略

### TDD Unit Tests

新增 `tests/test_tools/test_check_llm_fusion_contract.py`。

测试项：

- valid sample request + valid sample response 返回 `0`，stdout 包含 success 和 parsed section count。
- missing request 返回 `1`，stderr 包含 `request file does not exist`。
- invalid request JSON 返回 `1`。
- invalid request shape 返回 `1`。
- invalid markdown response 返回 `1`，stderr 指出 response JSON 无效。
- invalid schema response 返回 `1`，stderr 指出 parser 校验失败。
- checker 拒绝 bool timestamp。

测试直接调用 `tools.check_llm_fusion_contract.main(argv)`，不需要真实服务。

### Sample File Tests

测试会读取 repo 内 sample 文件，确保：

- sample request 能通过 checker request 校验。
- sample response 能被 `parse_llm_fusion_response()` 接受。
- invalid samples 保持无效，避免误改成有效样例。

### Full Verification

实现完成后运行：

```powershell
python -m unittest tests.test_tools.test_check_llm_fusion_contract
python -m unittest discover
```

## 验收口径

本阶段完成后应满足：

- sample request/response 文件存在并可被 checker 验证。
- invalid samples 会被 checker 拒绝。
- 外部服务组可以只拿 sample request 和 checker 命令完成自测。
- `llm-fusion-command-requirements.md` 能指向样例和 checker。
- 转交清单能直接发给服务组，不需要额外口头解释。
- 不访问网络。
- 不新增依赖。
- `python -m unittest discover` 通过。

## 风险与处理

- 风险：checker request 校验逻辑和 `tools/llm_fusion_stub.py` 重复。
  - 处理：接受少量重复，因为 checker 是 reference tool，后续如有更多复用需求再抽公共 helper。
- 风险：sample 内容被误解为模型质量标准。
  - 处理：文档明确 sample 只代表 contract 形态，不代表最终笔记质量。
- 风险：外部服务是 HTTP 而不是 command。
  - 处理：第一版仍要求服务组提供 command wrapper；HTTP 细节可隐藏在 wrapper 内。

## 后续工作

- 服务部署后，用 checker 验证真实服务生成的 response。
- 如服务组只提供 HTTP endpoint，再设计 `tools/llm_fusion_http_adapter.py`。
- 真实视觉服务 ready 后，单独推进 Qwen Vision health/analyze-frame smoke runner。
- 后续再设计 LLM response 的质量评价和专家笔记增强，不在本阶段混入。
