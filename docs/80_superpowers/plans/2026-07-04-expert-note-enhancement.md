# Expert Note Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance section-based `note.md` with deterministic learning objectives, review index, review questions, and tag index while keeping existing schemas and external-service contracts unchanged.

**Architecture:** Keep the enhancement inside `vbook_export.note.render_sections_note()` and private helpers. Existing CLI paths already call this renderer for deterministic evidence sections and LLM sections, so no CLI parameter or schema change is needed. Tests first lock the Markdown contract, then implementation adds small formatting helpers, followed by CLI assertions and documentation updates.

**Tech Stack:** Python 3, `unittest`, existing vBook dataclasses, Markdown documentation, Git.

---

## File Structure

- Modify: `tests/test_export/test_note.py`
  - Add failing unit coverage for enhanced section note structure, derived content, empty fields, and tag index behavior.
- Modify: `vbook_export/note.py`
  - Add private helper functions for learning objectives, review index, review questions, tag index, and image reference formatting.
  - Keep public APIs unchanged.
- Modify: `tests/test_client/test_manifest_cli.py`
  - Strengthen existing CLI tests so default build, manual-json build, manifest note export, and LLM fusion note export all assert the enhanced note sections.
- Modify: `docs/20_architecture/output-contracts.md`
  - Update the Markdown note contract from first-version expert template to enhanced expert template.
- Modify: `docs/30_pipeline/overview.md`
  - Update stage 8 export description.
- Modify: `docs/00_project/status.md`
  - Update current status and remaining partial work.
- Modify: `docs/00_project/task-board.md`
  - Mark expert note enhancement done and update next recommended work.

Do not modify `KnowledgeSection`, manifest schema, LLM fusion request/response schema, Qwen vision adapter, CLI arguments, or real-service runbooks.

---

## Task 1: Add Failing Unit Tests for Enhanced Section Notes

**Files:**
- Modify: `tests/test_export/test_note.py`

- [ ] **Step 1: Replace `test_render_sections_note_uses_expert_course_note_structure` with enhanced expectations**

Replace the full method `test_render_sections_note_uses_expert_course_note_structure` with:

