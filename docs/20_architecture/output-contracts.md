# vBook 输出行为

## 默认输出目录

默认情况下，vBook 应将每节课的输出写入独立目录：

```text
outputs/<lesson_id>/
```

输出位置应可通过 CLI 参数和 TOML 配置覆盖。

## 规划目录结构

```text
outputs/<lesson_id>/
|-- note.md
|-- manifest.json
|-- transcript/
|   |-- raw.json
|   |-- raw.txt
|   +-- clean.md
|-- frames/
|   |-- candidates/
|   +-- selected/
|-- vision/
|   +-- analysis.json
|-- fusion/
|   |-- prompt.json
|   +-- sections.json
+-- assets/
    +-- images/
```

## 双核心输出

MVP 输出以 `note.md` 和 `manifest.json` 为双核心。`note.md` 面向人阅读，`manifest.json` 面向复跑、审计和后续知识库。

## Markdown 笔记

`note.md` 是面向用户阅读的最终产物。section-based note 使用第一版专家笔记结构：
`课程信息`、`课程总览`、`核心结论` 和 `知识结构`。每个知识段落保留讲解摘要、关键要点、来源时间戳、图片引用和 tags，确保用户阅读时仍可回看证据。

## Manifest

`manifest.json` 是机器可读的运行索引。它应记录源文件、transcript 来源、配置、阶段状态、关键产物路径、视觉后端、OCR 后端和可复跑信息。

## Transcript 输出

转写目录保存导入或生成的 transcript。MVP 标准路径是导入已有带时间戳 transcript；如果通过外部 `vtext` CLI 生成，manifest 应记录该来源为 external command。

## Frame 输出

`frames/candidates/` 保存抽样得到的候选帧。`frames/selected/` 保存最终进入视觉分析和笔记引用的图片。

## Vision 输出

`vision/analysis.json` 保存统一后的 OCR 和多模态图像理解结果。该文件应区分 `slide`、`kline_case` 和 `other`，并足以支持重新执行时间轴对齐和知识融合，而无需重复视觉分析。

## Fusion 输出

融合产物应保留 prompt 输入和生成的知识段落，方便审计和优化 LLM 行为。

## Git 排除规则

课程视频、生成帧、转写文本、模型文件和输出目录不得进入 Git 历史。仓库只跟踪源码、文档、协议和小型测试 fixture。
