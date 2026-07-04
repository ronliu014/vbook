# Frame Extraction

## 阶段目标

从源视频按固定时间间隔抽取候选帧，生成带时间戳、图片路径和尺寸信息的 `FrameCandidate[]`。

## 当前状态

Status: `Done`

当前实现基于 ffmpeg 命令构造和候选帧发现。它是本地 MVP pipeline 的可运行基础。

## 输入

- `VideoAsset`
- CLI `--video`
- CLI `--frame-interval-seconds`
- 输出目录中的 `frames/candidates/`

## 输出

- `FrameCandidate[]`
- Candidate fields: `id`, `video_id`, `timestamp`, `image_path`, `width`, `height`, `filter_status`, `filter_reason`
- 候选帧图片文件

## 关键代码

- `vbook_vision/frames.py::build_ffmpeg_frame_command`
- `vbook_vision/frames.py::extract_frame_candidates`
- `vbook_vision/frames.py::discover_frame_candidates`
- `vbook_common/types.py::FrameCandidate`

## CLI 与配置入口

- `python -m vbook_client build --video <path> --frame-interval-seconds <seconds>`
- `python -m vbook_client build-batch --input <dir> --frame-interval-seconds <seconds>`

## 产物路径

- `outputs/<lesson_id>/frames/candidates/`
- `outputs/<lesson_id>/manifest.json` 中的 frame artifact summary

## 失败边界

- ffmpeg 不可用时无法抽帧。
- 视频路径不存在、不可读或格式不被 ffmpeg 支持时无法抽帧。
- `--frame-interval-seconds` 必须是正数。
- 候选帧目录为空时，下游视觉分析不会获得真实图片证据。

## 验收与测试

```powershell
python -m unittest tests.test_vision.test_frames
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- 当前抽帧按固定间隔运行，不做镜头切分。
- 当前不内置视频内容理解。
- 当前不把大视频 fixture 放入 Git。

## 后续任务

- 在真实课程样例可用后记录推荐抽帧间隔。
- 根据课程类型评估是否需要 scene detection 或 slide-change detection。

## 相关文档

- [frame-selection.md](./frame-selection.md)
- [vision-analysis.md](./vision-analysis.md)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
