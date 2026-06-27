# Evidence Section Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic adjacent-section merge rules so evidence fusion produces fewer, more readable `KnowledgeSection[]` without relying on Qwen or any LLM.

**Architecture:** Keep the public `build_evidence_sections()` signature and `KnowledgeSection` dataclass unchanged. Internally convert transcript segments into evidence segments, merge adjacent evidence segments conservatively, then render each group into one `KnowledgeSection`.

**Tech Stack:** Python 3.11+ standard library, `dataclasses`, existing vBook dataclasses, `unittest`, existing CLI pipeline.

---

## File Structure

- Modify: `vbook_fusion/sections.py`
  - Update module docstring from placeholder-only wording to evidence-section wording.
  - Add merge threshold constants.
  - Add internal `_EvidenceSegment` dataclass.
  - Refactor `build_evidence_sections()` through evidence segment grouping.
  - Add helpers for semantic heading, frame-id extraction, group merging, and group rendering.
  - Keep `build_placeholder_sections()` unchanged.
- Modify: `tests/test_fusion/test_sections.py`
  - Add failing merge behavior tests before production changes.
  - Keep placeholder tests unchanged.
- Modify: `tests/test_client/test_manifest_cli.py`
  - Add or update CLI assertions only if section counts or titles change in existing fixtures.
- Modify: docs after verification:
  - `docs/00_project/status.md`
  - `docs/30_pipeline/overview.md`
  - `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

---

## Task 1: Add Shared-Frame and Same-Heading Merge Tests

**Files:**
- Modify: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Add shared-frame merge test**

Add this test after `test_build_evidence_sections_uses_transcript_and_visual_evidence`:

```python
    def test_build_evidence_sections_merges_adjacent_segments_with_shared_frame(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=4.0,
                text="先介绍均线多头排列。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=4.5,
                end=8.0,
                text="这里补充成交量放大。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                ocr_text="短线选股条件\n均线多头排列",
                vision_description="一页短线选股条件幻灯片。",
                structured_observations={
                    "topic": "短线选股",
                    "key_points": ["均线多头排列"],
                    "language": "zh-CN",
                },
                confidence=0.9,
                backend="manual-json",
            )
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001", "seg-000002"],
                window_start=0.0,
                window_end=8.0,
            )
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "短线选股")
        self.assertEqual(section.source_timestamps, [0.0, 8.0])
        self.assertIn("讲解：先介绍均线多头排列。 这里补充成交量放大。", section.summary)
        self.assertIn("视觉：一页短线选股条件幻灯片。", section.summary)
        self.assertIn("画面文字：短线选股条件", section.summary)
        self.assertEqual(
            section.image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertIn("讲解：先介绍均线多头排列。", section.key_points)
        self.assertIn("讲解：这里补充成交量放大。", section.key_points)
        self.assertIn("画面文字：短线选股条件\n均线多头排列", section.key_points)
        self.assertIn("视觉描述：一页短线选股条件幻灯片。", section.key_points)
        self.assertIn("主题：短线选股", section.key_points)
        self.assertIn("均线多头排列", section.key_points)
        self.assertEqual(
            section.tags,
            ["evidence", "visual:slide", "has_ocr", "has_image", "lang:zh-CN"],
        )
```

- [ ] **Step 2: Add same-heading merge test**

Add this test after the shared-frame test:

```python
    def test_build_evidence_sections_merges_adjacent_segments_with_same_heading(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=6.0,
                text="第一张图说明买点条件。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=9.0,
                end=14.0,
                text="第二张图继续解释买点条件。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                vision_description="买点条件第一页。",
                structured_observations={"topic": "买点条件"},
                backend="manual-json",
            ),
            VisualAnalysis(
                frame_id="frame-000002",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000002.jpg"),
                vision_description="买点条件第二页。",
                structured_observations={"heading": "买点条件"},
                backend="manual-json",
            ),
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=6.0,
            ),
            TimelineLink(
                frame_id="frame-000002",
                transcript_segment_ids=["seg-000002"],
                window_start=9.0,
                window_end=14.0,
            ),
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "买点条件")
        self.assertEqual(section.source_timestamps, [0.0, 14.0])
        self.assertEqual(
            section.image_refs,
            [
                "outputs/lesson/frames/selected/frame_000001.jpg",
                "outputs/lesson/frames/selected/frame_000002.jpg",
            ],
        )
        self.assertIn("视觉描述：买点条件第一页。", section.key_points)
        self.assertIn("视觉描述：买点条件第二页。", section.key_points)
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections.FusionSectionsTest.test_build_evidence_sections_merges_adjacent_segments_with_shared_frame tests.test_fusion.test_sections.FusionSectionsTest.test_build_evidence_sections_merges_adjacent_segments_with_same_heading
```

Expected: FAIL with assertion failures like:

```text
AssertionError: 2 != 1
```

- [ ] **Step 4: Commit failing tests only if project workflow allows red commits**

Do not commit red tests in this repo. Continue to Task 2 and commit after the implementation turns them green.

---

## Task 2: Implement Visual-Evidence Merge Rules

**Files:**
- Modify: `vbook_fusion/sections.py`
- Test: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Update imports, docstring, constants, and internal dataclass**

At the top of `vbook_fusion/sections.py`, replace:

```python
"""Placeholder knowledge-section construction and writing."""
```

with:

```python
"""Knowledge-section construction and writing."""
```

Add the dataclass import:

```python
from dataclasses import dataclass
```

Add these constants and dataclass after the type imports:

```python
MAX_TOPIC_MERGE_GAP_SECONDS = 30.0
MAX_SHARED_FRAME_MERGE_GAP_SECONDS = 30.0
MAX_SHORT_TEXT_MERGE_GAP_SECONDS = 1.0
MAX_MERGED_TRANSCRIPT_CHARS = 240


