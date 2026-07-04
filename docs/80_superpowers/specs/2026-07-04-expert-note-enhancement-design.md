# Expert Note Enhancement Design

## 背景

vBook 已经具备第一版 section-based 专家笔记模板。当前 `render_sections_note()` 会把
`KnowledgeSection[]` 渲染为中文 Markdown，包含：

- `课程信息`
- `课程总览`
- `核心结论`
- `知识结构`

每个知识段落已经保留标题、摘要、关键要点、来源时间戳、图片引用和 tags。这一版解决了
“artifact 展示”到“课程笔记”的基础转变，但学习辅助能力仍然不足。用户在等待 Qwen 视觉服务
部署期间，希望继续推进不冲突的任务，因此本阶段聚焦 `note.md` 的阅读和复习价值增强。

本设计采用已确认的方案 A：不改变上游数据结构，不改变外部 LLM/Qwen 协议，不调用真实服务，
只在 Markdown 输出层基于现有字段做确定性派生。

## 目标

- 提升 `note.md` 对课程复习、回看和知识整理的直接价值。
- 保持 `KnowledgeSection` dataclass、fusion artifacts、manifest schema 和 LLM response
  contract 不变。
- 新增内容必须能从现有 `KnowledgeSection` 字段或固定模板推导出来。
- 保留证据回溯能力：时间戳、图片引用、tags 仍然可见。
- 同时兼容 deterministic evidence sections 和 LLM sections。
- 空 sections 和空字段必须输出自然，不暴露调试式占位文本。
- 使用现有 `unittest` 体系，通过先写失败测试再实现的方式完成。

## 非目标

本阶段不做：

- 不新增 `KnowledgeSection.learning_objectives`、`review_questions`、`glossary` 等字段。
- 不扩展 LLM fusion request 或 response contract。
- 不新增 `CourseNote` 中间模型。
- 不引入 Markdown 模板引擎依赖。
- 不生成真正的术语定义，因为当前数据没有术语解释来源。
- 不让复习问题变成 LLM 风格的自由生成内容。
- 不改变 `render_placeholder_note()`。
- 不执行真实 Qwen 视觉服务或真实 LLM 服务联调。

## 输出结构

新版 `render_sections_note()` 的顶层结构为：

```markdown
# <lesson_title_or_video_id>

## 课程信息

## 课程总览

## 学习目标

## 核心结论

## 知识结构

## 回看索引

## 复习问题

## 标签索引
```

其中：

- `课程信息`、`课程总览`、`核心结论`、`知识结构` 继续承担现有职责。
- `学习目标`、`回看索引`、`复习问题`、`标签索引` 是本阶段新增结构。
- 如果 `sections=[]`，只输出 `课程信息` 和 `课程总览`，不输出派生章节。
- 如果没有 tags，不输出 `标签索引`。

## 字段映射

| Markdown Area | Source |
| --- | --- |
| `#` title | `video.lesson_title` or `video.id` |
| 课程 | `video.course_title` |
| 课节 | `video.lesson_title` or `video.id` |
| 视频 | `video.path` |
| 知识段落 | `len(sections)` |
| 时间范围 | 所有 section 的最早和最晚 `source_timestamps` |
| 学习目标 | `section.title` 和 `section.key_points` |
| 核心结论 | 排序后的 `section.title` 列表 |
| 知识结构 | 每个 `KnowledgeSection` 的原始可读内容 |
| 回看索引 | `section.title`、`source_timestamps`、`image_refs` |
| 复习问题 | `section.title`、`source_timestamps` 和固定模板 |
| 标签索引 | 所有 `section.tags` 去重排序后的列表 |

## 学习目标

`学习目标` 用来告诉用户本节课应该掌握什么，但不能编造新的专业结论。生成规则：

- 对每个 section 至少生成一条目标。
- 如果 section 有 `key_points`，优先从 key point 派生：
  - `掌握：<key point>`
- 如果 section 没有 `key_points`，从 section title 派生：
  - `理解：<section title>`
- 目标顺序跟随 section 排序。
- 不对 key point 做语义改写，只套固定前缀。

示例：

