# Pipeline Stage Documents Design

## 背景

vBook 目前处于 local MVP pipeline 阶段，已经可以从视频和时间戳 transcript 生成
`manifest.json`、`note.md`、`vision/analysis.json`、`fusion/prompt.json`、
`fusion/sections.json`，并且具备 external-command 形式的视觉分析和 LLM fusion 接口边界。

当前文档分层已经建立：

- `docs/00_project/` 说明项目状态、术语、任务看板和路线图。
- `docs/20_architecture/` 说明架构、数据模型、模块边界和输出 contract。
- `docs/30_pipeline/` 用于说明每个处理阶段。
- `docs/60_operations/` 说明本地 smoke、Qwen 联调和 batch 操作。
- `docs/80_superpowers/` 保存设计、计划和执行交接。

`docs/30_pipeline/` 目前只有 `README.md` 和 `overview.md`。它能说明端到端数据流，但还不能让
操作者或后续开发者快速回答每个阶段的关键问题：这一阶段吃什么、吐什么、由哪个模块负责、
当前能力到什么程度、失败边界在哪里、如何验收、真实 Qwen 或 LLM 服务 ready 后应该改哪里。

用户已经确认采用方案 A：每个 pipeline stage 单独成页，`README.md` 做总入口矩阵。

## 目标

- 补齐 `docs/30_pipeline/` 的阶段文档基础版。
- 让每个核心阶段拥有独立页面，固定说明输入、输出、状态、代码入口、CLI 入口、产物路径、
  失败边界、测试入口、当前限制和后续任务。
- 让 `docs/30_pipeline/README.md` 成为可扫描的阶段矩阵和阅读入口。
- 如实记录当前 local MVP 能力，不把 placeholder、stub、manual-json 或 external-command
  说成真实模型能力。
- 明确 Qwen Vision Service 和真实 LLM/Qwen 文本综合服务仍属于外部部署条件，不在本阶段触发调用。
- 同步更新 `docs/00_project/task-board.md` 和 `docs/00_project/status.md`，让项目状态反映
  pipeline stage documents 已补齐。

## 非目标

本阶段不做：

- 不修改 Python 运行逻辑。
- 不新增 CLI 参数。
- 不改变 `manifest.json`、`note.md`、`vision/analysis.json`、`fusion/*.json` 的 schema。
- 不调用真实 Qwen Vision Service。
- 不调用真实 LLM/Qwen 文本综合服务。
- 不新增长期保留的大视频 fixture。
- 不把未来 `vbook_server` 服务化设计写成当前能力。
- 不把 `.vtt`、`.txt` 说成当前稳定推荐 transcript 输入。
- 不移动既有文档目录结构。

## 方案选择

### 方案 A：阶段页 + README 矩阵

在 `docs/30_pipeline/` 下为核心阶段创建独立文档，并更新 README 为阶段入口矩阵。

优点：

- 每个阶段的边界清楚，后续联调和排障可以直接链接到对应页面。
- 文档颗粒度适合持续维护，不会把所有细节堆进一个巨大 overview。
- 与现有文档分层一致。
- 用户可以快速了解项目进度和每个阶段的真实能力。

缺点：

- 一次性新增的文档数量较多，需要统一模板避免风格发散。

### 方案 B：继续扩写 `overview.md`

把所有阶段说明追加到现有 `docs/30_pipeline/overview.md`。

优点：

- 改动文件少。

缺点：

- 随着视觉、LLM、batch、server 继续演进，overview 会变得难以维护。
- 操作者想查某个阶段时需要在长文档中搜索。
- 不利于在 task board、runbook 和需求文档中做精准引用。

### 方案 C：只写状态矩阵

只在 README 中补一个阶段状态表，不写独立阶段页。

优点：

- 最省时间。

缺点：

- 只能回答“现在做到哪里”，不能回答“如何验收、失败在哪里、要改哪段代码”。
- 对真实 Qwen/LLM 联调帮助不足。

## 决策

采用方案 A。

原因：

- 当前最重要的缺口是阶段边界和项目进度表达，而不是 runtime 能力。
- 用户明确提出需要术语和阶段任务梳理，阶段页能把项目状态从“整体描述”拆成可检查单元。
- Qwen 服务仍未部署完成，等待期间补齐阶段文档不会与后续真实服务联调冲突。