@dataclass(frozen=True)
class _EvidenceSegment:
    segment: TranscriptSegment
    evidence_items: tuple[VisualAnalysis, ...]
```

- [ ] **Step 2: Replace `build_evidence_sections()` body**

Replace the current `build_evidence_sections()` implementation with:

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

    evidence_segments = [
        _EvidenceSegment(
            segment=segment,
            evidence_items=tuple(evidence_by_segment_id.get(segment.id, [])),
        )
        for segment in sorted(segments, key=lambda item: (item.start, item.end, item.id))
    ]
    return [_section_from_group(group) for group in _merge_evidence_segments(evidence_segments)]
```

- [ ] **Step 3: Add group merge helpers**

Add these helpers below `_build_visual_evidence_by_segment_id()`:

```python
def _merge_evidence_segments(
    evidence_segments: Sequence[_EvidenceSegment],
) -> list[list[_EvidenceSegment]]:
    groups: list[list[_EvidenceSegment]] = []
    for evidence_segment in evidence_segments:
        if groups and _should_merge_with_group(groups[-1], evidence_segment):
            groups[-1].append(evidence_segment)
            continue
        groups.append([evidence_segment])
    return groups


def _should_merge_with_group(
    group: Sequence[_EvidenceSegment],
    next_item: _EvidenceSegment,
) -> bool:
    gap_seconds = _gap_seconds(group[-1].segment, next_item.segment)
    if _merged_transcript_length([*group, next_item]) > MAX_MERGED_TRANSCRIPT_CHARS:
        return False

    group_heading = _group_semantic_heading(group)
    next_heading = _semantic_heading(next_item.evidence_items)
    if group_heading and next_heading and group_heading != next_heading:
        return False

    group_has_evidence = _group_has_visual_evidence(group)
    next_has_evidence = bool(next_item.evidence_items)

    if _groups_share_frame(group, next_item):
        return gap_seconds <= MAX_SHARED_FRAME_MERGE_GAP_SECONDS
    if group_heading and next_heading and group_heading == next_heading:
        return gap_seconds <= MAX_TOPIC_MERGE_GAP_SECONDS
    if group_has_evidence and next_has_evidence:
        return False
    if not group_has_evidence and not next_has_evidence:
        return gap_seconds <= MAX_SHORT_TEXT_MERGE_GAP_SECONDS
    if group_has_evidence and not next_has_evidence:
        return gap_seconds <= MAX_SHORT_TEXT_MERGE_GAP_SECONDS
    return False


def _gap_seconds(left: TranscriptSegment, right: TranscriptSegment) -> float:
    return max(0.0, right.start - left.end)


def _merged_transcript_length(group: Sequence[_EvidenceSegment]) -> int:
    return len(_combined_transcript_text(item.segment for item in group))


def _combined_transcript_text(segments: Sequence[TranscriptSegment] | Any) -> str:
    return " ".join(segment.text.strip() for segment in segments if segment.text.strip())
```

