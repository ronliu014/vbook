# LLM Fusion Command Requirements

## 1. 背景与目标

vBook 已经支持显式的 `--llm-fusion-command`。当用户提供这个参数时，vBook 会先把
deterministic evidence sections 写成 `fusion/llm_request.json`，再调用外部命令生成
`fusion/llm_response.json`，最后由 vBook 校验 response、写出
`fusion/llm_sections.json`，并用 LLM sections 渲染 `note.md`。

本需求书面向外部 LLM command 实现方。目标是让另一个项目组可以独立实现一个兼容 vBook
的命令行工具，而不需要修改 vBook core。

第一版目标：

- 从 vBook 生成的 `fusion/llm_request.json` 读取课程证据。
- 调用任意可用 LLM、工作流或人工辅助流程进行课程笔记综合。
- 写出符合 vBook contract 的 `fusion/llm_response.json`。
- 在失败时以非 0 exit code 和清晰 stderr 反馈原因。
- 不依赖 vBook 内部 Python API。

## 2. 总体设计

vBook 和外部 LLM command 通过两个 JSON 文件交接：

```text
vBook build
  -> fusion/sections.json
  -> fusion/llm_request.json
  -> external LLM command
  -> fusion/llm_response.json
  -> vBook parse_llm_fusion_response()
  -> fusion/llm_sections.json
  -> note.md
```

外部 command 只需要关心：

- 读取 `{input}` 指向的 request JSON。
- 严格写出 `{output}` 指向的 response JSON。
- 保证 response 是标准 JSON object，不是 Markdown、日志文本或代码块。

外部 command 不需要读取 vBook manifest，也不需要直接生成 `note.md`。

## 3. 命令行接口

外部实现方应提供一个可由 vBook 直接执行的命令，例如：

```powershell
python your_llm_fusion.py --input fusion/llm_request.json --output fusion/llm_response.json
```