```markdown
## 学习目标

- 理解：Intro
- 掌握：Define the support area
- 掌握：Watch volume confirmation
```

## 回看索引

`回看索引` 用来把课程知识点映射回视频证据。生成规则：

- 每个 section 输出一条索引。
- 索引包含 section title 和时间范围。
- 如果有图片引用，追加图片路径。
- 如果没有图片引用，只输出时间。
- 如果没有时间戳，时间显示 `未知`。

建议格式：

```markdown
## 回看索引

- Intro：0.00s - 3.00s；图片：outputs/lesson/frames/selected/frame_000001.jpg
- Case detail：8.00s - 12.00s；图片：outputs/lesson/frames/selected/frame_000002.jpg
```

多张图片使用逗号连接。路径保持原样，不改成 Markdown image embed，避免本地路径渲染差异。

## 复习问题

`复习问题` 提供固定模板问题，帮助用户回忆每个知识段落。它不是模型自由生成内容。

生成规则：

- 每个 section 输出一到两条问题。
- 第一条问题基于 section title 和时间范围：
  - 有时间戳：`<title> 的核心观点是什么？请回看 <time_range>。`
  - 无时间戳：`<title> 的核心观点是什么？请结合本节笔记回看。`
- 如果 section 有图片引用，追加一条证据问题：
  - `哪些图片证据支持 <title> 这一段的判断？`
- 如果 section 没有图片引用，不生成图片证据问题。
- 不根据 summary 或 key points 改写成新的事实判断。

示例：

```markdown
## 复习问题

- Intro 的核心观点是什么？请回看 0.00s - 3.00s。
- 哪些图片证据支持 Intro 这一段的判断？
- Sparse 的核心观点是什么？请结合本节笔记回看。
```

## 标签索引

当前数据只有 tags，没有术语定义。因此新增章节命名为 `标签索引`，不命名为 `术语表` 或
`术语与标签`。这样能避免用户误以为系统已经生成了经过解释的术语库。

生成规则：

- 汇总所有 `section.tags`。
- 去重。
- 按字典序排序，保证输出稳定。
- 以 inline code 形式展示 tag。
- 如果没有 tags，不输出 `标签索引` 章节。

示例：

```markdown
## 标签索引

- `evidence`
- `final`
- `llm`
- `visual:slide`
```

## 知识结构

`知识结构` 继续沿用现有 section 展示方式：

```markdown
## 知识结构

### 1. <section title>

**讲解摘要**

<section.summary or 暂无摘要。>

**关键要点**

- <key point>

**证据与回看**

- 时间：<source time range>
- 图片：<image ref>

**元数据**

- 标签：tag1, tag2
```

本阶段不改变单个 section 的核心信息，只在必要时补齐 helper，让新增章节复用一致的时间、
图片和 tag 格式化逻辑。

## 排序和稳定性

继续沿用现有 `_section_sort_key()`：

- 有 `source_timestamps` 的 section 按第一个时间戳升序。
- 没有时间戳的 section 排在后面。
- 时间戳相同或都缺失时按标题排序。

新增章节必须使用同一份排序后的 section list，避免 `学习目标`、`核心结论`、`知识结构`、
`回看索引` 和 `复习问题` 顺序不一致。

tags 排序独立处理：

- 去重后按字符串升序。
- 保持大小写原样。
- 不拆分 `visual:slide` 这类带冒号的 tag。

## 空字段处理

### Empty Sections

如果没有 section：

- 保留 `课程信息`。
- `课程总览` 输出 `当前没有可导出的知识段落。`
- 不输出 `学习目标`、`核心结论`、`知识结构`、`回看索引`、`复习问题`、`标签索引`。

### Empty Summary

如果 `section.summary == ""`：

- 在 `讲解摘要` 下输出 `暂无摘要。`
- 不改变原始 section 数据。

### Empty Key Points

如果 `section.key_points == []`：

- 不输出该 section 的 `关键要点` 小节。
- `学习目标` 退回 `理解：<section title>`。

### Empty Image Refs

如果 `section.image_refs == []`：

- `证据与回看` 不输出图片行。
- `回看索引` 只输出标题和时间。
- `复习问题` 不输出图片证据问题。

