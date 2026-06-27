# Evidence Fusion Note Design

## 背景

vBook 现在已经完成本地 MVP pipeline，并新增了 Qwen Vision Service adapter。
但真实 Qwen 服务今天大概率还不能部署完成，因此下一步应推进一条不依赖 Qwen endpoint
的主线：提升 `fusion/sections.json` 和 `note.md` 的内容质量。

当前 `vbook_fusion.sections.build_placeholder_sections()` 的行为是：

- 每个 `TranscriptSegment` 生成一个 `KnowledgeSection`。
- `title` 是 `Segment <id>`。
- `summary` 直接等于 transcript 文本。
- `image_refs` 只记录通过 timeline link 关联到该 segment 的图片。
- `key_points` 为空。
- `tags` 只有 `placeholder`。

这能保证 pipeline 可运行，但用户读到的 `note.md` 仍然接近调试输出，而不是课程笔记。

本阶段目标是在不接 LLM、不接真实 Qwen 服务、不改变 Qwen adapter 的前提下，把 deterministic
fusion 升级为“证据驱动的知识草稿”。它应该能使用 transcript、OCR 文本、视觉描述、
结构化观察和时间轴关联生成更有用的章节内容。

## 目标

新增 evidence-based deterministic fusion，用已有数据生成更接近课程笔记的
`KnowledgeSection[]` 和 Markdown。

具体目标：

- 保持 pipeline 不依赖外部服务。
- 保持 `KnowledgeSection` dataclass 不变，避免扩大数据模型改动面。
- 使用 transcript 文本作为章节主线。
- 将关联 frame 的 `ocr_text` 和 `vision_description` 纳入 summary 或 key points。
- 将 `structured_observations` 中常见字段转换为 key points 或 tags。
- 保留 image refs 和 source timestamps。
- 输出仍然可序列化到现有 `fusion/sections.json`。
- `note.md` 渲染能展示课程概览、章节、证据图片、要点和标签。

## 非目标

本阶段不做：

- 不调用 Qwen 服务。
- 不调用 OpenAI 或任何 LLM。
- 不新增 prompt execution。
- 不新增 searchable knowledge base。
- 不设计数据库。
- 不新增并发、队列或服务 runtime。
- 不改变 Qwen adapter。
- 不改变 `VisualAnalysis` 契约。
- 不改变 `KnowledgeSection` dataclass 字段。

## 方案选择

### 方案 A：直接增强 placeholder builder

把 `build_placeholder_sections()` 改成更聪明的 builder。

优点：

- 改动少。
- CLI 不需要变化。

缺点：

- “placeholder” 名称会变得不准确。
- 旧测试语义会混在新语义里。
- 后续接 LLM 时缺少清晰扩展点。

### 方案 B：新增 evidence builder，保留 placeholder builder

新增 `build_evidence_sections()`，并让默认 `build` 使用它。保留
`build_placeholder_sections()` 作为兼容函数或 fallback。

优点：

- 边界清晰。
- 不破坏旧 placeholder 语义。
- 后续可继续新增 LLM builder，而不用重写调用链。
- 可以用确定性 fixture 覆盖。

缺点：

- 需要多写少量测试和 CLI wiring。

### 方案 C：直接设计 LLM fusion

新增 prompt schema、外部 LLM command、response parser。

优点：

- 最接近最终智能目标。

缺点：

- 依赖外部模型服务，和当前“不要等 Qwen”的要求冲突。
- 容易在视觉服务未稳定前扩大不确定性。

## 决策

采用方案 B：新增 evidence builder，保留 placeholder builder。

原因：

- 与 Qwen 服务部署不冲突。
- 不引入新依赖。
- 让当前 `note.md` 明显更接近用户可读课程笔记。
- 为后续 LLM fusion 留出清晰扩展点。

## 设计范围

### 模块边界

`vbook_fusion.sections` 负责：

- 从 transcript、visual analyses、timeline links 构造 `KnowledgeSection[]`。
- 把视觉证据转换成 deterministic key points。
- 写 `fusion/sections.json`。

`vbook_export.note` 负责：

- 把 `KnowledgeSection[]` 渲染为 Markdown。
- 不理解 Qwen、OCR backend 或具体视觉 provider。

`vbook_client.cli` 负责：

- 在 `build` 默认流程中使用 evidence sections。
- 在 `manifest --write-fusion-sections` 中也使用 evidence sections。
- 不新增用户必须理解的新 backend。

### 新函数

新增：

```python
def build_evidence_sections(
    segments: Sequence[TranscriptSegment],
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    timeline_links: Sequence[TimelineLink] | None = None,
) -> list[KnowledgeSection]:
    ...
```

保留：

```python
def build_placeholder_sections(...):
    ...
```

`build_placeholder_sections()` 继续维持旧行为，方便测试和未来 fallback。

### Fusion sections JSON

`write_fusion_sections()` 当前写：

