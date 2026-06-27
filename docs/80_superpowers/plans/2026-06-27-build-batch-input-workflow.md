# Build Batch Input Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a vtext-compatible `build-batch` command that discovers media files, matches transcript files, runs the existing per-lesson `build` pipeline for each lesson, and writes `batch_manifest.json`.

**Architecture:** Add a focused `vbook_pipeline.batch` module for deterministic filesystem discovery, transcript matching, output naming, and batch manifest writing. Keep single-lesson build logic in `vbook_client.cli`; `build-batch` should orchestrate repeated calls to the existing pipeline without importing or depending on vtext code.

**Tech Stack:** Python 3.11 standard library, dataclasses, `unittest`, existing CLI and serialization helpers.

---

## File Structure

- Create `vbook_pipeline/batch.py`: media discovery, transcript matching, lesson planning, batch result dataclasses, and JSON writer.
- Create `tests/test_pipeline/test_batch.py`: unit tests for discovery, ignored directories, transcript priority, nested relative paths, output naming, and batch manifest serialization.
- Modify `vbook_client/cli.py`: add `build-batch` parser and orchestrate repeated per-lesson builds.
- Modify `tests/test_client/test_manifest_cli.py`: add CLI coverage for successful batch builds and missing-transcript resilience.
- Modify `README.md`: document the `build-batch` command and vtext-compatible layout.
- Modify `docs/00_project/status.md`: update current state after implementation.
- Modify `docs/00_project/roadmap.md`: mark batch workflow as functional foundation after implementation.

---

### Task 1: Batch Discovery and Transcript Matching

**Files:**
- Create: `tests/test_pipeline/test_batch.py`
- Create: `vbook_pipeline/batch.py`

- [ ] **Step 1: Write failing batch discovery tests**

Create `tests/test_pipeline/test_batch.py` with:

```python
import json
import tempfile
import unittest
from pathlib import Path

from vbook_pipeline.batch import (
    BatchLessonPlan,
    BatchLessonResult,
    discover_batch_lessons,
    write_batch_manifest,
)


class BatchDiscoveryTest(unittest.TestCase):
    def test_discovers_media_and_matches_transcript_by_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            text_dir = input_dir / "text"
            input_dir.mkdir()
            text_dir.mkdir()
            video = input_dir / "lesson.mp4"
            video.write_text("video", encoding="utf-8")
            (text_dir / "lesson.srt").write_text("plain", encoding="utf-8")
            raw = text_dir / "lesson_raw.srt"
            raw.write_text("raw", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].media_path, video)
        self.assertEqual(plans[0].transcript_path, raw)
        self.assertEqual(plans[0].output_dir, output / "lesson")
        self.assertEqual(plans[0].lesson_id, "lesson")
        self.assertTrue(plans[0].vtext_compatible)
        self.assertIsNone(plans[0].skip_reason)

    def test_preserves_nested_relative_paths_for_output_and_transcript_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            video = input_dir / "course-a" / "lesson one.mp4"
            transcript = input_dir / "text" / "course-a" / "lesson one.srt"
            video.parent.mkdir(parents=True)
            transcript.parent.mkdir(parents=True)
            video.write_text("video", encoding="utf-8")
            transcript.write_text("transcript", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].relative_media_path, Path("course-a") / "lesson one.mp4")
        self.assertEqual(plans[0].transcript_path, transcript)
        self.assertEqual(plans[0].output_dir, output / "course-a" / "lesson one")
        self.assertEqual(plans[0].lesson_id, "course-a/lesson one")

    def test_ignores_generated_and_coordination_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            real_video = input_dir / "lesson.mp4"
            real_transcript = input_dir / "text" / "lesson.srt"
            ignored_video = input_dir / "outputs" / "old.mp4"
            sync_video = input_dir / "sync" / "handoff.mp4"
            real_transcript.parent.mkdir(parents=True)
            ignored_video.parent.mkdir(parents=True)
            sync_video.parent.mkdir(parents=True)
            real_video.write_text("video", encoding="utf-8")
            real_transcript.write_text("transcript", encoding="utf-8")
            ignored_video.write_text("ignore", encoding="utf-8")
            sync_video.write_text("ignore", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual([plan.media_path for plan in plans], [real_video])

    def test_records_missing_transcript_without_dropping_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            video = input_dir / "lesson.mp4"
            input_dir.mkdir()
            video.write_text("video", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].media_path, video)
        self.assertIsNone(plans[0].transcript_path)
        self.assertEqual(plans[0].skip_reason, "missing_transcript")

    def test_write_batch_manifest_serializes_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "batch_manifest.json"
            result = BatchLessonResult(
                lesson_id="lesson",
                media_path=Path("lesson.mp4"),
                transcript_path=Path("text/lesson.srt"),
                output_dir=Path("outputs/lesson"),
                status="done",
                vtext_compatible=True,
                manifest_path=Path("outputs/lesson/manifest.json"),
            )

            written = write_batch_manifest([result], manifest_path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(data["lesson_count"], 1)
        self.assertEqual(data["done_count"], 1)
        self.assertEqual(data["failed_count"], 0)
        self.assertEqual(data["skipped_count"], 0)
        self.assertEqual(data["lessons"][0]["status"], "done")
        self.assertEqual(data["lessons"][0]["vtext_compatible"], True)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_pipeline.test_batch
```

