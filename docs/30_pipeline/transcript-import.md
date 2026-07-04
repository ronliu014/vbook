# Transcript Import

## 阶段目标

把外部 transcript 文件转换成 vBook 内部统一的 `TranscriptSegment[]`，为后续时间轴对齐、融合和导出提供稳定文本证据。

## 当前状态

Status: `Done`

当前稳定支持 timestamped JSON 和 SRT。Batch discovery 会匹配 `.vtt` 和 `.txt` 文件名，但当前稳定推荐格式仍是 `.srt` 或 timestamped JSON。

## 输入

- CLI `--transcript`
- Timestamped JSON transcript
- SRT transcript
- Batch layout 中的 `input/text/<relative_parent>/<stem>.srt`

## 输出

- `TranscriptSegment[]`
- Segment fields: `id`, `start`, `end`, `text`, `language`, `confidence`, `source`

## 关键代码

- `vbook_audio/transcript.py::load_transcript`
- `vbook_audio/transcript.py::_load_json_transcript`
- `vbook_audio/transcript.py::_load_srt_transcript`
- `vbook_common/types.py::TranscriptSegment`
- `vbook_common/types.py::TranscriptSourceType`

## CLI 与配置入口

- `python -m vbook_client manifest --transcript <path>`
- `python -m vbook_client build --transcript <path>`
- `python -m vbook_client build-batch --input <dir> --output <dir>`

## 产物路径

当前 transcript import 没有独立默认持久化文件。导入结果进入内存中的 `TranscriptSegment[]`，并通过下游 `manifest.json`、`fusion/prompt.json`、`fusion/sections.json` 和 `note.md` 间接可见。

## 失败边界

- 文件路径不存在或不可读时，CLI build 无法继续。
- Transcript 文件格式不受 `load_transcript()` 支持时，单课 build 失败。
- Batch 中找不到匹配 transcript 时，该 lesson 记录为 `skipped`，原因是 `missing_transcript`。
- Batch 中匹配到当前 loader 不支持的 transcript 格式时，该 lesson 记录为 `failed`，原因通常是 `unsupported_transcript_format`。

## 验收与测试

```powershell
python -m unittest tests.test_audio.test_transcript
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- vBook 当前不内置语音识别。
- vBook 可以借鉴 vtext 流程，但不 import、不 vendor、不依赖 vtext 代码。
- `.srt` 是当前稳定推荐 batch transcript 格式。

## 后续任务

- 在真实 smoke fixture 可用后补充长期保留的 transcript 样例策略。
- 如需支持 `.vtt` 或 `.txt`，需要先扩展 loader 和测试，再更新 batch 文档。

## 相关文档

- [overview.md](./overview.md)
- [../20_architecture/data-model.md](../20_architecture/data-model.md)
- [../60_operations/batch-processing.md](../60_operations/batch-processing.md)