```json
{
  "schema_version": "1",
  "intent": "fusion_sections_placeholder",
  "section_count": 1,
  "sections": [...]
}
```

为了避免扩大写函数签名，本阶段让 `write_fusion_sections()` 自动判断 sections 是否包含
`evidence` tag：

- 如果任意 section 包含 `evidence` tag：
  - `intent = "fusion_sections_evidence"`
- 否则：
  - `intent = "fusion_sections_placeholder"`

这样可以保持旧调用兼容，也让 artifact 自描述更准确。

### Evidence section 构造规则

每个 transcript segment 仍生成一个 section。后续可以合并相邻 segment，但本阶段不做。

对每个 segment：

- `title`
  - 优先使用视觉结构化字段：
    - `topic`
    - `title`
    - `heading`
  - 如果没有，则从 transcript 文本中取前 18 个可读字符。
  - 如果 transcript 为空，则使用 `Segment <id>`。
- `summary`
  - 包含 transcript 文本。
  - 如果有关联视觉描述，追加 `视觉：<vision_description>`。
  - 如果有关联 OCR 文本，追加 `画面文字：<ocr_text>`。
  - 每段 summary 保持 deterministic，不做模型改写。
- `source_timestamps`
  - `[segment.start, segment.end]`
- `image_refs`
  - 来自 timeline links 和 visual analysis image path。
  - 去重，保持确定性顺序。
- `key_points`
  - transcript 文本作为一个要点，前缀 `讲解：`。
  - OCR 文本作为一个要点，前缀 `画面文字：`。
  - 视觉描述作为一个要点，前缀 `视觉描述：`。
  - `structured_observations.key_points` list 中的 string 直接加入。
  - `structured_observations.visible_elements` list 中的 string 组合为：
    `可见元素：a、b、c`
  - `structured_observations.topic` string 加入：
    `主题：...`
  - 去重，丢弃空字符串。
- `tags`
  - 固定包含 `evidence`。
  - 按视觉类型加入：
    - `visual:slide`
    - `visual:kline_case`
    - `visual:other`
  - 如果有关联 OCR 文本，加入 `has_ocr`。
  - 如果有关联图片，加入 `has_image`。
  - 如果 `structured_observations.language` 是 string，加入 `lang:<value>`。

### Note 渲染规则

`render_sections_note()` 保持函数签名不变，但输出更像笔记：

- 标题仍使用 lesson title。
- Course metadata 保留。
- `## Knowledge Sections` 保留。
- 每个 section 输出：
  - section title。
  - summary。
  - source timestamp。
  - images。
  - key points。
  - tags。

新增标签展示：

```markdown
Tags:
- evidence
- visual:slide
- has_ocr
```

这不改变 `KnowledgeSection` 数据结构，只增强 Markdown 可读性。

## 与 Qwen 服务的关系

本阶段不依赖 Qwen 服务部署。

后续 Qwen 服务上线后：

- Qwen adapter 生成更真实的 `VisualAnalysis[]`。
- `build_evidence_sections()` 自动吸收其中的 OCR、视觉描述和结构化观察。
- 不需要改 Qwen adapter 才能看到 note 质量提升。

## 测试策略

使用 `unittest` 和现有 deterministic fixture。

新增/修改测试：

- `tests/test_fusion/test_sections.py`
  - 验证 `build_evidence_sections()` 能把 transcript、OCR、视觉描述、结构化观察、图片引用组合进 section。
  - 验证无视觉输入时也能生成 transcript-only evidence section。
  - 验证 `write_fusion_sections()` 对 evidence sections 写出 `intent = fusion_sections_evidence`。
- `tests/test_export/test_note.py`
  - 验证 `render_sections_note()` 展示 tags。
- `tests/test_client/test_manifest_cli.py`
  - 验证 `build` 默认生成 evidence sections，而不是 placeholder intent。
  - 验证 manual-json 视觉输入能进入 evidence note。

最终验证：

```powershell
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

## 验收口径

完成后应满足：

- Qwen 服务未部署时，默认 `build` 仍可运行。
- `fusion/sections.json` 的 intent 对 evidence sections 显示为
  `fusion_sections_evidence`。
- `note.md` 能展示：
  - transcript 主线
  - OCR 文本
  - 视觉描述
  - 图片引用
  - key points
  - tags
- `manual-json` 或 `external-command` stub 的视觉分析能影响最终 note。
- 全量测试通过。

## 风险与控制

- 风险：确定性规则可能不如 LLM 总结自然。
  - 控制：本阶段明确定位为知识草稿，不声称最终智能总结。
- 风险：每个 transcript segment 一个 section 会导致章节过碎。
  - 控制：先保持简单和可追溯，后续再做相邻 segment 合并。
- 风险：结构化观察字段多样，规则可能覆盖不全。
  - 控制：只处理高频字段：`topic`、`title`、`heading`、`key_points`、
    `visible_elements`、`language`。