vBook 侧使用命令模板调用该工具。模板必须包含 `{input}` 和 `{output}` 两个占位符：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-command "python your_llm_fusion.py --input {input} --output {output}"
```

vBook 会在运行时把 `{input}` 替换为 `fusion/llm_request.json` 路径，把 `{output}` 替换为
`fusion/llm_response.json` 路径。

推荐参数：

| Argument | Required | Description |
| --- | --- | --- |
| `--input` | yes | vBook 生成的 LLM fusion request JSON 路径。 |
| `--output` | yes | command 必须写出的 LLM fusion response JSON 路径。 |
| `--model` | no | 模型名称或部署名。 |
| `--endpoint` | no | HTTP LLM 服务地址；如果使用本地 SDK 可省略。 |
| `--timeout-seconds` | no | 单次处理超时时间。 |
| `--temperature` | no | 采样温度，建议默认较低。 |

推荐第一版保持同步命令行模式：命令退出时，`--output` 文件必须已经写完。

## 4. 输入文件：`fusion/llm_request.json`

vBook 写出的 request 是 UTF-8 JSON object。示例：

```json
{
  "schema_version": "1",
  "intent": "llm_fusion_request",
  "task": "course_note_synthesis",
  "output_contract": {
    "schema_version": "1",
    "required_top_level_fields": ["title", "overview", "sections"],
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
      "summary": "讲解短线选股的基本观察条件。",
      "key_points": ["均线多头排列", "成交量放大"],
      "source_timestamps": [0.0, 14.0],
      "image_refs": ["outputs/lesson/frames/selected/frame_000001.jpg"],
      "tags": ["evidence", "visual:slide", "has_ocr"]
    }
  ]
}
```

### 4.1 Top-Level Fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | 当前固定为 `"1"`。 |
| `intent` | string | 当前固定为 `"llm_fusion_request"`。 |
| `task` | string | 当前固定为 `"course_note_synthesis"`。 |
| `output_contract` | object | vBook 期望的 response contract。 |
| `video` | object | 视频和课节元数据。 |
| `instructions` | list[string] | vBook 对模型行为的基础要求。 |
| `evidence_sections` | list[object] | 可引用的课程证据 section。 |

外部 command 可以忽略未知字段，但不得要求 vBook 提供本需求书之外的必填字段。

### 4.2 Evidence Section Fields

`evidence_sections` 中每个元素一般包含：

| Field | Type | Meaning |
| --- | --- | --- |
| `title` | string | evidence section 标题。 |
| `summary` | string | vBook deterministic fusion 生成的摘要。 |
| `key_points` | list[string] | 证据中的要点。 |
| `source_timestamps` | list[number] | 证据来源时间点，单位为秒。 |
| `image_refs` | list[string] | 证据关联的图片路径。 |
| `tags` | list[string] | 证据标签，例如 `evidence`、`visual:slide`、`has_ocr`。 |

这些字段已经是 vBook 对 transcript、OCR、视觉描述和 timeline link 的融合结果。第一版
LLM command 不需要再读取视频、音频或图片。

## 5. 输出文件：`fusion/llm_response.json`

外部 command 必须写出标准 UTF-8 JSON object。示例：

```json
{
  "schema_version": "1",
  "title": "课程标题",
  "overview": "本节课讲解短线选股的核心判断条件。",
  "sections": [
    {
      "title": "短线选股条件",
      "summary": "本节重点说明均线多头排列和成交量放大的组合条件。",
      "key_points": [
        "均线多头排列表示趋势方向较强。",
        "成交量放大用于确认资金参与度。"
      ],
      "source_timestamps": [0.0, 14.0],
      "image_refs": [
        "outputs/lesson/frames/selected/frame_000001.jpg"
      ],
      "tags": ["evidence", "visual:slide", "final"]
    }
  ]
}
```

### 5.1 Required Top-Level Fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | 必须为 `"1"`。 |
| `title` | string | 整体课程或课节标题。 |
| `overview` | string | 整体概述。 |
| `sections` | list[object] | 最终笔记 sections。 |

`title` 和 `overview` 当前会被 vBook parser 校验，但第一版 `note.md` 主要使用
`sections` 渲染。仍然必须提供这两个字段，以便后续模板升级时可以直接使用。

### 5.2 Forbidden Output Shapes

以下输出不兼容 vBook：

- Markdown 文本。
- 包在 Markdown code fence 中的 JSON。
- JSON array 作为顶层结构。
- 多个 JSON object 连续输出。
- 带注释的 JSON。
- Python dict 字面量。
- 包含 `NaN`、`Infinity` 或 `-Infinity` 的 JSON。

## 6. Section Schema

`sections` 中每个元素必须包含：

| Field | Type | Rule |
| --- | --- | --- |
| `title` | string | section 标题。 |
| `summary` | string | section 摘要，建议 1-3 段内。 |
| `key_points` | list[string] | 要点列表。 |
| `source_timestamps` | list[number] | 来源时间点，必须是有限数字；不能是 bool。 |
| `image_refs` | list[string] | 来源图片路径列表。 |
| `tags` | list[string] | 标签列表。 |

vBook 会稳定去重 `image_refs` 和 `tags`，并确保 parsed section 中包含 `llm` tag。外部
command 可以显式提供 `llm` tag，也可以不提供。

### 6.1 Timestamp Rules

- 单位为秒。
- 可以使用整数或浮点数。
- 只允许有限数字。
- 不允许 `true`、`false`、`NaN`、`Infinity`、`-Infinity`。
- 应尽量保留相关 evidence section 的 `source_timestamps`，方便用户回看视频。

### 6.2 Image Reference Rules

- `image_refs` 应来自输入 evidence。
- 当 section 基于某张图、OCR 或视觉描述形成时，应保留对应图片路径。
- 如果某个 section 纯粹来自 transcript evidence 且没有图片，可以使用空列表。
- 不要伪造不存在的图片路径。

### 6.3 Tag Rules

推荐 tags：

| Tag | Meaning |
| --- | --- |
| `final` | 外部 LLM command 生成的最终笔记 section。 |
| `visual:slide` | section 主要来自 slide 类视觉证据。 |
| `visual:kline_case` | section 主要来自 K 线或图表案例。 |
| `has_ocr` | section 使用了 OCR 文本。 |
| `transcript` | section 主要来自 transcript。 |
| `needs_review` | 模型认为该 section 需要人工复核。 |

Tags 应使用稳定、简短、可机器读取的英文标识。

## 7. 模型行为要求

外部 command 的模型或工作流应遵守：

- 只使用 `evidence_sections` 中提供的信息。
- 不编造没有证据支持的事实、数字、股票代码、结论或建议。
- 优先输出简体中文；除非输入证据明显是其他语言。
- 合并重复 evidence，而不是机械复述每个输入 section。
- 保留重要来源时间点和图片引用。
- 对 OCR 可疑、画面模糊、证据不足的内容降低确定性表达。
- 不输出投资建议式结论；如果课程证据本身包含观点，应表达为“课程中提到”或类似语气。
- 不把 prompt、系统消息、调试日志写入 response JSON。

推荐生成风格：

- `summary` 讲清楚本 section 的主要知识点。
- `key_points` 使用短句，便于后续搜索和复习。
- 不追求长篇文章式输出；vBook 后续还会继续迭代专家笔记模板。

## 8. 错误处理

### 8.1 成功条件

命令成功时必须满足：

- 进程 exit code 为 `0`。
- `{output}` 文件存在。
- `{output}` 是合法 JSON object。
- JSON 符合本需求书的 response schema。

### 8.2 失败条件

遇到以下情况时，命令应返回非 0 exit code：

- `--input` 缺失或不可读。
- input JSON 无法解析。
- input `schema_version` 不支持。
- LLM endpoint 不可用。
- 模型调用超时。
- 模型返回内容无法整理为合法 response JSON。
- output 路径不可写。

失败时应向 stderr 写出可定位的信息，例如：

```text
llm fusion failed: endpoint timeout after 120 seconds
```

失败时不要写出部分 response。vBook 会在执行 command 前删除旧的 response 文件，避免读取
stale output；外部 command 也应避免在失败时留下半截 JSON。

### 8.3 推荐原子写入

为了避免 vBook 读取到半写入文件，推荐先写临时文件，再替换目标文件：

```text
fusion/llm_response.json.tmp
  -> fsync/close
  -> rename to fusion/llm_response.json
