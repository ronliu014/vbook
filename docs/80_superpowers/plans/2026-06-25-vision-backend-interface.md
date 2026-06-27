# Vision Backend Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight visual analysis backend interface with `placeholder` and `manual-json` backends.

**Architecture:** Keep the boundary in `vbook_vision.analysis` as a function dispatcher that returns normalized `VisualAnalysis[]`. Keep `build` runnable without external dependencies by defaulting to `placeholder`; allow explicit `manual-json` input for real-video smoke tests and future external model output. Preserve the existing `--analyze-vision-placeholder` CLI flag as compatibility syntax.

**Tech Stack:** Python 3.11 standard library, dataclasses from `vbook_common.types`, `unittest`, existing CLI test helpers.

---

## File Structure

- Modify `vbook_vision/analysis.py`: add `analyze_frames()`, `load_manual_visual_analysis()`, JSON validation helpers, and keep `analyze_frames_placeholder()` / `write_visual_analysis()`.
- Modify `tests/test_vision/test_analysis.py`: add unit coverage for dispatcher and `manual-json` validation.
- Modify `vbook_client/cli.py`: add `--vision-backend` and `--visual-analysis-input`, route visual analysis through `analyze_frames()`, and preserve existing placeholder flag behavior.
- Modify `tests/test_client/test_manifest_cli.py`: add CLI build coverage for `manual-json` and keep compatibility test expectations.

---

### Task 1: Vision Analysis Dispatcher and Manual JSON Loader

**Files:**
- Modify: `tests/test_vision/test_analysis.py`
- Modify: `vbook_vision/analysis.py`

- [ ] **Step 1: Write failing dispatcher and manual-json tests**

Append these tests inside `VisualAnalysisTest` in `tests/test_vision/test_analysis.py`:

```python
    def test_analyze_frames_dispatches_placeholder_backend(self) -> None:
        frames = [
            FrameCandidate("frame-000001", "lesson", 0.0, Path("frame_000001.jpg"), 0, 0)
        ]

        analyses = analyze_frames(frames, backend="placeholder")

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].backend, "placeholder")

    def test_manual_json_loads_object_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps(
                    {
                        "backend": "manual-json",
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "visual_type": "slide",
                                "ocr_text": "entry signal",
                                "vision_description": "A short-term stock selection slide.",
                                "structured_observations": {"topic": "stock selection"},
                                "confidence": 0.9,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            analyses = analyze_frames(
                frames,
                backend="manual-json",
                visual_analysis_input=manual,
            )

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].visual_type, VisualType.SLIDE)
        self.assertEqual(analyses[0].image_path, image)
        self.assertEqual(analyses[0].ocr_text, "entry signal")
        self.assertEqual(
            analyses[0].vision_description,
            "A short-term stock selection slide.",
        )
        self.assertEqual(analyses[0].structured_observations["topic"], "stock selection")
        self.assertEqual(analyses[0].confidence, 0.9)
        self.assertEqual(analyses[0].backend, "manual-json")

    def test_manual_json_loads_list_format_and_defaults_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000002.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps(
                    [
                        {
                            "frame_id": "frame-000002",
                            "vision_description": "A chart example.",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000002", "lesson", 5.0, image, 0, 0)]

            analyses = analyze_frames(
                frames,
                backend="manual-json",
                visual_analysis_input=manual,
            )

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
        self.assertEqual(analyses[0].image_path, image)
        self.assertEqual(analyses[0].ocr_text, "")
        self.assertEqual(analyses[0].structured_observations, {})
        self.assertEqual(analyses[0].backend, "manual-json")

    def test_manual_json_allows_partial_frame_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_a = root / "frame_000001.jpg"
            image_b = root / "frame_000002.jpg"
            manual = root / "manual.json"
            image_a.write_bytes(b"a")
            image_b.write_bytes(b"b")
            manual.write_text(
                json.dumps(
                    [
                        {
                            "frame_id": "frame-000002",
                            "visual_type": "kline_case",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            frames = [
                FrameCandidate("frame-000001", "lesson", 0.0, image_a, 0, 0),
                FrameCandidate("frame-000002", "lesson", 5.0, image_b, 0, 0),
            ]

            analyses = analyze_frames(
                frames,
                backend="manual-json",
                visual_analysis_input=manual,
            )

        self.assertEqual([analysis.frame_id for analysis in analyses], ["frame-000002"])
        self.assertEqual(analyses[0].visual_type, VisualType.KLINE_CASE)

    def test_manual_json_rejects_invalid_visual_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps([{"frame_id": "frame-000001", "visual_type": "chart"}]),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "visual_type"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_manual_json_rejects_duplicate_frame_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps(
                    [
                        {"frame_id": "frame-000001"},
                        {"frame_id": "frame-000001"},
                    ]
                ),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "Duplicate frame_id"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_manual_json_rejects_unknown_frame_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps([{"frame_id": "frame-999999"}]),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "Unknown frame_id"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_manual_json_rejects_malformed_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(json.dumps({"items": []}), encoding="utf-8")
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "analyses"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )
```