```python
    def test_render_sections_note_uses_expert_course_note_structure(self) -> None:
        video = VideoAsset(
            id="lesson",
            path=Path("course/lesson.mp4"),
            course_title="Stock Course",
            lesson_title="MA Support",
        )
        sections = [
            KnowledgeSection(
                title="Case detail",
                summary="Watch the follow-up case.",
                source_timestamps=[12.0, 8.0],
                image_refs=["outputs/lesson/frames/selected/frame_000002.jpg"],
                key_points=["Watch volume confirmation"],
                tags=["llm", "final", "visual:slide"],
            ),
            KnowledgeSection(
                title="Intro",
                summary="Introduce moving-average support.",
                source_timestamps=[0.0, 3.0],
                image_refs=["outputs/lesson/frames/selected/frame_000001.jpg"],
                key_points=["Define the support area"],
                tags=["evidence", "visual:slide"],
            ),
        ]

        markdown = render_sections_note(video=video, sections=sections)

        self.assertIn("# MA Support", markdown)
        self.assertIn("## 课程信息", markdown)
        self.assertIn("- 课程：Stock Course", markdown)
        self.assertIn("- 课节：MA Support", markdown)
        self.assertIn("- 视频：course\\lesson.mp4", markdown.replace("/", "\\"))
        self.assertIn("- 知识段落：2", markdown)
        self.assertIn("- 时间范围：0.00s - 12.00s", markdown)
        self.assertIn("## 课程总览", markdown)
        self.assertIn("本节共整理 2 个知识段落，覆盖 0.00s - 12.00s。", markdown)
        self.assertIn("## 学习目标", markdown)
        self.assertIn("- 掌握：Define the support area", markdown)
        self.assertIn("- 掌握：Watch volume confirmation", markdown)
        self.assertIn("## 核心结论", markdown)
        self.assertIn("- Intro", markdown)
        self.assertIn("- Case detail", markdown)
        self.assertIn("## 知识结构", markdown)
        self.assertIn("## 回看索引", markdown)
        self.assertIn(
            "- Intro：0.00s - 3.00s；图片：outputs/lesson/frames/selected/frame_000001.jpg",
            markdown,
        )
        self.assertIn(
            "- Case detail：8.00s - 12.00s；图片：outputs/lesson/frames/selected/frame_000002.jpg",
            markdown,
        )
        self.assertIn("## 复习问题", markdown)
        self.assertIn("Intro 的核心观点是什么？请回看 0.00s - 3.00s。", markdown)
        self.assertIn("哪些图片证据支持 Intro 这一段的判断？", markdown)
        self.assertIn(
            "Case detail 的核心观点是什么？请回看 8.00s - 12.00s。",
            markdown,
        )
        self.assertIn("## 标签索引", markdown)
        self.assertLess(markdown.index("- `evidence`"), markdown.index("- `final`"))
        self.assertLess(markdown.index("- `final`"), markdown.index("- `llm`"))
        self.assertLess(markdown.index("- `llm`"), markdown.index("- `visual:slide`"))
        self.assertEqual(markdown.count("- `visual:slide`"), 1)
        self.assertLess(
            markdown.index("## 课程总览"),
            markdown.index("## 学习目标"),
        )
        self.assertLess(
            markdown.index("## 学习目标"),
            markdown.index("## 核心结论"),
        )
        self.assertLess(
            markdown.index("## 核心结论"),
            markdown.index("## 知识结构"),
        )
        self.assertLess(
            markdown.index("## 知识结构"),
            markdown.index("## 回看索引"),
        )
        self.assertLess(
            markdown.index("## 回看索引"),
            markdown.index("## 复习问题"),
        )
        self.assertLess(
            markdown.index("## 复习问题"),
            markdown.index("## 标签索引"),
        )
        self.assertLess(
            markdown.index("### 1. Intro"),
            markdown.index("### 2. Case detail"),
        )
        self.assertIn("**讲解摘要**", markdown)
        self.assertIn("Introduce moving-average support.", markdown)
        self.assertIn("**关键要点**", markdown)
        self.assertIn("- Define the support area", markdown)
        self.assertIn("**证据与回看**", markdown)
        self.assertIn("- 时间：0.00s - 3.00s", markdown)
        self.assertIn(
            "- 图片：outputs/lesson/frames/selected/frame_000001.jpg",
            markdown,
        )
        self.assertIn("**元数据**", markdown)
        self.assertIn("- 标签：evidence, visual:slide", markdown)
        self.assertIn("- 时间：8.00s - 12.00s", markdown)
```

- [ ] **Step 2: Replace `test_render_sections_note_handles_empty_sections_and_empty_fields` with enhanced empty-field expectations**

Replace the full method `test_render_sections_note_handles_empty_sections_and_empty_fields` with:

```python
    def test_render_sections_note_handles_empty_sections_and_empty_fields(self) -> None:
        video = VideoAsset(
            id="lesson",
            path=Path("course/lesson.mp4"),
            course_title="",
            lesson_title="",
        )

        empty_markdown = render_sections_note(video=video, sections=[])

        self.assertIn("# lesson", empty_markdown)
        self.assertIn("## 课程信息", empty_markdown)
        self.assertIn("- 课程：", empty_markdown)
        self.assertIn("- 课节：lesson", empty_markdown)
        self.assertIn("- 知识段落：0", empty_markdown)
        self.assertIn("- 时间范围：未知", empty_markdown)
        self.assertIn("当前没有可导出的知识段落。", empty_markdown)
        self.assertNotIn("## 学习目标", empty_markdown)
        self.assertNotIn("## 核心结论", empty_markdown)
        self.assertNotIn("## 知识结构", empty_markdown)
        self.assertNotIn("## 回看索引", empty_markdown)
        self.assertNotIn("## 复习问题", empty_markdown)
        self.assertNotIn("## 标签索引", empty_markdown)

        sparse_markdown = render_sections_note(
            video=video,
            sections=[
                KnowledgeSection(
                    title="Sparse",
                    summary="",
                    source_timestamps=[],
                    image_refs=[],
                    key_points=[],
                    tags=[],
                )
            ],
        )

        self.assertIn("## 学习目标", sparse_markdown)
        self.assertIn("- 理解：Sparse", sparse_markdown)
        self.assertIn("### 1. Sparse", sparse_markdown)
        self.assertIn("暂无摘要。", sparse_markdown)
        self.assertIn("**证据与回看**", sparse_markdown)
        self.assertIn("- 时间：未知", sparse_markdown)
        self.assertIn("## 回看索引", sparse_markdown)
        self.assertIn("- Sparse：未知", sparse_markdown)
        self.assertIn("## 复习问题", sparse_markdown)
        self.assertIn("Sparse 的核心观点是什么？请结合本节笔记回看。", sparse_markdown)
        self.assertNotIn("哪些图片证据支持 Sparse", sparse_markdown)
        self.assertNotIn("**关键要点**", sparse_markdown)
        self.assertNotIn("- 图片：", sparse_markdown)
        self.assertNotIn("**元数据**", sparse_markdown)
        self.assertNotIn("## 标签索引", sparse_markdown)
        self.assertNotIn("(empty)", sparse_markdown)
```

- [ ] **Step 3: Run export note tests and verify they fail for the new contract**

Run:

```powershell
python -m unittest tests.test_export.test_note
```

Expected: command exits non-zero. The failure must mention missing `## 学习目标` or another newly expected enhanced section.

Do not commit yet.

---

## Task 2: Implement Enhanced Section Note Rendering

**Files:**
- Modify: `vbook_export/note.py`
- Test: `tests/test_export/test_note.py`

- [ ] **Step 1: Insert enhanced section calls in `render_sections_note()`**

Inside `render_sections_note()`, replace this block:

```python
    lines.extend(
        [
            f"本节共整理 {len(section_list)} 个知识段落，覆盖 {time_range}。",
            "",
            "## 核心结论",
            "",
        ]
    )
    lines.extend(f"- {section.title}" for section in section_list)
    lines.extend(["", "## 知识结构", ""])

    for index, section in enumerate(section_list, start=1):
        _append_expert_section(lines, index, section)
```

with:

```python
    lines.extend(
        [
            f"本节共整理 {len(section_list)} 个知识段落，覆盖 {time_range}。",
            "",
            "## 学习目标",
            "",
        ]
    )
    _append_learning_objectives(lines, section_list)
    lines.extend(["", "## 核心结论", ""])
    lines.extend(f"- {section.title}" for section in section_list)
    lines.extend(["", "## 知识结构", ""])

    for index, section in enumerate(section_list, start=1):
        _append_expert_section(lines, index, section)

    _append_review_index(lines, section_list)
    _append_review_questions(lines, section_list)
    _append_tag_index(lines, section_list)
```

- [ ] **Step 2: Add private helpers below `_append_expert_section()`**

Insert these helper functions after `_append_expert_section()` and before `_format_tags()`:

```python

def _append_learning_objectives(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    for section in sections:
        if section.key_points:
            lines.extend(f"- 掌握：{point}" for point in section.key_points)
        else:
            lines.append(f"- 理解：{section.title}")


def _append_review_index(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    lines.extend(["", "## 回看索引", ""])
    for section in sections:
        image_suffix = (
            f"；图片：{_format_image_refs(section.image_refs)}"
            if section.image_refs
            else ""
        )
        lines.append(
            f"- {section.title}：{_format_section_source(section)}{image_suffix}"
        )


def _append_review_questions(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    lines.extend(["", "## 复习问题", ""])
    for section in sections:
        if section.source_timestamps:
            lines.append(
                f"- {section.title} 的核心观点是什么？"
                f"请回看 {_format_section_source(section)}。"
            )
        else:
            lines.append(
                f"- {section.title} 的核心观点是什么？请结合本节笔记回看。"
            )
        if section.image_refs:
            lines.append(f"- 哪些图片证据支持 {section.title} 这一段的判断？")


def _append_tag_index(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    tags = sorted({tag for section in sections for tag in section.tags})
    if not tags:
        return

    lines.extend(["", "## 标签索引", ""])
    lines.extend(f"- `{tag}`" for tag in tags)


def _format_image_refs(image_refs: Sequence[str]) -> str:
    return ", ".join(image_refs)
```

