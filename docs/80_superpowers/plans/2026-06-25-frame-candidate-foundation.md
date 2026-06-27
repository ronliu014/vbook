# vBook Frame Candidate Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the P2 foundation for frame candidate extraction metadata without implementing duplicate filtering, OCR, or visual understanding.

**Architecture:** `vbook_vision.frames` owns ffmpeg command construction, injectable execution, and discovery of generated candidate files. `vbook_export.manifest` records optional frame candidates as machine-readable artifacts. `vbook_client manifest` can include an existing candidate frame directory in the manifest, while direct ffmpeg execution remains available through the vision module for later pipeline orchestration.

**Tech Stack:** Python 3.11+, stdlib `pathlib`, `subprocess`, `unittest`, existing dataclasses and JSON serialization.

---

## File Structure

- Create `vbook_vision/frames.py` for frame extraction command construction and candidate discovery.
- Create `tests/test_vision/test_frames.py` for deterministic frame tests with an injected runner.
- Modify `vbook_export/manifest.py` to accept optional `FrameCandidate` records.
- Modify `tests/test_export/test_manifest.py` to verify frame artifact serialization.
- Modify `vbook_client/cli.py` to accept `--frame-candidates-dir` and `--frame-interval-seconds` on `manifest`.
- Modify `tests/test_client/test_manifest_cli.py` to verify existing candidate frames are included.

### Task 1: Frame Candidate Module

**Files:**
- Create: `tests/test_vision/__init__.py`
- Create: `tests/test_vision/test_frames.py`
- Create: `vbook_vision/frames.py`

- [x] **Step 1: Write the failing frame command and discovery tests**

```python
def test_build_ffmpeg_frame_command_uses_interval_and_pattern(self) -> None:
    command = build_ffmpeg_frame_command(
        video_path=Path("videos/lesson.mp4"),
        candidate_dir=Path("outputs/lesson/frames/candidates"),
        interval_seconds=3.0,
    )

    self.assertEqual(command[:3], ["ffmpeg", "-y", "-i"])
    self.assertIn("videos/lesson.mp4", command)
    self.assertIn("fps=1/3", command)
    self.assertEqual(command[-1], "outputs/lesson/frames/candidates/frame_%06d.jpg")
```

```python
def test_extract_frame_candidates_runs_runner_and_discovers_frames(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        candidate_dir = Path(tmp) / "frames" / "candidates"
        captured = []

        def runner(command: list[str]) -> None:
            captured.append(command)
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            (candidate_dir / "frame_000002.jpg").write_text("b", encoding="utf-8")

        frames = extract_frame_candidates(
            video_path=Path("videos/lesson.mp4"),
            candidate_dir=candidate_dir,
            video_id="lesson",
            interval_seconds=2.5,
            runner=runner,
        )

    self.assertEqual(len(captured), 1)
    self.assertEqual([frame.id for frame in frames], ["frame-000001", "frame-000002"])
    self.assertEqual([frame.timestamp for frame in frames], [0.0, 2.5])
    self.assertEqual(frames[0].filter_status, FilterStatus.CANDIDATE)
```

- [x] **Step 2: Verify the tests fail**

Run: `python -m unittest tests.test_vision.test_frames`
Expected: FAIL because `vbook_vision.frames` does not exist.

- [x] **Step 3: Implement frame candidate functions**

Add:
- `build_ffmpeg_frame_command(video_path, candidate_dir, interval_seconds, ffmpeg_bin="ffmpeg") -> list[str]`
- `discover_frame_candidates(candidate_dir, video_id, interval_seconds, image_size=(0, 0)) -> list[FrameCandidate]`
- `extract_frame_candidates(video_path, candidate_dir, video_id, interval_seconds, runner=None, ffmpeg_bin="ffmpeg") -> list[FrameCandidate]`

Reject non-positive intervals. Use `frame_%06d.jpg` as the extraction pattern and infer timestamps by sorted file order.

