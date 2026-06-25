# vBook Frame Selection Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic P2 frame filtering foundation that promotes candidate frames into `frames/selected/` and records selected/rejected metadata.

**Architecture:** Keep selection separate from extraction. `vbook_vision.frames` will add a simple interval-based selector that copies selected image files to a selected directory, marks selected frames as `FilterStatus.SELECTED`, and marks skipped frames as `FilterStatus.REJECTED` with a reason. `vbook_export.manifest` records candidate and selected counts, while `vbook_client manifest` can optionally apply selection when an existing candidate directory is provided.

**Tech Stack:** Python 3.11+, stdlib `pathlib`, `shutil`, `unittest`, existing `FrameCandidate`/`FilterStatus` dataclasses.

---

## File Structure

- Modify `vbook_vision/frames.py` to add `select_frame_candidates(...)`.
- Modify `tests/test_vision/test_frames.py` for interval-based selection behavior.
- Modify `vbook_export/manifest.py` and `tests/test_export/test_manifest.py` to record selected frames.
- Modify `vbook_client/cli.py` and `tests/test_client/test_manifest_cli.py` to expose selection flags.

### Task 1: Frame Selection Function

**Files:**
- Modify: `tests/test_vision/test_frames.py`
- Modify: `vbook_vision/frames.py`

- [x] **Step 1: Write the failing frame selection test**

```python
def test_select_frame_candidates_copies_selected_frames_and_rejects_nearby_frames(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        selected_dir = root / "selected"
        source_a = root / "frame_000001.jpg"
        source_b = root / "frame_000002.jpg"
        source_c = root / "frame_000003.jpg"
        source_a.write_text("a", encoding="utf-8")
        source_b.write_text("b", encoding="utf-8")
        source_c.write_text("c", encoding="utf-8")
        candidates = [
            FrameCandidate("frame-000001", "lesson", 0.0, source_a, 0, 0),
            FrameCandidate("frame-000002", "lesson", 2.0, source_b, 0, 0),
            FrameCandidate("frame-000003", "lesson", 6.0, source_c, 0, 0),
        ]

        selected, rejected = select_frame_candidates(
            candidates,
            selected_dir=selected_dir,
            min_interval_seconds=5.0,
        )

    self.assertEqual([frame.id for frame in selected], ["frame-000001", "frame-000003"])
    self.assertEqual([frame.id for frame in rejected], ["frame-000002"])
    self.assertEqual(selected[0].filter_status, FilterStatus.SELECTED)
    self.assertEqual(rejected[0].filter_status, FilterStatus.REJECTED)
    self.assertEqual(rejected[0].filter_reason, "within_min_interval")
    self.assertTrue((selected_dir / "frame_000001.jpg").exists())
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_vision.test_frames`
Expected: FAIL because `select_frame_candidates` is not defined.

- [x] **Step 3: Implement selection**

Add `select_frame_candidates(candidates, selected_dir, min_interval_seconds, copier=shutil.copy2) -> tuple[list[FrameCandidate], list[FrameCandidate]]`. Sort by timestamp, always select the first frame, select later frames only when `timestamp - last_selected_timestamp >= min_interval_seconds`, copy selected images into `selected_dir`, and preserve ids/timestamps/video ids.

- [x] **Step 4: Verify frame tests pass**

Run: `python -m unittest tests.test_vision.test_frames`
Expected: OK.

### Task 2: Manifest Selected Frame Records

**Files:**
- Modify: `tests/test_export/test_manifest.py`
- Modify: `vbook_export/manifest.py`

- [x] **Step 1: Write the failing manifest selected-frame test**