- [ ] **Step 3: Run export note tests and verify they pass**

Run:

```powershell
python -m unittest tests.test_export.test_note
```

Expected: exits `0` and prints `OK`.

- [ ] **Step 4: Inspect export diff**

Run:

```powershell
git diff -- tests/test_export/test_note.py vbook_export/note.py
```

Expected manual checks:

- Public functions remain `render_placeholder_note`, `write_note`, and `render_sections_note`.
- `render_placeholder_note()` is unchanged.
- New helpers are private and deterministic.
- No external services, schemas, or CLI arguments are touched.

- [ ] **Step 5: Commit export renderer enhancement**

Run:

```powershell
git add tests/test_export/test_note.py vbook_export/note.py
git commit -m "Enhance expert note renderer"
```

---

## Task 3: Strengthen CLI Note Output Assertions

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Add enhanced note assertions to default build test**

In `test_build_command_writes_default_mvp_artifacts`, after:

```python
        self.assertIn("## 课程总览", note)
```

insert:

```python
        self.assertIn("## 学习目标", note)
        self.assertIn("## 回看索引", note)
        self.assertIn("## 复习问题", note)
        self.assertIn("## 标签索引", note)
```

- [ ] **Step 2: Add enhanced note assertions to manual-json build test**

In `test_build_command_can_use_manual_json_visual_analysis`, after:

```python
        self.assertIn("frame_000001.jpg", note)
```

insert:

```python
        self.assertIn("## 学习目标", note)
        self.assertIn("## 回看索引", note)
        self.assertIn("## 复习问题", note)
        self.assertIn("## 标签索引", note)
        self.assertIn("哪些图片证据支持", note)
        self.assertIn("`has_ocr`", note)
```

- [ ] **Step 3: Add enhanced note assertions to manifest fusion-note test**

In `test_manifest_command_renders_note_from_fusion_sections`, after:

```python
        self.assertIn("## 课程总览", note)
```

insert:

```python
        self.assertIn("## 学习目标", note)
        self.assertIn("## 回看索引", note)
        self.assertIn("## 复习问题", note)
        self.assertIn("## 标签索引", note)
```

- [ ] **Step 4: Add enhanced note assertions to custom LLM command test**

In `test_build_command_can_use_llm_fusion_command`, after:

```python
        self.assertIn("## 知识结构", note)
```

insert:

```python
        self.assertIn("## 学习目标", note)
        self.assertIn("## 回看索引", note)
        self.assertIn("## 复习问题", note)
        self.assertIn("## 标签索引", note)
        self.assertIn("- 掌握：LLM point", note)
        self.assertIn("`final`", note)
```

- [ ] **Step 5: Add enhanced note assertions to stub LLM command test**

In `test_build_command_can_use_llm_fusion_stub_tool`, after:

```python
        self.assertIn("## 课程信息", note)
```

insert:

```python
        self.assertIn("## 学习目标", note)
        self.assertIn("## 回看索引", note)
        self.assertIn("## 复习问题", note)
        self.assertIn("## 标签索引", note)
```

