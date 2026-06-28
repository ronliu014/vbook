# LLM Fusion Service 对接需求与回复清单

本文用于发给 LLM/Qwen 文本综合服务项目组，确认服务交付方式、命令契约和联调条件。

## vBook 当前状态

vBook 已经支持通过 `--llm-fusion-command` 调用外部 LLM fusion command：

```text
fusion/sections.json
  -> fusion/llm_request.json
  -> external LLM command
  -> fusion/llm_response.json
  -> fusion/llm_sections.json
  -> note.md
```

vBook core 不依赖模型 SDK，也不直接绑定某个 provider。外部服务组只需要提供一个可执行
command，读取 `--input` 指向的 request JSON，并写出 `--output` 指向的 response JSON。

## vBook 提供的样例

可用 request 样例：

```text
docs/90_reference/samples/llm_fusion_request.valid.json
```

可用 response 样例：

```text
docs/90_reference/samples/llm_fusion_response.valid.json
```

无效输出样例：

```text
docs/90_reference/samples/llm_fusion_response.invalid_markdown.txt
docs/90_reference/samples/llm_fusion_response.invalid_schema.json
```

## 服务组自测命令

服务组生成 response 后，请用 vBook checker 自测：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response path\to\service-generated-response.json
```

通过时输出：

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: <N>
```

失败时输出：

```text
ERROR: <reason>
```

## 请服务组回复的信息

请回复以下内容，便于 vBook 侧联调：

| Item | Reply |
| --- | --- |
| Service owner | |
| Contact | |
| Command path | |
| Command example | |
| Requires endpoint | yes/no |
| Endpoint URL | |
| Requires token | yes/no |
| Token passing method | env var / CLI arg / none |
| Model provider | |
| Model name | |
| Recommended timeout seconds | |
| Max evidence sections per lesson | |
| Output language | Simplified Chinese / configurable |
| Strict JSON confirmed | yes/no |
| Markdown fence never written to response | yes/no |
| Invalid input returns non-zero exit code | yes/no |
| stderr includes readable failure reason | yes/no |
| Valid sample response passes checker | yes/no |

## 第一版验收口径

第一版联调通过需要满足：

- command 能读取 vBook 生成的 `fusion/llm_request.json`。
- command 能写出合法 `fusion/llm_response.json`。
- response 能通过 `tools/check_llm_fusion_contract.py`。
- vBook 使用 `--llm-fusion-command` 后能生成：
  - `fusion/llm_request.json`
  - `fusion/llm_response.json`
  - `fusion/llm_sections.json`
  - `note.md`
  - `manifest.json`
- `manifest.json` 中 `stage_status.llm_fusion` 为 `"done"`。

## 非目标

第一版不要求服务组提供：

- vBook Python package 依赖。
- vBook manifest 解析。
- `note.md` 生成。
- 视频、音频或图片读取。
- Web UI。
- Streaming response。
- 多 provider 路由系统。

如果服务内部使用 HTTP、队列或 SDK，请封装在 command 内。vBook 第一接口仍然是同步
command。