Expected: FAIL with `ModuleNotFoundError` or import errors because `vbook_pipeline.batch` does not exist.

- [ ] **Step 3: Implement batch discovery module**

Create `vbook_pipeline/batch.py`:

```python
"""Batch input discovery and manifest helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from vbook_common.serialization import to_jsonable


SUPPORTED_MEDIA_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
}
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "outputs",
    "sync",
    "text",
}
TRANSCRIPT_CANDIDATE_SUFFIXES = (
    "_raw.srt",
    ".srt",
    "_raw.vtt",
    ".vtt",
    "_raw.txt",
    ".txt",
)


@dataclass(frozen=True)
class BatchLessonPlan:
    lesson_id: str
    media_path: Path
    relative_media_path: Path
    output_dir: Path
    transcript_path: Path | None
    vtext_compatible: bool
    skip_reason: str | None = None


@dataclass(frozen=True)
class BatchLessonResult:
    lesson_id: str
    media_path: Path
    transcript_path: Path | None
    output_dir: Path
    status: str
    vtext_compatible: bool
    manifest_path: Path | None = None
    failure_reason: str | None = None


def discover_batch_lessons(
    input_dir: Path | str,
    output_dir: Path | str,
) -> list[BatchLessonPlan]:
    """Discover vtext-compatible media inputs and matching transcript files."""
    root = Path(input_dir)
    output_root = Path(output_dir)
    plans: list[BatchLessonPlan] = []
    for media_path in _iter_media_files(root):
        relative_media = media_path.relative_to(root)
        transcript_path = _find_transcript(root, relative_media)
        output_lesson_dir = output_root / relative_media.with_suffix("")
        lesson_id = relative_media.with_suffix("").as_posix()
        plans.append(
            BatchLessonPlan(
                lesson_id=lesson_id,
                media_path=media_path,
                relative_media_path=relative_media,
                output_dir=output_lesson_dir,
                transcript_path=transcript_path,
                vtext_compatible=transcript_path is not None,
                skip_reason=None if transcript_path is not None else "missing_transcript",
            )
        )
    return plans


def write_batch_manifest(
    results: Sequence[BatchLessonResult],
    path: Path | str,
) -> Path:
    """Write the batch run manifest."""
    result_list = list(results)
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "lesson_count": len(result_list),
        "done_count": sum(1 for result in result_list if result.status == "done"),
        "failed_count": sum(1 for result in result_list if result.status == "failed"),
        "skipped_count": sum(1 for result in result_list if result.status == "skipped"),
        "lessons": result_list,
    }
    manifest_path.write_text(
        json.dumps(to_jsonable(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _iter_media_files(root: Path) -> list[Path]:
    media_files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _has_ignored_parent(path.relative_to(root)):
            continue
        if path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS:
            media_files.append(path)
    return sorted(media_files, key=lambda item: item.relative_to(root).as_posix())


def _has_ignored_parent(relative_path: Path) -> bool:
    return any(part in IGNORED_DIRECTORY_NAMES for part in relative_path.parts[:-1])


def _find_transcript(root: Path, relative_media: Path) -> Path | None:
    transcript_dir = root / "text" / relative_media.parent
    stem = relative_media.stem
    for suffix in TRANSCRIPT_CANDIDATE_SUFFIXES:
        candidate = transcript_dir / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    return None
```

- [ ] **Step 4: Run batch discovery tests**

Run:

```powershell
python -m unittest tests.test_pipeline.test_batch
```

Expected: PASS.

- [ ] **Step 5: Commit batch discovery module**

Run:

```powershell
git add vbook_pipeline/batch.py tests/test_pipeline/test_batch.py
git commit -m "feat: discover batch input lessons"
```

