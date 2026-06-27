# vBook 术语库

本术语库定义 vBook 讨论、文档、代码评审和进度汇报中的共享词汇。
代码对象、API 名称、文件名和 backend 名称保留英文；解释和协作口径使用
简体中文。

## 状态术语

### 功能基础版（Functional foundation）

已经可运行、可测试、可接入 pipeline 的确定性实现。它能支撑集成和回归测试，
但不一定代表最终产品智能已经完成。

### 占位实现（Placeholder）

为了保持数据结构和 pipeline 流程完整而刻意写的简单实现。占位实现不是 bug，
但必须在文档、状态和输出中明确标注，避免被误解为最终能力。

### 部分完成（Partial）

某个阶段已经超过纯占位实现，但仍未完成最终目标。例如视觉分析已经支持
`manual-json`，但还没有真正调用 OCR 或多模态模型。

### 已完成（Done）

某个阶段在一次 pipeline 运行中成功执行，并产出了预期 artifact。在
`manifest.json` 中通常表现为 `"done"` 这类阶段状态。

### 已跳过（Skipped）

某个阶段没有被请求，或因为缺少前置输入而不能执行。在 `manifest.json` 中
通常表现为 `"skipped"`。

## 项目术语

### vBook

本仓库对应的项目。vBook 的目标是把视频课程自动分析成带图片理解的课程笔记，
并进一步形成可检索的知识库。

### vtext

相关参考项目，提供“视频 -> 音频 -> 文本 -> 知识”工作流方面的设计参考。
vBook 可以借鉴 vtext 的设计思路，但不能依赖、复制或 vendor vtext 代码。

### MVP

当前最小可用本地 pipeline：导入 transcript、抽帧、筛帧、产出视觉分析结果、
时间线对齐、融合 artifact、导出笔记，并生成 manifest。

## 输入术语

### Video

源课程视频文件，通常是 MP4。当前主要用于抽取 frames，未来也会作为音频转写的
来源。

### Transcript

带时间戳的课程文本。当前支持 JSON 和 SRT 输入格式，vBook 会将其规范化为
`TranscriptSegment[]`。

### TranscriptSegment

一段带时间戳 transcript 的标准数据对象，记录开始时间、结束时间、文本、来源和
可选 metadata。

## 视觉术语

### FrameCandidate

一个已抽取或已发现 frame 的标准数据对象，记录 frame id、video id、时间戳、
图片路径、尺寸和筛选状态。

### 候选帧（Candidate frame）

从视频中抽取出来，或从已有 frame 目录中发现，但尚未完成最终筛选的 frame。

### 入选帧（Selected frame）

被筛选保留下来的候选帧，会进入视觉分析、时间线对齐、融合和笔记导出等后续阶段。

### 剔除帧（Rejected frame）

被筛选排除的候选帧。剔除记录仍然有价值，用于审计筛选原因和复现 pipeline 行为。

### VisualAnalysis

视觉理解输出的标准数据对象，记录 frame id、visual type、图片路径、OCR 文本、
视觉描述、结构化观察结果、置信度和 backend 名称。

### VisualType

视觉分析记录的分类。当前取值包括 `slide`、`kline_case` 和 `other`。

### Vision backend

负责从 frames 生成 `VisualAnalysis[]` 的实现。当前 backend 包括 `placeholder`
和 `manual-json`。

### placeholder backend

默认的无外部服务 backend。它生成确定性的 `VisualAnalysis` 记录，让 pipeline
在没有 OCR 或模型服务时也能完整运行。

### manual-json backend

从外部准备或人工编写的 JSON 中读取视觉分析结果，并规范化为 `VisualAnalysis[]`
的 backend。

## Pipeline 术语

### Timeline alignment

将 frame 时间戳和附近 transcript segment 关联起来的阶段，输出
`TimelineLink[]`。

### Fusion prompt snapshot

一个 JSON artifact，记录后续知识融合会使用的 transcript、视觉分析和时间线对齐
上下文。

### Fusion sections

结构化的 `KnowledgeSection[]` 输出。当前实现是确定性的 evidence draft：
会吸收 transcript、OCR、视觉描述、结构化观察和图片引用，但还不是最终的
LLM 知识综合。

### Evidence draft

确定性的知识草稿。它把已有证据转换成可审计的章节、摘要、要点、图片引用和标签，
但不做模型改写，也不声称是最终专家级笔记。

### Section merge

把相邻 `TranscriptSegment` 对应的 evidence sections 保守合并为更少
`KnowledgeSection` 的规则。目标是减少字幕切分造成的碎片章节，同时保持来源时间和
图片证据可追溯。

### KnowledgeSection

一段笔记章节的标准数据对象，可包含标题、摘要、时间戳、图片引用、要点和标签。

## 输出术语

### note.md

vBook 导出的、给人阅读的 Markdown 笔记。

### manifest.json

机器可读的运行索引，记录输入、阶段状态、输出路径和 artifact 摘要。

### vision/analysis.json

规范化后的视觉分析 artifact。

### fusion/prompt.json

融合提示词快照 artifact。

### fusion/sections.json

结构化融合章节 artifact。
