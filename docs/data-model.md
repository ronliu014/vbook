# vBook 数据模型规划

## 设计原则

数据模型应描述业务产物，而不是某个具体库的内部实现。所有核心模型都应能序列化为 JSON，方便检查、缓存和复跑。

## VideoAsset

表示源课程视频。

- `id`
- `path`
- `course_title`
- `lesson_title`
- `duration_seconds`
- `metadata`

## AudioTrack

表示从视频中抽取的音频。

- `source_video_id`
- `path`
- `sample_rate`
- `channels`
- `duration_seconds`

## TranscriptSegment

表示带时间戳的讲解文本片段。

- `start`
- `end`
- `text`
- `language`
- `confidence`

## FrameCandidate

表示抽取出的候选视频帧。

- `id`
- `video_id`
- `timestamp`
- `image_path`
- `width`
- `height`
- `filter_status`
- `filter_reason`

## VisualAnalysis

表示 OCR 或图像理解后的统一结果。

- `frame_id`
- `visual_type`：`slide`、`kline_case`、`other`
- `ocr_text`
- `vision_description`
- `structured_observations`
- `confidence`
- `backend`

## VisualType

表示画面类型。MVP 只承诺稳定处理前两类：

- `slide`：PPT/幻灯片。
- `kline_case`：K 线或行情案例图。
- `other`：其他暂不进入核心 MVP 的画面。

## TimelineLink

表示图片与转写上下文之间的关系。

- `frame_id`
- `transcript_segment_ids`
- `window_start`
- `window_end`
- `match_strategy`

## KnowledgeSection

表示最终笔记中的一个融合知识段落。

- `title`
- `summary`
- `source_timestamps`
- `image_refs`
- `key_points`
- `tags`

## CourseNote

表示最终课程笔记。

- `video_id`
- `title`
- `sections`
- `assets`
- `manifest_path`

## Manifest

表示机器可读的运行索引，是 MVP 双核心输出之一。

- `video_asset`
- `transcript_source`
- `pipeline_run`
- `artifacts`
- `note_path`
- `stage_status`
- `schema_version`

## PipelineRun

表示一次可复现的流水线执行记录。

- `run_id`
- `started_at`
- `config`
- `stage_status`
- `input_hashes`
- `output_paths`

## 序列化要求

每个阶段都应写出稳定字段名的 JSON 记录。后续字段变更应在 manifest 中记录 schema 版本，保证旧产物仍可理解。
