# Expert Note Markdown Template Design

## 背景

vBook 现在已经能把视频、带时间戳 transcript、视觉分析、时间轴关联和融合结果导出为
`note.md` 与 `manifest.json`。在 LLM fusion external-command 完成后，`note.md` 可以
来自两种 section：

- 默认路径：deterministic evidence sections。
- 显式 `--llm-fusion-command` 路径：外部模型返回并通过 parser 校验后的 LLM sections。

当前 `render_sections_note()` 仍然是早期 artifact 展示模板。它按时间排序输出：

- 课程基础信息。
- `Knowledge Sections` 数量。
- 每个 section 的标题、summary、source、image、key points、tags。

这个结构可审计，但阅读体验偏工程化，不像最终用户期待的课程学习笔记。下一阶段应优先
优化 Markdown 模板，把已有 `KnowledgeSection[]` 更好地组织为专家讲义形态。

## 目标

- 提升 `note.md` 的默认阅读体验，让输出更像可复习课程笔记，而不是中间 artifact。
- 保持 `KnowledgeSection` dataclass、`fusion/sections.json`、`fusion/llm_sections.json`
  和 LLM response schema 不变。
- 继续保留来源时间戳、图片引用和 tags，确保每个重点可回溯。
- 同时兼容 deterministic evidence sections 和 LLM sections。
- 让输出在空 sections、缺少图片、缺少 key points、缺少 tags 时仍然自然。
- 用现有 `unittest` 覆盖模板结构和关键兼容行为。

## 非目标

本阶段不做：

- 不新增 `CourseNote` 中间模型。
- 不扩展 `KnowledgeSection` 字段。
- 不改变 LLM fusion request/response contract。
- 不改变 manifest schema。
- 不引入 Markdown 模板引擎依赖。
- 不生成复习题、术语表或学习目标等新内容，因为当前上游 schema 尚未提供这些字段。
- 不实现 HTML、PDF、Obsidian 或静态站点导出。
- 不改变 `render_placeholder_note()` 的旧 placeholder artifact 展示模板，除非测试需要共享小工具。

## 方案选择

### 方案 A：只优化 `render_sections_note()` 模板

在现有 `vbook_export.note` 内重写 sections note 的 Markdown 结构，不改变输入类型。

优点：

- 改动小，风险低。
- 不影响外部 LLM command 和已写好的需求文档。
- 默认 evidence draft 和 LLM sections 都能直接受益。
- 可以用现有测试快速约束输出结构。

缺点：

- 只能重新组织已有字段，不能凭空生成复习题、术语表或专家判断。

### 方案 B：扩展 LLM contract 的 expert note 字段

在 LLM response 中加入 `learning_objectives`、`core_takeaways`、`glossary`、
`review_questions` 等字段，并由 note renderer 使用。

优点：

- 笔记质量上限更高。

缺点：

- 会牵动 `llm_contract`、外部需求书、fake command 测试和兼容策略。
- 在真实 LLM command 尚未稳定前，过早扩大协议面。

### 方案 C：新增 `CourseNote` 中间模型

把 `KnowledgeSection[]` 转换为 `CourseNote`，再由 Markdown renderer 输出。

优点：

- 架构更清晰，适合未来知识库、HTML 和多格式导出。

缺点：

- 本阶段跨度偏大，需要同时设计新数据模型、转换器和 artifact。

## 决策

采用方案 A：只优化 `render_sections_note()` 的 Markdown 模板。

原因：

- 当前瓶颈是最终 Markdown 阅读层，而不是上游数据 contract。
- `KnowledgeSection[]` 已包含标题、摘要、要点、来源时间戳、图片引用和 tags，足够支撑
  第一版专家讲义模板。
- 先把输出体验做好，可以更快帮助用户判断真实视觉和 LLM 输出是否有价值。
- 后续如果需要方案 B 或 C，可以在模板稳定后再扩展数据模型。

## 新版 Markdown 结构

新版 `render_sections_note()` 输出结构：

```markdown
# <lesson_title_or_video_id>

## 课程信息

- 课程：<course_title_or_empty>
- 课节：<lesson_title_or_video_id>
- 视频：<video_path>
- 知识段落：<section_count>
- 时间范围：<first_source_time> - <last_source_time>

## 课程总览

本节共整理 <section_count> 个知识段落，覆盖 <time_range>。

## 核心结论

- <section 1 title>
- <section 2 title>
- ...

## 知识结构

### 1. <section title>

**讲解摘要**

<section.summary>

**关键要点**

- <point>

**证据与回看**

- 时间：<source time range>
- 图片：<image ref>

**元数据**

- 标签：tag1, tag2
```

如果 `sections` 为空：

```markdown
# <lesson_title_or_video_id>

## 课程信息

...

## 课程总览

当前没有可导出的知识段落。
```

## 字段映射

| Markdown Area | Source |
| --- | --- |
| `#` title | `video.lesson_title` or `video.id` |
| 课程 | `video.course_title` |
| 课节 | `video.lesson_title` or `video.id` |
| 视频 | `video.path` |
| 知识段落 | `len(sections)` |
| 时间范围 | 所有 section 的最早和最晚 `source_timestamps` |
| 核心结论 | 按排序后的 section title 列表 |
| 讲解摘要 | `section.summary` |
| 关键要点 | `section.key_points` |
| 时间 | `section.source_timestamps` |
| 图片 | `section.image_refs` |
| 标签 | `section.tags` |

## 排序和编号

继续沿用现有 `_section_sort_key()`：

- 有 `source_timestamps` 的 section 按第一个时间戳升序。
- 没有时间戳的 section 排在后面。
- 时间戳相同或都缺失时按标题排序。

输出中的 section 标题使用稳定编号：

```markdown
### 1. 第一个标题
### 2. 第二个标题
```