## 文档范围

### 更新

```text
docs/30_pipeline/README.md
docs/30_pipeline/overview.md
docs/00_project/task-board.md
docs/00_project/status.md
```

### 新增

```text
docs/30_pipeline/transcript-import.md
docs/30_pipeline/frame-extraction.md
docs/30_pipeline/frame-selection.md
docs/30_pipeline/vision-analysis.md
docs/30_pipeline/timeline-alignment.md
docs/30_pipeline/fusion-prompt.md
docs/30_pipeline/fusion-sections.md
docs/30_pipeline/note-export.md
docs/30_pipeline/manifest.md
```

## 阶段页统一结构

每个阶段页使用同一组标题，方便横向比较：

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

### 阶段目标

说明这个阶段在整条 pipeline 中解决什么问题。语言要面向操作者和后续开发者，不写成内部实现注释。

### 当前状态

使用项目看板中的状态标签：

| Status | 含义 |
| --- | --- |
| `Done` | 当前可作为项目基础使用，并已有验证。 |
| `Partial` | 已有可运行基础，但不是最终形态。 |
| `Blocked` | 被外部服务、数据或决策阻塞。 |
| `Planned` | 已纳入方向，但当前不是运行能力。 |

阶段页可以补充更细的文字说明，但状态词必须与 task board 保持一致。

### 输入

列出当前代码实际消费的数据类型、文件路径或 dataclass，例如：

- `VideoAsset`
- `TranscriptSegment[]`
- `FrameCandidate[]`
- `VisualAnalysis[]`
- `TimelineLink[]`
- `KnowledgeSection[]`

如果输入来自 CLI 参数，也要列出参数名。

### 输出

列出当前实际产出的 dataclass、JSON 或 Markdown 文件。输出必须能在代码、测试或架构文档中找到来源。

### 关键代码

列出负责该阶段的包、模块和主要函数。只列当前真实存在的代码路径，例如：

- `vbook_audio/transcript.py::load_transcript`
- `vbook_vision/frames.py::extract_frame_candidates`
- `vbook_vision/analysis.py::analyze_frames`
- `vbook_pipeline/timeline.py::link_frames_to_transcript`
- `vbook_fusion/sections.py::build_evidence_sections`
- `vbook_export/note.py::render_sections_note`
- `vbook_export/manifest.py::build_manifest`

### CLI 与配置入口

说明当前 CLI 如何触发该阶段：

- `python -m vbook_client manifest`
- `python -m vbook_client build`
- `python -m vbook_client build-batch`

只记录实际存在的参数。对于尚未透传到 batch 的参数，必须明确说明只属于 per-lesson `build`。

### 产物路径

记录默认输出位置，例如：

- `outputs/<lesson_id>/vision/analysis.json`
- `outputs/<lesson_id>/fusion/prompt.json`
- `outputs/<lesson_id>/fusion/sections.json`
- `outputs/<lesson_id>/fusion/llm_request.json`
- `outputs/<lesson_id>/fusion/llm_response.json`
- `outputs/<lesson_id>/fusion/llm_sections.json`
- `outputs/<lesson_id>/note.md`
- `outputs/<lesson_id>/manifest.json`

如果阶段当前没有独立持久化文件，也要说明它是内存中间结果，最终由 manifest 或下游 artifact 间接记录。

### 失败边界

记录当前常见失败类型和处理方向。示例：

- transcript 文件格式不受 `load_transcript()` 支持。
- ffmpeg 不可用或视频路径不可读。
- `external-command` backend 缺少 `vision_command`。
- manual-json 不符合 visual analysis schema。
- LLM fusion command 缺少 `{input}` 或 `{output}` 输入/输出插槽。
- LLM response 不符合 `parse_llm_fusion_response()` contract。

失败边界要以当前代码和测试为准，不引入未来异常体系。

### 验收与测试

列出与该阶段直接相关的测试文件和建议命令。例如：

```powershell
python -m unittest tests.test_audio.test_transcript
python -m unittest tests.test_vision.test_frames
python -m unittest tests.test_vision.test_analysis
python -m unittest tests.test_pipeline.test_timeline
python -m unittest tests.test_fusion.test_snapshot
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_export.test_note
python -m unittest tests.test_export.test_manifest
python -m unittest tests.test_client.test_manifest_cli
```