### Empty Tags

如果所有 sections 都没有 tags：

- 不输出 `标签索引`。
- 单个 section 没有 tags 时，不输出该 section 的 `元数据` 小节。

### Empty Timestamps

如果 `section.source_timestamps == []`：

- section 时间显示 `未知`。
- 复习问题使用 `请结合本节笔记回看。`

## 模块边界

### `vbook_export.note`

保持当前模块职责：

- `render_sections_note(video, sections)` 负责专家笔记 Markdown。
- `render_placeholder_note(...)` 保持 placeholder 运行概览。
- `write_note(markdown, path)` 不变。

可以新增或调整私有 helper：

- `_append_learning_objectives(lines, sections)`
- `_append_review_index(lines, sections)`
- `_append_review_questions(lines, sections)`
- `_append_tag_index(lines, sections)`
- `_format_image_refs(image_refs)`
- `_format_review_question(section)`

不新增公共 API。

### `vbook_client.cli`

不需要新增 CLI 参数。当前 CLI 已经在 build、manifest note 写入、LLM fusion 输出路径中调用
`render_sections_note()`，模板增强会自然作用于这些路径。

### `vbook_fusion`

不改融合算法、section schema 或 LLM contract。

## 错误处理

`render_sections_note()` 不应因为缺少可选内容而抛错。它应对以下输入稳定输出：

- `sections=[]`
- `course_title=""`
- `lesson_title=""`
- `summary=""`
- `source_timestamps=[]`
- `key_points=[]`
- `image_refs=[]`
- `tags=[]`

如果传入对象不是 `KnowledgeSection` 或 `VideoAsset`，本阶段不新增运行时类型防御。现有
dataclass、parser 和测试负责保证结构正确。

## 测试策略

实现阶段必须先写失败测试，再改实现。

### Unit Tests: `tests/test_export/test_note.py`

新增或扩展测试覆盖：

- 输出包含新增标题：
  - `## 学习目标`
  - `## 回看索引`
  - `## 复习问题`
  - `## 标签索引`
- 新增标题顺序稳定，且位于 `课程总览`、`核心结论`、`知识结构` 的预期位置。
- `学习目标` 使用 key points，缺少 key points 时退回 section title。
- `回看索引` 包含 section title、时间范围和图片路径。
- `复习问题` 使用固定模板，有时间戳和无时间戳两种路径都覆盖。
- `标签索引` 对 tags 去重、排序，并以 inline code 展示。
- 空 sections 不输出派生章节。
- 空图片不输出图片证据问题。
- 空 tags 不输出 `标签索引`。
- 输出中不出现 `(empty)`。

### CLI Tests

根据现有断言情况更新或补充：

- 默认 build 生成的 `note.md` 仍包含 section title、summary、image refs 和 tags。
- `manifest --write-fusion-sections --write-note` 仍从 fusion sections 渲染增强模板。
- `build --llm-fusion-command` 仍从 LLM sections 渲染增强模板。
- 不降低现有对 manifest、fusion sections 和 note 路径的覆盖。

### Verification

实现完成后运行：

```powershell
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

## 验收口径

本阶段完成后，应满足：

- 不新增任何外部服务依赖。
- 不改变现有输入输出 schema。
- `note.md` 顶层包含学习目标、回看索引、复习问题和标签索引。
- 新增章节全部来自现有 section 数据和固定模板。
- 不生成伪术语解释。
- 空数据输出自然，不出现 `(empty)`。
- deterministic evidence sections 和 LLM sections 都能使用同一增强模板。
- 全量 `python -m unittest discover` 通过。

## 后续工作

完成本阶段后，可以继续：

- 设计真正的 LLM response expert fields，例如 `learning_objectives`、`review_questions`、
  `glossary`。
- 引入 `CourseNote` 中间模型，为 HTML、PDF、Obsidian 或知识库导出做准备。
- 在真实 Qwen 视觉服务 ready 后，用真实图片证据检查 `回看索引` 的可读性。
- 将用户定义的中文术语库接入导出层，生成真正的术语解释章节。