- [ ] **Step 6: Run CLI tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli
```

Expected: exits `0` and prints `OK`.

- [ ] **Step 7: Commit CLI assertion coverage**

Run:

```powershell
git add tests/test_client/test_manifest_cli.py
git commit -m "Cover enhanced notes in CLI tests"
```

---

## Task 4: Update Project Documentation for Enhanced Notes

**Files:**
- Modify: `docs/20_architecture/output-contracts.md`
- Modify: `docs/30_pipeline/overview.md`
- Modify: `docs/00_project/status.md`
- Modify: `docs/00_project/task-board.md`

- [ ] **Step 1: Update `docs/20_architecture/output-contracts.md` Markdown note contract**

Replace the paragraph under `## Markdown 笔记` with:

```markdown
`note.md` 是面向用户阅读的最终产物。section-based note 使用增强专家笔记结构：
`课程信息`、`课程总览`、`学习目标`、`核心结论`、`知识结构`、`回看索引`、`复习问题`
和 `标签索引`。每个知识段落保留讲解摘要、关键要点、来源时间戳、图片引用和 tags；
新增学习目标、复习问题和标签索引均由现有 `KnowledgeSection` 字段和固定模板确定性派生，
不伪造术语定义或额外专业判断。
```

- [ ] **Step 2: Update `docs/30_pipeline/overview.md` stage 8**

Replace the final paragraph under `## 阶段 8：导出` with:

```markdown
导出双核心产物：`note.md` 面向用户阅读，`manifest.json` 面向机器复跑和后续知识库。
同步保存图片素材、转写记录、视觉分析 JSON 和融合结果。section-based `note.md` 使用增强
专家笔记 Markdown 模板组织 `课程信息`、`课程总览`、`学习目标`、`核心结论`、`知识结构`、
`回看索引`、`复习问题` 和 `标签索引`，并保留每个重点对应的原始视频时间点、相关图片和
tags。新增学习辅助内容来自现有 section 数据和固定模板，不依赖真实 Qwen 或 LLM 服务。
```

- [ ] **Step 3: Update `docs/00_project/status.md` date and capability bullets**

Replace:

```markdown
Last updated: 2026-06-27
```

with:

```markdown
Last updated: 2026-07-04
```

Replace:

```markdown
- Markdown note export from transcript or fusion sections, including a
  first-version expert-note template for section-based notes.
```

with:

```markdown
- Markdown note export from transcript or fusion sections, including an
  enhanced expert-note template with learning objectives, review index,
  review questions, and tag index for section-based notes.
```

Replace:

```markdown
- `note.md` has a first-version expert-note structure, but review questions,
  glossary, learning objectives, and multi-format exports are still future work.
```

with:

```markdown
- `note.md` now has deterministic learning objectives, review index, review
  questions, and tag index, but true glossary definitions and multi-format
  exports are still future work.
```

Replace the `## Most Important Next Work` numbered list with:

```markdown
1. Execute the Qwen Vision Service integration runbook once the service team
   confirms deployment readiness.
2. Add a real smoke-test sample path once both local MP4 and transcript files
   are available.
3. Complete batch workflow runbook and failure-report documentation.
4. Expand pipeline-stage documents under `docs/30_pipeline/`.
5. Keep `manifest.json` and `note.md` as the primary output contract while
   intelligence improves behind the same artifacts.
```

- [ ] **Step 4: Update `docs/00_project/task-board.md` expert note status**

Replace this row:

```markdown
| Expert note export | `Partial` | `note.md` 已支持第一版 section-based expert-note 模板。 | 增加 review questions、glossary、learning objectives。 |
```

with:

```markdown
| Expert note export | `Partial` | `note.md` 已支持增强 section-based expert-note 模板，包含学习目标、回看索引、复习问题和标签索引。 | 后续接入真实 glossary 定义、多格式导出和更高质量 LLM synthesis。 |
```

Replace this row:

```markdown
| 增强专家笔记模板 | `Ready` | `note.md` 增加 review questions、glossary、learning objectives 的稳定结构。 |
```

with:

```markdown
| 增强专家笔记模板 | `Done` | `note.md` 已增加学习目标、回看索引、复习问题和标签索引；内容来自现有 section 数据和固定模板。 |
```