- [x] **Step 4: Verify frame tests pass**

Run: `python -m unittest tests.test_vision.test_frames`
Expected: OK.

### Task 2: Manifest Frame Artifacts

**Files:**
- Modify: `tests/test_export/test_manifest.py`
- Modify: `vbook_export/manifest.py`

- [x] **Step 1: Write the failing manifest frame artifact test**

```python
def test_build_manifest_can_record_frame_candidates(self) -> None:
    frames = [
        FrameCandidate(
            id="frame-000001",
            video_id="lesson",
            timestamp=0.0,
            image_path=Path("outputs/lesson/frames/candidates/frame_000001.jpg"),
            width=0,
            height=0,
        )
    ]

    manifest = build_manifest(
        video_path=Path("course/lesson.mp4"),
        transcript_path=Path("course/transcript.json"),
        output_dir=Path("outputs/lesson"),
        segments=[],
        config={},
        frames=frames,
    )

    self.assertEqual(manifest.artifacts["frames"]["candidate_count"], 1)
    self.assertEqual(manifest.pipeline_run.stage_status["frame_extraction"], StageStatus.DONE)
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: FAIL because `build_manifest` has no `frames` argument.

- [x] **Step 3: Extend manifest construction**

Add optional `frames: Sequence[FrameCandidate] | None = None`. If `frames is None`, mark `frame_extraction` as `StageStatus.SKIPPED`; otherwise include `artifacts["frames"]` with candidate directory, candidate count, and candidate records, and mark `frame_extraction` as `StageStatus.DONE`.

- [x] **Step 4: Verify manifest tests pass**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: OK.

### Task 3: CLI Manifest Frame Directory

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Write the failing CLI frame directory test**

```python
def test_manifest_command_includes_existing_frame_candidates(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        video = root / "lesson.mp4"
        transcript = root / "transcript.json"
        candidate_dir = root / "outputs" / "lesson" / "frames" / "candidates"
        output = root / "outputs" / "lesson"
        video.write_text("placeholder", encoding="utf-8")
        transcript.write_text(
            json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
            encoding="utf-8",
        )
        candidate_dir.mkdir(parents=True)
        (candidate_dir / "frame_000001.jpg").write_text("image", encoding="utf-8")

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
                "--frame-interval-seconds",
                "2",
            ]
        )

        data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    self.assertEqual(code, 0)
    self.assertEqual(data["artifacts"]["frames"]["candidate_count"], 1)
    self.assertEqual(data["artifacts"]["frames"]["candidates"][0]["timestamp"], 0.0)
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: FAIL because the CLI does not accept frame candidate arguments.

- [x] **Step 3: Implement CLI frame candidate wiring**

Add `--frame-candidates-dir` and `--frame-interval-seconds` to the `manifest` command. If a frame directory is provided, call `discover_frame_candidates` and pass the resulting frames into `build_manifest`.

- [x] **Step 4: Verify CLI tests pass**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: OK.

### Task 4: Verification and Delivery

**Files:**
- Modify only if verification exposes small consistency issues.

- [x] Run `python -m unittest discover`.
- [x] Run `python -m ruff check .`; if `ruff` is unavailable, record the missing tool.
- [x] Run `git status --short --branch`.
- [ ] Commit with `git commit -m "feat: add frame candidate foundation"`.
- [ ] Push to `origin main`, then verify remote with `git ls-remote --heads origin main`, `git rev-parse HEAD`, and `git rev-parse origin/main`.

## Self-Review

- Spec coverage: this plan covers configurable frame interval, candidate directory structure, frame metadata, and manifest traceability.
- Scope boundary: no duplicate filtering, image-size probing, OCR, multimodal analysis, visual type classification, timeline alignment, fusion, note generation, or server API.
- Type consistency: the plan uses existing `FrameCandidate`, `FilterStatus`, `StageStatus`, and `Manifest` contracts.
