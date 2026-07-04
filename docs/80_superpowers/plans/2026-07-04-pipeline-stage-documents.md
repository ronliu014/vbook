# Pipeline Stage Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first complete `docs/30_pipeline/` stage-document set so operators and developers can inspect each vBook pipeline stage by input, output, code owner, artifact, limits, and verification command.

**Architecture:** This is a docs-only change. `docs/30_pipeline/README.md` becomes the scan-friendly stage matrix, `docs/30_pipeline/overview.md` remains the end-to-end flow, and nine stage pages carry the detailed contracts. Project status files are updated only after stage pages exist.

**Tech Stack:** Markdown documentation, existing Python package/module names, existing `unittest` suite, PowerShell commands from the repository root.

---

## Source Spec

Use this approved design as the source of truth:

```text
docs/80_superpowers/specs/2026-07-04-pipeline-stage-documents-design.md
```

This implementation must not modify Python runtime code, CLI behavior, JSON schemas, or external service contracts.

## File Structure

Create or modify these files:

```text
docs/30_pipeline/README.md
docs/30_pipeline/overview.md
docs/30_pipeline/transcript-import.md
docs/30_pipeline/frame-extraction.md
docs/30_pipeline/frame-selection.md
docs/30_pipeline/vision-analysis.md
docs/30_pipeline/timeline-alignment.md
docs/30_pipeline/fusion-prompt.md
docs/30_pipeline/fusion-sections.md
docs/30_pipeline/note-export.md
docs/30_pipeline/manifest.md
docs/00_project/task-board.md
docs/00_project/status.md
```

Do not edit source code. Do not call Qwen Vision Service. Do not call a real LLM service.

## Common Stage Page Contract

Every new stage page must use these headings in this order:

```markdown
# <Stage Name>

## 阶段目标

## 当前状态

## 输入

## 输出

## 关键代码

## CLI 与配置入口

## 产物路径

## 失败边界

## 验收与测试

## 当前限制

## 后续任务

## 相关文档
```

Use Simplified Chinese for explanations. Keep code paths, CLI flags, JSON field names, dataclass names, and backend names in English.

Allowed status words in stage pages:

```text
Done
Partial
Blocked
Planned
```

Do not describe `placeholder`, `stub`, `manual-json`, or `external-command` as real model intelligence.

---

### Task 1: Pipeline Index And Overview

**Files:**
- Modify: `docs/30_pipeline/README.md`
- Modify: `docs/30_pipeline/overview.md`

- [ ] **Step 1: Inspect current pipeline docs**

Run:

```powershell
Get-Content -Raw docs/30_pipeline/README.md
Get-Content -Raw docs/30_pipeline/overview.md
```

Expected: README currently has a short stage table and planned stage document list; overview currently has the end-to-end Chinese pipeline flow.

- [ ] **Step 2: Replace `docs/30_pipeline/README.md` with the stage matrix**

Use `apply_patch` to replace the file with a concise index containing these sections and facts:

```markdown
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
```

- [ ] **Step 3: Update `docs/30_pipeline/overview.md` to link stage docs**

Use `apply_patch` to keep the existing end-to-end flow and add a short link after each stage heading. The file must retain this data-flow block:

```text
VideoAsset + TranscriptInput
  +-- TranscriptSegment[]
  +-- FrameCandidate[]
        +-- VisualAnalysis[]
              +-- TimelineLink[]
                    +-- KnowledgeSection[]
                          +-- CourseNote
```

Required overview facts:

- In the opening section, state that detailed stage contracts live in individual stage docs.
- Stage 2 links to `[transcript-import.md](./transcript-import.md)`.
- Stage 3 links to `[frame-extraction.md](./frame-extraction.md)`.
- Stage 4 links to `[frame-selection.md](./frame-selection.md)`.
- Stage 5 links to `[vision-analysis.md](./vision-analysis.md)`.
- Stage 6 links to `[timeline-alignment.md](./timeline-alignment.md)`.
- Stage 7 links to `[fusion-prompt.md](./fusion-prompt.md)` and `[fusion-sections.md](./fusion-sections.md)`.
- Stage 8 links to `[note-export.md](./note-export.md)` and `[manifest.md](./manifest.md)`.
- Preserve the statement that vBook does not import or depend on the vtext package.
- Preserve the statement that default output still uses deterministic evidence draft unless external LLM fusion is explicitly configured.