Update the import in the same test file:

```python
from vbook_vision.analysis import (
    analyze_frames,
    analyze_frames_placeholder,
    write_visual_analysis,
)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_vision.test_analysis
```

Expected: FAIL with `ImportError` or `AttributeError` because `analyze_frames` does not exist.

- [ ] **Step 3: Implement dispatcher and manual-json loader**

Replace `vbook_vision/analysis.py` with this implementation while preserving the module docstring:

```python
"""Visual analysis helpers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import FrameCandidate, VisualAnalysis, VisualType


def analyze_frames(
    frames: Sequence[FrameCandidate],
    backend: str = "placeholder",
    visual_analysis_input: Path | str | None = None,
) -> list[VisualAnalysis]:
    """Analyze frames using a supported visual backend."""
    if backend == "placeholder":
        return analyze_frames_placeholder(frames)
    if backend == "manual-json":
        return load_manual_visual_analysis(frames, visual_analysis_input)
    raise ValueError(f"Unsupported vision backend: {backend}")


def analyze_frames_placeholder(
    frames: Sequence[FrameCandidate],
    backend: str = "placeholder",
) -> list[VisualAnalysis]:
    """Create placeholder visual analysis records for frames."""
    return [
        VisualAnalysis(
            frame_id=frame.id,
            visual_type=VisualType.OTHER,
            image_path=frame.image_path,
            vision_description="Visual analysis pending backend implementation.",
            structured_observations={
                "source": "placeholder",
                "timestamp": frame.timestamp,
            },
            confidence=None,
            backend=backend,
        )
        for frame in frames
    ]


def load_manual_visual_analysis(
    frames: Sequence[FrameCandidate],
    visual_analysis_input: Path | str | None,
) -> list[VisualAnalysis]:
    """Load normalized visual analysis records from a manual JSON file."""
    if visual_analysis_input is None:
        raise ValueError("manual-json backend requires visual_analysis_input")

    input_path = Path(visual_analysis_input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    records = _extract_manual_records(data)
    frame_by_id = {frame.id: frame for frame in frames}
    seen_frame_ids: set[str] = set()
    analyses: list[VisualAnalysis] = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"manual-json record at index {index} must be an object")
        frame_id = _required_string(record, "frame_id", index)
        if frame_id in seen_frame_ids:
            raise ValueError(f"Duplicate frame_id in manual-json input: {frame_id}")
        seen_frame_ids.add(frame_id)
        frame = frame_by_id.get(frame_id)
        if frame is None:
            raise ValueError(f"Unknown frame_id in manual-json input: {frame_id}")
        observations = record.get("structured_observations", {})
        if not isinstance(observations, dict):
            raise ValueError(
                f"manual-json structured_observations for {frame_id} must be an object"
            )
        analyses.append(
            VisualAnalysis(
                frame_id=frame_id,
                visual_type=_parse_visual_type(record.get("visual_type", "other"), frame_id),
                image_path=Path(record["image_path"]) if record.get("image_path") else frame.image_path,
                ocr_text=str(record.get("ocr_text", "")),
                vision_description=str(record.get("vision_description", "")),
                structured_observations=dict(observations),
                confidence=_parse_confidence(record.get("confidence"), frame_id),
                backend="manual-json",
            )
        )

    return analyses


def write_visual_analysis(
    analyses: Sequence[VisualAnalysis],
    path: Path | str,
    backend: str = "placeholder",
) -> Path:
    """Write visual analyses as formatted UTF-8 JSON."""
    analysis_path = Path(path)
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text(
        json.dumps(
            to_jsonable(
                {
                    "backend": backend,
                    "analysis_count": len(analyses),
                    "analyses": list(analyses),
                }
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return analysis_path


def _extract_manual_records(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        records = data.get("analyses")
        if isinstance(records, list):
            return records
        raise ValueError("manual-json object input must contain an analyses list")
    raise ValueError("manual-json input must be an object with analyses or a list")


def _required_string(record: dict[str, Any], key: str, index: int) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"manual-json record at index {index} requires string {key}")
    return value


def _parse_visual_type(value: Any, frame_id: str) -> VisualType:
    try:
        return VisualType(value)
    except ValueError as exc:
        raise ValueError(f"Invalid visual_type for {frame_id}: {value}") from exc


def _parse_confidence(value: Any, frame_id: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    raise ValueError(f"manual-json confidence for {frame_id} must be a number")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest tests.test_vision.test_analysis
```

