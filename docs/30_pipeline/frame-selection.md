# Frame Selection

## 阶段目标

从候选帧中标记进入后续视觉分析的图片，并保留 rejected 记录，避免所有候选帧都进入下游。

## 当前状态

Status: `Partial`

当前已有基础选择逻辑和 `FilterStatus` 字段，但还不是语义级 PPT、K 线案例或低信息量画面的完整筛选系统。

## 输入

- `FrameCandidate[]`
- 抽帧阶段写出的候选图片

## 输出

- 标记为 `selected` 或 `rejected` 的 `FrameCandidate[]`
- `filter_status`
- `filter_reason`

## 关键代码

- `vbook_vision/frames.py::select_frame_candidates`
- `vbook_common/types.py::FilterStatus`
- `vbook_common/types.py::FrameCandidate`

## CLI 与配置入口

- `python -m vbook_client build`
- `python -m vbook_client build-batch`

当前没有独立的 frame selection CLI 命令。

## 产物路径

- `outputs/<lesson_id>/frames/selected/`
- `outputs/<lesson_id>/manifest.json` 中的 frame artifact summary

## 失败边界

- 输入候选帧为空时，选择结果为空。
- 图片文件缺失时，下游视觉分析可能无法读取对应图片。
- 当前筛选逻辑无法保证只保留高信息量画面。

## 验收与测试

```powershell
python -m unittest tests.test_vision.test_frames
```

## 当前限制

- 当前不是 OCR 文本密度筛选。
- 当前不是感知哈希去重系统。
- 当前不是 K 线案例专用筛选器。
- 当前 selection 结果仍需要下游视觉分析和人工抽查确认质量。

## 后续任务

- 引入真实样例后评估 duplicate frame、讲师画面、空白画面和低信息量画面的规则。
- 设计更可解释的 `filter_reason` 分类。

## 相关文档

- [frame-extraction.md](./frame-extraction.md)
- [vision-analysis.md](./vision-analysis.md)
- [../20_architecture/data-model.md](../20_architecture/data-model.md)
