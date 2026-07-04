# 30 Pipeline

`docs/30_pipeline/` 记录 vBook local MVP pipeline 的阶段边界。这里回答每个阶段当前负责什么、输入是什么、输出是什么、由哪个模块维护、当前状态如何、如何验收。

## 阅读顺序

1. [overview.md](./overview.md) - 端到端数据流。
2. 单个 stage doc - 查看某一阶段的输入、输出、失败边界和测试入口。
3. [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md) - 查看 `note.md` 和 `manifest.json` 输出 contract。
4. [../60_operations/](../60_operations/) - 查看本地 smoke、Qwen 联调和 batch 操作 runbook。

## Stage Matrix

| Stage | Status | Main artifact | Owner module | Stage doc |
| --- | --- | --- | --- | --- |
| Transcript import | `Done` | `TranscriptSegment[]` | `vbook_audio` | [transcript-import.md](./transcript-import.md) |
| Frame extraction | `Done` | `FrameCandidate[]` | `vbook_vision` | [frame-extraction.md](./frame-extraction.md) |
| Frame selection | `Partial` | selected/rejected frames | `vbook_vision` | [frame-selection.md](./frame-selection.md) |
| Vision analysis | `Partial` | `vision/analysis.json` | `vbook_vision` | [vision-analysis.md](./vision-analysis.md) |
| Timeline alignment | `Done` | `TimelineLink[]` | `vbook_pipeline` | [timeline-alignment.md](./timeline-alignment.md) |
| Fusion prompt | `Partial` | `fusion/prompt.json` | `vbook_fusion` | [fusion-prompt.md](./fusion-prompt.md) |
| Fusion sections | `Partial` | `fusion/sections.json` | `vbook_fusion` | [fusion-sections.md](./fusion-sections.md) |
| Note export | `Partial` | `note.md` | `vbook_export` | [note-export.md](./note-export.md) |
| Manifest | `Done` | `manifest.json` | `vbook_export` | [manifest.md](./manifest.md) |

## 当前能力边界

- Local MVP pipeline 已经能生成 `manifest.json`、`note.md`、`vision/analysis.json`、`fusion/prompt.json` 和 `fusion/sections.json`。
- 视觉分析仍是 `placeholder`、`manual-json`、`external-command`、`tools/vision_stub.py` 或 `tools/vision_qwen_adapter.py` 边界；vBook core 不内置 OCR 或多模态模型。
- LLM fusion 只通过显式 `--llm-fusion-command` 调用外部命令；vBook core 不内置模型 provider。
- Batch workflow 是 per-lesson pipeline 的薄编排；当前不支持并发、manifest-based resume 或自动只重跑失败项。
- `vbook_server` 仍是未来边界，没有服务运行时。

## 状态标签

| Status | 含义 |
| --- | --- |
| `Done` | 当前可作为项目基础使用，并已有验证。 |
| `Partial` | 已有可运行基础，但不是最终形态。 |
| `Blocked` | 被外部服务、数据或决策阻塞。 |
| `Planned` | 已纳入方向，但当前不是运行能力。 |

## 相关文档

- [../00_project/task-board.md](../00_project/task-board.md)
- [../00_project/status.md](../00_project/status.md)
- [../20_architecture/data-model.md](../20_architecture/data-model.md)
- [../20_architecture/module-boundaries.md](../20_architecture/module-boundaries.md)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
- [../60_operations/smoke-tests.md](../60_operations/smoke-tests.md)
- [../60_operations/qwen-vision-integration.md](../60_operations/qwen-vision-integration.md)
- [../60_operations/batch-processing.md](../60_operations/batch-processing.md)
