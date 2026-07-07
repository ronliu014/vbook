# Vault Enhancement Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a preview-only workflow that combines an existing vtext-created vault note with vBook visual artifacts and writes an enhancement package under `outputs/vault-enhancement-preview/` without modifying `F:\vault`.

**Architecture:** Keep the current `build` pipeline as the producer of video artifacts. Add a thin export layer that reads an existing vault note, a vBook lesson output directory, `manifest.json`, `vision/analysis.json`, and `fusion/sections.json`, then writes `enhancement.md`, copied image assets, and a preview manifest. Add a CLI command that orchestrates only this preview export.

**Tech Stack:** Python standard library, existing vBook dataclasses/contracts, `unittest`, existing CLI parser in `vbook_client/cli.py`.

---

## File Structure

- Create: `vbook_export/vault_preview.py`  
  Responsible for loading lesson artifacts, rendering enhancement Markdown, copying referenced images into a preview package, and writing a preview manifest.
- Modify: `vbook_client/cli.py`  
  Add a `vault-preview` command that calls `vbook_export.vault_preview`.
- Create: `tests/test_export/test_vault_preview.py`  
  Unit tests for artifact loading, rendering, asset copying, and manifest shape.
- Modify: `tests/test_client/test_manifest_cli.py` or create `tests/test_client/test_vault_preview_cli.py`  
  CLI smoke tests for the new command.
- Modify: `docs/60_operations/batch-processing.md` or create `docs/60_operations/vault-enhancement-preview.md`  
  Runbook for using the workflow with `F:\vault\20_Learning\投资训练营` and `F:\downloads\allwin\投资训练营`.
- Modify: `docs/00_project/task-board.md` and `docs/00_project/status.md` after implementation.

## Task 1: Preview Artifact Loader

**Files:**
- Create: `vbook_export/vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Write failing loader tests**

Create `tests/test_export/test_vault_preview.py` with:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vbook_export.vault_preview import load_preview_sources


class VaultPreviewTest(unittest.TestCase):
    def test_load_preview_sources_reads_vault_note_and_lesson_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_note = root / "vault" / "lesson.md"
            lesson_output = root / "lesson-output"
            vault_note.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            vault_note.write_text("# Existing Note\n\n纯文本笔记。", encoding="utf-8")
            (lesson_output / "manifest.json").write_text(
                json.dumps({"stage_status": {"vision_analysis": "done"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (lesson_output / "vision" / "analysis.json").write_text(
                json.dumps(
                    {
                        "backend": "qwen-vision-service",
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "visual_type": "slide",
                                "image_path": str(lesson_output / "frames" / "selected" / "frame_000001.jpg"),
                                "ocr_text": "量比排行榜",
                                "vision_description": "A slide about stock ranking.",
                                "structured_observations": {"topic": "stock selection"},
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (lesson_output / "fusion" / "sections.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "intent": "fusion_sections_evidence",
                        "section_count": 1,
                        "sections": [
                            {
                                "title": "短线股票池",
                                "summary": "结合量比和盘口信息筛选短线候选。",
                                "source_timestamps": [12.0, 30.0],
                                "image_refs": [str(lesson_output / "frames" / "selected" / "frame_000001.jpg")],
                                "key_points": ["画面文字：量比排行榜"],
                                "tags": ["evidence", "visual:slide", "has_ocr"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            sources = load_preview_sources(vault_note, lesson_output)

        self.assertIn("Existing Note", sources.vault_note_markdown)
        self.assertEqual(sources.vision["analysis_count"], 1)
        self.assertEqual(sources.sections["section_count"], 1)
        self.assertEqual(sources.manifest["stage_status"]["vision_analysis"], "done")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_load_preview_sources_reads_vault_note_and_lesson_artifacts
```

Expected: fail because `vbook_export.vault_preview` does not exist.

- [ ] **Step 3: Implement minimal loader**

Create `vbook_export/vault_preview.py`:

```python
"""Preview export for enhancing existing vault notes with vBook evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PreviewSources:
    vault_note_path: Path
    lesson_output_dir: Path
    vault_note_markdown: str
    manifest: dict[str, Any]
    vision: dict[str, Any]
    sections: dict[str, Any]


def load_preview_sources(
    vault_note_path: Path | str,
    lesson_output_dir: Path | str,
) -> PreviewSources:
    note_path = Path(vault_note_path)
    output_dir = Path(lesson_output_dir)
    if not note_path.is_file():
        raise ValueError(f"vault note does not exist: {note_path}")
    manifest = _read_json(output_dir / "manifest.json")
    vision = _read_json(output_dir / "vision" / "analysis.json")
    sections = _read_json(output_dir / "fusion" / "sections.json")
    return PreviewSources(
        vault_note_path=note_path,
        lesson_output_dir=output_dir,
        vault_note_markdown=note_path.read_text(encoding="utf-8"),
        manifest=manifest,
        vision=vision,
        sections=sections,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required artifact does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"artifact must be a JSON object: {path}")
    return data
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_load_preview_sources_reads_vault_note_and_lesson_artifacts
```