Expected: PASS with all `VisualAnalysisTest` tests OK.

- [ ] **Step 5: Commit**

Run:

```powershell
git add vbook_vision/analysis.py tests/test_vision/test_analysis.py
git commit -m "feat: add vision backend dispatcher"
```

---

### Task 2: CLI Backend Selection

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [ ] **Step 1: Write failing CLI manual-json build test**

Append this test inside `ManifestCliTest` in `tests/test_client/test_manifest_cli.py`:

```python
    def test_build_command_can_use_manual_json_visual_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            manual = root / "manual-vision.json"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            manual.write_text(
                json.dumps(
                    {
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "visual_type": "slide",
                                "ocr_text": "buy point",
                                "vision_description": "A slide about a buy point.",
                                "structured_observations": {"topic": "entry"},
                                "confidence": 0.8,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "build",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--frame-candidates-dir",
                    str(candidate_dir),
                    "--alignment-window-seconds",
                    "3",
                    "--vision-backend",
                    "manual-json",
                    "--visual-analysis-input",
                    str(manual),
                ]
            )

            vision = json.loads((output / "vision" / "analysis.json").read_text(encoding="utf-8"))
            sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )
            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(vision["backend"], "manual-json")
        self.assertEqual(vision["analysis_count"], 1)
        self.assertEqual(vision["analyses"][0]["visual_type"], "slide")
        self.assertEqual(vision["analyses"][0]["ocr_text"], "buy point")
        self.assertEqual(vision["analyses"][0]["backend"], "manual-json")
        self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)
        self.assertEqual(
            manifest["artifacts"]["vision"]["analyses"][0]["structured_observations"]["topic"],
            "entry",
        )
        self.assertEqual(sections["sections"][0]["image_refs"][0].endswith("frame_000001.jpg"), True)
        self.assertIn("frame_000001.jpg", note)
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_use_manual_json_visual_analysis
```

Expected: FAIL with argparse rejecting `--vision-backend` or `--visual-analysis-input`.

- [ ] **Step 3: Implement CLI arguments and routing**

In `vbook_client/cli.py`, change the import:

```python
from vbook_vision.analysis import analyze_frames, write_visual_analysis
```

In `_add_pipeline_arguments()`, add these arguments after `--analyze-vision-placeholder` handling and before `--visual-analysis-path`:

```python
    command_parser.add_argument(
        "--vision-backend",
        choices=("placeholder", "manual-json"),
        help="Visual analysis backend; build defaults to placeholder",
    )
    command_parser.add_argument(
        "--visual-analysis-input",
        help="Input JSON for backends such as manual-json",
    )
```

In `_run_manifest_pipeline()`, replace the existing visual analysis block:

```python
    should_analyze_vision = _should_analyze_vision(args, defaults)
    if should_analyze_vision:
        analysis_frames = selected_frames if selected_frames is not None else frames
        if analysis_frames is None:
            parser.error(f"{args.command} requires frame metadata for vision analysis")
        vision_backend = _vision_backend(args, defaults)
        try:
            visual_analyses = analyze_frames(
                analysis_frames,
                backend=vision_backend,
                visual_analysis_input=args.visual_analysis_input,
            )
        except ValueError as exc:
            parser.error(str(exc))
        visual_analysis_path = (
            Path(args.visual_analysis_path)
            if args.visual_analysis_path
            else Path(args.output) / "vision" / "analysis.json"
        )
        write_visual_analysis(visual_analyses, visual_analysis_path, backend=vision_backend)
```

