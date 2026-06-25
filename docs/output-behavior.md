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

## Markdown 笔记

`note.md` 是面向用户阅读的最终产物。它应包含课程元数据、章节摘要、关键知识点、图片引用和来源时间戳。

## Manifest

`manifest.json` 是机器可读的运行索引。它应记录源文件、配置、阶段状态、关键产物路径和可复跑信息。

## Transcript 输出

转写目录同时保存原始 ASR 输出和清理后的文本。如果用户提供了已有转写，manifest 应记录该阶段为导入而非生成。

## Frame 输出

`frames/candidates/` 保存抽样得到的候选帧。`frames/selected/` 保存最终进入视觉分析和笔记引用的图片。

## Vision 输出

`vision/analysis.json` 保存统一后的 OCR 和图像理解结果。该文件应足以支持重新执行时间轴对齐和知识融合，而无需重复 OCR。

## Fusion 输出

融合产物应保留 prompt 输入和生成的知识段落，方便审计和优化 LLM 行为。

## Git 排除规则

课程视频、生成帧、转写文本、模型文件和输出目录不得进入 Git 历史。仓库只跟踪源码、文档、协议和小型测试 fixture。