- [ ] **Step 4: Add visual heading and frame helpers**

Add these helpers below the merge helpers:

```python
def _group_semantic_heading(group: Sequence[_EvidenceSegment]) -> str | None:
    for item in group:
        heading = _semantic_heading(item.evidence_items)
        if heading:
            return heading
    return None


def _semantic_heading(evidence_items: Sequence[VisualAnalysis]) -> str | None:
    for analysis in evidence_items:
        for key in ("topic", "title", "heading"):
            value = analysis.structured_observations.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _group_has_visual_evidence(group: Sequence[_EvidenceSegment]) -> bool:
    return any(item.evidence_items for item in group)


def _groups_share_frame(
    group: Sequence[_EvidenceSegment],
    next_item: _EvidenceSegment,
) -> bool:
    group_frame_ids = {
        analysis.frame_id
        for item in group
        for analysis in item.evidence_items
    }
    next_frame_ids = {analysis.frame_id for analysis in next_item.evidence_items}
    return bool(group_frame_ids.intersection(next_frame_ids))
```

- [ ] **Step 5: Add group rendering helper**

Add this helper above `_section_title()`:

```python
def _section_from_group(group: Sequence[_EvidenceSegment]) -> KnowledgeSection:
    segments = [item.segment for item in group]
    evidence_items = _group_evidence_items(group)
    return KnowledgeSection(
        title=_section_title(segments[0], evidence_items),
        summary=_section_summary(segments, evidence_items),
        source_timestamps=[segments[0].start, segments[-1].end],
        image_refs=_section_image_refs(evidence_items),
        key_points=_section_key_points(segments, evidence_items),
        tags=_section_tags(evidence_items),
    )


def _group_evidence_items(
    group: Sequence[_EvidenceSegment],
) -> list[VisualAnalysis]:
    evidence_items: list[VisualAnalysis] = []
    for item in group:
        for analysis in item.evidence_items:
            if analysis not in evidence_items:
                evidence_items.append(analysis)
    return evidence_items
```

- [ ] **Step 6: Update section title to reuse semantic heading helper**

Replace `_section_title()` with:

```python
def _section_title(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    heading = _semantic_heading(evidence_items)
    if heading:
        return heading
    transcript_title = _compact_text(segment.text, max_chars=18)
    if transcript_title:
        return transcript_title
    return f"Segment {segment.id}"
```

- [ ] **Step 7: Update summary and key point helpers to accept multiple segments**

Replace `_section_summary()` with:

```python
def _section_summary(
    segments: Sequence[TranscriptSegment],
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    parts = []
    transcript_text = _combined_transcript_text(segments)
    if transcript_text:
        parts.append(f"讲解：{transcript_text}")
    for analysis in evidence_items:
        if analysis.vision_description.strip():
            parts.append(f"视觉：{analysis.vision_description.strip()}")
        if analysis.ocr_text.strip():
            parts.append(f"画面文字：{_first_line(analysis.ocr_text.strip())}")
    return " ".join(_unique(parts))
```

Replace `_section_key_points()` with:

```python
def _section_key_points(
    segments: Sequence[TranscriptSegment],
    evidence_items: Sequence[VisualAnalysis],
) -> list[str]:
    points = []
    for segment in segments:
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
            elements = [
                item.strip()
                for item in visible_elements
                if isinstance(item, str) and item.strip()
            ]
            if elements:
                points.append(f"可见元素：{'、'.join(elements)}")
    return _unique(point for point in points if point.strip())
```

- [ ] **Step 8: Run fusion tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
```

Expected:

```text
Ran 7 tests
OK
```

- [ ] **Step 9: Commit visual merge behavior**

```powershell
git add vbook_fusion/sections.py tests/test_fusion/test_sections.py
git commit -m "Merge adjacent evidence sections by visual context"
```

---

## Task 3: Add Short-Transcript and Split-Guard Tests

**Files:**
- Modify: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Add short transcript merge test**

Add this test after the same-heading test:

```python
    def test_build_evidence_sections_merges_short_adjacent_transcript_segments(self) -> None:
        sections = build_evidence_sections(
            segments=[
                TranscriptSegment(
                    id="seg-000001",
                    start=0.0,
                    end=1.2,
                    text="先看定义。",
                ),
                TranscriptSegment(
                    id="seg-000002",
                    start=1.6,
                    end=3.0,
                    text="再看例子。",
                ),
            ]
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "先看定义。")
        self.assertEqual(sections[0].source_timestamps, [0.0, 3.0])
        self.assertEqual(sections[0].summary, "讲解：先看定义。 再看例子。")
        self.assertEqual(
            sections[0].key_points,
            ["讲解：先看定义。", "讲解：再看例子。"],
        )
        self.assertEqual(sections[0].tags, ["evidence"])
