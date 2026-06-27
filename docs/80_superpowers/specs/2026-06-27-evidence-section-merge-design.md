# Evidence Section Merge Design

## 背景

vBook 当前已经完成 deterministic evidence draft：`build_evidence_sections()`
能把 transcript、视觉分析、OCR、图像描述、结构化观察和时间线关联转换为
`KnowledgeSection[]`，并导出到 `fusion/sections.json` 和 `note.md`。

当前剩余的主要问题是章节粒度仍然偏碎：每个 `TranscriptSegment` 默认生成一个
`KnowledgeSection`。这对审计和调试有利，但用户阅读 `note.md` 时会看到很多短小
片段，尤其是字幕输入较细时，笔记会更像流水账而不是课程章节。

本阶段目标是在不等待真实 Qwen 服务、不调用 LLM、不改变 Qwen adapter 的前提下，
给 evidence sections 增加保守的相邻段落合并规则，让输出更接近可读课程笔记。

## 目标

- 保持 pipeline 本地可运行，不新增外部服务依赖。
- 保持 `KnowledgeSection` dataclass 不变。
- 保持 `build_placeholder_sections()` 旧语义不变。
- 让 `build_evidence_sections()` 输出更少、更有章节感的 sections。
- 合并后仍保留来源时间范围、图片引用、OCR、视觉描述、key points 和 tags。
- 合并规则必须 deterministic、可测试、可解释。
- 避免过度合并导致不同主题混在同一个 section。

## 非目标

本阶段不做：

- 不调用 Qwen 服务。
- 不调用 OpenAI 或任何 LLM。
- 不设计最终专家笔记文风。
- 不做语义向量相似度。
- 不改变 transcript、visual analysis 或 timeline link 数据契约。
- 不新增用户可配置 CLI 参数。
- 不改变 `fusion/sections.json` schema。

## 方案选择

### 方案 A：仍保持一段 transcript 一个 section

优点：

- 最简单。
- 当前行为稳定。

缺点：

- `note.md` 章节会持续偏碎。
- 真实 Qwen 上线后，视觉证据变丰富，但笔记仍可能不好读。

### 方案 B：在 evidence builder 内部做保守相邻合并

优点：

- 不改变 public API。
- 不改变 artifact schema。
- 直接改善当前 `note.md` 可读性。
- 可以通过 deterministic fixtures 做完整回归。
- 后续 LLM fusion 可以在更稳定的 section 粒度上工作。

缺点：

- 需要清晰定义合并边界，避免误合并。
- 需要重构 `vbook_fusion.sections` 的部分 helper。

### 方案 C：新增独立 section merge stage

优点：

- 阶段边界最清晰。
- 未来可以单独配置和审计。

缺点：

- 当前项目还处于轻量 MVP，新增 stage 会扩大 CLI、manifest 和文档改动面。
- 对这一阶段目标来说偏重。

## 决策

采用方案 B：在 `build_evidence_sections()` 内部做保守相邻合并。

原因：

- 与真实 Qwen 服务部署完全解耦。
- 不改变现有 public data model。
- 改动范围集中在 `vbook_fusion.sections` 和相关测试。
- 用户立刻能在 `note.md` 里看到更少、更连贯的章节。

## 术语

### Evidence segment

由一个 `TranscriptSegment` 和它通过 `TimelineLink` 关联到的
`VisualAnalysis[]` 组成的内部中间对象。它不是新的 public dataclass。

### Evidence section group

一个或多个相邻 evidence segments 的内部组合。最终每个 group 会生成一个
`KnowledgeSection`。

### Semantic heading

从视觉结构化观察中提取的章节语义标题，按优先级读取：

1. `topic`
2. `title`
3. `heading`

这些字段只在值为非空 string 时生效。

## 合并规则

合并只发生在时间排序后的相邻 segments 之间。规则按保守优先级判断。

### 必须分开

以下情况不合并：

- 两边都有非空 semantic heading，但 heading 不同。
- 两边都有视觉证据，但没有共享 frame，且 semantic heading 不同或缺失。
- 相邻时间间隔超过合并阈值。
- 合并后 transcript 文本过长，超过本阶段固定上限。

### 可以合并

以下情况可以合并：

1. **共享 frame**
   - 相邻 segments 关联到同一个 `frame_id`。
   - 这通常说明同一张图对应连续讲解。

2. **相同 semantic heading**
   - 相邻 segments 的视觉证据提取到相同 `topic/title/heading`。
   - 用于合并同一幻灯片主题下的连续字幕。

3. **短间隔纯 transcript**
   - 两边都没有视觉证据。
   - 时间间隔很短。
   - 合并后 transcript 总长度不超过固定上限。
   - 用于把字幕切分造成的碎片合成较自然的小段。

4. **短间隔视觉后续讲解**
   - 前一组有视觉证据，后一段没有视觉证据。
   - 后一段与前一组时间间隔很短。
   - 合并后 transcript 总长度不超过固定上限。
   - 用于吸收紧跟在图片后的补充讲解。