- [ ] **Step 4: Verify Task 1 links**

Run:

```powershell
rg -n "Stage Matrix|transcript-import.md|frame-extraction.md|vision-analysis.md|fusion-sections.md|manifest.md" docs/30_pipeline/README.md docs/30_pipeline/overview.md
```

Expected: matches in both files for stage links and matrix content.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add docs/30_pipeline/README.md docs/30_pipeline/overview.md
git commit -m "Document pipeline stage index"
```

Expected: commit succeeds with two modified docs.

---

### Task 2: Transcript And Frame Stage Pages

**Files:**
- Create: `docs/30_pipeline/transcript-import.md`
- Create: `docs/30_pipeline/frame-extraction.md`
- Create: `docs/30_pipeline/frame-selection.md`

- [ ] **Step 1: Create `docs/30_pipeline/transcript-import.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
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
```

- [ ] **Step 2: Create `docs/30_pipeline/frame-extraction.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
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
```

- [ ] **Step 3: Create `docs/30_pipeline/frame-selection.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
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
```

- [ ] **Step 4: Verify Task 2 content**

Run:

```powershell
rg -n "TranscriptSegment|FrameCandidate|FilterStatus|missing_transcript|unsupported_transcript_format|ffmpeg|frames/selected" docs/30_pipeline/transcript-import.md docs/30_pipeline/frame-extraction.md docs/30_pipeline/frame-selection.md
```

Expected: matches show the stage pages include the required data contracts, failures, and artifacts.

- [ ] **Step 5: Commit Task 2**

Run:

```powershell
git add docs/30_pipeline/transcript-import.md docs/30_pipeline/frame-extraction.md docs/30_pipeline/frame-selection.md
git commit -m "Document transcript and frame stages"
```

Expected: commit succeeds with three new docs.

---

### Task 3: Vision And Timeline Stage Pages

**Files:**
- Create: `docs/30_pipeline/vision-analysis.md`
- Create: `docs/30_pipeline/timeline-alignment.md`

- [ ] **Step 1: Create `docs/30_pipeline/vision-analysis.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
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
```

- [ ] **Step 2: Create `docs/30_pipeline/timeline-alignment.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
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
```

- [ ] **Step 3: Verify Task 3 content**

Run:

```powershell
rg -n "VisualAnalysis|VisualType|TimelineLink|external-command|vision/analysis.json|alignment-window-seconds|timestamp window" docs/30_pipeline/vision-analysis.md docs/30_pipeline/timeline-alignment.md
```

Expected: matches show backend boundaries, artifacts, and timestamp-window alignment.

- [ ] **Step 4: Commit Task 3**

Run:

```powershell
git add docs/30_pipeline/vision-analysis.md docs/30_pipeline/timeline-alignment.md
git commit -m "Document vision and timeline stages"
```

Expected: commit succeeds with two new docs.

---

### Task 4: Fusion And Export Stage Pages

**Files:**
- Create: `docs/30_pipeline/fusion-prompt.md`
- Create: `docs/30_pipeline/fusion-sections.md`
- Create: `docs/30_pipeline/note-export.md`
- Create: `docs/30_pipeline/manifest.md`

- [ ] **Step 1: Create `docs/30_pipeline/fusion-prompt.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
# Fusion Prompt

## 阶段目标

把 video、transcript、visual analysis 和 timeline links 打包成可审计的 prompt snapshot，为后续知识融合和 LLM contract 调试提供输入视图。

## 当前状态

Status: `Partial`

当前会写出 `fusion/prompt.json`。该 artifact 是审计输入，不代表已经调用真实模型。

## 输入

- `VideoAsset`
- `TranscriptSegment[]`
- `VisualAnalysis[]`
- `TimelineLink[]`

## 输出

- `fusion/prompt.json`
- Prompt snapshot JSON

## 关键代码

- `vbook_fusion/snapshot.py::build_fusion_prompt_snapshot`
- `vbook_fusion/snapshot.py::write_fusion_prompt_snapshot`

## CLI 与配置入口

- `python -m vbook_client build`
- `python -m vbook_client manifest --write-fusion-prompt`

## 产物路径

- `outputs/<lesson_id>/fusion/prompt.json`
- `outputs/<lesson_id>/manifest.json` 中的 `artifacts.fusion.prompt_path`

## 失败边界

