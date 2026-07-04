# Manifest

## 阶段目标

写出机器可读的 `manifest.json`，记录一次 lesson pipeline 的输入、配置、阶段状态和关键产物路径，支撑复跑、审计和后续知识库接入。

## 当前状态

Status: `Done`

`manifest.json` 是 MVP 双核心输出之一。Batch 的 `batch_manifest.json` 是批处理汇总，不替代每节课自己的 `manifest.json`。

## 输入

- `VideoAsset`
- Transcript source
- `PipelineRun`
- Stage status
- Artifact paths
- `note.md` path

## 输出

- `Manifest`
- `manifest.json`
- Batch workflow 中的 `batch_manifest.json`

## 关键代码

- `vbook_export/manifest.py::build_manifest`
- `vbook_export/manifest.py::write_manifest`
- `vbook_common/types.py::Manifest`
- `vbook_common/types.py::PipelineRun`
- `vbook_common/types.py::StageStatus`
- `vbook_pipeline/batch.py::write_batch_manifest`

## CLI 与配置入口

- `python -m vbook_client manifest`
- `python -m vbook_client build`
- `python -m vbook_client build-batch`

## 产物路径

- `outputs/<lesson_id>/manifest.json`
- `outputs/<batch_run>/batch_manifest.json`

## 失败边界

- 上游阶段失败时，manifest 可能无法写出完整 artifact summary。
- Batch command 返回成功不代表每节课都成功，必须检查 `batch_manifest.json` 中的 `done_count`、`failed_count` 和 `skipped_count`。
- `batch_manifest.json` 不包含每节课所有 stage details；lesson 级细节仍以 per-lesson `manifest.json` 为准。

## 验收与测试

```powershell
python -m unittest tests.test_export.test_manifest
python -m unittest tests.test_pipeline.test_batch
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- 当前 schema version 是基础版本。
- 当前 batch manifest 不支持自动 resume。
- 当前不提供 manifest-driven rerun 命令。

## 后续任务

- 真实 batch 使用反馈稳定后再设计 manifest-based resume。
- 如后续 schema 扩展，必须保留旧产物可理解性。

## 相关文档

- [note-export.md](./note-export.md)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
- [../60_operations/batch-processing.md](../60_operations/batch-processing.md)
