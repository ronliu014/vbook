# Evidence Fusion Note Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic evidence-based fusion path that turns transcript, visual analysis, timeline links, OCR text, visual descriptions, and structured observations into more useful `KnowledgeSection[]` and `note.md` output without waiting for Qwen service deployment.

**Architecture:** Add `build_evidence_sections()` beside the existing placeholder builder in `vbook_fusion.sections`, keep `KnowledgeSection` unchanged, and route the existing CLI fusion sections path through the new builder. Keep Markdown rendering in `vbook_export.note`, only extending it to display tags.

**Tech Stack:** Python 3.11+ standard library, existing dataclasses, `unittest`, existing vBook CLI and serialization helpers.

---

## File Structure

- Modify: `vbook_fusion/sections.py`
  - Add `build_evidence_sections()`.
  - Add small helper functions for visual evidence indexing, title selection, key point extraction, tag extraction, and de-duplication.
  - Keep `build_placeholder_sections()` available.
  - Make `write_fusion_sections()` write `intent = fusion_sections_evidence` when sections contain an `evidence` tag.
- Modify: `vbook_client/cli.py`
  - Import and call `build_evidence_sections()` for default fusion sections.
- Modify: `vbook_export/note.py`
  - Extend `render_sections_note()` to include tags when present.
- Modify: `tests/test_fusion/test_sections.py`
  - Add evidence fusion tests.
- Modify: `tests/test_export/test_note.py`
  - Add tag rendering assertion.
- Modify: `tests/test_client/test_manifest_cli.py`
  - Update/extend build and manual-json assertions for evidence sections.