- 上游 transcript、vision 或 timeline 数据为空时，prompt snapshot 内容也会变弱。
- 当前 prompt snapshot 不负责调用 LLM。
- 当前 prompt snapshot 不评价模型输出质量。

## 验收与测试

```powershell
python -m unittest tests.test_fusion.test_snapshot
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- Prompt snapshot 是本地 artifact，不是最终知识综合。
- 真实 LLM prompt engineering 仍需要基于服务联调结果迭代。

## 后续任务

- 真实 LLM/Qwen 文本综合服务 ready 后，对照 request/response contract 检查 prompt 信息是否足够。
- 根据真实课程输出优化 prompt fields。

## 相关文档

- [fusion-sections.md](./fusion-sections.md)
- [../90_reference/llm-fusion-command-requirements.md](../90_reference/llm-fusion-command-requirements.md)
```

- [ ] **Step 2: Create `docs/30_pipeline/fusion-sections.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
# Fusion Sections

## 阶段目标

把 transcript、视觉证据和 timeline links 转换为 `KnowledgeSection[]`，供 `note.md` 和后续知识库使用。

## 当前状态

Status: `Partial`

默认路径使用 deterministic evidence draft，并会保守合并相邻同主题或共享视觉证据的片段。显式提供 `--llm-fusion-command` 时，vBook 会执行 external-command LLM fusion contract。

## 输入

- `TranscriptSegment[]`
- `VisualAnalysis[]`
- `TimelineLink[]`
- CLI `--llm-fusion-command`
- CLI `--llm-fusion-request-path`
- CLI `--llm-fusion-response-path`
- CLI `--llm-fusion-sections-path`

## 输出

- `KnowledgeSection[]`
- `fusion/sections.json`
- `fusion/llm_request.json`
- `fusion/llm_response.json`
- `fusion/llm_sections.json`

## 关键代码

- `vbook_fusion/sections.py::build_evidence_sections`
- `vbook_fusion/sections.py::write_fusion_sections`
- `vbook_fusion/llm_contract.py::build_llm_fusion_request`
- `vbook_fusion/llm_contract.py::parse_llm_fusion_response`
- `vbook_fusion/llm_external.py::run_llm_fusion_command`
- `vbook_common/types.py::KnowledgeSection`
- `tools/llm_fusion_stub.py`
- `tools/check_llm_fusion_contract.py`

## CLI 与配置入口

- `python -m vbook_client build`
- `python -m vbook_client build --llm-fusion-command "<command with input and output slots>"`

`build-batch` 当前不透传 batch-level LLM fusion command 参数。

## 产物路径

- `outputs/<lesson_id>/fusion/sections.json`
- `outputs/<lesson_id>/fusion/llm_request.json`
- `outputs/<lesson_id>/fusion/llm_response.json`
- `outputs/<lesson_id>/fusion/llm_sections.json`
- `outputs/<lesson_id>/manifest.json` 中的 `artifacts.fusion`

## 失败边界

- `--llm-fusion-command` 缺少输入或输出插槽时 CLI 直接报错。
- 外部 LLM fusion command 非零退出时 build 失败。
- `llm_response.json` 不符合 parser contract 时 build 失败。
- 未提供 `--llm-fusion-command` 时不会调用真实模型，仍使用 deterministic evidence sections。

## 验收与测试

```powershell
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_fusion.test_llm_contract
python -m unittest tests.test_fusion.test_llm_external
python -m unittest tests.test_tools.test_llm_fusion_stub
python -m unittest tests.test_tools.test_check_llm_fusion_contract
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- deterministic evidence draft 不是最终高质量模型综合。
- vBook core 不内置 LLM SDK 或模型 provider。
- contract samples 只验证 shape 和 parser compatibility，不评价笔记质量。

## 后续任务

- 真实 LLM/Qwen 文本综合服务 ready 后执行 contract smoke。
- 根据真实输出决定是否扩展 response fields。
- 后续可设计 glossary、learning objectives 或 review questions 的模型字段。

## 相关文档

- [fusion-prompt.md](./fusion-prompt.md)
- [note-export.md](./note-export.md)
- [../90_reference/llm-fusion-command-requirements.md](../90_reference/llm-fusion-command-requirements.md)
- [../90_reference/llm-fusion-service-integration-request.md](../90_reference/llm-fusion-service-integration-request.md)
```

- [ ] **Step 3: Create `docs/30_pipeline/note-export.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
# Note Export