---

### Task 2: CLI build-batch Orchestration

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [ ] **Step 1: Add failing successful build-batch CLI test**

Append this test inside `ManifestCliTest`:

```python
    def test_build_batch_runs_each_matched_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output = root / "outputs" / "batch"
            video = input_dir / "lesson.mp4"
            transcript = input_dir / "text" / "lesson.srt"
            video.parent.mkdir(parents=True)
            transcript.parent.mkdir(parents=True)
            video.write_text("video", encoding="utf-8")
            transcript.write_text(
                "1\n00:00:00,000 --> 00:00:03,000\nintro\n",
                encoding="utf-8",
            )

            with patch("vbook_client.cli.extract_frame_candidates") as extract:

                def fake_extract(
                    video_path: str,
                    candidate_dir: Path,
                    video_id: str,
                    interval_seconds: float,
                ) -> list[FrameCandidate]:
                    directory = Path(candidate_dir)
                    directory.mkdir(parents=True, exist_ok=True)
                    frame = directory / "frame_000001.jpg"
                    frame.write_bytes(b"image")
                    return [
                        FrameCandidate(
                            id="frame-000001",
                            video_id=video_id,
                            timestamp=0.0,
                            image_path=frame,
                            width=0,
                            height=0,
                        )
                    ]

                extract.side_effect = fake_extract
                code = main(
                    [
                        "build-batch",
                        "--input",
                        str(input_dir),
                        "--output",
                        str(output),
                        "--frame-interval-seconds",
                        "30",
                        "--alignment-window-seconds",
                        "5",
                    ]
                )

            batch_manifest = json.loads(
                (output / "batch_manifest.json").read_text(encoding="utf-8")
            )
            lesson_manifest = json.loads(
                (output / "lesson" / "manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertEqual(batch_manifest["lesson_count"], 1)
        self.assertEqual(batch_manifest["done_count"], 1)
        self.assertEqual(batch_manifest["lessons"][0]["status"], "done")
        self.assertEqual(
            batch_manifest["lessons"][0]["manifest_path"],
            str(output / "lesson" / "manifest.json"),
        )
        self.assertEqual(lesson_manifest["stage_status"]["manifest"], "done")
        self.assertEqual(lesson_manifest["stage_status"]["vision_analysis"], "done")
```

- [ ] **Step 2: Add failing missing-transcript CLI test**

Append this test inside `ManifestCliTest`:

```python
    def test_build_batch_records_missing_transcript_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output = root / "outputs" / "batch"
            matched_video = input_dir / "matched.mp4"
            missing_video = input_dir / "missing.mp4"
            transcript = input_dir / "text" / "matched.srt"
            input_dir.mkdir()
            transcript.parent.mkdir(parents=True)
            matched_video.write_text("video", encoding="utf-8")
            missing_video.write_text("video", encoding="utf-8")
            transcript.write_text(
                "1\n00:00:00,000 --> 00:00:03,000\nintro\n",
                encoding="utf-8",
            )

            with patch("vbook_client.cli.extract_frame_candidates") as extract:

                def fake_extract(
                    video_path: str,
                    candidate_dir: Path,
                    video_id: str,
                    interval_seconds: float,
                ) -> list[FrameCandidate]:
                    directory = Path(candidate_dir)
                    directory.mkdir(parents=True, exist_ok=True)
                    frame = directory / "frame_000001.jpg"
                    frame.write_bytes(b"image")
                    return [
                        FrameCandidate(
                            id="frame-000001",
                            video_id=video_id,
                            timestamp=0.0,
                            image_path=frame,
                            width=0,
                            height=0,
                        )
                    ]

                extract.side_effect = fake_extract
                code = main(["build-batch", "--input", str(input_dir), "--output", str(output)])

            batch_manifest = json.loads(
                (output / "batch_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertEqual(batch_manifest["lesson_count"], 2)
        self.assertEqual(batch_manifest["done_count"], 1)
        self.assertEqual(batch_manifest["skipped_count"], 1)
        statuses = {
            lesson["lesson_id"]: lesson for lesson in batch_manifest["lessons"]
        }
        self.assertEqual(statuses["matched"]["status"], "done")
        self.assertEqual(statuses["missing"]["status"], "skipped")
        self.assertEqual(statuses["missing"]["failure_reason"], "missing_transcript")
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_batch_runs_each_matched_lesson tests.test_client.test_manifest_cli.ManifestCliTest.test_build_batch_records_missing_transcript_and_continues
```