```

- [ ] **Step 2: Add split guard test for different headings and long gaps**

Add this test after the short transcript test:

```python
    def test_build_evidence_sections_keeps_different_headings_and_long_gaps_separate(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=3.0,
                text="这里讲短线选股。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=5.0,
                end=8.0,
                text="这里讲实战案例。",
            ),
            TranscriptSegment(
                id="seg-000003",
                start=20.0,
                end=22.0,
                text="间隔较长的新段落。",
            ),
            TranscriptSegment(
                id="seg-000004",
                start=25.0,
                end=27.0,
                text="不会和上一段合并。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                structured_observations={"topic": "短线选股"},
                backend="manual-json",
            ),
            VisualAnalysis(
                frame_id="frame-000002",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000002.jpg"),
                structured_observations={"topic": "实战案例"},
                backend="manual-json",
            ),
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=3.0,
            ),
            TimelineLink(
                frame_id="frame-000002",
                transcript_segment_ids=["seg-000002"],
                window_start=5.0,
                window_end=8.0,
            ),
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 4)
        self.assertEqual([section.title for section in sections], [
            "短线选股",
            "实战案例",
            "间隔较长的新段落。",
            "不会和上一段合并。",
        ])
```

- [ ] **Step 3: Run short transcript test to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections.FusionSectionsTest.test_build_evidence_sections_merges_short_adjacent_transcript_segments
```

Expected before Task 4: FAIL with:

```text
AssertionError: 2 != 1
```

The split guard test may already pass after Task 2. Keep it because it protects the conservative boundary while adding short-text merge.

---

## Task 4: Implement Short-Text Merge and Verify Guards

**Files:**
- Modify: `vbook_fusion/sections.py`
- Test: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Check if Task 2 already includes short-text rule**

If `_should_merge_with_group()` from Task 2 already contains these lines, no production change is needed for this task:

```python
    if not group_has_evidence and not next_has_evidence:
        return gap_seconds <= MAX_SHORT_TEXT_MERGE_GAP_SECONDS
    if group_has_evidence and not next_has_evidence:
        return gap_seconds <= MAX_SHORT_TEXT_MERGE_GAP_SECONDS
```

If those lines are missing, add them before the final `return False`.

- [ ] **Step 2: Run full fusion section tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
```

Expected:

```text
Ran 9 tests
OK
```

- [ ] **Step 3: Commit short-text merge tests and implementation**

If Task 2 already implemented the short-text rule, this commit contains only tests:

```powershell
git add vbook_fusion/sections.py tests/test_fusion/test_sections.py
git commit -m "Cover short evidence section merge rules"
```

If Task 4 added production code, use the same commit command and message.

---

## Task 5: Verify CLI Behavior and Update Assertions If Needed

**Files:**
- Test: `tests/test_client/test_manifest_cli.py`
- Modify only if a test expectation now reflects intentionally merged sections.

- [ ] **Step 1: Run targeted CLI tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_writes_default_mvp_artifacts tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_use_manual_json_visual_analysis tests.test_client.test_manifest_cli.ManifestCliTest.test_manifest_command_can_write_evidence_fusion_sections tests.test_client.test_manifest_cli.ManifestCliTest.test_manifest_command_renders_note_from_fusion_sections
```

Expected: PASS.

- [ ] **Step 2: If CLI tests fail because section count/title changed, inspect the assertion**

Open `tests/test_client/test_manifest_cli.py` and update only expectations that describe the new intended merged output. Do not change CLI code.

Acceptable changes:

```python
self.assertEqual(sections["intent"], "fusion_sections_evidence")
self.assertIn("evidence", sections["sections"][0]["tags"])
```

Do not remove assertions that prove OCR, visual description, image refs, or tags enter `note.md`.

