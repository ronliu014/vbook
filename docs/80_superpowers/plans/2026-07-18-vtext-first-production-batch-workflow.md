# Vtext-First Production Batch Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible production batch workflow for the accepted `vtext_first_vault_enhance` route, starting with preview-only batches and ending with gated, backed-up vault publication.

**Architecture:** Keep the first production hardening pass in `tools/` because the existing experiment, preflight, publication-plan, conflict-report, and publish utilities live there and already have tests. Add one preview batch orchestrator and one post-publication checker, then expose the stable workflow through docs and optional `vbook_client` CLI wiring after the tool behavior is proven.

**Tech Stack:** Python standard library, existing `vbook_export.vault_enhance.write_vtext_first_package`, existing `tools.vtext_first_preflight`, existing `tools.vault_publication_plan`, existing `tools.vault_publication_publish`, `unittest`, PowerShell runbook commands, experiment root `F:/vbook/experiments`.

---

## File Structure

- Create: `tools/vtext_first_batch_preview.py`
  - Reads an explicit batch input JSON.
  - Writes preview-only enhanced notes under `F:/vbook/experiments/<experiment>/renders/vtext_first_vault_enhance/<variant>/<lesson>/`.
  - Writes `batch-preview-manifest.json` and `batch-preview-manifest.md`.
  - Does not write `F:/vault`.
- Create: `tools/vault_publication_postcheck.py`
  - Reads `publication-result.json`.
  - Verifies every copied source/target hash pair matches.
  - Verifies Markdown image links in published notes resolve after URL decoding.
  - Writes `publication-postcheck.json` and `publication-postcheck.md`.
- Create: `tests/test_tools/test_vtext_first_batch_preview.py`
  - Covers preview-only batch output, skipped lessons, and safety rejection of vault output roots.
- Create: `tests/test_tools/test_vault_publication_postcheck.py`
  - Covers hash matching, hash mismatch, and missing Markdown image detection.
- Modify: `docs/60_operations/vault-enhance.md`
  - Add production batch workflow section.
  - Point users to preview-first, preflight, review, publication plan, conflict report, backup, publish, postcheck.
- Create: `docs/60_operations/production-batch.md`
  - Dedicated runbook for the accepted production route.
- Optional later modify: `vbook_client/cli.py`
  - Add CLI wrappers only after tool-level behavior passes tests and real preview smoke.

## Safety Invariants

- `F:/vault/20_Learning/vtext` is always read-only.
- Preview batch output must not be under `F:/vault/20_Learning/vbook` or `F:/vault/20_Learning/vtext`.
- Publication remains a separate explicit step requiring a reviewed `publication-plan.json`.
- Existing vault targets are never overwritten without `--overwrite --backup-existing`.
- Production route is fixed to `vtext_first_vault_enhance` until a later route passes the same maturity gate.
- Formal artifacts live under `F:/vbook/experiments`; repo-local `outputs/` remains for short smoke runs only.

---

### Task 1: Preview Batch Input Contract

**Files:**
- Create: `tests/test_tools/test_vtext_first_batch_preview.py`
- Create: `tools/vtext_first_batch_preview.py`

- [ ] **Step 1: Write the failing contract test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from tools.vtext_first_batch_preview import load_batch_input