编号只影响 Markdown 展示，不写回 `KnowledgeSection`。

## 空字段处理

### Empty Sections

如果没有 section：

- 保留课程信息。
- `课程总览` 写“当前没有可导出的知识段落。”
- 不输出 `核心结论` 和 `知识结构`。

### Empty Key Points

如果 `section.key_points` 为空：

- 不输出 `关键要点` 小节。
- 避免输出 `(empty)`。

### Empty Image Refs

如果 `section.image_refs` 为空：

- `证据与回看` 中只输出时间。
- 不输出图片行。

### Empty Tags

如果 `section.tags` 为空：

- 不输出 `元数据` 小节。

### Empty Summary

`KnowledgeSection.summary` 是 string，可能为空字符串。为空时：

- 输出“暂无摘要。”作为 Markdown 展示文本。
- 不改变原始 section 数据。

## 时间格式

沿用当前两位小数秒格式：

```text
0.00s - 14.00s
```

规则：

- 0 个时间戳：`未知`
- 1 个时间戳：`12.50s`
- 2 个或更多时间戳：使用第一个和最后一个时间戳，输出 `start - end`

这里要微调当前 `_format_section_source()`：当前实现使用前两个时间戳；新版应使用排序后
section timestamps 的最小值和最大值，避免合并 section 的时间范围被中间顺序影响。

## Markdown 兼容性

模板继续生成普通 GitHub-flavored Markdown：

- 不使用 HTML。
- 不使用外部图片 embed 语法，仍以路径形式列出图片，避免本地路径渲染差异。
- 不使用表格承载主要内容，保证移动端和纯文本查看器可读。
- 中文标题用于用户阅读；代码、路径、tag 保持英文。

## 模块边界

### `vbook_export.note`

保持当前模块职责：

- `render_sections_note(video, sections)` 负责新版专家笔记 Markdown。
- `render_placeholder_note(...)` 保持现有 placeholder 运行概览。
- `write_note(markdown, path)` 不变。

可以新增私有 helper：

- `_format_course_time_range(sections)`
- `_format_timestamps(timestamps)`
- `_append_section(lines, index, section)`
- `_format_tags(tags)`

不新增公共 API。

### `vbook_client.cli`

不需要新增参数。当前逻辑已经在有 LLM sections 时把 `note_sections` 指向 LLM 输出，在无 LLM
command 时指向 evidence sections。新版模板自然作用于两条路径。

### `vbook_fusion`

不改融合算法和 LLM contract。

## 错误处理

`render_sections_note()` 不应因内容为空而抛错。它应对以下情况有稳定输出：

- `sections=[]`
- `course_title=""`
- `lesson_title=""`
- `source_timestamps=[]`
- `key_points=[]`
- `image_refs=[]`
- `tags=[]`
- `summary=""`

如果 `KnowledgeSection` 自身不是预期类型，不在本阶段做防御式运行时校验；现有 dataclass
和 parser 已负责保证结构。

## 测试策略

### Unit Tests: `tests/test_export/test_note.py`

扩展或替换当前 `test_render_sections_note_uses_knowledge_sections`：

- 输出包含中文标题：
  - `## 课程信息`
  - `## 课程总览`
  - `## 核心结论`
  - `## 知识结构`
- section 按时间排序并带编号。
- summary 出现在 `讲解摘要` 下。
- key points 出现在 `关键要点` 下。
- source timestamps 出现在 `证据与回看` 下。
- image refs 出现在 `证据与回看` 下。
- tags 出现在 `元数据` 下，并以逗号形式展示。

新增空字段测试：

- `sections=[]` 时输出“当前没有可导出的知识段落。”，不输出 `## 知识结构`。
- 空 `key_points` 不输出 `**关键要点**`。
- 空 `image_refs` 不输出图片行。
- 空 `tags` 不输出 `**元数据**`。
- 空 summary 输出“暂无摘要。”。

### CLI Integration Tests

现有 CLI tests 只断言 note 中包含 section 标题、summary、图片、tags 等关键内容。实现时需要
更新断言以匹配新版中文结构，但不应降低覆盖：

- `build` 默认路径仍生成 `note.md`。
- `manifest --write-fusion-sections --write-note` 仍从 fusion sections 渲染。
- `build --llm-fusion-command` 仍从 LLM sections 渲染，`note.md` 包含 LLM section title
  和 summary。

### Full Verification

```powershell
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

## 文档更新

实现后更新：

- `docs/00_project/status.md`
  - 把 `note.md` 从“not yet polished expert-level course note”调整为“第一版专家笔记模板”。
  - 更新 verification snapshot 测试数。
- `docs/20_architecture/output-contracts.md`
  - 补充新版 `note.md` 的主要结构。
- `docs/30_pipeline/overview.md`
  - 阶段 8 说明 `note.md` 已使用专家笔记 Markdown 模板组织 sections。

## 验收口径

本阶段完成后，应满足：

- 默认 build 不需要新增参数，仍生成 `note.md`。
- `note.md` 顶层结构从 artifact 展示改为专家课程笔记：
  - `课程信息`
  - `课程总览`
  - `核心结论`
  - `知识结构`
- 每个 section 保留：
  - 标题
  - 摘要
  - 关键要点
  - 来源时间戳
  - 图片引用
  - tags
- evidence sections 和 LLM sections 都能使用同一模板。
- 空字段输出自然，不暴露调试式 `(empty)`。
- `python -m unittest discover` 通过。

## 后续工作

完成本阶段后，可以继续：

- 设计 LLM response expert-note 扩展字段。
- 引入 `CourseNote` 中间模型，为多格式导出做准备。
- 增加复习题、术语表、学习目标和案例索引。
- 结合真实 Qwen 视觉输出检查图片证据在笔记中的可读性。
