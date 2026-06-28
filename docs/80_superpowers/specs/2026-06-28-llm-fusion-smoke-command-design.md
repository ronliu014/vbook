# LLM Fusion Smoke Command Design

## 背景

vBook 已经具备 LLM fusion external-command 执行入口：

```text
fusion/sections.json
  -> fusion/llm_request.json
  -> external command
  -> fusion/llm_response.json
  -> fusion/llm_sections.json
  -> note.md
```

但当前仓库内还没有一个可直接使用的 LLM fusion smoke command。测试里会临时生成
`fake_llm_fusion.py`，外部需求书里也使用 `your_llm_fusion.py` 作为示例。这对自动化测试
足够，但对用户、本地演示和跨团队联调不够方便。

Qwen 视觉服务尚未准备好时，可以先补上一个确定性的本地 LLM fusion smoke 工具，让
`--llm-fusion-command` 的完整闭环不依赖真实模型、网络服务或外部项目。

## 目标

- 新增 repo 内置 smoke command：`tools/llm_fusion_stub.py`。
- 读取 vBook 生成的 `fusion/llm_request.json`。
- 写出符合 `parse_llm_fusion_response()` contract 的 `fusion/llm_response.json`。
- 保留 evidence section 的来源时间戳、图片引用和关键要点。
- 生成 deterministic、可测试、无网络依赖的输出。
- 提供明确错误处理：输入缺失、非法 JSON、非法 request shape 时返回非 0 exit code。
- 在 CLI integration test 中使用真实 `tools/llm_fusion_stub.py` 跑完整 build 流程。

## 非目标

本阶段不做：

- 不调用真实 LLM。
- 不接入 Qwen、OpenAI、Ollama 或任何 SDK。
- 不读取视频、音频或图片文件。
- 不修改 LLM request/response contract。
- 不新增 CLI 参数。
- 不替代外部团队实现的真实 LLM command。
- 不生成学习目标、术语表、复习题等 schema 外字段。

## 方案选择

### 方案 A：新增 `tools/llm_fusion_stub.py`

新增一个和 `tools/vision_stub.py` 类似的 deterministic smoke 工具。

命令：

```powershell
python tools\llm_fusion_stub.py --input fusion\llm_request.json --output fusion\llm_response.json
```

优点：

- 用户可以直接复制命令跑完整 LLM fusion smoke。
- 不依赖真实服务，适合 CI、本地演示和故障排查。
- 与现有 `vision_stub.py` 工具定位一致。
- 能把临时 fake script 从 integration test 升级为仓库内稳定工具。

缺点：

- 输出只是 deterministic 改写，不代表真实模型质量。

### 方案 B：只补文档示例

只在文档中写一个临时脚本示例，不把脚本放入仓库。

优点：

- 改动更少。

缺点：

- 用户仍需复制脚本，容易和 vBook contract 漂移。
- CLI smoke 仍只能依赖测试中临时生成的 fake command。

### 方案 C：直接设计真实 provider command

开始设计一个真实 LLM provider wrapper，读取 endpoint/model/API key。

优点：

- 更接近最终智能输出。

缺点：

- 真实服务、认证、模型行为和提示词都尚未稳定。
- 会过早引入 provider 差异和网络失败面。

## 决策

采用方案 A：新增 `tools/llm_fusion_stub.py`。

原因：

- 它补齐了本地可演示闭环，不等待 Qwen 或真实 LLM 服务。
- 它不改变 vBook core 的 provider-neutral 边界。
- 它能作为外部团队实现真实 command 的最小参考实现。
- 它让后续排查问题时可以区分：vBook pipeline 问题、外部 command 问题、真实模型质量问题。

## 用户接口

### Command

```powershell
python tools\llm_fusion_stub.py --input <path-to-llm-request.json> --output <path-to-llm-response.json>
```

参数：

| Argument | Required | Description |
| --- | --- | --- |
| `--input` | yes | vBook 生成的 `fusion/llm_request.json`。 |
| `--output` | yes | 工具写出的 `fusion/llm_response.json`。 |

与 vBook 集成：

```powershell
python -m vbook_client build `
  --video data\lesson.mp4 `
  --transcript data\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-command "python tools\llm_fusion_stub.py --input {input} --output {output}"
```

## 输入要求

工具读取 UTF-8 JSON object。最低要求：

```json
{
  "schema_version": "1",
  "intent": "llm_fusion_request",
  "task": "course_note_synthesis",
  "video": {
    "id": "lesson",
    "course_title": "Course",
    "lesson_title": "Lesson"
  },
  "evidence_sections": [
    {
      "title": "短线选股",
      "summary": "讲解短线选股的基本观察条件。",
      "key_points": ["均线多头排列"],
      "source_timestamps": [0.0, 14.0],
      "image_refs": ["outputs/lesson/frames/selected/frame_000001.jpg"],
      "tags": ["evidence", "visual:slide"]
    }
  ]
}
```

校验规则：

- 顶层必须是 object。
- `schema_version` 必须是 `"1"`。
- `intent` 必须是 `"llm_fusion_request"`。
- `evidence_sections` 必须是 list。
- 每个 evidence section 必须是 object。
- 每个 evidence section 的这些字段必须满足 response contract：
  - `title`: string
  - `summary`: string
  - `key_points`: list[string]
  - `source_timestamps`: list[number]，不能是 bool
  - `image_refs`: list[string]
  - `tags`: list[string]