每页至少列出一个相关测试入口。端到端阶段可以列出 `tests.test_client.test_manifest_cli`。

### 当前限制

必须把限制写清楚，避免误解当前能力：

- 视觉智能仍依赖 placeholder、manual-json、external-command、stub 或外部 Qwen adapter。
- vBook core 不内置 OCR 或多模态模型。
- LLM fusion 只通过显式 external command 执行，vBook core 不内置模型 provider。
- deterministic evidence sections 不是最终高质量模型综合。
- batch 目前不支持并发、自动续跑或失败项自动重跑。
- server runtime 仍是未来边界。

### 后续任务

只写与该阶段直接相关的后续任务，避免跨阶段扩散。

## 阶段列表

### Transcript Import

文件：`docs/30_pipeline/transcript-import.md`

职责：

- 说明 timestamped JSON 和 SRT transcript 如何进入 vBook。
- 说明 `TranscriptSegment[]` 是内部统一表示。
- 说明 `.srt` 是当前稳定推荐格式。
- 说明 batch discovery 会匹配 `.vtt` 和 `.txt`，但当前 loader 不把它们作为稳定推荐输入。

当前状态：`Done`

关键代码：

- `vbook_audio/transcript.py`
- `vbook_common/types.py::TranscriptSegment`

测试入口：

- `python -m unittest tests.test_audio.test_transcript`
- `python -m unittest tests.test_client.test_manifest_cli`

### Frame Extraction

文件：`docs/30_pipeline/frame-extraction.md`

职责：

- 说明 ffmpeg-based 抽帧命令构造和候选帧发现。
- 说明 `FrameCandidate[]` 的字段和时间戳规则。
- 说明默认输出到 `frames/candidates/`。

当前状态：`Done`

关键代码：

- `vbook_vision/frames.py::build_ffmpeg_frame_command`
- `vbook_vision/frames.py::extract_frame_candidates`
- `vbook_vision/frames.py::discover_frame_candidates`

测试入口：

- `python -m unittest tests.test_vision.test_frames`
- `python -m unittest tests.test_client.test_manifest_cli`

### Frame Selection

文件：`docs/30_pipeline/frame-selection.md`

职责：

- 说明当前基础选择逻辑如何把候选帧标记为 selected 或 rejected。
- 说明 `FilterStatus` 和 `filter_reason`。
- 说明当前不是语义级 PPT/K 线筛选。

当前状态：`Partial`

关键代码：

- `vbook_vision/frames.py::select_frame_candidates`
- `vbook_common/types.py::FilterStatus`

测试入口：

- `python -m unittest tests.test_vision.test_frames`

### Vision Analysis

文件：`docs/30_pipeline/vision-analysis.md`

职责：

- 说明 `placeholder`、`manual-json`、`external-command` 三种后端。
- 说明 `tools/vision_stub.py` 和 `tools/vision_qwen_adapter.py` 的边界。
- 说明统一输出是 `VisualAnalysis[]` 和 `vision/analysis.json`。
- 说明 Qwen 服务 ready 后按 `docs/60_operations/qwen-vision-integration.md` 联调。

当前状态：`Partial`

关键代码：

- `vbook_vision/analysis.py::analyze_frames`
- `vbook_vision/analysis.py::analyze_frames_placeholder`
- `vbook_vision/analysis.py::load_manual_visual_analysis`
- `vbook_vision/analysis.py::run_external_vision_command`
- `tools/vision_stub.py`
- `tools/vision_qwen_adapter.py`

测试入口：

- `python -m unittest tests.test_vision.test_analysis`
- `python -m unittest tests.test_tools.test_vision_stub`
- `python -m unittest tests.test_tools.test_vision_qwen_adapter`
- `python -m unittest tests.test_client.test_manifest_cli`

### Timeline Alignment

文件：`docs/30_pipeline/timeline-alignment.md`

职责：

- 说明按时间窗口把视觉分析结果绑定到 transcript segments。
- 说明 `TimelineLink[]` 的字段。
- 说明当前策略是 timestamp window，不是语义相似度匹配。

当前状态：`Done`

关键代码：