## 阶段目标

把 transcript 或 `KnowledgeSection[]` 渲染成面向用户阅读的 `note.md`，作为 vBook MVP 的核心输出之一。

## 当前状态

Status: `Partial`

当前 section-based note 已使用增强专家笔记模板，包含课程信息、课程总览、学习目标、核心结论、知识结构、回看索引、复习问题和标签索引。

## 输入

- `VideoAsset`
- `TranscriptSegment[]`
- `KnowledgeSection[]`

## 输出

- `note.md`

## 关键代码

- `vbook_export/note.py::render_placeholder_note`
- `vbook_export/note.py::render_sections_note`
- `vbook_export/note.py::write_note`

## CLI 与配置入口

- `python -m vbook_client manifest --write-note`
- `python -m vbook_client build`
- `python -m vbook_client build --llm-fusion-command "<command with input and output slots>"`
- `python -m vbook_client build-batch`

## 产物路径

- `outputs/<lesson_id>/note.md`
- `outputs/<lesson_id>/manifest.json` 中的 `note_path`

## 失败边界

- 上游 sections 为空时，section-based note 只能输出有限课程信息和总览。
- 当前不会生成真实术语解释，因为 `KnowledgeSection` 没有术语定义来源。
- 图片引用保持路径文本，不保证所有 Markdown renderer 都能直接显示本地图片。

## 验收与测试

```powershell
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- 当前只输出 Markdown。
- 当前没有 HTML、PDF、Obsidian 或知识库导出。
- 学习目标、复习问题和标签索引由现有 section 字段确定性派生，不是自由模型生成。

## 后续任务

- 接入真实术语库后再生成术语解释章节。
- 设计多格式导出前，先稳定 `CourseNote` 或等价中间模型。

## 相关文档

- [fusion-sections.md](./fusion-sections.md)
- [manifest.md](./manifest.md)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
```

- [ ] **Step 4: Create `docs/30_pipeline/manifest.md`**

Use `apply_patch` to add a stage page with the common headings and these facts:

```markdown
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
```

- [ ] **Step 5: Verify Task 4 content**

Run:

```powershell
rg -n "fusion/prompt.json|fusion/sections.json|llm_request.json|llm_response.json|llm_sections.json|KnowledgeSection|note.md|manifest.json|batch_manifest.json" docs/30_pipeline/fusion-prompt.md docs/30_pipeline/fusion-sections.md docs/30_pipeline/note-export.md docs/30_pipeline/manifest.md
```

Expected: matches show fusion, note, and manifest artifacts are documented.

- [ ] **Step 6: Commit Task 4**

Run:

```powershell
git add docs/30_pipeline/fusion-prompt.md docs/30_pipeline/fusion-sections.md docs/30_pipeline/note-export.md docs/30_pipeline/manifest.md
git commit -m "Document fusion and export stages"
```

Expected: commit succeeds with four new docs.

---

### Task 5: Project Status Synchronization

**Files:**
- Modify: `docs/00_project/task-board.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Inspect project status files**

Run:

```powershell
Get-Content -Raw docs/00_project/task-board.md
Get-Content -Raw docs/00_project/status.md
```

Expected: task board currently lists `扩展 pipeline stage documents` as `Ready`; status currently lists expanding pipeline-stage documents as important next work.

- [ ] **Step 2: Update `docs/00_project/task-board.md`**

Use `apply_patch` with these exact semantic changes:

- In `阶段总览`, update `Documentation foundation` current description to mention pipeline stage docs.
- In `等待 Qwen 服务期间可推进的任务`, change `扩展 pipeline stage documents` from `Ready` to `Done`, and set acceptance to say `docs/30_pipeline/` now has key stage input, output, status, test, and limit docs.
- In `最近完成`, add a `Pipeline stage documents` row that says `docs/30_pipeline/` now has README matrix, overview links, and stage pages.
- In `下一步推荐任务`, change recommendation away from pipeline docs. If Qwen service is still not confirmed ready, recommend `梳理真实 smoke fixture 要求`.
- Keep Qwen Vision Service and real LLM/Qwen text synthesis blockers in place.

Required wording for the new recommendation:

```markdown
推荐下一步：梳理真实 smoke fixture 要求。

理由：