```python
def test_build_manifest_can_record_selected_and_rejected_frames(self) -> None:
    selected = [
        FrameCandidate(
            id="frame-000001",
            video_id="lesson",
            timestamp=0.0,
            image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
            width=0,
            height=0,
            filter_status=FilterStatus.SELECTED,
        )
    ]
    rejected = [
        FrameCandidate(
            id="frame-000002",
            video_id="lesson",
            timestamp=2.0,
            image_path=Path("outputs/lesson/frames/candidates/frame_000002.jpg"),
            width=0,
            height=0,
            filter_status=FilterStatus.REJECTED,
            filter_reason="within_min_interval",
        )
    ]

    manifest = build_manifest(
        video_path=Path("course/lesson.mp4"),
        transcript_path=Path("course/transcript.json"),
        output_dir=Path("outputs/lesson"),
        segments=[],
        config={},
        frames=selected + rejected,
        selected_frames=selected,
        rejected_frames=rejected,
    )

    self.assertEqual(manifest.artifacts["frames"]["selected_count"], 1)
    self.assertEqual(manifest.artifacts["frames"]["rejected_count"], 1)
    self.assertEqual(manifest.artifacts["frames"]["selection_strategy"], "min_interval")
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: FAIL because `build_manifest` does not accept selected/rejected frame arguments.

- [x] **Step 3: Extend manifest artifacts**

Add optional `selected_frames`, `rejected_frames`, and `selection_strategy="min_interval"` arguments. When present, include `selected_dir`, `selected_count`, `rejected_count`, `selected`, `rejected`, and `selection_strategy` in `artifacts["frames"]`.

- [x] **Step 4: Verify manifest tests pass**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: OK.

### Task 3: CLI Selection Wiring

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Write the failing CLI selection test**

```python
def test_manifest_command_can_select_existing_frame_candidates(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        video = root / "lesson.mp4"
        transcript = root / "transcript.json"
        output = root / "outputs" / "lesson"
        candidate_dir = output / "frames" / "candidates"
        selected_dir = output / "frames" / "selected"
        video.write_text("placeholder", encoding="utf-8")
        transcript.write_text(
            json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
            encoding="utf-8",
        )
        candidate_dir.mkdir(parents=True)
        (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
        (candidate_dir / "frame_000002.jpg").write_text("b", encoding="utf-8")

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
                "--select-frames",
                "--selected-frames-dir",
                str(selected_dir),
                "--min-selected-frame-interval-seconds",
                "3",
            ]
        )

        data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    self.assertEqual(code, 0)
    self.assertEqual(data["artifacts"]["frames"]["selected_count"], 1)
    self.assertEqual(data["artifacts"]["frames"]["rejected_count"], 1)
    self.assertTrue((selected_dir / "frame_000001.jpg").exists())
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: FAIL because selection CLI arguments do not exist.

- [x] **Step 3: Implement CLI selection**

Add `--select-frames`, `--selected-frames-dir`, and `--min-selected-frame-interval-seconds`. If `--select-frames` is present, require `--frame-candidates-dir`, default selected dir to `<output>/frames/selected`, call `select_frame_candidates`, and pass selected/rejected frames into `build_manifest`.

- [x] **Step 4: Verify CLI tests pass**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: OK.

### Task 4: Verification and Delivery

**Files:**
- Modify only if verification exposes small consistency issues.

- [x] Run `python -m unittest discover`.
- [x] Run `python -m ruff check .`; if `ruff` is unavailable, record the missing tool.
- [x] Run a temporary CLI manifest command with `--select-frames` and inspect `selected_count`.
- [x] Run `git status --short --branch`.
- [ ] Commit with `git commit -m "feat: add frame selection foundation"`.
- [ ] Push to `origin main`, then verify remote with `git ls-remote --heads origin main`, `git rev-parse HEAD`, and `git rev-parse origin/main`.

## Self-Review

- Spec coverage: this plan covers `frames/selected/`, selected/rejected metadata, and manifest auditability.
- Scope boundary: no perceptual hash, visual-type classifier, OCR, multimodal analysis, timeline alignment, fusion, note generation, or server API.
- Type consistency: the plan uses existing `FrameCandidate`, `FilterStatus`, `StageStatus`, and `Manifest` contracts.