### 阈值

本阶段先使用模块内固定常量，不暴露 CLI 配置：

- `MAX_TOPIC_MERGE_GAP_SECONDS = 30.0`
- `MAX_SHARED_FRAME_MERGE_GAP_SECONDS = 30.0`
- `MAX_SHORT_TEXT_MERGE_GAP_SECONDS = 1.0`
- `MAX_MERGED_TRANSCRIPT_CHARS = 240`

这些值的定位是“保守可读默认值”，不是最终产品配置。

## 输出规则

每个 evidence section group 生成一个 `KnowledgeSection`。

### title

优先级：

1. group 内第一个非空 semantic heading。
2. group 内第一个非空 transcript 文本的前 18 个可读字符。
3. `Segment <id>`，使用 group 第一个 segment id。

### summary

- transcript 文本按时间顺序合并成一条 `讲解：...`。
- group 内视觉描述按出现顺序追加 `视觉：...`。
- group 内 OCR 文本取每条 OCR 的第一行，追加 `画面文字：...`。
- 所有条目稳定去重。

### source_timestamps

- `[group_start, group_end]`
- `group_start` 使用第一个 segment 的 `start`。
- `group_end` 使用最后一个 segment 的 `end`。

### image_refs

- 来自 group 内所有视觉证据的 `image_path`。
- 转为 POSIX path string。
- 稳定去重。

### key_points

- 每个非空 transcript segment 保留一条 `讲解：...`。
- 每条 OCR 文本保留一条 `画面文字：...`。
- 每条视觉描述保留一条 `视觉描述：...`。
- `structured_observations.topic` 输出为 `主题：...`。
- `structured_observations.key_points` 中的 string 直接加入。
- `structured_observations.visible_elements` 输出为 `可见元素：a、b、c`。
- 稳定去重，丢弃空字符串。

### tags

- 固定包含 `evidence`。
- 按视觉类型加入 `visual:<value>`。
- 有 OCR 时加入 `has_ocr`。
- 有图片证据时加入 `has_image`。
- 有语言字段时加入 `lang:<value>`。
- 本阶段不新增 `merged` tag，避免把内部构造策略暴露给用户输出。

## 模块边界

`vbook_fusion.sections`：

- 建立 segment 到 visual evidence 的索引。
- 把单个 transcript segment 转为内部 evidence segment。
- 执行相邻合并。
- 把 evidence section group 转为 `KnowledgeSection`。
- 写 `fusion/sections.json`。

`vbook_client.cli`：

- 不需要改动。继续调用 `build_evidence_sections()`。

`vbook_export.note`：

- 不需要改动。它只负责渲染 `KnowledgeSection[]`。

`tools/vision_qwen_adapter.py`：

- 不改动。

## 与 Qwen 服务的关系

本阶段不依赖真实 Qwen 服务。

真实 Qwen 服务上线后，它会让 `VisualAnalysis` 中的 OCR、视觉描述和结构化观察更真实。
section merge 会自然利用这些字段产生更合理的章节分组，但不需要改 adapter。

## 测试策略

使用 `unittest` 和 deterministic fixtures。

新增或调整测试：

- 同一 frame 关联多个相邻 transcript segments 时合并为一个 section。
- 相同 `topic/title/heading` 的相邻 visual evidence 合并。
- 不同 semantic heading 的相邻 visual evidence 不合并。
- 短间隔纯 transcript segments 合并。
- 超过短间隔阈值的纯 transcript segments 不合并。
- 合并后 `source_timestamps`、`summary`、`image_refs`、`key_points`、`tags`
  均稳定去重并保持顺序。
- 既有 placeholder builder 测试保持不变。
- CLI 默认输出仍是 `fusion_sections_evidence`。

最终验证：

```powershell
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

## 验收口径

完成后应满足：

- 不部署 Qwen 服务时，默认 `build` 仍可运行。
- `build_evidence_sections()` 输出的 section 数量在相邻证据连续时减少。
- 不同主题或明显间隔的内容不会被误合并。
- `fusion/sections.json` 仍写出 `intent = fusion_sections_evidence`。
- `note.md` 不需要改渲染逻辑即可展示合并后的更连贯章节。
- 全量测试通过。

## 风险与控制

- 风险：过度合并导致不同主题混在一起。
  - 控制：不同 semantic heading 必须分开，长间隔必须分开。
- 风险：纯 transcript 合并过长。
  - 控制：使用 `MAX_MERGED_TRANSCRIPT_CHARS` 上限。
- 风险：后续需要用户配置阈值。
  - 控制：本阶段先用模块常量，等真实样本积累后再决定是否公开配置。
- 风险：合并逻辑让 helper 变复杂。
  - 控制：拆成 evidence segment、group、merge predicate、group rendering
    这几个小 helper，并用测试覆盖每类行为。