- `vbook_pipeline/timeline.py::link_frames_to_transcript`

测试入口：

- `python -m unittest tests.test_pipeline.test_timeline`

### Fusion Prompt

文件：`docs/30_pipeline/fusion-prompt.md`

职责：

- 说明 `fusion/prompt.json` 是当前 prompt snapshot 和审计 artifact。
- 说明它为后续 LLM 综合提供输入视图，但默认不触发模型调用。

当前状态：`Partial`

关键代码：

- `vbook_fusion/snapshot.py::build_fusion_prompt_snapshot`
- `vbook_fusion/snapshot.py::write_fusion_prompt_snapshot`

测试入口：

- `python -m unittest tests.test_fusion.test_snapshot`
- `python -m unittest tests.test_client.test_manifest_cli`

### Fusion Sections

文件：`docs/30_pipeline/fusion-sections.md`

职责：

- 说明 deterministic evidence sections 和 external-command LLM fusion 的关系。
- 说明 `fusion/sections.json`、`fusion/llm_request.json`、`fusion/llm_response.json`、
  `fusion/llm_sections.json`。
- 说明未提供 `--llm-fusion-command` 时默认使用 evidence draft。

当前状态：`Partial`

关键代码：

- `vbook_fusion/sections.py::build_evidence_sections`
- `vbook_fusion/sections.py::write_fusion_sections`
- `vbook_fusion/llm_contract.py::build_llm_fusion_request`
- `vbook_fusion/llm_contract.py::parse_llm_fusion_response`
- `vbook_fusion/llm_external.py::run_llm_fusion_command`
- `tools/llm_fusion_stub.py`
- `tools/check_llm_fusion_contract.py`

测试入口：

- `python -m unittest tests.test_fusion.test_sections`
- `python -m unittest tests.test_fusion.test_llm_contract`
- `python -m unittest tests.test_fusion.test_llm_external`
- `python -m unittest tests.test_tools.test_llm_fusion_stub`
- `python -m unittest tests.test_tools.test_check_llm_fusion_contract`

### Note Export

文件：`docs/30_pipeline/note-export.md`

职责：

- 说明 `note.md` 是面向用户阅读的核心输出。
- 说明增强专家笔记模板包含课程信息、课程总览、学习目标、核心结论、知识结构、回看索引、
  复习问题和标签索引。
- 说明 note 内容来自 transcript 或 `KnowledgeSection[]`，不伪造术语解释。

当前状态：`Partial`

关键代码：

- `vbook_export/note.py::render_placeholder_note`
- `vbook_export/note.py::render_sections_note`
- `vbook_export/note.py::write_note`

测试入口：

- `python -m unittest tests.test_export.test_note`
- `python -m unittest tests.test_client.test_manifest_cli`

### Manifest

文件：`docs/30_pipeline/manifest.md`

职责：

- 说明 `manifest.json` 是机器可读运行索引。
- 说明 `stage_status`、`artifacts`、`pipeline_run`、`transcript_source` 等关键字段。
- 说明 batch 的 `batch_manifest.json` 是批处理汇总，不替代每课的 `manifest.json`。

当前状态：`Done`

关键代码：

- `vbook_export/manifest.py::build_manifest`
- `vbook_export/manifest.py::write_manifest`
- `vbook_pipeline/batch.py::write_batch_manifest`

测试入口：

- `python -m unittest tests.test_export.test_manifest`
- `python -m unittest tests.test_pipeline.test_batch`
- `python -m unittest tests.test_client.test_manifest_cli`

## README 矩阵设计

`docs/30_pipeline/README.md` 应包含：

- 目录定位。
- 端到端阶段顺序。
- 阶段状态矩阵。
- 每个阶段文档链接。
- 当前最重要限制。
- 与架构、运营 runbook、项目看板的交叉链接。

建议矩阵字段：