Expected: pass.

## Task 2: Enhancement Markdown Renderer

**Files:**
- Modify: `vbook_export/vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Write failing renderer test**

Append to `VaultPreviewTest`:

```python
    def test_render_enhancement_markdown_keeps_original_note_and_adds_visual_evidence(self) -> None:
        sources = _preview_sources_for_render()

        markdown = render_enhancement_markdown(sources, image_prefix="images")

        self.assertIn("# Existing Note", markdown)
        self.assertIn("## vBook 图文增强预览", markdown)
        self.assertIn("### 短线股票池", markdown)
        self.assertIn("结合量比和盘口信息筛选短线候选。", markdown)
        self.assertIn("量比排行榜", markdown)
        self.assertIn("![frame-000001](images/frame_000001.jpg)", markdown)
        self.assertIn("当前文件是预览，不会写回 vault。", markdown)
```

Add a helper in the same test file:

```python
def _preview_sources_for_render():
    from vbook_export.vault_preview import PreviewSources

    return PreviewSources(
        vault_note_path=Path("F:/vault/20_Learning/投资训练营/demo.md"),
        lesson_output_dir=Path("outputs/demo"),
        vault_note_markdown="# Existing Note\n\n纯文本笔记。",
        manifest={"stage_status": {"vision_analysis": "done"}},
        vision={
            "analysis_count": 1,
            "analyses": [
                {
                    "frame_id": "frame-000001",
                    "image_path": "outputs/demo/frames/selected/frame_000001.jpg",
                    "ocr_text": "量比排行榜",
                    "vision_description": "A slide about stock ranking.",
                }
            ],
        },
        sections={
            "sections": [
                {
                    "title": "短线股票池",
                    "summary": "结合量比和盘口信息筛选短线候选。",
                    "source_timestamps": [12.0, 30.0],
                    "image_refs": ["outputs/demo/frames/selected/frame_000001.jpg"],
                    "key_points": ["画面文字：量比排行榜"],
                    "tags": ["evidence", "visual:slide", "has_ocr"],
                }
            ]
        },
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_render_enhancement_markdown_keeps_original_note_and_adds_visual_evidence
```

Expected: fail because `render_enhancement_markdown` is not implemented or not imported.

- [ ] **Step 3: Implement renderer**

Add to `vbook_export/vault_preview.py`:

```python
def render_enhancement_markdown(
    sources: PreviewSources,
    image_prefix: str = "images",
) -> str:
    lines = [
        sources.vault_note_markdown.rstrip(),
        "",
        "---",
        "",
        "## vBook 图文增强预览",
        "",
        "> 当前文件是预览，不会写回 vault。",
        "",
        f"- 原笔记：{sources.vault_note_path}",
        f"- vBook 输出：{sources.lesson_output_dir}",
        f"- 视觉分析：{sources.vision.get('analysis_count', 0)} 帧",
        "",
    ]
    analyses_by_image = _analyses_by_image_path(sources.vision)
    for section in sources.sections.get("sections", []):
        if not isinstance(section, dict):
            continue
        lines.extend(_render_section(section, analyses_by_image, image_prefix))
    return "\n".join(lines).rstrip() + "\n"


def _render_section(
    section: dict[str, Any],
    analyses_by_image: dict[str, dict[str, Any]],
    image_prefix: str,
) -> list[str]:
    title = str(section.get("title") or "未命名知识点")
    summary = str(section.get("summary") or "")
    lines = ["### " + title, "", summary, ""]
    key_points = section.get("key_points")
    if isinstance(key_points, list) and key_points:
        lines.extend(["**关键要点**", ""])
        lines.extend(f"- {point}" for point in key_points if isinstance(point, str))
        lines.append("")
    image_refs = section.get("image_refs")
    if isinstance(image_refs, list) and image_refs:
        lines.extend(["**图像证据**", ""])
        for ref in image_refs:
            if not isinstance(ref, str):
                continue
            image_name = Path(ref).name
            lines.append(f"![{Path(ref).stem}]({image_prefix}/{image_name})")
            analysis = analyses_by_image.get(ref) or analyses_by_image.get(image_name)
            if analysis:
                ocr = str(analysis.get("ocr_text") or "").strip()
                desc = str(analysis.get("vision_description") or "").strip()
                if ocr:
                    lines.append(f"- OCR：{ocr}")
                if desc:
                    lines.append(f"- 画面理解：{desc}")
        lines.append("")
    return lines


def _analyses_by_image_path(vision: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    analyses = vision.get("analyses")
    if not isinstance(analyses, list):
        return result
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        image_path = analysis.get("image_path")
        if isinstance(image_path, str) and image_path:
            result[image_path] = analysis
            result[Path(image_path).name] = analysis
    return result
```

Update imports in the test file:

```python
from vbook_export.vault_preview import load_preview_sources, render_enhancement_markdown
```

- [ ] **Step 4: Run renderer tests**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview
```

Expected: pass.

## Task 3: Preview Package Writer

**Files:**
- Modify: `vbook_export/vault_preview.py`
- Test: `tests/test_export/test_vault_preview.py`

- [ ] **Step 1: Write failing package writer test**

Append:

```python
    def test_write_preview_package_writes_markdown_manifest_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "lesson-output" / "frames" / "selected" / "frame_000001.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"fake image")
            sources = _preview_sources_for_render()
            sources = replace(sources, lesson_output_dir=root / "lesson-output")
            sources.sections["sections"][0]["image_refs"] = [str(image)]
            sources.vision["analyses"][0]["image_path"] = str(image)
            preview_dir = root / "preview"

            result = write_preview_package(sources, preview_dir)

            self.assertTrue((preview_dir / "enhancement.md").is_file())
            self.assertTrue((preview_dir / "manifest.json").is_file())
            self.assertTrue((preview_dir / "images" / "frame_000001.jpg").is_file())
            manifest = json.loads((preview_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "1")
            self.assertEqual(manifest["status"], "preview")
            self.assertEqual(manifest["outputs"]["enhancement_md"], "enhancement.md")
            self.assertEqual(result.preview_dir, preview_dir)
```

Update imports:

```python
from dataclasses import replace
from vbook_export.vault_preview import load_preview_sources, render_enhancement_markdown, write_preview_package
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview.VaultPreviewTest.test_write_preview_package_writes_markdown_manifest_and_images
```

Expected: fail because `write_preview_package` is not implemented.

- [ ] **Step 3: Implement package writer**

Add:

```python
import shutil


@dataclass(frozen=True)
class PreviewPackage:
    preview_dir: Path
    enhancement_path: Path
    manifest_path: Path
    image_paths: list[Path]


def write_preview_package(
    sources: PreviewSources,
    preview_dir: Path | str,
) -> PreviewPackage:
    target_dir = Path(preview_dir)
    images_dir = target_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    copied_images = _copy_referenced_images(sources, images_dir)
    enhancement = render_enhancement_markdown(sources, image_prefix="images")
    enhancement_path = target_dir / "enhancement.md"
    enhancement_path.write_text(enhancement, encoding="utf-8")
    manifest_path = target_dir / "manifest.json"
    manifest = {
        "schema_version": "1",
        "status": "preview",
        "vault_note": str(sources.vault_note_path),
        "lesson_output_dir": str(sources.lesson_output_dir),
        "outputs": {
            "enhancement_md": "enhancement.md",
            "images_dir": "images",
        },
        "image_count": len(copied_images),
        "images": [str(path.relative_to(target_dir)) for path in copied_images],
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return PreviewPackage(
        preview_dir=target_dir,
        enhancement_path=enhancement_path,
        manifest_path=manifest_path,
        image_paths=copied_images,
    )


def _copy_referenced_images(sources: PreviewSources, images_dir: Path) -> list[Path]:
    copied: list[Path] = []
    seen: set[Path] = set()
    for section in sources.sections.get("sections", []):
        if not isinstance(section, dict):
            continue
        image_refs = section.get("image_refs")
        if not isinstance(image_refs, list):
            continue
        for ref in image_refs:
            if not isinstance(ref, str):
                continue
            source = Path(ref)
            if not source.is_file() or source in seen:
                continue
            target = images_dir / source.name
            shutil.copy2(source, target)
            copied.append(target)
            seen.add(source)
    return copied
```

- [ ] **Step 4: Run export tests**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview
```

Expected: pass.

## Task 4: CLI Command

**Files:**
- Modify: `vbook_client/cli.py`
- Test: `tests/test_client/test_vault_preview_cli.py`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_client/test_vault_preview_cli.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vbook_client.cli import main


class VaultPreviewCliTest(unittest.TestCase):
    def test_vault_preview_command_writes_preview_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_note = root / "vault" / "lesson.md"
            lesson_output = root / "lesson-output"
            image = lesson_output / "frames" / "selected" / "frame_000001.jpg"
            preview_dir = root / "preview"
            vault_note.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            vault_note.write_text("# Existing Note\n\n纯文本笔记。", encoding="utf-8")
            image.write_bytes(b"fake image")
            (lesson_output / "manifest.json").write_text(
                json.dumps({"stage_status": {"vision_analysis": "done"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (lesson_output / "vision" / "analysis.json").write_text(
                json.dumps(
                    {
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "image_path": str(image),
                                "ocr_text": "量比排行榜",
                                "vision_description": "A slide about stock ranking.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (lesson_output / "fusion" / "sections.json").write_text(
                json.dumps(
                    {
                        "sections": [
                            {
                                "title": "短线股票池",
                                "summary": "结合量比和盘口信息筛选短线候选。",
                                "source_timestamps": [12.0],
                                "image_refs": [str(image)],
                                "key_points": ["画面文字：量比排行榜"],
                                "tags": ["evidence"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "vault-preview",
                    "--vault-note",
                    str(vault_note),
                    "--lesson-output",
                    str(lesson_output),
                    "--output",
                    str(preview_dir),
                ]
            )

        self.assertEqual(code, 0)
        self.assertTrue((preview_dir / "enhancement.md").is_file())
        self.assertTrue((preview_dir / "manifest.json").is_file())
        self.assertTrue((preview_dir / "images" / "frame_000001.jpg").is_file())
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_client.test_vault_preview_cli
```

Expected: fail because `vault-preview` is not a known command.

- [ ] **Step 3: Add parser command**

In `vbook_client/cli.py`, import:

```python
from vbook_export.vault_preview import load_preview_sources, write_preview_package
```

In `_build_parser()`, add a subparser:

```python
    preview_parser = subparsers.add_parser(
        "vault-preview",
        help="Write a preview-only vault enhancement package.",
    )
    preview_parser.add_argument("--vault-note", required=True)
    preview_parser.add_argument("--lesson-output", required=True)
    preview_parser.add_argument("--output", required=True)
    preview_parser.set_defaults(handler=_run_vault_preview)
```

Add the handler near other command handlers:

```python
def _run_vault_preview(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        sources = load_preview_sources(args.vault_note, args.lesson_output)
        package = write_preview_package(sources, args.output)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(package.manifest_path)
    return 0
```

If the existing command-dispatch helper expects a different signature, adapt
the handler to the local pattern in `main()` while keeping the same behavior.

- [ ] **Step 4: Run CLI test**

Run:

```powershell
python -m unittest tests.test_client.test_vault_preview_cli
```

Expected: pass.

## Task 5: Operations Runbook And Real Fixture Smoke

**Files:**
- Create: `docs/60_operations/vault-enhancement-preview.md`
- Modify: `docs/00_project/status.md`
- Modify: `docs/00_project/task-board.md`

- [ ] **Step 1: Add runbook**

Create `docs/60_operations/vault-enhancement-preview.md` with:

````markdown
# Vault Enhancement Preview

## Purpose

This workflow creates a preview package that combines an existing vault note
with vBook visual evidence. It does not modify `F:\vault`.

## Inputs

- Existing note: `F:\vault\20_Learning\投资训练营\<series>\<lesson>.md`
- vBook lesson output: `outputs/<run>/<lesson>/`
- Preview output: `outputs/vault-enhancement-preview/<series>/<lesson>/`

## Step 1: Produce vBook Lesson Output

Use the existing `build` command with a transcript and Qwen Vision adapter.

## Step 2: Write Preview Package

```powershell
python -m vbook_client vault-preview `
  --vault-note "F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\<run>\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output "outputs\vault-enhancement-preview\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池"
```

## Expected Output

```text
enhancement.md
manifest.json
images/
```

## Safety Rules

- Do not write to `F:\vault` in this workflow.
- Review `enhancement.md` before designing any write-back command.
- Keep copied images inside the preview output directory.
````

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m unittest tests.test_export.test_vault_preview tests.test_client.test_vault_preview_cli
```

Expected: pass.

- [ ] **Step 3: Run full tests**

Run:

```powershell
python -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 4: Run real preview smoke**

After a vBook lesson output exists for the fixture, run:

```powershell
python -m vbook_client vault-preview `
  --vault-note "F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\<real-run>\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output "outputs\vault-enhancement-preview\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池"
```

Expected:

- command exits `0`;
- preview manifest path is printed;
- `enhancement.md` contains the original note plus `## vBook 图文增强预览`;
- copied image files exist under `images/`;
- no files under `F:\vault` are modified.

- [ ] **Step 5: Update status docs**

Update:

- `docs/00_project/status.md`
- `docs/00_project/task-board.md`
- `docs/70_progress/YYYY-MM-DD-vault-enhancement-preview.md`

Record:

- tests run;
- real fixture paths;
- output preview path;
- whether any vault file changed.

## Execution Order

1. Implement Task 1 and commit loader.
2. Implement Task 2 and commit renderer.
3. Implement Task 3 and commit package writer.
4. Implement Task 4 and commit CLI command.
5. Implement Task 5 and commit docs/runbook.

The first implementation milestone is complete when the focused tests pass and
a preview package can be produced from synthetic artifacts. The second
milestone is complete when the real `投资训练营` fixture produces a preview
without modifying `F:\vault`.
