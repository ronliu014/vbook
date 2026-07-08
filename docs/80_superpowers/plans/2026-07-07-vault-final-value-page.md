# Deprecated: Vault Final Value Page Implementation Plan

> Status: deprecated on 2026-07-07.
>
> This plan was implemented as an intermediate preview-quality improvement, but
> it should not guide new development. The user review showed that the resulting
> `enhancement.md` remained too verbose and did not preserve vtext's superior
> correction, summarization, heading, and emphasis choices.
>
> Keep this file only as historical implementation context for scene grouping
> and final-value image selection. New work must follow the vtext-first
> direction in
> [../specs/2026-07-07-vtext-first-vault-augmentation-design.md](../specs/2026-07-07-vtext-first-vault-augmentation-design.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `vault-preview` so online-course visual enhancement renders scene-level final-value pages instead of repeating the same image across adjacent transcript sections.

**Architecture:** Keep the change in `vbook_export/vault_preview.py`. Treat the source vault as read-only, create a staged workcopy for generated or modified notes, build preview-only scene grouping from existing `fusion/sections.json` and `vision/analysis.json`, select one primary final-value frame per scene, render scene-level Markdown, and add preview manifest metrics. Do not change vtext, Qwen service contracts, core fusion, or vault-write behavior.

**Tech Stack:** Python 3.13, standard library dataclasses/pathlib/json/shutil, `unittest`, existing vBook `PreviewSources` and `write_preview_package` APIs.

---

## File Structure

- Modify: `tests/test_export/test_vault_preview.py`
  - Add focused red-green tests for scene grouping, final-value frame selection, failed-frame exclusion, and manifest metrics.
  - Reuse `PreviewSources` fixtures with small in-memory JSON-like dictionaries.

- Modify: `vbook_export/vault_preview.py`
  - Add preview-only `PreviewScene` and `PreviewMetrics` dataclasses.
  - Add staged workcopy metadata so preview output clearly distinguishes source
    vault files from modified copies.
  - Add helpers to group adjacent sections into scenes.
  - Add helpers to select a primary final-value image.
  - Change `render_enhancement_markdown()` to render scenes instead of raw sections.
  - Change `write_preview_package()` to include scene metrics in `manifest.json`.

- Use existing docs:
  - Spec: `docs/80_superpowers/specs/2026-07-07-vault-final-value-page-design.md`
  - Progress context: `docs/70_progress/2026-07-07-real-vtext-qwen-vault-preview.md`

---

### Task 1: Add Red Tests for Scene-Level Rendering

**Files:**
- Modify: `tests/test_export/test_vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Add helper fixture functions for scene rendering**

Append these helper functions below `_preview_sources_for_render()`:

```python
def _scene_preview_sources() -> PreviewSources:
    first_image = "outputs/demo/frames/selected/frame_000001.jpg"
    final_image = "outputs/demo/frames/selected/frame_000002.jpg"
    return PreviewSources(
        vault_note_path=Path("F:/vault/20_Learning/投资训练营/demo.md"),
        lesson_output_dir=Path("outputs/demo"),
        vault_note_markdown="# Existing Note\n\n纯文本笔记。",
        manifest={"stage_status": {"vision_analysis": "done"}},
        vision={
            "analysis_count": 2,
            "analyses": [
                {
                    "frame_id": "frame-000001",
                    "image_path": first_image,
                    "timestamp": 60.0,
                    "ocr_text": "构建股票池之前的准备",
                    "vision_description": "板书刚开始，只有标题。",
                    "structured_observations": {
                        "topic": "构建股票池的准备条件"
                    },
                },
                {
                    "frame_id": "frame-000002",
                    "image_path": final_image,
                    "timestamp": 180.0,
                    "ocr_text": "构建股票池之前的准备\n1、聚焦龙头\n2、近期热点\n3、频繁涨停",
                    "vision_description": "完成态PPT页面，包含股票池筛选清单。",
                    "structured_observations": {
                        "topic": "构建股票池的准备条件"
                    },
                },
            ],
        },
        sections={
            "sections": [
                {
                    "title": "构建股票池之前的准备",
                    "summary": "讲师开始说明股票池需要层层筛选。",
                    "source_timestamps": [0.0, 90.0],
                    "image_refs": [first_image],
                    "key_points": ["讲解：股票池不是越多越好"],
                    "tags": ["evidence", "visual:slide"],
                },
                {
                    "title": "构建股票池之前的准备",
                    "summary": "讲师补全股票池筛选条件。",
                    "source_timestamps": [90.0, 210.0],
                    "image_refs": [final_image],
                    "key_points": ["讲解：必须聚焦龙头", "画面文字：近期热点"],
                    "tags": ["evidence", "visual:slide", "has_ocr"],
                },
            ]
        },
    )
```

- [ ] **Step 2: Add failing test for final-value primary image selection**

Add this method to `VaultPreviewTest`:

```python
    def test_render_groups_scene_and_uses_latest_final_value_image(self) -> None:
        sources = _scene_preview_sources()

        markdown = render_enhancement_markdown(sources, image_prefix="images")

        self.assertEqual(markdown.count("### 构建股票池之前的准备"), 1)
        self.assertNotIn("![frame-000001](images/frame_000001.jpg)", markdown)
        self.assertIn("![frame-000002](images/frame_000002.jpg)", markdown)
        self.assertIn("完成态画面", markdown)
        self.assertIn("完成态PPT页面，包含股票池筛选清单。", markdown)
        self.assertIn("股票池不是越多越好", markdown)
        self.assertIn("必须聚焦龙头", markdown)
```

- [ ] **Step 3: Run the focused test and verify it fails**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_render_groups_scene_and_uses_latest_final_value_image
```

Expected: FAIL because current rendering creates two `### 构建股票池之前的准备` sections and still renders `frame_000001.jpg`.

---

### Task 2: Implement Preview Scene Grouping and Final-Value Frame Selection

**Files:**
- Modify: `vbook_export/vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Add preview dataclasses**

Add these dataclasses after `PreviewPackage`:

```python
@dataclass(frozen=True)
class PreviewScene:
    title: str
    start_timestamp: float | None
    end_timestamp: float | None
    sections: list[dict[str, Any]]
    image_refs: list[str]
    primary_image_ref: str | None
    key_points: list[str]
    summary: str


@dataclass(frozen=True)
class PreviewMetrics:
    scene_count: int
    rendered_primary_image_count: int
    omitted_repeated_image_count: int
```

- [ ] **Step 2: Replace raw section rendering with scene rendering**

Change `render_enhancement_markdown()` so the loop becomes:

```python
    analyses_by_image = _analyses_by_image_path(sources.vision)
    scenes = build_preview_scenes(sources, analyses_by_image)
    for scene in scenes:
        lines.extend(_render_scene(scene, analyses_by_image, image_prefix))
```

- [ ] **Step 3: Add `build_preview_scenes()`**

Add this function before `_render_section()`:

```python
def build_preview_scenes(
    sources: PreviewSources,
    analyses_by_image: dict[str, dict[str, Any]] | None = None,
) -> list[PreviewScene]:
    analysis_lookup = analyses_by_image or _analyses_by_image_path(sources.vision)
    scenes: list[list[dict[str, Any]]] = []
    for section in sources.sections.get("sections", []):
        if not isinstance(section, dict):
            continue
        if scenes and _sections_belong_to_same_scene(
            scenes[-1][-1],
            section,
            analysis_lookup,
        ):
            scenes[-1].append(section)
        else:
            scenes.append([section])
    return [_preview_scene_from_sections(group, analysis_lookup) for group in scenes]
```

- [ ] **Step 4: Add scene grouping helpers**

Add these helpers below `build_preview_scenes()`:

```python
def _sections_belong_to_same_scene(
    current: dict[str, Any],
    next_section: dict[str, Any],
    analyses_by_image: dict[str, dict[str, Any]],
) -> bool:
    current_refs = set(_section_image_refs(current))
    next_refs = set(_section_image_refs(next_section))
    if current_refs.intersection(next_refs):
        return True
    current_topic = _section_visual_topic(current, analyses_by_image)
    next_topic = _section_visual_topic(next_section, analyses_by_image)
    if current_topic and current_topic == next_topic:
        return True
    return _normalized_title(current) == _normalized_title(next_section)


def _section_visual_topic(
    section: dict[str, Any],
    analyses_by_image: dict[str, dict[str, Any]],
) -> str:
    for ref in _section_image_refs(section):
        analysis = analyses_by_image.get(ref) or analyses_by_image.get(Path(ref).name)
        if not analysis:
            continue
        observations = analysis.get("structured_observations")
        if not isinstance(observations, dict):
            continue
        topic = observations.get("topic")
        if isinstance(topic, str) and topic.strip():
            return " ".join(topic.split())
    return ""


def _normalized_title(section: dict[str, Any]) -> str:
    title = str(section.get("title") or "")
    return " ".join(title.split())
```

- [ ] **Step 5: Add scene construction helpers**

Add these helpers after the grouping helpers:

```python
def _preview_scene_from_sections(
    sections: list[dict[str, Any]],
    analyses_by_image: dict[str, dict[str, Any]],
) -> PreviewScene:
    image_refs = _unique(
        ref
        for section in sections
        for ref in _section_image_refs(section)
    )
    primary_image_ref = _select_primary_image_ref(image_refs, analyses_by_image)
    title = _scene_title(sections)
    return PreviewScene(
        title=title,
        start_timestamp=_scene_start(sections),
        end_timestamp=_scene_end(sections),
        sections=sections,
        image_refs=image_refs,
        primary_image_ref=primary_image_ref,
        key_points=_scene_key_points(sections),
        summary=_scene_summary(sections),
    )


def _section_image_refs(section: dict[str, Any]) -> list[str]:
    image_refs = section.get("image_refs")
    if not isinstance(image_refs, list):
        return []
    return [ref for ref in image_refs if isinstance(ref, str) and ref.strip()]


def _scene_title(sections: list[dict[str, Any]]) -> str:
    for section in sections:
        title = str(section.get("title") or "").strip()
        if title:
            return title
    return "未命名知识点"


def _scene_summary(sections: list[dict[str, Any]]) -> str:
    summaries = []
    for section in sections:
        summary = str(section.get("summary") or "").strip()
        if summary:
            summaries.append(summary)
    return " ".join(_unique(summaries))


def _scene_key_points(sections: list[dict[str, Any]]) -> list[str]:
    points = []
    for section in sections:
        key_points = section.get("key_points")
        if not isinstance(key_points, list):
            continue
        points.extend(point for point in key_points if isinstance(point, str))
    return _unique(point.strip() for point in points if point.strip())
```

- [ ] **Step 6: Add timestamp and primary-image selection helpers**

Add these helpers after `_scene_key_points()`:

```python
def _scene_start(sections: list[dict[str, Any]]) -> float | None:
    values = [
        _source_timestamp(section, 0)
        for section in sections
        if _source_timestamp(section, 0) is not None
    ]
    return min(values) if values else None


def _scene_end(sections: list[dict[str, Any]]) -> float | None:
    values = [
        _source_timestamp(section, 1)
        for section in sections
        if _source_timestamp(section, 1) is not None
    ]
    return max(values) if values else None


def _source_timestamp(section: dict[str, Any], index: int) -> float | None:
    timestamps = section.get("source_timestamps")
    if not isinstance(timestamps, list) or len(timestamps) <= index:
        return None
    value = timestamps[index]
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _select_primary_image_ref(
    image_refs: list[str],
    analyses_by_image: dict[str, dict[str, Any]],
) -> str | None:
    if not image_refs:
        return None
    successful = [
        ref
        for ref in image_refs
        if not _analysis_has_qwen_error(_analysis_for_ref(ref, analyses_by_image))
    ]
    candidates = successful or image_refs
    return max(
        candidates,
        key=lambda ref: _image_selection_key(ref, analyses_by_image),
    )


def _analysis_for_ref(
    ref: str,
    analyses_by_image: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    return analyses_by_image.get(ref) or analyses_by_image.get(Path(ref).name)


def _analysis_has_qwen_error(analysis: dict[str, Any] | None) -> bool:
    if not analysis:
        return False
    observations = analysis.get("structured_observations")
    if not isinstance(observations, dict):
        return False
    service = observations.get("qwen_service")
    return isinstance(service, dict) and service.get("status") == "error"


def _image_selection_key(
    ref: str,
    analyses_by_image: dict[str, dict[str, Any]],
) -> tuple[float, int, int, str]:
    analysis = _analysis_for_ref(ref, analyses_by_image)
    timestamp = _analysis_timestamp(analysis)
    ocr = str(analysis.get("ocr_text") or "") if analysis else ""
    return (timestamp, 1 if ocr.strip() else 0, len(ocr), ref)


def _analysis_timestamp(analysis: dict[str, Any] | None) -> float:
    if not analysis:
        return 0.0
    value = analysis.get("timestamp")
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    frame_id = analysis.get("frame_id")
    if isinstance(frame_id, str):
        digits = "".join(ch for ch in frame_id if ch.isdigit())
        if digits:
            return float(int(digits))
    return 0.0
```

- [ ] **Step 7: Add scene rendering helper**

Add this helper before `_render_section()` and keep `_render_section()` in place until all old tests are updated or still passing:

```python
def _render_scene(
    scene: PreviewScene,
    analyses_by_image: dict[str, dict[str, Any]],
    image_prefix: str,
) -> list[str]:
    lines = ["### " + scene.title, ""]
    if scene.summary:
        lines.extend([scene.summary, ""])
    if scene.primary_image_ref:
        image_name = Path(scene.primary_image_ref).name
        analysis = _analysis_for_ref(scene.primary_image_ref, analyses_by_image)
        alt_text = _image_alt_text(scene.primary_image_ref, analysis)
        lines.append(f"![{alt_text}]({image_prefix}/{image_name})")
        if analysis:
            lines.extend(["", "**完成态画面**", ""])
            ocr = str(analysis.get("ocr_text") or "").strip()
            desc = str(analysis.get("vision_description") or "").strip()
            if ocr:
                lines.append(f"- OCR：{ocr}")
            if desc:
                lines.append(f"- 画面理解：{desc}")
            lines.append("")
    if scene.key_points:
        lines.extend(["**知识要点**", ""])
        lines.extend(f"- {point}" for point in scene.key_points)
        lines.append("")
    return lines
```

- [ ] **Step 8: Run the focused test and verify it passes**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_render_groups_scene_and_uses_latest_final_value_image
```

Expected: PASS.

---

### Task 3: Add Failed-Frame Exclusion Test

**Files:**
- Modify: `tests/test_export/test_vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Add failing test for Qwen error placeholder exclusion**

Add this method to `VaultPreviewTest`:

```python
    def test_render_avoids_failed_qwen_placeholder_as_primary_image(self) -> None:
        sources = _scene_preview_sources()
        failed_image = "outputs/demo/frames/selected/frame_000003.jpg"
        sources.vision["analyses"].append(
            {
                "frame_id": "frame-000003",
                "image_path": failed_image,
                "timestamp": 240.0,
                "ocr_text": "",
                "vision_description": "Visual analysis unavailable because the Qwen Vision Service failed for this frame.",
                "structured_observations": {
                    "topic": "构建股票池的准备条件",
                    "qwen_service": {
                        "status": "error",
                        "message": "Qwen service request timed out for frame-000003",
                    },
                },
            }
        )
        sources.sections["sections"].append(
            {
                "title": "构建股票池之前的准备",
                "summary": "服务超时帧不应成为主图。",
                "source_timestamps": [210.0, 260.0],
                "image_refs": [failed_image],
                "key_points": ["讲解：失败帧仍保留文字上下文"],
                "tags": ["evidence", "visual:other"],
            }
        )

        markdown = render_enhancement_markdown(sources, image_prefix="images")

        self.assertIn("![frame-000002](images/frame_000002.jpg)", markdown)
        self.assertNotIn("![frame-000003](images/frame_000003.jpg)", markdown)
        self.assertIn("失败帧仍保留文字上下文", markdown)
```

- [ ] **Step 2: Run the test**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_render_avoids_failed_qwen_placeholder_as_primary_image
```

Expected: PASS if Task 2 implemented `_analysis_has_qwen_error()` correctly. If it fails, fix only primary-image selection.

---

### Task 4: Add Preview Manifest Scene Metrics

**Files:**
- Modify: `vbook_export/vault_preview.py`
- Modify: `tests/test_export/test_vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Add failing manifest metrics assertions**

In `test_write_preview_package_writes_markdown_manifest_and_images`, after the existing manifest assertions, add:

```python
            self.assertEqual(manifest["scene_count"], 1)
            self.assertEqual(manifest["rendered_primary_image_count"], 1)
            self.assertEqual(manifest["omitted_repeated_image_count"], 0)
```

Add a new test method:

```python
    def test_write_preview_package_records_scene_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = _scene_preview_sources()
            for analysis in sources.vision["analyses"]:
                image = root / Path(analysis["image_path"])
                image.parent.mkdir(parents=True, exist_ok=True)
                image.write_bytes(b"fake image")
                analysis["image_path"] = str(image)
            for index, section in enumerate(sources.sections["sections"]):
                section["image_refs"] = [sources.vision["analyses"][index]["image_path"]]
            preview_dir = root / "preview"

            write_preview_package(sources, preview_dir)

            manifest = json.loads(
                (preview_dir / "manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(manifest["scene_count"], 1)
        self.assertEqual(manifest["image_count"], 2)
        self.assertEqual(manifest["rendered_primary_image_count"], 1)
        self.assertEqual(manifest["omitted_repeated_image_count"], 1)
```

- [ ] **Step 2: Run manifest tests and verify failure**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_writes_markdown_manifest_and_images tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_records_scene_metrics
```

Expected: FAIL because manifest does not yet include scene metrics.

- [ ] **Step 3: Add metrics helper**

Add this function before `_read_json()`:

```python
def preview_metrics(sources: PreviewSources) -> PreviewMetrics:
    analyses_by_image = _analyses_by_image_path(sources.vision)
    scenes = build_preview_scenes(sources, analyses_by_image)
    rendered_primary_image_count = sum(
        1 for scene in scenes if scene.primary_image_ref
    )
    image_ref_count = sum(len(scene.image_refs) for scene in scenes)
    return PreviewMetrics(
        scene_count=len(scenes),
        rendered_primary_image_count=rendered_primary_image_count,
        omitted_repeated_image_count=max(
            0,
            image_ref_count - rendered_primary_image_count,
        ),
    )
```

- [ ] **Step 4: Include metrics in `write_preview_package()` manifest**

In `write_preview_package()`, after `copied_images = _copy_referenced_images(...)`, add:

```python
    metrics = preview_metrics(sources)
```

Then add these keys to the manifest dictionary after `image_count`:

```python
        "scene_count": metrics.scene_count,
        "rendered_primary_image_count": metrics.rendered_primary_image_count,
        "omitted_repeated_image_count": metrics.omitted_repeated_image_count,
```

- [ ] **Step 5: Run manifest tests and verify pass**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_writes_markdown_manifest_and_images tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_records_scene_metrics
```

Expected: PASS.

---

### Task 5: Record Source-Vault Read-Only Workcopy Metadata

**Files:**
- Modify: `vbook_export/vault_preview.py`
- Modify: `tests/test_export/test_vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Add manifest assertions for source and workcopy paths**

In `test_write_preview_package_writes_markdown_manifest_and_images`, after the
scene metric assertions, add:

```python
            self.assertEqual(manifest["source_vault_note"], str(sources.vault_note_path))
            self.assertEqual(manifest["workcopy_note"], "enhancement.md")
            self.assertEqual(manifest["safety"], {"source_vault": "read_only"})
```

- [ ] **Step 2: Run the focused test and verify failure**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_writes_markdown_manifest_and_images
```

Expected: FAIL because the manifest does not yet include workcopy safety
metadata.

- [ ] **Step 3: Add safety metadata to the preview manifest**

In `write_preview_package()`, add these fields to the manifest dictionary:

```python
        "source_vault_note": str(sources.vault_note_path),
        "workcopy_note": "enhancement.md",
        "safety": {
            "source_vault": "read_only",
        },
```

- [ ] **Step 4: Run the focused test and verify pass**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_writes_markdown_manifest_and_images
```

Expected: PASS.

---

### Task 6: Run Focused and Full Verification

**Files:**
- Test: `tests/test_export/test_vault_preview.py`
- Test: full suite

- [ ] **Step 1: Run vault preview tests**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_export.test_vault_preview
```

Expected: all tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest discover
```

Expected: `OK`.

- [ ] **Step 3: Run diff whitespace check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 4: Check git status**

Run:

```powershell
git status --short --branch
```

Expected: only intended vBook files are modified or added.

---

### Task 7: Regenerate Real Preview Sample and Inspect Scene Output

**Files:**
- Generated only: `outputs/vault-enhancement-preview-real-final-value/...`

- [ ] **Step 1: Regenerate preview from the already-built real lesson output**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m vbook_client vault-preview `
  --vault-note "F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output "outputs\vault-enhancement-preview-real-final-value\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池"
```

Expected: command exits `0` and writes `manifest.json`.

- [ ] **Step 2: Inspect generated manifest metrics**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -c "import json; from pathlib import Path; root=Path(r'outputs\vault-enhancement-preview-real-final-value\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池'); m=json.loads((root/'manifest.json').read_text(encoding='utf-8')); print('scene_count=', m.get('scene_count')); print('image_count=', m.get('image_count')); print('rendered_primary_image_count=', m.get('rendered_primary_image_count')); print('omitted_repeated_image_count=', m.get('omitted_repeated_image_count'))"
```

Expected: `scene_count` is less than the old repeated section count, `image_count` remains the number of copied unique images, and `omitted_repeated_image_count` is non-negative.

- [ ] **Step 3: Inspect enhancement image repetition**

Run:

```powershell
Select-String -Path "outputs\vault-enhancement-preview-real-final-value\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\enhancement.md" -Pattern "!\[frame-" | Select-Object -First 40
```

Expected: the same frame image is not repeated many times across adjacent sections. The enhancement should read as scene-level blocks with one final-value image per scene.

---

## Self-Review

Spec coverage:

- Scene grouping is covered by Tasks 1 and 2.
- Final-value frame selection is covered by Tasks 1, 2, and 3.
- Qwen error placeholder exclusion is covered by Task 3.
- Manifest scene metrics are covered by Task 4.
- Source-vault read-only workcopy metadata is covered by Task 5.
- Existing preview packaging and no-vault-write behavior remain covered by existing tests plus Task 5.
- Real sample verification is covered by Task 7.

Placeholder scan:

- No TBD/TODO placeholders.
- Every task lists exact files, commands, and expected results.

Type consistency:

- `PreviewScene`, `PreviewMetrics`, `build_preview_scenes()`, `preview_metrics()`, `_render_scene()`, and helper names are consistent across tasks.
- Existing public APIs remain `render_enhancement_markdown()` and `write_preview_package()`.
