# Expert Note Markdown Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `note.md` rendered from `KnowledgeSection[]` into a first-version expert course-note Markdown template while preserving the existing fusion and LLM contracts.

**Architecture:** Keep `KnowledgeSection` as the only input model for section-aware note export. Rewrite `vbook_export.note.render_sections_note()` and add small private formatting helpers; then update unit and CLI integration tests to assert the new Chinese note structure without changing CLI flags, manifest schema, fusion sections, or LLM response parsing.

**Tech Stack:** Python 3.11 standard library, existing vBook dataclasses, Markdown string rendering, `unittest`.

---

## File Structure

- Modify: `tests/test_export/test_note.py`
  - Adds failing tests for the new expert-note Markdown structure and empty-field behavior.
- Modify: `vbook_export/note.py`
  - Replaces the current engineering-oriented `Knowledge Sections` renderer with the expert-note template.
  - Adds private helpers for time-range formatting, section appending, and tag formatting.
- Modify: `tests/test_client/test_manifest_cli.py`
  - Updates existing CLI assertions that still expect `## Knowledge Sections`, unnumbered headings, and `Tags:`.
- Modify: `docs/00_project/status.md`
  - Records that `note.md` now has a first-version expert-note template.
- Modify: `docs/20_architecture/output-contracts.md`
  - Documents the new `note.md` section structure.
- Modify: `docs/30_pipeline/overview.md`
  - Updates export-stage wording to mention the expert-note Markdown template.

No new public API, no new artifact, no schema migration, no model call, and no dependency is introduced.

---

## Task 1: Add Failing Renderer Tests

**Files:**
- Modify: `tests/test_export/test_note.py`
- Test: `tests/test_export/test_note.py`

- [ ] **Step 1: Replace the current section renderer unit test**

In `tests/test_export/test_note.py`, replace `test_render_sections_note_uses_knowledge_sections` with:

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
                tags=["llm", "final"],
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
        self.assertIn("## 核心结论", markdown)
        self.assertIn("- Intro", markdown)
        self.assertIn("- Case detail", markdown)
        self.assertIn("## 知识结构", markdown)
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

- [ ] **Step 2: Add empty-field behavior test**

Append this test in `NoteExportTest`:

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
        self.assertNotIn("## 核心结论", empty_markdown)
        self.assertNotIn("## 知识结构", empty_markdown)

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

        self.assertIn("### 1. Sparse", sparse_markdown)
        self.assertIn("暂无摘要。", sparse_markdown)
        self.assertIn("**证据与回看**", sparse_markdown)
        self.assertIn("- 时间：未知", sparse_markdown)
        self.assertNotIn("**关键要点**", sparse_markdown)
        self.assertNotIn("- 图片：", sparse_markdown)
        self.assertNotIn("**元数据**", sparse_markdown)
        self.assertNotIn("(empty)", sparse_markdown)
```

- [ ] **Step 3: Run focused renderer tests to verify RED**

Run:

```powershell
python -m unittest tests.test_export.test_note
```

Expected: FAIL because the current renderer still outputs `## Course`, `## Knowledge Sections`, unnumbered `###` headings, and `Tags:`.

---

## Task 2: Implement Expert Note Renderer

**Files:**
- Modify: `vbook_export/note.py`
- Test: `tests/test_export/test_note.py`

- [ ] **Step 1: Replace `render_sections_note()`**

In `vbook_export/note.py`, replace the full body of `render_sections_note()` with:

```python
def render_sections_note(
    video: VideoAsset,
    sections: Sequence[KnowledgeSection],
) -> str:
    """Render a readable expert course note from fused knowledge sections."""
    section_list = sorted(sections, key=_section_sort_key)
    title = video.lesson_title or video.id
    course_title = video.course_title or ""
    time_range = _format_course_time_range(section_list)

    lines = [
        f"# {title}",
        "",
        "## 课程信息",
        "",
        f"- 课程：{course_title}",
        f"- 课节：{title}",
        f"- 视频：{video.path}",
        f"- 知识段落：{len(section_list)}",
        f"- 时间范围：{time_range}",
        "",
        "## 课程总览",
        "",
    ]

    if not section_list:
        lines.append("当前没有可导出的知识段落。")
        return "\n".join(lines).rstrip() + "\n"

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

    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 2: Replace `_format_section_source()`**

In `vbook_export/note.py`, replace `_format_section_source()` with:

```python
def _format_section_source(section: KnowledgeSection) -> str:
    return _format_timestamps(section.source_timestamps)