class VtextFirstBatchPreviewTest(unittest.TestCase):
    def test_load_batch_input_accepts_explicit_lessons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note = root / "vtext" / "Lesson A.md"
            lesson_output = root / "lesson-output" / "Lesson A"
            vtext_note.parent.mkdir(parents=True)
            vtext_note.write_text("# Lesson A\n", encoding="utf-8")
            lesson_output.mkdir(parents=True)
            batch_input = root / "batch-input.json"
            batch_input.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "kind": "vtext_first_batch_input",
                        "dataset_id": "dataset-a",
                        "lessons": [
                            {
                                "lesson": "Lesson A",
                                "vtext_note": str(vtext_note),
                                "lesson_output": str(lesson_output),
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            loaded = load_batch_input(batch_input)

            self.assertEqual(loaded.dataset_id, "dataset-a")
            self.assertEqual(len(loaded.lessons), 1)
            self.assertEqual(loaded.lessons[0].lesson, "Lesson A")
            self.assertEqual(loaded.lessons[0].vtext_note, vtext_note)
            self.assertEqual(loaded.lessons[0].lesson_output, lesson_output)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vtext_first_batch_preview
```

Expected:

```text
ImportError: cannot import name 'load_batch_input'
```

- [ ] **Step 3: Implement the minimal input dataclasses and loader**

Add to `tools/vtext_first_batch_preview.py`:

```python
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BatchPreviewLesson:
    lesson: str
    vtext_note: Path
    lesson_output: Path


@dataclass(frozen=True)
class BatchPreviewInput:
    dataset_id: str
    lessons: list[BatchPreviewLesson]


def load_batch_input(path: Path | str) -> BatchPreviewInput:
    input_path = Path(path)
    data = json.loads(input_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("batch input must be a JSON object")
    if data.get("schema_version") != "1":
        raise ValueError("unsupported batch input schema_version")
    if data.get("kind") != "vtext_first_batch_input":
        raise ValueError("unsupported batch input kind")
    dataset_id = str(data.get("dataset_id") or "").strip()
    if not dataset_id:
        raise ValueError("batch input requires dataset_id")
    raw_lessons = data.get("lessons")
    if not isinstance(raw_lessons, list) or not raw_lessons:
        raise ValueError("batch input requires non-empty lessons")
    lessons = []
    for index, item in enumerate(raw_lessons):
        if not isinstance(item, dict):
            raise ValueError(f"lessons[{index}] must be an object")
        lesson = str(item.get("lesson") or "").strip()
        vtext_note = Path(str(item.get("vtext_note") or ""))
        lesson_output = Path(str(item.get("lesson_output") or ""))
        if not lesson:
            raise ValueError(f"lessons[{index}].lesson is required")
        lessons.append(
            BatchPreviewLesson(
                lesson=lesson,
                vtext_note=vtext_note,
                lesson_output=lesson_output,
            )
        )
    return BatchPreviewInput(dataset_id=dataset_id, lessons=lessons)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vtext_first_batch_preview
```

Expected:

```text
Ran 1 test
OK
```

- [ ] **Step 5: Commit**

```powershell
git add tools\vtext_first_batch_preview.py tests\test_tools\test_vtext_first_batch_preview.py
git commit -m "Add vtext-first batch input contract"
```

---

### Task 2: Preview-Only Batch Renderer

**Files:**
- Modify: `tests/test_tools/test_vtext_first_batch_preview.py`
- Modify: `tools/vtext_first_batch_preview.py`

- [ ] **Step 1: Write the failing preview batch test**

Append to `VtextFirstBatchPreviewTest`:

```python
    def test_run_batch_preview_writes_preview_manifest_without_vault_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_input, output_root = _write_valid_preview_fixture(root)

            package = run_batch_preview(
                batch_input_path=batch_input,
                output_root=output_root,
                route="vtext_first_vault_enhance",
                variant="baseline",
                max_images_per_note=1,
                min_image_gap_seconds=0,
            )

            self.assertEqual(package.status, "preview_ready")
            self.assertEqual(package.done_count, 1)
            self.assertEqual(package.failed_count, 0)
            self.assertTrue(package.json_path.is_file())
            self.assertTrue(package.markdown_path.is_file())
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["safety"]["vault_write"], "disabled")
            self.assertEqual(payload["route"], "vtext_first_vault_enhance")
            self.assertEqual(payload["variant"], "baseline")
            self.assertEqual(payload["done_count"], 1)
            note = output_root / "renders" / "vtext_first_vault_enhance" / "baseline" / "Lesson A" / "note.md"
            self.assertTrue(note.is_file())
            self.assertNotIn("F:\\vault", str(note))
```

Add this helper in the same test file:

```python
def _write_valid_preview_fixture(root: Path) -> tuple[Path, Path]:
    vtext_note = root / "vtext" / "Lesson A.md"
    lesson_output = root / "lesson-output" / "Lesson A"
    output_root = root / "experiment"
    assets = lesson_output / "frames" / "selected"
    vision = lesson_output / "vision"
    vtext_note.parent.mkdir(parents=True)
    vtext_note.write_text("# Lesson A\n\n## 龙头筛选\n\n这里讲筛选条件。\n", encoding="utf-8")
    assets.mkdir(parents=True)
    image = assets / "frame_000001.jpg"
    image.write_bytes(b"image")
    vision.mkdir(parents=True)
    (vision / "analysis.json").write_text(
        json.dumps(
            {
                "analyses": [
                    {
                        "image_path": str(image),
                        "timestamp_seconds": 240,
                        "ocr_text": "龙头筛选",
                        "vision_description": "讲师展示龙头筛选条件完成页",
                        "structured_observations": {"topic": "龙头筛选"},
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (lesson_output / "manifest.json").write_text(
        json.dumps(
            {
                "video": {"title": "Lesson A"},
                "frames": [{"path": str(image), "timestamp_seconds": 240}],
                "visual_analysis_path": str(vision / "analysis.json"),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    batch_input = root / "batch-input.json"
    batch_input.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "kind": "vtext_first_batch_input",
                "dataset_id": "dataset-a",
                "lessons": [
                    {
                        "lesson": "Lesson A",
                        "vtext_note": str(vtext_note),
                        "lesson_output": str(lesson_output),
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return batch_input, output_root
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vtext_first_batch_preview
```

Expected:

```text
NameError: name 'run_batch_preview' is not defined
```

- [ ] **Step 3: Implement the preview runner and package dataclass**

Add imports and dataclass:

```python
from datetime import datetime, timezone

from vbook_export.vault_enhance import write_vtext_first_package


@dataclass(frozen=True)
class BatchPreviewPackage:
    status: str
    json_path: Path
    markdown_path: Path
    done_count: int
    failed_count: int
    skipped_count: int
```

Add functions:

```python
def run_batch_preview(
    *,
    batch_input_path: Path | str,
    output_root: Path | str,
    route: str,
    variant: str,
    max_images_per_note: int | None,
    min_image_gap_seconds: float,
) -> BatchPreviewPackage:
    if route != "vtext_first_vault_enhance":
        raise ValueError("only vtext_first_vault_enhance is supported")
    root = Path(output_root)
    _reject_vault_output_root(root)
    batch = load_batch_input(batch_input_path)
    render_root = root / "renders" / route / variant
    results = []
    for lesson in batch.lessons:
        lesson_dir = render_root / lesson.lesson
        note_path = lesson_dir / "note.md"
        manifest_path = lesson_dir / "note.manifest.json"
        try:
            if not lesson.vtext_note.is_file():
                raise FileNotFoundError(f"vtext note does not exist: {lesson.vtext_note}")
            if not lesson.lesson_output.is_dir():
                raise FileNotFoundError(f"lesson output does not exist: {lesson.lesson_output}")
            package = write_vtext_first_package(
                vtext_note_path=lesson.vtext_note,
                lesson_output_dir=lesson.lesson_output,
                output_note_path=note_path,
                manifest_path=manifest_path,
                max_images_per_note=max_images_per_note,
                min_image_gap_seconds=min_image_gap_seconds,
            )
            results.append(
                {
                    "lesson": lesson.lesson,
                    "status": "done",
                    "vtext_note": str(lesson.vtext_note),
                    "lesson_output": str(lesson.lesson_output),
                    "output_note": str(package.output_note_path),
                    "manifest": str(package.manifest_path),
                    "asset_count": len(package.asset_paths),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "lesson": lesson.lesson,
                    "status": "failed",
                    "vtext_note": str(lesson.vtext_note),
                    "lesson_output": str(lesson.lesson_output),
                    "failure_reason": str(exc),
                }
            )
    done_count = sum(1 for item in results if item["status"] == "done")
    failed_count = sum(1 for item in results if item["status"] == "failed")
    payload = {
        "schema_version": "1",
        "kind": "vtext_first_batch_preview",
        "status": "preview_ready" if failed_count == 0 else "preview_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": batch.dataset_id,
        "route": route,
        "variant": variant,
        "output_root": str(root),
        "render_root": str(render_root),
        "done_count": done_count,
        "failed_count": failed_count,
        "skipped_count": 0,
        "safety": {"vault_write": "disabled", "source_vtext": "read_only"},
        "lessons": results,
    }
    json_path = root / "batch-preview-manifest.json"
    markdown_path = root / "batch-preview-manifest.md"
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_batch_preview_markdown(payload), encoding="utf-8")
    return BatchPreviewPackage(
        status=str(payload["status"]),
        json_path=json_path,
        markdown_path=markdown_path,
        done_count=done_count,
        failed_count=failed_count,
        skipped_count=0,
    )
```

Add safety and renderer:

```python
def _reject_vault_output_root(path: Path) -> None:
    normalized = str(path.resolve()).replace("/", "\\").lower()
    blocked = [
        "f:\\vault\\20_learning\\vbook",
        "f:\\vault\\20_learning\\vtext",
    ]
    if any(normalized.startswith(item) for item in blocked):
        raise ValueError("batch preview output root must not be under F:/vault/20_Learning")


def _render_batch_preview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vtext-First Batch Preview: {payload['dataset_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Route: `{payload['route']}`",
        f"- Variant: `{payload['variant']}`",
        f"- Done: {payload['done_count']}",
        f"- Failed: {payload['failed_count']}",
        f"- Vault write: `{payload['safety']['vault_write']}`",
        "",
        "## Lessons",
        "",
    ]
    for item in payload["lessons"]:
        line = f"- `{item['status']}` {item['lesson']}"
        if item["status"] == "done":
            line += f" -> `{item['output_note']}`"
        else:
            line += f" -> {item['failure_reason']}"
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 4: Add CLI entry point for the tool**

Add to `tools/vtext_first_batch_preview.py`:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run preview-only vtext-first vault enhancement for a lesson batch."
    )
    parser.add_argument("--batch-input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--route", default="vtext_first_vault_enhance")
    parser.add_argument("--variant", default="baseline")
    parser.add_argument("--max-images-per-note", type=int)
    parser.add_argument("--min-image-gap-seconds", type=float, default=0.0)
    args = parser.parse_args(argv)
    package = run_batch_preview(
        batch_input_path=args.batch_input,
        output_root=args.output_root,
        route=args.route,
        variant=args.variant,
        max_images_per_note=args.max_images_per_note,
        min_image_gap_seconds=args.min_image_gap_seconds,
    )
    print(str(package.json_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vtext_first_batch_preview
```

Expected:

```text
Ran 2 tests
OK
```

- [ ] **Step 6: Commit**

```powershell
git add tools\vtext_first_batch_preview.py tests\test_tools\test_vtext_first_batch_preview.py
git commit -m "Add vtext-first batch preview runner"
```

---

### Task 3: Batch Preview Safety And Failure Reporting

**Files:**
- Modify: `tests/test_tools/test_vtext_first_batch_preview.py`
- Modify: `tools/vtext_first_batch_preview.py`

- [ ] **Step 1: Write failing safety and failure tests**

Append:

```python
    def test_rejects_vault_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_input, _ = _write_valid_preview_fixture(root)

            with self.assertRaises(ValueError):
                run_batch_preview(
                    batch_input_path=batch_input,
                    output_root=Path("F:/vault/20_Learning/vbook/course"),
                    route="vtext_first_vault_enhance",
                    variant="baseline",
                    max_images_per_note=1,
                    min_image_gap_seconds=0,
                )

    def test_missing_lesson_output_is_recorded_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_input, output_root = _write_valid_preview_fixture(root)
            data = json.loads(batch_input.read_text(encoding="utf-8"))
            missing = root / "missing-output"
            data["lessons"][0]["lesson_output"] = str(missing)
            batch_input.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            package = run_batch_preview(
                batch_input_path=batch_input,
                output_root=output_root,
                route="vtext_first_vault_enhance",
                variant="baseline",
                max_images_per_note=1,
                min_image_gap_seconds=0,
            )

            self.assertEqual(package.status, "preview_failed")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["failed_count"], 1)
            self.assertIn("lesson output does not exist", payload["lessons"][0]["failure_reason"])
```

- [ ] **Step 2: Run tests to verify behavior**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vtext_first_batch_preview
```

Expected:

```text
Ran 4 tests
OK
```

- [ ] **Step 3: Commit**

```powershell
git add tools\vtext_first_batch_preview.py tests\test_tools\test_vtext_first_batch_preview.py
git commit -m "Harden vtext-first batch preview safety"
```

---

### Task 4: Publication Postcheck Tool

**Files:**
- Create: `tests/test_tools/test_vault_publication_postcheck.py`
- Create: `tools/vault_publication_postcheck.py`

- [ ] **Step 1: Write failing postcheck success test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from tools.vault_publication_postcheck import run_publication_postcheck


class VaultPublicationPostcheckTest(unittest.TestCase):
    def test_postcheck_passes_when_hashes_and_markdown_images_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = _write_publication_result_fixture(root, target_image_exists=True)

            package = run_publication_postcheck(publication_result_path=result_path)

            self.assertEqual(package.status, "pass")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["hash_match_count"], 2)
            self.assertEqual(payload["hash_mismatch_count"], 0)
            self.assertEqual(payload["markdown_image_link_count"], 1)
            self.assertEqual(payload["missing_markdown_image_count"], 0)


def _write_publication_result_fixture(root: Path, *, target_image_exists: bool) -> Path:
    source = root / "source"
    target = root / "target"
    source.mkdir()
    target.mkdir()
    source_image = source / "frame_000001.jpg"
    target_image = target / "assets" / "Lesson" / "frame_000001.jpg"
    source_note = source / "note.md"
    target_note = target / "Lesson.md"
    source_image.write_bytes(b"image")
    target_image.parent.mkdir(parents=True)
    if target_image_exists:
        target_image.write_bytes(b"image")
    source_note.write_text("![x](assets/Lesson/frame_000001.jpg)\n", encoding="utf-8")
    target_note.write_text("![x](assets/Lesson/frame_000001.jpg)\n", encoding="utf-8")
    result_path = root / "publication-result.json"
    result_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "kind": "vault_publication_result",
                "plan_id": "plan-a",
                "status": "applied",
                "copied_notes": [{"source": str(source_note), "target": str(target_note)}],
                "copied_assets": [{"source": str(source_image), "target": str(target_image)}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return result_path
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vault_publication_postcheck
```

Expected:

```text
ImportError: cannot import name 'run_publication_postcheck'
```

- [ ] **Step 3: Implement the postcheck tool**

Add to `tools/vault_publication_postcheck.py`:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote


_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class PublicationPostcheckPackage:
    status: str
    json_path: Path
    markdown_path: Path


def run_publication_postcheck(
    *, publication_result_path: Path | str
) -> PublicationPostcheckPackage:
    path = Path(publication_result_path)
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if result.get("kind") != "vault_publication_result":
        raise ValueError("unsupported publication result kind")
    if result.get("status") != "applied":
        raise ValueError("publication result must be applied")
    file_checks = []
    for pair in list(result.get("copied_notes", [])) + list(result.get("copied_assets", [])):
        if not isinstance(pair, dict):
            continue
        source = Path(str(pair.get("source") or ""))
        target = Path(str(pair.get("target") or ""))
        source_hash = _sha256(source) if source.is_file() else None
        target_hash = _sha256(target) if target.is_file() else None
        file_checks.append(
            {
                "source": str(source),
                "target": str(target),
                "source_exists": source.is_file(),
                "target_exists": target.is_file(),
                "source_sha256": source_hash,
                "target_sha256": target_hash,
                "hash_match": source_hash is not None and source_hash == target_hash,
            }
        )
    image_checks = []
    for pair in result.get("copied_notes", []):
        if not isinstance(pair, dict):
            continue
        note = Path(str(pair.get("target") or ""))
        if not note.is_file():
            continue
        for raw_link in _markdown_image_links(note):
            resolved = (note.parent / unquote(raw_link)).resolve()
            image_checks.append(
                {
                    "note": str(note),
                    "link": raw_link,
                    "resolved": str(resolved),
                    "exists": resolved.is_file(),
                }
            )
    mismatch_count = sum(1 for item in file_checks if not item["hash_match"])
    missing_image_count = sum(1 for item in image_checks if not item["exists"])
    status = "pass" if mismatch_count == 0 and missing_image_count == 0 else "fail"
    payload = {
        "schema_version": "1",
        "kind": "vault_publication_postcheck",
        "plan_id": str(result.get("plan_id") or ""),
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "publication_result": str(path),
        "file_check_count": len(file_checks),
        "hash_match_count": sum(1 for item in file_checks if item["hash_match"]),
        "hash_mismatch_count": mismatch_count,
        "markdown_image_link_count": len(image_checks),
        "missing_markdown_image_count": missing_image_count,
        "file_checks": file_checks,
        "markdown_image_checks": image_checks,
    }
    json_path = path.parent / "publication-postcheck.json"
    markdown_path = path.parent / "publication-postcheck.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_postcheck_markdown(payload), encoding="utf-8")
    return PublicationPostcheckPackage(status=status, json_path=json_path, markdown_path=markdown_path)
```

Add helpers:

```python
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _markdown_image_links(note: Path) -> list[str]:
    links = []
    markdown = note.read_text(encoding="utf-8")
    for match in _IMAGE_LINK_RE.finditer(markdown):
        target = match.group(1).strip()
        if " \"" in target:
            target = target.split(" \"", 1)[0].strip()
        if target.startswith(("http://", "https://", "#")):
            continue
        links.append(target)
    return links


def _render_postcheck_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vault Publication Postcheck: {payload['plan_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- File checks: {payload['file_check_count']}",
        f"- Hash matches: {payload['hash_match_count']}",
        f"- Hash mismatches: {payload['hash_mismatch_count']}",
        f"- Markdown image links: {payload['markdown_image_link_count']}",
        f"- Missing Markdown images: {payload['missing_markdown_image_count']}",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify an applied vault publication result.")
    parser.add_argument("--publication-result", required=True)
    args = parser.parse_args(argv)
    package = run_publication_postcheck(publication_result_path=args.publication_result)
    print(str(package.json_path))
    return 0 if package.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the success test**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vault_publication_postcheck
```

Expected:

```text
Ran 1 test
OK
```

- [ ] **Step 5: Commit**

```powershell
git add tools\vault_publication_postcheck.py tests\test_tools\test_vault_publication_postcheck.py
git commit -m "Add vault publication postcheck tool"
```

---

### Task 5: Postcheck Failure Coverage

**Files:**
- Modify: `tests/test_tools/test_vault_publication_postcheck.py`
- Modify: `tools/vault_publication_postcheck.py`

- [ ] **Step 1: Add tests for hash mismatch and missing images**

Append:

```python
    def test_postcheck_fails_when_target_hash_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = _write_publication_result_fixture(root, target_image_exists=True)
            target_note = root / "target" / "Lesson.md"
            target_note.write_text("changed\n", encoding="utf-8")

            package = run_publication_postcheck(publication_result_path=result_path)

            self.assertEqual(package.status, "fail")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["hash_mismatch_count"], 1)

    def test_postcheck_fails_when_markdown_image_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = _write_publication_result_fixture(root, target_image_exists=False)

            package = run_publication_postcheck(publication_result_path=result_path)

            self.assertEqual(package.status, "fail")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["missing_markdown_image_count"], 1)
```

- [ ] **Step 2: Run tests**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vault_publication_postcheck
```

Expected:

```text
Ran 3 tests
OK
```

- [ ] **Step 3: Commit**

```powershell
git add tools\vault_publication_postcheck.py tests\test_tools\test_vault_publication_postcheck.py
git commit -m "Cover vault publication postcheck failures"
```

---

### Task 6: Production Runbook

**Files:**
- Create: `docs/60_operations/production-batch.md`
- Modify: `docs/60_operations/vault-enhance.md`

- [ ] **Step 1: Write the production runbook**

Create `docs/60_operations/production-batch.md`:

```markdown
# Production Batch Workflow

This runbook is the controlled production workflow for the accepted
`vtext_first_vault_enhance` route.

## Status

- Route: `vtext_first_vault_enhance`
- Stage: production candidate
- Preview output root: `F:/vbook/experiments`
- Vault target root: `F:/vault/20_Learning/vbook`
- Source vtext root: `F:/vault/20_Learning/vtext`
- Source vtext policy: read-only

## Phase 1: Batch Input

Create an explicit batch input JSON:

```json
{
  "schema_version": "1",
  "kind": "vtext_first_batch_input",
  "dataset_id": "invest-training-small-batch-001",
  "lessons": [
    {
      "lesson": "如何筛选龙头股？",
      "vtext_note": "F:/vault/20_Learning/vtext/投资训练营/韩珂龙头班：基础篇/如何筛选龙头股？.md",
      "lesson_output": "F:/vbook/experiments/E20260711-existing-model-baselines/lesson-outputs/如何筛选龙头股？"
    }
  ]
}
```

## Phase 2: Preview Batch

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_batch_preview.py `
  --batch-input "F:/vbook/inputs/invest-training-small-batch-001/batch-input.json" `
  --output-root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --max-images-per-note 3 `
  --min-image-gap-seconds 180
```

## Phase 3: Preflight

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_preflight.py `
  --root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline" `
  --json-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.json" `
  --markdown-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.md"
```

## Phase 4: Human Review

Create or update a review round before publication. The user must inspect image
placement, image value, note readability, and whether vtext remains the primary
body.

## Phase 5: Publication Plan

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_plan.py `
  --experiment-root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --target-vault-root "F:/vault/20_Learning/vbook/投资训练营/韩珂龙头班：基础篇" `
  --plan-id "vtext_first_vault_enhance-production-batch-001"
```

## Phase 6: Conflict Report

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_publish.py `
  --plan "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/publication-plans/vtext_first_vault_enhance-production-batch-001/publication-plan.json" `
  --conflict-report
```

## Phase 7: Apply With Backup

Only run after explicit user approval for the specific plan id.

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_publish.py `
  --plan "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/publication-plans/vtext_first_vault_enhance-production-batch-001/publication-plan.json" `
  --apply `
  --confirm-plan-id vtext_first_vault_enhance-production-batch-001 `
  --overwrite `
  --backup-existing
```

## Phase 8: Postcheck

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_postcheck.py `
  --publication-result "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/publication-plans/vtext_first_vault_enhance-production-batch-001/publication-result.json"
```

Publication is accepted only when the postcheck status is `pass`.
```

- [ ] **Step 2: Add a short pointer to `docs/60_operations/vault-enhance.md`**

Append under `Controlled Publication`:

```markdown
For multi-lesson production runs, use
[production-batch.md](./production-batch.md). The production workflow adds
batch preview manifests and a publication postcheck after controlled publish.
```

- [ ] **Step 3: Commit**

```powershell
git add docs\60_operations\production-batch.md docs\60_operations\vault-enhance.md
git commit -m "Document vtext-first production batch workflow"
```

---

### Task 7: CLI Wiring After Tool Stabilization

**Files:**
- Modify: `vbook_client/cli.py`
- Modify: `tests/test_client/test_cli.py`

- [ ] **Step 1: Add CLI smoke test for command availability**

Add to `tests/test_client/test_cli.py`:

```python
    def test_production_batch_preview_help_is_available(self) -> None:
        stdout = io.StringIO()

        with self.assertRaises(SystemExit) as ctx, redirect_stdout(stdout):
            main(["production-batch-preview", "--help"])

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("Run preview-only vtext-first production batch", stdout.getvalue())
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_client.test_cli
```

Expected:

```text
SystemExit: 2
```

- [ ] **Step 3: Wire parser and runner**

Modify `vbook_client/cli.py` imports:

```python
from tools.vtext_first_batch_preview import run_batch_preview
```

Add to `main` before the final help:

```python
    if args.command == "production-batch-preview":
        return _run_production_batch_preview(args, parser)
```

Add parser:

```python
    production_batch_parser = subparsers.add_parser(
        "production-batch-preview",
        help="Run preview-only vtext-first production batch",
    )
    production_batch_parser.add_argument("--batch-input", required=True)
    production_batch_parser.add_argument("--output-root", required=True)
    production_batch_parser.add_argument("--route", default="vtext_first_vault_enhance")
    production_batch_parser.add_argument("--variant", default="baseline")
    production_batch_parser.add_argument("--max-images-per-note", type=int)
    production_batch_parser.add_argument("--min-image-gap-seconds", type=float, default=0.0)
```

Add runner:

```python
def _run_production_batch_preview(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        package = run_batch_preview(
            batch_input_path=args.batch_input,
            output_root=args.output_root,
            route=args.route,
            variant=args.variant,
            max_images_per_note=args.max_images_per_note,
            min_image_gap_seconds=args.min_image_gap_seconds,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(package.json_path)
    return 0 if package.status == "preview_ready" else 1
```

- [ ] **Step 4: Run tests**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_client.test_cli tests.test_tools.test_vtext_first_batch_preview
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```powershell
git add vbook_client\cli.py tests\test_client\test_cli.py
git commit -m "Expose production batch preview CLI"
```

---

### Task 8: Real 10-20 Lesson Preview Smoke

**Files:**
- Create outside repo: `F:/vbook/inputs/invest-training-production-batch-001/batch-input.json`
- Generate outside repo: `F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/`
- Modify: `docs/70_progress/2026-07-18-vtext-first-production-batch.md`

- [ ] **Step 1: Select the first production batch**

Use these roots:

```text
Video source: F:/downloads/allwin/投资训练营
vtext source: F:/vault/20_Learning/vtext/投资训练营
experiment output: F:/vbook/experiments/E20260718-vtext-first-production-batch-preview
```

Select 10-20 lessons that already have:

- vtext `.md` source note;
- corresponding vBook lesson output with `manifest.json`;
- visual analysis from the 240s baseline.

- [ ] **Step 2: Write the batch input JSON**

Create:

```text
F:/vbook/inputs/invest-training-production-batch-001/batch-input.json
```

Each lesson object must use:

```json
{
  "lesson": "课程标题",
  "vtext_note": "F:/vault/20_Learning/vtext/投资训练营/课程路径/课程标题.md",
  "lesson_output": "F:/vbook/experiments/<existing-or-new-run>/lesson-outputs/课程标题"
}
```

- [ ] **Step 3: Run preview-only batch**

Run:

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_batch_preview.py `
  --batch-input "F:/vbook/inputs/invest-training-production-batch-001/batch-input.json" `
  --output-root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --max-images-per-note 3 `
  --min-image-gap-seconds 180
```

Expected:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/batch-preview-manifest.json
```

- [ ] **Step 4: Run preflight**

Run:

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_preflight.py `
  --root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline" `
  --json-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.json" `
  --markdown-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.md"
```

Expected:

```text
ok: true
missing_image_count: 0
error_count: 0
```

- [ ] **Step 5: Write progress note**

Create `docs/70_progress/2026-07-18-vtext-first-production-batch.md` with:

```markdown
# 2026-07-18 Vtext-First Production Batch Preview

## Scope

- Route: `vtext_first_vault_enhance`
- Mode: preview-only
- Dataset: `invest-training-production-batch-001`
- Output root: `F:/vbook/experiments/E20260718-vtext-first-production-batch-preview`
- Vault write: disabled

## Results

- Lessons requested:
- Lessons done:
- Lessons failed:
- Preflight:

## Findings

- Image placement:
- Final value page quality:
- Qwen error placeholder handling:
- Markdown preview image links:
- Note readability:

## Decision

- Status:
- Next:
```

- [ ] **Step 6: Commit repo docs only**

Do not commit `F:/vbook` generated artifacts.

```powershell
git add docs\70_progress\2026-07-18-vtext-first-production-batch.md
git commit -m "Record vtext-first production batch preview"
```

---

### Task 9: Regression Suite And Branch Readiness

**Files:**
- No production file changes unless tests reveal a defect.

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vtext_first_batch_preview
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vault_publication_postcheck
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_vault_publication_publish
```

Expected:

```text
OK
```

- [ ] **Step 2: Run full test suite**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest discover
```

Expected:

```text
OK
```

- [ ] **Step 3: Check repository state**

Run:

```powershell
git status -sb
git log --oneline --decorate -5
```

Expected:

```text
## codex-semantic-visual-note-test
```

- [ ] **Step 4: Decide integration path**

If the preview batch and tests pass:

```powershell
git checkout main
git merge --ff-only codex-semantic-visual-note-test
```

If `main` cannot fast-forward, stop and inspect the diff before merging.

---

## Self-Review

- Spec coverage: The plan covers preview-only batch generation, source safety, publication postcheck, documentation, optional CLI exposure, real 10-20 lesson smoke, and final regression checks.
- Placeholder scan: No unresolved placeholder markers or unspecified implementation steps remain. Real batch lesson paths are intentionally selected during Task 8 because the available 240s lesson-output set must be discovered from the local `F:/vbook` state at execution time.
- Type consistency: `BatchPreviewLesson`, `BatchPreviewInput`, `BatchPreviewPackage`, and `PublicationPostcheckPackage` are defined before use. Function names in tests match the planned implementations.
- Known risk: Task 2 fixture may need small adjustment if `load_preview_sources` requires a more complete manifest shape than shown. If that happens, update only the test fixture to match the existing `vbook_export.vault_preview` contract and keep production behavior unchanged.
