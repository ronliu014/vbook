# vBook Vision Placeholder Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a P2 placeholder visual analysis foundation that produces `VisualAnalysis[]`, writes `vision/analysis.json`, and records it in `manifest.json`.

**Architecture:** `vbook_vision.analysis` owns backend-neutral visual analysis records and JSON writing. The initial backend is `placeholder`, which marks frames as `VisualType.OTHER` and records deterministic metadata without OCR or model calls. `vbook_export.manifest` records the analysis artifact. `vbook_client manifest` can generate placeholder analysis from selected frames or candidate frames.

**Tech Stack:** Python 3.11+, stdlib `json`, existing dataclasses, `unittest`.

---

## File Structure

- Create `vbook_vision/analysis.py` for placeholder `VisualAnalysis` generation and writing.
- Create `tests/test_vision/test_analysis.py`.
- Modify `vbook_export/manifest.py` and `tests/test_export/test_manifest.py` to record visual analysis artifacts.
- Modify `vbook_client/cli.py` and `tests/test_client/test_manifest_cli.py` to expose `--analyze-vision-placeholder`.

### Task 1: Placeholder Visual Analysis

**Files:**
- Create: `tests/test_vision/test_analysis.py`
- Create: `vbook_vision/analysis.py`

- [x] **Step 1: Write the failing visual analysis tests**

```python
def test_analyze_frames_placeholder_creates_visual_analysis_records(self) -> None:
    frames = [
        FrameCandidate("frame-000001", "lesson", 0.0, Path("frame_000001.jpg"), 0, 0)
    ]

    analyses = analyze_frames_placeholder(frames)

    self.assertEqual(len(analyses), 1)
    self.assertEqual(analyses[0].frame_id, "frame-000001")
    self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
    self.assertEqual(analyses[0].image_path, Path("frame_000001.jpg"))
    self.assertEqual(analyses[0].backend, "placeholder")
    self.assertIn("pending", analyses[0].vision_description)
```

```python
def test_write_visual_analysis_writes_json(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "vision" / "analysis.json"
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.OTHER,
                image_path=Path("frame.jpg"),
                backend="placeholder",
            )
        ]

        written = write_visual_analysis(analyses, path)
        data = json.loads(written.read_text(encoding="utf-8"))

    self.assertEqual(data["analysis_count"], 1)
    self.assertEqual(data["analyses"][0]["visual_type"], "other")
    self.assertEqual(data["backend"], "placeholder")
```

- [x] **Step 2: Verify the tests fail**

Run: `python -m unittest tests.test_vision.test_analysis`
Expected: FAIL because `vbook_vision.analysis` does not exist.

- [x] **Step 3: Implement placeholder analysis**

Add `analyze_frames_placeholder(frames, backend="placeholder") -> list[VisualAnalysis]` and `write_visual_analysis(analyses, path, backend="placeholder") -> Path`. Use `to_jsonable`, formatted UTF-8 JSON, and create parent directories.

- [x] **Step 4: Verify analysis tests pass**

Run: `python -m unittest tests.test_vision.test_analysis`
Expected: OK.

### Task 2: Manifest Vision Artifacts

**Files:**
- Modify: `tests/test_export/test_manifest.py`
- Modify: `vbook_export/manifest.py`

- [x] **Step 1: Write the failing manifest vision test**

```python
def test_build_manifest_can_record_visual_analysis(self) -> None:
    analyses = [
        VisualAnalysis(
            frame_id="frame-000001",
            visual_type=VisualType.OTHER,
            image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
            backend="placeholder",
        )
    ]

    manifest = build_manifest(
        video_path=Path("course/lesson.mp4"),
        transcript_path=Path("course/transcript.json"),
        output_dir=Path("outputs/lesson"),
        segments=[],
        config={},
        visual_analyses=analyses,
        visual_analysis_path=Path("outputs/lesson/vision/analysis.json"),
    )

    self.assertEqual(manifest.artifacts["vision"]["analysis_count"], 1)
    self.assertEqual(manifest.artifacts["vision"]["analysis_path"], Path("outputs/lesson/vision/analysis.json"))
    self.assertEqual(manifest.pipeline_run.stage_status["vision_analysis"], StageStatus.DONE)
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: FAIL because `build_manifest` does not accept `visual_analyses`.

- [x] **Step 3: Extend manifest construction**

Add optional `visual_analyses` and `visual_analysis_path`. Stage status should include `vision_analysis: skipped` by default and `done` when analyses are provided. Record `artifacts["vision"]` with `analysis_count`, `analysis_path`, and `analyses`.

- [x] **Step 4: Verify manifest tests pass**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: OK.

### Task 3: CLI Placeholder Vision Wiring

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Write the failing CLI placeholder vision test**

```python
def test_manifest_command_can_write_placeholder_visual_analysis(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        video = root / "lesson.mp4"
        transcript = root / "transcript.json"
        output = root / "outputs" / "lesson"
        candidate_dir = output / "frames" / "candidates"
        video.write_text("placeholder", encoding="utf-8")
        transcript.write_text(
            json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
            encoding="utf-8",
        )
        candidate_dir.mkdir(parents=True)
        (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

        code = main(
            [
                "manifest",
                "--video",
                str(video),
                "--transcript",
                str(transcript),
                "--output",
                str(output),
                "--frame-candidates-dir",
                str(candidate_dir),
                "--analyze-vision-placeholder",
            ]
        )

        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        vision = json.loads((output / "vision" / "analysis.json").read_text(encoding="utf-8"))

    self.assertEqual(code, 0)
    self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)
    self.assertEqual(vision["analyses"][0]["backend"], "placeholder")
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: FAIL because the CLI flag does not exist.

- [x] **Step 3: Implement CLI placeholder vision**

Add `--analyze-vision-placeholder` and optional `--visual-analysis-path`. Require frame metadata when the flag is used. Use selected frames if selection ran, otherwise candidates. Default path is `<output>/vision/analysis.json`. Write analysis JSON and pass analyses/path into `build_manifest`.

- [x] **Step 4: Verify CLI tests pass**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: OK.

### Task 4: Verification and Delivery

**Files:**
- Modify only if verification exposes small consistency issues.

- [x] Run `python -m unittest discover`.
- [x] Run `python -m ruff check .`; if `ruff` is unavailable, record the missing tool.
- [x] Run a temporary CLI manifest command with `--analyze-vision-placeholder` and inspect `vision.analysis_count`.
- [x] Run `git status --short --branch`.
- [ ] Commit with `git commit -m "feat: add vision placeholder foundation"`.
- [ ] Push to `origin main`, then verify remote with `git ls-remote --heads origin main`, `git rev-parse HEAD`, and `git rev-parse origin/main`.

## Self-Review

- Spec coverage: this plan covers `vision/analysis.json`, `VisualAnalysis[]`, and manifest traceability.
- Scope boundary: no OCR, multimodal model call, visual type classifier, prompt generation, fusion, note generation, or server API.
- Type consistency: the plan uses existing `VisualAnalysis`, `VisualType`, `FrameCandidate`, `StageStatus`, and `Manifest` contracts.