- Qwen 服务尚未确认部署完成，真实视觉联调仍保持 blocked。
- pipeline stage documents 已补齐，阶段边界和验收入口更清楚。
- 下一步需要明确可长期复用或可外部挂载的 MP4 + transcript 样例要求，方便服务 ready 后执行稳定验收。
```

- [ ] **Step 3: Update `docs/00_project/status.md`**

Use `apply_patch` with these exact semantic changes:

- In `What Works Now`, add a bullet saying pipeline stage docs now cover transcript import, frame extraction, frame selection, vision analysis, timeline alignment, fusion prompt, fusion sections, note export, and manifest.
- In `Most Important Next Work`, remove pipeline-stage documents as an active next item.
- Add or keep these next items:
  1. Execute the Qwen Vision Service integration runbook once the service team confirms deployment readiness.
  2. Define the real smoke fixture requirements for MP4 plus transcript validation.
  3. Keep `manifest.json` and `note.md` as the primary output contract while intelligence improves behind the same artifacts.
- Keep the statement that local MVP works but intelligent visual understanding and final knowledge synthesis are not complete.

- [ ] **Step 4: Verify status synchronization**

Run:

```powershell
rg -n "Pipeline stage documents|扩展 pipeline stage documents|梳理真实 smoke fixture 要求|docs/30_pipeline|Most Important Next Work" docs/00_project/task-board.md docs/00_project/status.md
```

Expected: task board shows pipeline stage documents as completed and next work as real smoke fixture requirements.

- [ ] **Step 5: Commit Task 5**

Run:

```powershell
git add docs/00_project/task-board.md docs/00_project/status.md
git commit -m "Update project status after pipeline docs"
```

Expected: commit succeeds with two modified project docs.

---

### Task 6: Final Verification

**Files:**
- Verify all docs changed in Tasks 1-5.

- [ ] **Step 1: Verify required files exist**

Run:

```powershell
Get-ChildItem docs/30_pipeline | Sort-Object Name
```

Expected output includes:

```text
frame-extraction.md
frame-selection.md
fusion-prompt.md
fusion-sections.md
manifest.md
note-export.md
overview.md
README.md
timeline-alignment.md
transcript-import.md
vision-analysis.md
```

- [ ] **Step 2: Verify common headings exist in every stage page**

Run:

```powershell
rg -n "## 阶段目标|## 当前状态|## 输入|## 输出|## 关键代码|## CLI 与配置入口|## 产物路径|## 失败边界|## 验收与测试|## 当前限制|## 后续任务|## 相关文档" docs/30_pipeline/transcript-import.md docs/30_pipeline/frame-extraction.md docs/30_pipeline/frame-selection.md docs/30_pipeline/vision-analysis.md docs/30_pipeline/timeline-alignment.md docs/30_pipeline/fusion-prompt.md docs/30_pipeline/fusion-sections.md docs/30_pipeline/note-export.md docs/30_pipeline/manifest.md
```

Expected: each stage page has all common headings.

- [ ] **Step 3: Verify key stage terms**

Run:

```powershell
rg -n "Transcript import|Frame extraction|Vision analysis|Timeline alignment|Fusion sections|note.md|manifest.json" docs/30_pipeline
```

Expected: matches in README and relevant stage docs.

- [ ] **Step 4: Verify docs do not contain empty-content markers**

Run:

```powershell
$emptyContentPattern = ('T' + 'BD') + '|' + ('TO' + 'DO') + '|待' + '定|' + ('占' + '位') + '|' + ('未' + '完成') + '|' + ('fill' + ' in details') + '|' + ('implement' + ' later')
rg -n $emptyContentPattern docs/30_pipeline docs/00_project/task-board.md docs/00_project/status.md
```

Expected: exit code `1` with no matches.

- [ ] **Step 5: Verify whitespace**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 6: Run full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: all tests pass. At the time this plan was written, the suite had 129 tests.

- [ ] **Step 7: Inspect final branch state**

Run:

```powershell
git status --short --branch
git log --oneline -8
```

Expected: worktree clean, local `main` ahead of `origin/main` by the previously local commits plus the commits created by this plan.

## Self-Review Checklist

- Spec coverage: Tasks 1-5 cover README matrix, overview links, nine stage pages, task board sync, and status sync.
- Runtime scope: no task edits Python code or invokes a real Qwen/LLM service.
- Verification coverage: Task 6 checks required files, common headings, key terms, empty-content markers, whitespace, and the full unittest suite.
- Commit cadence: each logical docs batch has its own commit.