In the `最近完成` table, add this row immediately before `Qwen Vision integration runbook`:

```markdown
| Expert note enhancement | `Done` | `note.md` 新增学习目标、回看索引、复习问题和标签索引，不改变上游 schema 或外部服务 contract。 |
```

Replace the `## 下一步推荐任务` section with:

```markdown
## 下一步推荐任务

推荐下一步：完善 batch workflow 说明。

理由：

- Qwen 服务尚未确认部署完成，真实视觉联调仍保持 blocked。
- 专家笔记模板增强已经完成，`note.md` 的本地输出价值已进一步提升。
- batch workflow 已有基础实现，完善输入目录、输出目录、失败报告、manifest 检查和重跑策略，可以继续降低真实课程批量处理时的操作成本。
```

- [ ] **Step 5: Run documentation checks**

Run:

```powershell
rg -n "增强专家笔记|学习目标|回看索引|复习问题|标签索引|glossary|batch workflow" docs/20_architecture/output-contracts.md docs/30_pipeline/overview.md docs/00_project/status.md docs/00_project/task-board.md
git diff --check
```

Expected:

- `rg` shows the enhanced note structure in architecture, pipeline, status, and task-board docs.
- `git diff --check` exits `0` with no output.

- [ ] **Step 6: Commit documentation updates**

Run:

```powershell
git add docs/20_architecture/output-contracts.md docs/30_pipeline/overview.md docs/00_project/status.md docs/00_project/task-board.md
git commit -m "Document enhanced expert notes"
```

---

## Task 5: Full Verification and Final State Check

**Files:**
- All files modified in Tasks 1 through 4.

- [ ] **Step 1: Run focused export tests**

Run:

```powershell
python -m unittest tests.test_export.test_note
```

Expected: exits `0` and prints `OK`.

- [ ] **Step 2: Run focused CLI tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli
```

Expected: exits `0` and prints `OK`.

- [ ] **Step 3: Run full suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits `0` and prints `OK`. The previous expected count was `129`; if the count changes, record the exact new count in the final summary and update any verification snapshot that names the count.

- [ ] **Step 4: Run final diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 5: Inspect branch state**

Run:

```powershell
git status --short --branch
git log --oneline -5
```

Expected:

- Worktree is clean.
- Recent commits include:
  - `Enhance expert note renderer`
  - `Cover enhanced notes in CLI tests`
  - `Document enhanced expert notes`

Do not push to `origin/main` unless the user explicitly asks for a push.

---

## Self-Review

Spec coverage:

- Enhanced top-level sections are covered by Task 1 unit assertions and Task 2 implementation.
- Deterministic `学习目标` from key points or section title is covered by Task 1 and Task 2.
- `回看索引` with time range and optional images is covered by Task 1 and Task 2.
- Fixed-template `复习问题` with timestamp and no-timestamp paths is covered by Task 1 and Task 2.
- `标签索引` with de-duplicated sorted inline-code tags is covered by Task 1 and Task 2.
- Empty sections, empty summary, empty key points, empty images, empty tags, and empty timestamps are covered by Task 1.
- CLI compatibility for default evidence sections, manual-json sections, manifest-generated fusion sections, custom LLM fusion sections, and stub LLM sections is covered by Task 3.
- Architecture, pipeline, project status, and task board updates are covered by Task 4.
- Focused tests, full suite, diff check, and clean tree check are covered by Task 5.

Scope check:

- The plan touches one renderer, existing tests, and project documentation.
- The plan does not modify dataclasses, JSON schemas, CLI arguments, Qwen adapter code, LLM contract code, or real-service runbooks.
- The plan is small enough for one implementation cycle.

Type and naming consistency:

- `KnowledgeSection`, `VideoAsset`, and existing helper names match current code.
- New helpers are private functions in `vbook_export.note`.
- Markdown section names match the approved spec: `学习目标`, `回看索引`, `复习问题`, `标签索引`.
- Existing commands use `python -m unittest`, matching the repository guidelines.