```

- [ ] **Step 3: Add private helper functions**

In `vbook_export/note.py`, add these helpers after `_format_section_source()`:

```python
def _format_course_time_range(sections: Sequence[KnowledgeSection]) -> str:
    timestamps = [
        timestamp
        for section in sections
        for timestamp in section.source_timestamps
    ]
    return _format_timestamps(timestamps)


def _format_timestamps(timestamps: Sequence[float]) -> str:
    if not timestamps:
        return "未知"
    sorted_timestamps = sorted(timestamps)
    if len(sorted_timestamps) == 1:
        return f"{sorted_timestamps[0]:.2f}s"
    return f"{sorted_timestamps[0]:.2f}s - {sorted_timestamps[-1]:.2f}s"


def _append_expert_section(
    lines: list[str],
    index: int,
    section: KnowledgeSection,
) -> None:
    lines.extend(
        [
            f"### {index}. {section.title}",
            "",
            "**讲解摘要**",
            "",
            section.summary or "暂无摘要。",
            "",
        ]
    )

    if section.key_points:
        lines.extend(["**关键要点**", ""])
        lines.extend(f"- {point}" for point in section.key_points)
        lines.append("")

    lines.extend(
        [
            "**证据与回看**",
            "",
            f"- 时间：{_format_section_source(section)}",
        ]
    )
    lines.extend(f"- 图片：{image_ref}" for image_ref in section.image_refs)
    lines.append("")

    if section.tags:
        lines.extend(
            [
                "**元数据**",
                "",
                f"- 标签：{_format_tags(section.tags)}",
                "",
            ]
        )


def _format_tags(tags: Sequence[str]) -> str:
    return ", ".join(tags)
```

- [ ] **Step 4: Run focused renderer tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_export.test_note
```

Expected: PASS. Existing placeholder-note tests continue to pass because `render_placeholder_note()` is unchanged.

- [ ] **Step 5: Commit renderer implementation**

Run:

```powershell
git add vbook_export/note.py tests/test_export/test_note.py
git commit -m "Render expert note Markdown from sections"
```

---

## Task 3: Update CLI Integration Assertions

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Update build command note assertions**

In `test_build_command_writes_manifest_note_and_fusion_outputs`, replace:

```python
        self.assertIn("## Knowledge Sections", note)
```

with:

```python
        self.assertIn("## 课程信息", note)
        self.assertIn("## 课程总览", note)
        self.assertIn("## 核心结论", note)
        self.assertIn("## 知识结构", note)
```

- [ ] **Step 2: Update manual-json visual note assertions**

In `test_build_command_can_use_manual_json_visual_analysis`, replace:

```python
        self.assertIn("Tags:", note)
        self.assertIn("- visual:slide", note)
```

with:

```python
        self.assertIn("**元数据**", note)
        self.assertIn("标签：evidence, visual:slide, has_ocr", note)
```

- [ ] **Step 3: Update manifest fusion note assertions**

In `test_manifest_command_renders_note_from_fusion_sections`, replace:

```python
        self.assertIn("## Knowledge Sections", note)
        self.assertIn("### intro", note)
        self.assertIn("intro", note)
        self.assertIn("frame_000001.jpg", note)
        self.assertIn("Tags:", note)
        self.assertIn("- evidence", note)
        self.assertIn("- visual:other", note)
```

with:

```python
        self.assertIn("## 课程信息", note)
        self.assertIn("## 课程总览", note)
        self.assertIn("## 核心结论", note)
        self.assertIn("## 知识结构", note)
        self.assertIn("### 1. intro", note)
        self.assertIn("intro", note)
        self.assertIn("frame_000001.jpg", note)
        self.assertIn("**元数据**", note)
        self.assertIn("标签：evidence, visual:other, has_image", note)
```

- [ ] **Step 4: Update LLM fusion note assertion**

In `test_build_command_can_run_llm_fusion_external_command`, replace:

```python
        self.assertIn("### LLM refined intro", note)
```

with:

```python
        self.assertIn("## 知识结构", note)
        self.assertIn("### 1. LLM refined intro", note)
```

Keep the existing assertion:

```python
        self.assertIn("LLM summary from evidence.", note)
```

- [ ] **Step 5: Run focused CLI tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli
```

Expected: PASS.

- [ ] **Step 6: Run note and CLI suites together**

Run:

```powershell
python -m unittest tests.test_export.test_note tests.test_client.test_manifest_cli
```

Expected: PASS.

- [ ] **Step 7: Commit CLI test updates**

Run:

```powershell
git add tests/test_client/test_manifest_cli.py
git commit -m "Update CLI note assertions for expert template"
```

---

## Task 4: Update Documentation

**Files:**
- Modify: `docs/00_project/status.md`
- Modify: `docs/20_architecture/output-contracts.md`
- Modify: `docs/30_pipeline/overview.md`

- [ ] **Step 1: Update project status**

In `docs/00_project/status.md`, under "What Works Now", replace:

```text
- Markdown note export from transcript or fusion sections.
```

with:

```text
- Markdown note export from transcript or fusion sections, including a
  first-version expert-note template for section-based notes.