- Optional docs after verification:
  - `docs/00_project/status.md`
  - `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

---

## Task 1: Add Evidence Section Builder Tests

**Files:**
- Modify: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Write failing import and evidence section test**

Modify the import:

```python
from vbook_fusion.sections import (
    build_evidence_sections,
    build_placeholder_sections,
    write_fusion_sections,
)
```

Add this test to `FusionSectionsTest`:

```python
    def test_build_evidence_sections_uses_transcript_and_visual_evidence(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=6.0,
                text="这里讲均线多头排列是短线选股条件。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=8.0,
                end=12.0,
                text="后面进入实战案例。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                ocr_text="短线选股条件\n均线多头排列\n成交量放大",
                vision_description="一页讲解短线选股条件的幻灯片。",
                structured_observations={
                    "topic": "短线选股",
                    "key_points": ["均线多头排列", "成交量放大"],
                    "visible_elements": ["标题", "项目符号"],
                    "language": "zh-CN",
                },
                confidence=0.86,
                backend="manual-json",
            )
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=6.0,
            )
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 2)
        first = sections[0]
        self.assertEqual(first.title, "短线选股")
        self.assertIn("这里讲均线多头排列是短线选股条件。", first.summary)
        self.assertIn("视觉：一页讲解短线选股条件的幻灯片。", first.summary)
        self.assertIn("画面文字：短线选股条件", first.summary)
        self.assertEqual(first.source_timestamps, [0.0, 6.0])
        self.assertEqual(
            first.image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertIn("讲解：这里讲均线多头排列是短线选股条件。", first.key_points)
        self.assertIn("画面文字：短线选股条件\n均线多头排列\n成交量放大", first.key_points)
        self.assertIn("视觉描述：一页讲解短线选股条件的幻灯片。", first.key_points)
        self.assertIn("主题：短线选股", first.key_points)
        self.assertIn("均线多头排列", first.key_points)
        self.assertIn("成交量放大", first.key_points)
        self.assertIn("可见元素：标题、项目符号", first.key_points)
        self.assertEqual(
            first.tags,
            ["evidence", "visual:slide", "has_ocr", "has_image", "lang:zh-CN"],
        )
        self.assertEqual(sections[1].title, "后面进入实战案例。")
        self.assertEqual(sections[1].tags, ["evidence"])
```

- [ ] **Step 2: Run test to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections.FusionSectionsTest.test_build_evidence_sections_uses_transcript_and_visual_evidence
```

Expected: FAIL with import error or missing `build_evidence_sections`.

- [ ] **Step 3: Add transcript-only evidence test**

Add this test:

```python
    def test_build_evidence_sections_handles_transcript_without_visuals(self) -> None:
        sections = build_evidence_sections(
            segments=[
                TranscriptSegment(
                    id="seg-000001",
                    start=3.0,
                    end=5.0,
                    text="没有图片时仍然输出讲解主线。",
                )
            ],
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "没有图片时仍然输出讲解主线。")
        self.assertEqual(sections[0].summary, "讲解：没有图片时仍然输出讲解主线。")
        self.assertEqual(sections[0].source_timestamps, [3.0, 5.0])
        self.assertEqual(sections[0].image_refs, [])
        self.assertEqual(sections[0].key_points, ["讲解：没有图片时仍然输出讲解主线。"])
        self.assertEqual(sections[0].tags, ["evidence"])
```

- [ ] **Step 4: Run full fusion section tests to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
```

Expected: FAIL because `build_evidence_sections` is not implemented yet.

---

## Task 2: Implement Evidence Section Builder

**Files:**
- Modify: `vbook_fusion/sections.py`
- Test: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Add import typing support**

Ensure the top of `vbook_fusion/sections.py` contains:

```python
from typing import Any
```

- [ ] **Step 2: Add build_evidence_sections implementation**

Add this function above `build_placeholder_sections()`:

```python
def build_evidence_sections(
    segments: Sequence[TranscriptSegment],
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    timeline_links: Sequence[TimelineLink] | None = None,
) -> list[KnowledgeSection]:
    """Build deterministic evidence sections from transcript and visual context."""
    evidence_by_segment_id = _build_visual_evidence_by_segment_id(
        visual_analyses=visual_analyses or [],
        timeline_links=timeline_links or [],
    )

    sections: list[KnowledgeSection] = []
    for segment in sorted(segments, key=lambda item: (item.start, item.end, item.id)):
        evidence_items = evidence_by_segment_id.get(segment.id, [])
        sections.append(
            KnowledgeSection(
                title=_section_title(segment, evidence_items),
                summary=_section_summary(segment, evidence_items),
                source_timestamps=[segment.start, segment.end],
                image_refs=_section_image_refs(evidence_items),
                key_points=_section_key_points(segment, evidence_items),
                tags=_section_tags(evidence_items),
            )
        )
    return sections
```

- [ ] **Step 3: Add visual evidence helpers**

Add these helpers below `_build_image_refs_by_segment_id()`:

```python
def _build_visual_evidence_by_segment_id(
    visual_analyses: Sequence[VisualAnalysis],
    timeline_links: Sequence[TimelineLink],
) -> dict[str, list[VisualAnalysis]]:
    analysis_by_frame_id = {analysis.frame_id: analysis for analysis in visual_analyses}
    evidence_by_segment_id: dict[str, list[VisualAnalysis]] = {}
    for link in sorted(timeline_links, key=lambda item: item.frame_id):
        analysis = analysis_by_frame_id.get(link.frame_id)
        if analysis is None:
            continue
        for segment_id in link.transcript_segment_ids:
            items = evidence_by_segment_id.setdefault(segment_id, [])
            if analysis not in items:
                items.append(analysis)
    return evidence_by_segment_id
```

Add:

```python
def _section_title(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    for analysis in evidence_items:
        for key in ("topic", "title", "heading"):
            value = analysis.structured_observations.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    transcript_title = _compact_text(segment.text, max_chars=18)
    if transcript_title:
        return transcript_title
    return f"Segment {segment.id}"
```

Add:

```python
def _section_summary(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    parts = []
    transcript_text = segment.text.strip()
    if transcript_text:
        parts.append(f"讲解：{transcript_text}")
    for analysis in evidence_items:
        if analysis.vision_description.strip():
            parts.append(f"视觉：{analysis.vision_description.strip()}")
        if analysis.ocr_text.strip():
            parts.append(f"画面文字：{_first_line(analysis.ocr_text.strip())}")
    return " ".join(_unique(parts))
```

Add:

```python
def _section_image_refs(evidence_items: Sequence[VisualAnalysis]) -> list[str]:
    refs = [analysis.image_path.as_posix() for analysis in evidence_items]
    return _unique(refs)
```

Add:

```python
def _section_key_points(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> list[str]:
    points = []
    if segment.text.strip():
        points.append(f"讲解：{segment.text.strip()}")
    for analysis in evidence_items:
        if analysis.ocr_text.strip():
            points.append(f"画面文字：{analysis.ocr_text.strip()}")
        if analysis.vision_description.strip():
            points.append(f"视觉描述：{analysis.vision_description.strip()}")
        observations = analysis.structured_observations
        topic = observations.get("topic")
        if isinstance(topic, str) and topic.strip():
            points.append(f"主题：{topic.strip()}")
        key_points = observations.get("key_points")
        if isinstance(key_points, list):
            points.extend(item.strip() for item in key_points if isinstance(item, str))
        visible_elements = observations.get("visible_elements")
        if isinstance(visible_elements, list):
            elements = [item.strip() for item in visible_elements if isinstance(item, str) and item.strip()]
            if elements:
                points.append(f"可见元素：{'、'.join(elements)}")
    return _unique(point for point in points if point.strip())
```

Add:

```python
def _section_tags(evidence_items: Sequence[VisualAnalysis]) -> list[str]:
    tags = ["evidence"]
    for analysis in evidence_items:
        tags.append(f"visual:{analysis.visual_type.value}")
        if analysis.ocr_text.strip():
            tags.append("has_ocr")
        tags.append("has_image")
        language = analysis.structured_observations.get("language")
        if isinstance(language, str) and language.strip():
            tags.append(f"lang:{language.strip()}")
    return _unique(tags)
```

Add:

```python
def _compact_text(text: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars]
```

Add:

```python
def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""
```

Add:

```python
def _unique(values: Sequence[str] | Any) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
```

- [ ] **Step 4: Run fusion tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
```

Expected: all fusion section tests pass.

- [ ] **Step 5: Commit**

```powershell
git add vbook_fusion/sections.py tests/test_fusion/test_sections.py
git commit -m "Add evidence-based fusion sections"
```

---

## Task 3: Make Fusion Sections Artifact Intent Accurate

**Files:**
- Modify: `tests/test_fusion/test_sections.py`
- Modify: `vbook_fusion/sections.py`

- [ ] **Step 1: Add failing writer intent test**

Add this test:

```python
    def test_write_fusion_sections_marks_evidence_intent(self) -> None:
        sections = build_evidence_sections(
            segments=[
                TranscriptSegment(id="seg-000001", start=0.0, end=3.0, text="intro")
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs" / "lesson" / "fusion" / "sections.json"

            written = write_fusion_sections(sections, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(data["intent"], "fusion_sections_evidence")
        self.assertEqual(data["section_count"], 1)
        self.assertEqual(data["sections"][0]["tags"], ["evidence"])
```

- [ ] **Step 2: Run test to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections.FusionSectionsTest.test_write_fusion_sections_marks_evidence_intent
```

Expected: FAIL because writer still emits `fusion_sections_placeholder`.

- [ ] **Step 3: Implement intent detection**

Modify `write_fusion_sections()` in `vbook_fusion/sections.py`.

Replace:

```python
"intent": "fusion_sections_placeholder",
```

with:

```python
"intent": _fusion_sections_intent(sections),
```

Add helper:

```python
def _fusion_sections_intent(sections: Sequence[KnowledgeSection]) -> str:
    if any("evidence" in section.tags for section in sections):
        return "fusion_sections_evidence"
    return "fusion_sections_placeholder"
```

- [ ] **Step 4: Run fusion tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add vbook_fusion/sections.py tests/test_fusion/test_sections.py
git commit -m "Mark evidence fusion section artifacts"
```

---

## Task 4: Render Tags in Notes

**Files:**
- Modify: `tests/test_export/test_note.py`
- Modify: `vbook_export/note.py`

- [ ] **Step 1: Add failing note tag assertion**

In `test_render_sections_note_uses_knowledge_sections`, after existing key point assertions, add:

```python
        self.assertIn("Tags:", markdown)
        self.assertIn("- placeholder", markdown)
```

- [ ] **Step 2: Run note test to verify RED**

Run:

```powershell
python -m unittest tests.test_export.test_note.NoteExportTest.test_render_sections_note_uses_knowledge_sections
```

Expected: FAIL because tags are not rendered yet.

- [ ] **Step 3: Render tags**

In `render_sections_note()` in `vbook_export/note.py`, after key point rendering and before `lines.append("")`, add:

```python
        if section.tags:
            lines.extend(["", "Tags:"])
            lines.extend(f"- {tag}" for tag in section.tags)
```

- [ ] **Step 4: Run note tests**

Run:

```powershell
python -m unittest tests.test_export.test_note
```

Expected: all note tests pass.

- [ ] **Step 5: Commit**

```powershell
git add vbook_export/note.py tests/test_export/test_note.py
git commit -m "Render knowledge section tags in notes"
```

---

## Task 5: Wire Evidence Sections Into CLI Pipeline

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [ ] **Step 1: Update build default artifact expectation**

In `test_build_command_writes_default_mvp_artifacts`, after loading `sections_exists`, read sections JSON:

```python
            sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )
```

After existing assertions, add:

```python
        self.assertEqual(sections["intent"], "fusion_sections_evidence")
        self.assertEqual(sections["sections"][0]["tags"], ["evidence", "visual:other", "has_image"])
```

This expected tag list assumes placeholder visual analysis for selected frame has no OCR and visual type `other`.

- [ ] **Step 2: Update manual-json visual note expectation**

In `test_build_command_can_use_manual_json_visual_analysis`, add assertions:

```python
        self.assertEqual(sections["intent"], "fusion_sections_evidence")
        self.assertIn("画面文字：buy point", sections["sections"][0]["key_points"])
        self.assertIn("视觉描述：A slide about a buy point.", sections["sections"][0]["key_points"])
        self.assertIn("visual:slide", sections["sections"][0]["tags"])
        self.assertIn("has_ocr", sections["sections"][0]["tags"])
        self.assertIn("buy point", note)
        self.assertIn("Tags:", note)
        self.assertIn("- visual:slide", note)
```

- [ ] **Step 3: Run CLI tests to verify RED**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_writes_default_mvp_artifacts tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_use_manual_json_visual_analysis
```

Expected: FAIL because CLI still calls `build_placeholder_sections()`.

- [ ] **Step 4: Import evidence builder**

In `vbook_client/cli.py`, replace:

```python
from vbook_fusion.sections import build_placeholder_sections, write_fusion_sections
```

with:

```python
from vbook_fusion.sections import build_evidence_sections, write_fusion_sections
```

- [ ] **Step 5: Call evidence builder**

In `_run_manifest_pipeline()`, replace:

```python
        fusion_sections = build_placeholder_sections(
            segments=segments,
            visual_analyses=visual_analyses,
            timeline_links=timeline_links,
        )
```

with:

```python
        fusion_sections = build_evidence_sections(
            segments=segments,
            visual_analyses=visual_analyses,
            timeline_links=timeline_links,
        )
```

- [ ] **Step 6: Run targeted CLI tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_writes_default_mvp_artifacts tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_use_manual_json_visual_analysis tests.test_client.test_manifest_cli.ManifestCliTest.test_manifest_command_can_write_fusion_sections_placeholder tests.test_client.test_manifest_cli.ManifestCliTest.test_manifest_command_renders_note_from_fusion_sections
```

Expected: tests pass after updating expected intent/title where needed.

- [ ] **Step 7: Commit**

```powershell
git add vbook_client/cli.py tests/test_client/test_manifest_cli.py
git commit -m "Use evidence fusion sections in CLI"
```

---

## Task 6: Update Documentation and Verification Snapshot

**Files:**
- Modify: `docs/00_project/status.md`
- Modify: `docs/30_pipeline/README.md`
- Modify: `docs/30_pipeline/overview.md`
- Modify: `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

- [ ] **Step 1: Update project status**

In `docs/00_project/status.md`, update:

```text
- Deterministic placeholder fusion sections.
```

to:

```text
- Deterministic evidence-based fusion sections from transcript, visual analysis, and timeline links.
```

Update the partial status line:

```text
- Fusion sections are deterministic placeholders, not final knowledge synthesis.
```

to:

```text
- Fusion sections are deterministic evidence drafts, not final LLM knowledge synthesis.
```

- [ ] **Step 2: Update pipeline docs**

In `docs/30_pipeline/README.md`, change the Fusion sections row from placeholder wording to evidence draft wording.

In `docs/30_pipeline/overview.md`, update 阶段 7 to say current local implementation is deterministic evidence drafting, while future LLM fusion remains planned.

- [ ] **Step 3: Update stage summary**

In `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`, add a short note under P4 or current status that evidence-based fusion has now been started or completed depending on implementation state.

- [ ] **Step 4: Run full verification**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

Expected: all tests pass. Record the final full-suite count and update `docs/00_project/status.md` if the count changed.

- [ ] **Step 5: Commit docs**

```powershell
git add docs/00_project/status.md docs/30_pipeline/README.md docs/30_pipeline/overview.md docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md
git commit -m "Document evidence fusion progress"
```

---

## Final Verification

- [ ] **Step 1: Run full test suite**

```powershell
python -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 2: Check Git status**

```powershell
git status --short --branch
```

Expected: clean working tree on feature branch.

- [ ] **Step 3: Review diff against main**

```powershell
git diff --stat main..HEAD
```

Expected: only fusion, note, CLI tests, and documentation files changed.

---

## Self-Review

Spec coverage:

- Evidence builder covered by Tasks 1-2.
- Artifact intent covered by Task 3.
- Note tag rendering covered by Task 4.
- CLI integration covered by Task 5.
- Documentation and verification covered by Task 6.

Placeholder scan:

- No TBD/TODO placeholders are required for implementation.
- All commands and expected results are explicit.

Type consistency:

- Uses existing `KnowledgeSection`, `TranscriptSegment`, `VisualAnalysis`, and `TimelineLink`.
- Does not change dataclass fields.
- Keeps `write_fusion_sections()` public signature unchanged.

---

Plan complete. Recommended execution option:

1. Subagent-Driven - dispatch a fresh subagent per task, with review between tasks.
2. Inline Execution - execute tasks in this session with checkpoints.