Add these helpers near `_flag()`:

```python
def _should_analyze_vision(
    args: argparse.Namespace,
    defaults: dict[str, bool],
) -> bool:
    return bool(
        getattr(args, "analyze_vision_placeholder", False)
        or getattr(args, "vision_backend", None)
        or defaults.get("analyze_vision_placeholder", False)
    )


def _vision_backend(
    args: argparse.Namespace,
    defaults: dict[str, bool],
) -> str:
    if getattr(args, "vision_backend", None):
        return args.vision_backend
    if (
        getattr(args, "analyze_vision_placeholder", False)
        or defaults.get("analyze_vision_placeholder", False)
    ):
        return "placeholder"
    return "placeholder"
```

- [ ] **Step 4: Run CLI manual-json test**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_use_manual_json_visual_analysis
```

Expected: PASS.

- [ ] **Step 5: Run CLI compatibility tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_manifest_command_can_write_placeholder_visual_analysis tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_writes_default_mvp_artifacts
```

Expected: PASS. This confirms the old placeholder flag and build default still work.

- [ ] **Step 6: Commit**

Run:

```powershell
git add vbook_client/cli.py tests/test_client/test_manifest_cli.py
git commit -m "feat: add manual json vision backend cli"
```

---

### Task 3: Full Regression and Real-Style Smoke

**Files:**
- No planned source edits unless verification exposes a defect.

- [ ] **Step 1: Run focused vision and CLI tests**

Run:

```powershell
python -m unittest tests.test_vision.test_analysis tests.test_client.test_manifest_cli
```

Expected: PASS.

- [ ] **Step 2: Run full unit suite**

Run:

```powershell
python -m unittest discover
```

Expected: PASS. If a failure appears, inspect it before changing implementation.

- [ ] **Step 3: Run whitespace check**

Run:

```powershell
git diff --check
git diff --cached --check
```

Expected: no output and exit code 0.

- [ ] **Step 4: Run real-style manual-json smoke with existing temp sample when available**

Only run this if both local files exist:

```text
E:\projects\my_app\temp\三分钟学会选短线个股.mp4
E:\projects\my_app\temp\text\三分钟学会选短线个股.srt
```

Create a small manual analysis JSON under the vBook workspace after a build has generated selected frame IDs. Use the first selected frame ID and path from `manifest.json`, then rerun:

```powershell
python -m vbook_client build `
  --video E:\projects\my_app\temp\三分钟学会选短线个股.mp4 `
  --transcript E:\projects\my_app\temp\text\三分钟学会选短线个股.srt `
  --output outputs\manual-json-smoke `
  --frame-interval-seconds 30 `
  --alignment-window-seconds 5 `
  --vision-backend manual-json `
  --visual-analysis-input outputs\manual-json-smoke\manual-vision.json
```

Expected: `outputs\manual-json-smoke\vision\analysis.json` has `"backend": "manual-json"` and `manifest.json` has `stage_status.vision_analysis = "done"`.

- [ ] **Step 5: Commit smoke-related doc or fixture only if created intentionally**

Do not commit generated `outputs/` files. If a permanent sample fixture is created under `tests/fixtures/`, commit it with:

```powershell
git add tests/fixtures/<fixture-name>.json
git commit -m "test: add manual vision fixture"
```

Otherwise skip this step.

---

## Self-Review

- Spec coverage: Task 1 covers dispatcher, placeholder preservation, `manual-json` object/list formats, defaults, partial coverage, and validation. Task 2 covers CLI flags, build default behavior, compatibility flag behavior, normalized output, manifest, fusion, and note propagation. Task 3 covers regression and real-style smoke verification.
- Placeholder scan: This plan intentionally contains no `TBD`, `TODO`, or unspecified error-handling work.
- Type consistency: The plan consistently uses `analyze_frames()`, `load_manual_visual_analysis()`, `visual_analysis_input`, `VisualType`, `VisualAnalysis`, `--vision-backend`, and `--visual-analysis-input`.