Expected: FAIL because `build-batch` is not a recognized command.

- [ ] **Step 4: Add CLI imports and parser**

In `vbook_client/cli.py`, add:

```python
from vbook_pipeline.batch import (
    BatchLessonResult,
    discover_batch_lessons,
    write_batch_manifest,
)
```

In `_build_parser()`, after the `build` parser:

```python
    batch_parser = subparsers.add_parser("build-batch", help="Run the MVP pipeline for a directory of lessons")
    batch_parser.add_argument("--input", required=True, help="Input directory with media and text/")
    batch_parser.add_argument("--output", required=True, help="Output directory for batch results")
    batch_parser.add_argument(
        "--frame-interval-seconds",
        type=float,
        default=30.0,
        help="Seconds between candidate frames for each lesson",
    )
    batch_parser.add_argument(
        "--alignment-window-seconds",
        type=float,
        help="Seconds before and after each frame timestamp used for transcript matching",
    )
```

In `main()`, before `parser.print_help()`:

```python
    if args.command == "build-batch":
        return _run_build_batch(args, parser)
```

- [ ] **Step 5: Add build-batch runner**

Add this function near `_run_manifest_pipeline()`:

```python
def _run_build_batch(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    plans = discover_batch_lessons(input_dir=args.input, output_dir=args.output)
    results: list[BatchLessonResult] = []
    for plan in plans:
        if plan.skip_reason is not None or plan.transcript_path is None:
            results.append(
                BatchLessonResult(
                    lesson_id=plan.lesson_id,
                    media_path=plan.media_path,
                    transcript_path=plan.transcript_path,
                    output_dir=plan.output_dir,
                    status="skipped",
                    vtext_compatible=plan.vtext_compatible,
                    failure_reason=plan.skip_reason,
                )
            )
            continue
        build_args = argparse.Namespace(
            command="build",
            video=str(plan.media_path),
            transcript=str(plan.transcript_path),
            output=str(plan.output_dir),
            config=None,
            course_title="",
            lesson_title=plan.media_path.stem,
            frame_candidates_dir=None,
            frame_interval_seconds=args.frame_interval_seconds,
            select_frames=False,
            selected_frames_dir=None,
            min_selected_frame_interval_seconds=10.0,
            alignment_window_seconds=args.alignment_window_seconds,
            analyze_vision_placeholder=False,
            vision_backend=None,
            visual_analysis_input=None,
            visual_analysis_path=None,
            write_note=False,
            note_path=None,
            write_fusion_prompt=False,
            fusion_prompt_path=None,
            write_fusion_sections=False,
            fusion_sections_path=None,
        )
        try:
            _run_manifest_pipeline(
                build_args,
                parser,
                defaults={
                    "align_timeline": True,
                    "analyze_vision_placeholder": True,
                    "extract_frames": True,
                    "select_frames": True,
                    "write_fusion_prompt": True,
                    "write_fusion_sections": True,
                    "write_note": True,
                },
            )
        except Exception as exc:
            results.append(
                BatchLessonResult(
                    lesson_id=plan.lesson_id,
                    media_path=plan.media_path,
                    transcript_path=plan.transcript_path,
                    output_dir=plan.output_dir,
                    status="failed",
                    vtext_compatible=plan.vtext_compatible,
                    failure_reason=f"build_failed: {exc}",
                )
            )
            continue
        results.append(
            BatchLessonResult(
                lesson_id=plan.lesson_id,
                media_path=plan.media_path,
                transcript_path=plan.transcript_path,
                output_dir=plan.output_dir,
                status="done",
                vtext_compatible=plan.vtext_compatible,
                manifest_path=plan.output_dir / "manifest.json",
            )
        )
    batch_manifest_path = write_batch_manifest(
        results,
        Path(args.output) / "batch_manifest.json",
    )
    print(batch_manifest_path)
    return 0
```

- [ ] **Step 6: Run build-batch CLI tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_batch_runs_each_matched_lesson tests.test_client.test_manifest_cli.ManifestCliTest.test_build_batch_records_missing_transcript_and_continues
```

Expected: PASS.

- [ ] **Step 7: Commit build-batch CLI**

Run:

```powershell
git add vbook_client/cli.py tests/test_client/test_manifest_cli.py
git commit -m "feat: add build batch command"
```

---

### Task 3: Unsupported Transcript Result and Full Verification

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`
- Modify: `README.md`
- Modify: `docs/00_project/status.md`
- Modify: `docs/00_project/roadmap.md`

