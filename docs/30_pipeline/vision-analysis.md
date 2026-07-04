# Vision Analysis

## 阶段目标

把 selected frames 转换为统一的 `VisualAnalysis[]`，为时间轴对齐和知识融合提供 OCR 文本、视觉描述、结构化观察、后端信息和置信度。

## 当前状态

Status: `Partial`

当前支持 `placeholder`、`manual-json` 和 `external-command` 后端。`tools/vision_stub.py` 用于本地 deterministic smoke；`tools/vision_qwen_adapter.py` 用于通过 `external-command` 调用兼容 Qwen Vision Service 的 HTTP 服务。

## 输入

- Selected `FrameCandidate[]`
- CLI `--vision-backend`
- CLI `--manual-vision-json`
- CLI `--vision-command`
- CLI `--vision-output-path`

## 输出

- `VisualAnalysis[]`
- `vision/analysis.json`
- 使用 `external-command` 时的 `vision/external/analysis.json`

## 关键代码

- `vbook_vision/analysis.py::analyze_frames`
- `vbook_vision/analysis.py::analyze_frames_placeholder`
- `vbook_vision/analysis.py::load_manual_visual_analysis`
- `vbook_vision/analysis.py::run_external_vision_command`
- `vbook_vision/analysis.py::write_visual_analysis`
- `vbook_common/types.py::VisualAnalysis`
- `vbook_common/types.py::VisualType`
- `tools/vision_stub.py`
- `tools/vision_qwen_adapter.py`

## CLI 与配置入口

- `python -m vbook_client build --vision-backend placeholder`
- `python -m vbook_client build --vision-backend manual-json --manual-vision-json <path>`
- `python -m vbook_client build --vision-backend external-command --vision-command "<command with input and output slots>"`

`build-batch` 当前不透传 batch-level Qwen adapter 参数。

## 产物路径

- `outputs/<lesson_id>/vision/analysis.json`
- `outputs/<lesson_id>/vision/external/analysis.json`
- `outputs/<lesson_id>/manifest.json` 中的 `artifacts.vision`

## 失败边界

- `external-command` backend 缺少 `vision_command` 时 CLI 直接报错。
- `manual-json` 输入不符合 visual analysis schema 时加载失败。
- 外部命令非零退出时 build 失败。
- Qwen 服务未部署或 endpoint 不可达时，adapter 路径无法完成真实联调。

## 验收与测试

```powershell
python -m unittest tests.test_vision.test_analysis
python -m unittest tests.test_tools.test_vision_stub
python -m unittest tests.test_tools.test_vision_qwen_adapter
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- vBook core 不内置 OCR。
- vBook core 不内置多模态模型。
- `placeholder` 只保证 pipeline shape，不代表真实视觉理解质量。
- Qwen Vision Service 真实质量需要服务 ready 后按 runbook 验证。

## 后续任务

- Qwen Vision Service ready 后执行真实 `/health` 和 `/analyze-frame` smoke。
- 根据真实输出调整 adapter 或需求文档。
- 引入真实课程样例后抽查 `visual_type`、`ocr_text` 和 `structured_observations` 的可用性。

## 相关文档

- [frame-selection.md](./frame-selection.md)
- [timeline-alignment.md](./timeline-alignment.md)
- [../60_operations/qwen-vision-integration.md](../60_operations/qwen-vision-integration.md)
- [../90_reference/qwen-vision-service-requirements.md](../90_reference/qwen-vision-service-requirements.md)
