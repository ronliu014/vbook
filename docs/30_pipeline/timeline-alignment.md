# Timeline Alignment

## 阶段目标

按时间窗口把视觉分析结果绑定到附近的 transcript segments，生成可审计的 `TimelineLink[]`。

## 当前状态

Status: `Done`

当前策略是 timestamp window。它能稳定支持本地 MVP，但还不是语义相似度匹配。

## 输入

- `VisualAnalysis[]`
- `TranscriptSegment[]`
- CLI `--alignment-window-seconds`

## 输出

- `TimelineLink[]`
- Link fields: `frame_id`, `transcript_segment_ids`, `window_start`, `window_end`, `match_strategy`

## 关键代码

- `vbook_pipeline/timeline.py::link_frames_to_transcript`
- `vbook_common/types.py::TimelineLink`

## CLI 与配置入口

- `python -m vbook_client build --alignment-window-seconds <seconds>`
- `python -m vbook_client build-batch --alignment-window-seconds <seconds>`

## 产物路径

当前 timeline alignment 没有独立默认 JSON 文件。链接结果进入 fusion prompt、fusion sections、note 和 manifest 相关 artifact summary。

## 失败边界

- Transcript segments 为空时无法形成有文本上下文的 link。
- Visual analysis 为空时没有 frame 可对齐。
- 时间窗口过小会减少可匹配 transcript segments。
- 时间窗口过大会引入更宽泛的上下文。

## 验收与测试

```powershell
python -m unittest tests.test_pipeline.test_timeline
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- 当前不做语义相似度匹配。
- 当前不使用 OCR 文本和 transcript 文本做语义重排。
- 当前没有单独持久化 `timeline/links.json`。

## 后续任务

- 在真实样例可用后评估默认窗口大小。
- 根据视觉和 transcript 质量决定是否增加语义匹配或独立 timeline artifact。

## 相关文档

- [vision-analysis.md](./vision-analysis.md)
- [fusion-prompt.md](./fusion-prompt.md)
- [fusion-sections.md](./fusion-sections.md)