工具可以忽略 `output_contract` 和 `instructions`，但它们存在时不应导致失败。

## 输出行为

输出必须是标准 UTF-8 JSON object：

```json
{
  "schema_version": "1",
  "title": "Lesson",
  "overview": "Deterministic smoke synthesis from 1 evidence section.",
  "sections": [
    {
      "title": "短线选股",
      "summary": "讲解短线选股的基本观察条件。",
      "key_points": ["均线多头排列"],
      "source_timestamps": [0.0, 14.0],
      "image_refs": ["outputs/lesson/frames/selected/frame_000001.jpg"],
      "tags": ["evidence", "visual:slide", "final"]
    }
  ]
}
```

### Title Rule

顶层 `title` 优先级：

1. `video.lesson_title`
2. `video.course_title`
3. `video.id`
4. `"vBook LLM Fusion Smoke Note"`

### Overview Rule

`overview` 使用 deterministic 文案：

```text
Deterministic smoke synthesis from <N> evidence section(s).
```

### Section Rule

每个 output section 来自一个 evidence section：

- `title` 原样保留；如果为空字符串，使用 `Evidence Section <index>`。
- `summary` 原样保留；如果为空字符串，使用 `Smoke summary for <title>.`。
- `key_points` 原样保留。
- `source_timestamps` 原样保留。
- `image_refs` 原样保留。
- `tags` 原样保留并稳定追加 `final`。

如果没有 evidence sections，输出：

```json
{
  "schema_version": "1",
  "title": "...",
  "overview": "Deterministic smoke synthesis from 0 evidence sections.",
  "sections": []
}
```

## 错误处理

`tools/llm_fusion_stub.py` 失败时：

- 向 stderr 写出简短、可定位错误。
- 返回 exit code `1`。
- 不写成功 response。

错误示例：

```text
input file does not exist: fusion/llm_request.json
invalid input JSON: Expecting value: line 1 column 1 (char 0)
input JSON must be an object
schema_version must be '1'
intent must be 'llm_fusion_request'
evidence_sections must be a list
evidence_sections[0].title must be a string
```

## 文件写入

工具直接写 `--output` 指定路径：

- 自动创建 output parent directory。
- 使用 `json.dumps(..., ensure_ascii=False, indent=2)`。
- 文件末尾加换行。

本阶段不要求原子写入。原因是 smoke 工具只用于本地确定性演示，且 vBook 执行 command 前
已经删除旧 response，避免 stale output。

## 测试策略

### Unit Tests

新增 `tests/test_tools/test_llm_fusion_stub.py`：

- valid request 写出合法 response。
- 缺 input 文件返回 `1`，stderr 包含 `input file does not exist`。
- 非法 JSON 返回 `1`，stderr 包含 `invalid input JSON`。
- 顶层非 object 返回 `1`。
- `schema_version` 非 `"1"` 返回 `1`。
- `intent` 非 `"llm_fusion_request"` 返回 `1`。
- `evidence_sections` 非 list 返回 `1`。
- section 字段类型非法返回 `1`。

测试直接调用 `tools.llm_fusion_stub.main(argv)`，不需要 subprocess。

### CLI Integration

扩展 `tests/test_client/test_manifest_cli.py`：

- 使用真实 `tools/llm_fusion_stub.py` 作为 `--llm-fusion-command`。
- 跑 `build`。
- 断言生成：
  - `fusion/llm_request.json`
  - `fusion/llm_response.json`
  - `fusion/llm_sections.json`
  - `note.md`
  - `manifest.json`
- 断言 `manifest["stage_status"]["llm_fusion"] == "done"`。
- 断言 `note.md` 包含 smoke section title、summary 和专家笔记结构。

### Full Verification

```powershell
python -m unittest tests.test_tools.test_llm_fusion_stub
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

## 文档更新

实现后更新：

- `docs/00_project/status.md`
  - What Works Now 增加 `tools/llm_fusion_stub.py`。
  - Placeholder/Partial 说明：它是 deterministic smoke command，不是真实模型。
  - Verification Snapshot 更新测试数。
- `docs/30_pipeline/overview.md`
  - 阶段 7 增加本地 smoke command 说明。
- `docs/90_reference/llm-fusion-command-requirements.md`
  - 增加 repo 内置 smoke command 示例。

## 验收口径

本阶段完成后，应满足：

- 用户可以用 `tools/llm_fusion_stub.py` 跑通 `--llm-fusion-command`。
- smoke command 输出能被 `parse_llm_fusion_response()` 接受。
- CLI build 生成 LLM request、LLM response、LLM sections、expert `note.md` 和 manifest。
- 不访问网络。
- 不新增依赖。
- `python -m unittest discover` 通过。

## 后续工作

完成后可以继续：

- 等 Qwen 视觉服务 ready 后跑真实视觉 smoke。
- 让外部 LLM 团队参考 `tools/llm_fusion_stub.py` 实现真实模型 command。
- 设计下一版 LLM response expert-note schema，增加学习目标、术语表和复习题。