| Stage | Status | Main artifact | Owner module | Stage doc |
| --- | --- | --- | --- | --- |
| Transcript import | `Done` | `TranscriptSegment[]` | `vbook_audio` | link |
| Frame extraction | `Done` | `FrameCandidate[]` | `vbook_vision` | link |
| Frame selection | `Partial` | selected/rejected frames | `vbook_vision` | link |
| Vision analysis | `Partial` | `vision/analysis.json` | `vbook_vision` | link |
| Timeline alignment | `Done` | `TimelineLink[]` | `vbook_pipeline` | link |
| Fusion prompt | `Partial` | `fusion/prompt.json` | `vbook_fusion` | link |
| Fusion sections | `Partial` | `fusion/sections.json` | `vbook_fusion` | link |
| Note export | `Partial` | `note.md` | `vbook_export` | link |
| Manifest | `Done` | `manifest.json` | `vbook_export` | link |

## Overview 更新

`docs/30_pipeline/overview.md` 保留端到端数据流说明，但不再承担每个阶段的完整细节。

更新方向：

- 保持现有中文说明。
- 在开头说明详细阶段 contract 已拆到独立 stage docs。
- 对每个阶段补充对应文档链接。
- 不重复长篇失败处理和测试清单。

## 项目状态同步

### `docs/00_project/task-board.md`

更新：

- 把 `扩展 pipeline stage documents` 从 `Ready` 改为 `Done`。
- 在 `Documentation foundation` 当前说明中加入 pipeline stage docs 已补齐。
- `最近完成` 增加 `Pipeline stage documents`。
- 下一步推荐切换到一个不依赖 Qwen 服务的任务，例如：
  - 梳理真实 smoke fixture 要求。
  - 设计 batch runtime 增强。
  - 继续完善真实服务联调检查清单。

推荐下一步应根据当时状态选择。如果 Qwen 服务仍未 ready，优先推荐 smoke fixture 要求或 batch
runtime 增强设计；如果服务组通知 ready，则推荐执行 Qwen Vision integration runbook。

### `docs/00_project/status.md`

更新：

- `What Works Now` 中补充 pipeline stage documents 已经覆盖关键阶段。
- `Most Important Next Work` 中把 `Expand pipeline-stage documents` 移出当前重点。
- 保留 Qwen Vision Service 和真实 LLM/Qwen 文本综合服务的 blocked/partial 表述。

## 文档语言与术语

- 文档主体使用简体中文。
- 代码路径、CLI 参数、JSON 字段、dataclass、模块名保留英文。
- 专有名词首次出现时可以用中英混合，例如 “视觉分析（Vision Analysis）”。
- 不把 `placeholder` 翻译成“真实分析”。
- 不把 `stub` 翻译成“服务”。
- 不把 `external-command` 描述成内置模型能力。

## 验证策略

本阶段是 docs-only，但仍按项目习惯执行验证：

```powershell
git diff --check
python -m unittest discover
```

追加文档内容检查：

```powershell
rg -n "Transcript import|Frame extraction|Vision analysis|Timeline alignment|Fusion sections|note.md|manifest.json" docs/30_pipeline
```

追加空洞内容检查：

```powershell
$emptyContentPattern = ('T' + 'BD') + '|' + ('TO' + 'DO') + '|待' + '定|' + ('占' + '位') + '|' + ('未' + '完成') + '|' + ('fill' + ' in details') + '|' + ('implement' + ' later')
rg -n $emptyContentPattern docs/30_pipeline
```

该命令应无匹配。

## 验收口径

本阶段完成后，应满足：

- `docs/30_pipeline/README.md` 提供阶段矩阵和所有阶段页入口。
- 九个阶段页存在，并且统一包含目标、状态、输入、输出、关键代码、CLI 入口、产物路径、
  失败边界、验收与测试、限制和后续任务。
- `docs/30_pipeline/overview.md` 保留端到端数据流，并链接到阶段页。
- 文档准确反映当前代码能力，不夸大真实 Qwen、OCR、LLM 或 server runtime。
- `docs/00_project/task-board.md` 和 `docs/00_project/status.md` 与阶段文档状态一致。
- `git diff --check` 通过。
- `python -m unittest discover` 通过。

## 后续工作

完成阶段文档后，可以继续推进：

- 真实 smoke fixture 要求说明，定义可长期保留或可外部挂载的 MP4 + transcript 验收样例。
- batch runtime 增强设计，例如显式透传视觉/LLM 参数、并发、失败项重跑和 resume。
- Qwen Vision Service ready 后执行真实联调 runbook。
- 真实 LLM/Qwen 文本综合服务 ready 后执行 fusion contract smoke。