- [ ] **Step 1: Add failing unsupported-transcript batch test**

Append this test inside `ManifestCliTest`:

```python
    def test_build_batch_records_unsupported_transcript_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output = root / "outputs" / "batch"
            video = input_dir / "lesson.mp4"
            transcript = input_dir / "text" / "lesson.txt"
            input_dir.mkdir()
            transcript.parent.mkdir(parents=True)
            video.write_text("video", encoding="utf-8")
            transcript.write_text("untimed transcript", encoding="utf-8")

            code = main(["build-batch", "--input", str(input_dir), "--output", str(output)])

            batch_manifest = json.loads(
                (output / "batch_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertEqual(batch_manifest["lesson_count"], 1)
        self.assertEqual(batch_manifest["failed_count"], 1)
        self.assertEqual(batch_manifest["lessons"][0]["status"], "failed")
        self.assertEqual(
            batch_manifest["lessons"][0]["failure_reason"],
            "unsupported_transcript_format",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_batch_records_unsupported_transcript_failure
```

Expected: FAIL because current failure reason is a generic `build_failed: ...` string.

- [ ] **Step 3: Normalize unsupported transcript failures**

In `vbook_client/cli.py`, change the `_run_build_batch()` exception block to:

```python
        except Exception as exc:
            message = str(exc)
            failure_reason = (
                "unsupported_transcript_format"
                if "unsupported transcript format" in message
                else f"build_failed: {message}"
            )
            results.append(
                BatchLessonResult(
                    lesson_id=plan.lesson_id,
                    media_path=plan.media_path,
                    transcript_path=plan.transcript_path,
                    output_dir=plan.output_dir,
                    status="failed",
                    vtext_compatible=plan.vtext_compatible,
                    failure_reason=failure_reason,
                )
            )
            continue
```

- [ ] **Step 4: Run unsupported-transcript test**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_batch_records_unsupported_transcript_failure
```

Expected: PASS.

- [ ] **Step 5: Update README**

In `README.md`, add a short `build-batch` example near the build command section:

```markdown
Batch input can use a vtext-compatible directory with media files at the input
root and matching transcripts under `text/`:

```powershell
python -m vbook_client build-batch --input E:\projects\my_app\temp --output outputs\temp-batch
```

The command writes one lesson output directory per media file plus
`batch_manifest.json`.
```

- [ ] **Step 6: Update status and roadmap**

In `docs/00_project/status.md`, change the batch bullet under partial work from:

```markdown
- Batch processing is designed in prior specs but is not part of the current
  main execution path.
```

to:

```markdown
- Batch processing has a functional foundation through `build-batch`, but it
  still uses the local MVP placeholder intelligence path for each lesson.
```

In `docs/00_project/roadmap.md`, change P4 status from:

```markdown
Status: designed in part, not implemented as the main path.
```

to:

```markdown
Status: functional foundation for batch input; knowledge workflow still partial.
```

- [ ] **Step 7: Run focused tests**

Run:

```powershell
python -m unittest tests.test_pipeline.test_batch tests.test_client.test_manifest_cli
```

Expected: PASS.

- [ ] **Step 8: Run full suite and whitespace checks**

Run:

```powershell
python -m unittest discover
git diff --check
git diff --cached --check
```

Expected: unit tests PASS and diff checks produce no output.

- [ ] **Step 9: Commit verification and docs**

Run:

```powershell
git add README.md docs/00_project/status.md docs/00_project/roadmap.md vbook_client/cli.py tests/test_client/test_manifest_cli.py
git commit -m "docs: document build batch workflow"
```

If the unsupported transcript normalization changed `vbook_client/cli.py`, include it in the commit above.

---

## Self-Review

- Spec coverage: The plan implements vtext-compatible discovery, transcript priority, ignored directories, nested output layout, `batch_manifest.json`, resilient missing-transcript handling, and `build-batch` orchestration over existing per-lesson build.
- Intentional scope limit: VTT and plain text transcript parsing are not implemented in this plan. VTT/TXT paths can be discovered; unsupported transcript formats are recorded as `unsupported_transcript_format` during batch execution. This preserves resilience without expanding transcript import scope.
- Placeholder scan: This plan contains no unresolved `TBD`, `TODO`, or placeholder implementation steps.
- Type consistency: `BatchLessonPlan`, `BatchLessonResult`, `discover_batch_lessons()`, `write_batch_manifest()`, and `build-batch` names are used consistently across tasks.