- [ ] **Step 3: Run all CLI manifest tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli
```

Expected:

```text
Ran 20 tests
OK
```

- [ ] **Step 4: Commit CLI test updates only if files changed**

If `git status --short` shows changes in `tests/test_client/test_manifest_cli.py`, commit them:

```powershell
git add tests/test_client/test_manifest_cli.py
git commit -m "Update CLI expectations for merged evidence sections"
```

If no files changed, do not create an empty commit.

---

## Task 6: Update Documentation and Verification Snapshot

**Files:**
- Modify: `docs/00_project/status.md`
- Modify: `docs/30_pipeline/overview.md`
- Modify: `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

- [ ] **Step 1: Update project status wording**

In `docs/00_project/status.md`, replace this bullet:

```text
- Deterministic evidence-based fusion sections from transcript, visual
  analysis, and timeline links.
```

with:

```text
- Deterministic evidence-based fusion sections from transcript, visual
  analysis, and timeline links, including conservative adjacent-section merge.
```

Replace this limitation:

```text
- Fusion sections are deterministic evidence drafts, not final LLM knowledge
  synthesis.
```

with:

```text
- Fusion sections are deterministic evidence drafts with conservative section
  merge, not final LLM knowledge synthesis.
```

- [ ] **Step 2: Update pipeline overview**

In `docs/30_pipeline/overview.md`, update 阶段 7 paragraph to mention conservative adjacent-section merge:

```text
当前本地实现先使用确定性 evidence draft：把 transcript、OCR 文本、图像描述、
结构化视觉观察和时间轴关联转换为可审计的 `KnowledgeSection[]`。它会保留图片引用、
来源时间戳、要点和标签，并对相邻同主题或共享视觉证据的片段做保守合并，但还不是
最终 LLM 知识综合。后续 LLM 融合会在这个稳定 artifact 基础上生成去重后的高质量
知识段落。
```

- [ ] **Step 3: Update stage summary**

In `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`, update the fusion section to mention section merge:

```text
- fusion sections 会吸收 transcript、OCR、视觉描述、结构化观察和图片引用，并对相邻
  同主题或共享视觉证据的片段做保守合并。
```

- [ ] **Step 4: Run final full verification**

Run:

```powershell
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_client.test_manifest_cli
python -m unittest discover
```

Expected:

```text
OK
```

Record the final full-suite test count and update `docs/00_project/status.md` if it changed.

- [ ] **Step 5: Commit docs**

```powershell
git add docs/00_project/status.md docs/30_pipeline/overview.md docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md
git commit -m "Document evidence section merge progress"
```

---

## Final Verification

- [ ] **Step 1: Run full test suite**

```powershell
python -m unittest discover
```

Expected:

```text
OK
```

- [ ] **Step 2: Check git status**

```powershell
git status --short --branch
```

Expected: clean `main` or clean feature branch, depending on execution workspace.

- [ ] **Step 3: Review changed files**

```powershell
git diff --stat origin/main..HEAD
```

Expected: changes limited to:

- `vbook_fusion/sections.py`
- `tests/test_fusion/test_sections.py`
- `tests/test_client/test_manifest_cli.py` only if needed
- the three documentation files from Task 6
- this plan and the design spec if they were not already pushed

- [ ] **Step 4: Push after clean verification**

```powershell
git push origin main
```

Expected: push succeeds without force.

---

## Self-Review

Spec coverage:

- Shared frame merge is covered by Task 1 and Task 2.
- Same semantic heading merge is covered by Task 1 and Task 2.
- Short transcript merge is covered by Task 3 and Task 4.
- Different heading and long-gap split guards are covered by Task 3.
- Output stability for timestamps, summary, image refs, key points, and tags is covered by Task 1 and Task 3.
- CLI compatibility is covered by Task 5.
- Documentation and verification snapshot are covered by Task 6.

Placeholder scan:

- No TBD, TODO, or incomplete implementation steps are present.
- Each code-changing step includes exact code or exact acceptable assertions.
- Each verification step includes the command and expected result.

Type consistency:

- Internal `_EvidenceSegment` uses existing `TranscriptSegment` and `VisualAnalysis`.
- `build_evidence_sections()` keeps its public signature unchanged.
- `KnowledgeSection` construction still uses existing fields only.
- Private helper signatures consistently use `Sequence[...]` and existing dataclass names.