```

In "What Is Still Placeholder or Partial", replace:

```text
- `note.md` is structurally useful, but not yet a polished expert-level course
  note.
```

with:

```text
- `note.md` has a first-version expert-note structure, but review questions,
  glossary, learning objectives, and multi-format exports are still future work.
```

- [ ] **Step 2: Update output contracts**

In `docs/20_architecture/output-contracts.md`, replace the current "Markdown 笔记" paragraph:

```text
`note.md` 是面向用户阅读的最终产物。它应包含课程元数据、章节摘要、关键知识点、图片引用和来源时间戳。
```

with:

```text
`note.md` 是面向用户阅读的最终产物。section-based note 使用第一版专家笔记结构：
`课程信息`、`课程总览`、`核心结论` 和 `知识结构`。每个知识段落保留讲解摘要、关键要点、来源时间戳、图片引用和 tags，确保用户阅读时仍可回看证据。
```

- [ ] **Step 3: Update pipeline overview**

In `docs/30_pipeline/overview.md`, replace the final stage 8 paragraph:

```text
导出双核心产物：`note.md` 面向用户阅读，`manifest.json` 面向机器复跑和后续知识库。同步保存图片素材、转写记录、视觉分析 JSON 和融合结果。最终笔记中的每个重点都应能追溯到原始视频时间点和相关图片。
```

with:

```text
导出双核心产物：`note.md` 面向用户阅读，`manifest.json` 面向机器复跑和后续知识库。同步保存图片素材、转写记录、视觉分析 JSON 和融合结果。section-based `note.md` 使用第一版专家笔记 Markdown 模板组织 `课程信息`、`课程总览`、`核心结论` 和 `知识结构`，并保留每个重点对应的原始视频时间点、相关图片和 tags。
```

- [ ] **Step 4: Run documentation checks**

Run:

```powershell
git diff --check
rg -n "占位未完成" docs/00_project/status.md docs/20_architecture/output-contracts.md docs/30_pipeline/overview.md
```

Expected:

- `git diff --check` exits 0 with no output.
- `rg` exits 1 with no matches.

- [ ] **Step 5: Commit documentation updates**

Run:

```powershell
git add docs/00_project/status.md docs/20_architecture/output-contracts.md docs/30_pipeline/overview.md
git commit -m "Document expert note Markdown template"
```

---

## Task 5: Full Verification and Push

**Files:**
- All changed files from Tasks 1-4.

- [ ] **Step 1: Run focused verification**

Run:

```powershell
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
```

Expected: each command exits 0 with `OK`.

- [ ] **Step 2: Run full suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits 0 with `OK`.

- [ ] **Step 3: Run diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 4: Check git status**

Run:

```powershell
git status --short --branch
```

Expected: clean branch with local commits ahead of `origin/main` before push.

- [ ] **Step 5: Push to main**

Run:

```powershell
git push origin main
```

Expected: push updates `main -> main` without force.

- [ ] **Step 6: Verify remote alignment**

Run:

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline -1
```

Expected:

- `git status --short --branch` prints `## main...origin/main`.
- `git rev-parse HEAD` and `git rev-parse origin/main` print the same commit hash.
- `git log --oneline -1` shows the last commit from this implementation stage.

---

## Self-Review

Spec coverage:

- The new `课程信息`、`课程总览`、`核心结论` and `知识结构` layout is covered by Tasks 1-2.
- Section summary, key points, source timestamps, image refs, and tags are covered by Tasks 1-3.
- Empty sections, empty summary, empty key points, empty image refs, and empty tags are covered by Task 1.
- No `KnowledgeSection`, LLM contract, fusion artifact, manifest schema, or CLI parameter changes are included.
- Documentation updates are covered by Task 4.
- Full verification and remote alignment are covered by Task 5.

Placeholder scan:

- The plan contains concrete test methods, implementation snippets, commands, and expected outcomes.
- No task requires inventing a new public API.
- No task depends on generated content from an external model or network service.

Type consistency:

- `render_sections_note(video: VideoAsset, sections: Sequence[KnowledgeSection]) -> str` remains unchanged.
- Private helpers only accept `Sequence[KnowledgeSection]`, `Sequence[float]`, `list[str]`, `int`, and `KnowledgeSection`.
- Tests keep using existing dataclasses from `vbook_common.types`.