```

Windows 和 Linux 都应使用同一目录内的 rename 或 replace 操作。

## 9. 运行参数建议

第一版建议：

| Setting | Recommendation |
| --- | --- |
| timeout | 120-300 seconds per lesson，按课程长度调整。 |
| temperature | 0.1-0.3，优先稳定可复现。 |
| retries | 对临时网络错误可重试 1-2 次。 |
| logging | 记录 input path、output path、model、latency、错误原因。 |
| stdout | 尽量只输出简短进度；不要把 response JSON 打到 stdout 作为唯一输出。 |
| secrets | API key 从环境变量或配置读取，不写入 request/response。 |

如果底层是 HTTP LLM 服务，建议支持：

```powershell
python your_llm_fusion.py `
  --input fusion/llm_request.json `
  --output fusion/llm_response.json `
  --endpoint http://127.0.0.1:8000 `
  --model qwen-or-other-model `
  --timeout-seconds 180
```

## 10. vBook 集成命令示例

### 10.1 默认路径

```powershell
python -m vbook_client build `
  --video data\lesson.mp4 `
  --transcript data\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-command "python tools\your_llm_fusion.py --input {input} --output {output}"
```

预期生成：

```text
outputs/lesson/fusion/sections.json
outputs/lesson/fusion/llm_request.json
outputs/lesson/fusion/llm_response.json
outputs/lesson/fusion/llm_sections.json
outputs/lesson/note.md
outputs/lesson/manifest.json
```

### 10.2 自定义路径

```powershell
python -m vbook_client build `
  --video data\lesson.mp4 `
  --transcript data\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-request-path runs\lesson\request.json `
  --llm-fusion-response-path runs\lesson\response.json `
  --llm-fusion-sections-path runs\lesson\sections.json `
  --llm-fusion-command "python tools\your_llm_fusion.py --input {input} --output {output}"
```

## 11. 验收测试

外部实现方交付时，应至少提供本地测试脚本或说明，覆盖以下场景。

### 11.1 Valid Request

输入：

- 一个合法 `llm_request.json`。
- 至少包含一个 `evidence_sections` 元素。

执行：

```powershell
python your_llm_fusion.py --input llm_request.json --output llm_response.json
```

期望：

- exit code 为 `0`。
- `llm_response.json` 存在。
- 顶层 `schema_version = "1"`。
- 顶层包含 `title`、`overview`、`sections`。
- `sections` 是 list。
- 每个 section 包含所有必填字段。

### 11.2 vBook Integration

执行 vBook：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-command "python your_llm_fusion.py --input {input} --output {output}"
```

期望：

- `fusion/llm_request.json` 存在。
- `fusion/llm_response.json` 存在。
- `fusion/llm_sections.json` 存在。
- `note.md` 包含 LLM response 中的 section title 或 summary。
- `manifest.json` 中 `stage_status.llm_fusion` 为 `"done"`。

### 11.3 Invalid Input Path

执行：

```powershell
python your_llm_fusion.py --input missing.json --output llm_response.json
```

期望：

- exit code 非 `0`。
- stderr 说明 input 不存在或不可读。
- 不生成成功 response。

### 11.4 Invalid Model Output

模拟模型返回 Markdown 或不合法 JSON。

期望：

- command 不应把无效内容原样写成最终 response。
- 如果无法修复为合法 JSON，应 exit code 非 `0`。
- stderr 说明模型输出无法解析或不符合 schema。

## 12. 非目标

第一版外部 LLM command 不需要提供：

- HTTP server。
- Web UI。
- 异步任务队列。
- Streaming response。
- vBook manifest 解析。
- 视频、音频或图片直接读取。
- `note.md` 生成。
- vBook Python package 依赖。
- 模型质量评估平台。
- 多 provider 路由系统。

如果实现方内部需要 HTTP 服务或队列，可以自行封装，但暴露给 vBook 的第一接口仍应是同步
command。

## 13. 交付 Checklist

交付给 vBook 侧联调前，应提供：

- 可执行命令或脚本路径。
- 运行环境说明，例如 Python 版本、依赖安装命令、环境变量。
- 支持的模型或 endpoint 配置方式。
- `--input` / `--output` 参数说明。
- 一份可用的 sample `llm_request.json`。
- 一份由工具生成的 sample `llm_response.json`。
- 本地验收测试结果。
- 超时、失败和重试策略说明。
- 如果需要网络服务，提供 host、port、认证方式和健康检查方式。

当 vBook 使用 `--llm-fusion-command` 能完整生成 `llm_request.json`、
`llm_response.json`、`llm_sections.json`、`note.md`，并在 manifest 中记录
`llm_fusion = done` 时，可以认为第一版联调完成。
