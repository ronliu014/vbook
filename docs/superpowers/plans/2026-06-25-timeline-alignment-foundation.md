# vBook Timeline Alignment Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a P2 timestamp-window alignment foundation that links selected or candidate frames to nearby transcript segments.

**Architecture:** `vbook_pipeline.timeline` owns timestamp-window matching and returns existing `TimelineLink` dataclasses. `vbook_export.manifest` records optional timeline links as a machine-readable artifact. `vbook_client manifest` can align frames and transcript during manifest generation when frame metadata is available.

**Tech Stack:** Python 3.11+, stdlib `unittest`, existing `FrameCandidate`, `TranscriptSegment`, `TimelineLink`, and manifest serialization.

---

## File Structure

- Create `vbook_pipeline/timeline.py` for timestamp-window linking.
- Create `tests/test_pipeline/test_timeline.py` for deterministic alignment tests.
- Modify `vbook_export/manifest.py` and `tests/test_export/test_manifest.py` to record timeline links.
- Modify `vbook_client/cli.py` and `tests/test_client/test_manifest_cli.py` to expose CLI alignment flags.

### Task 1: Timeline Linking Module

**Files:**
- Create: `tests/test_pipeline/__init__.py`
- Create: `tests/test_pipeline/test_timeline.py`
- Create: `vbook_pipeline/timeline.py`

- [x] **Step 1: Write the failing timeline-linking test**

```python
def test_link_frames_to_transcript_uses_timestamp_window_overlap(self) -> None:
    frames = [
        FrameCandidate("frame-000001", "lesson", 10.0, Path("frame1.jpg"), 0, 0),
        FrameCandidate("frame-000002", "lesson", 30.0, Path("frame2.jpg"), 0, 0),
    ]
    segments = [
        TranscriptSegment("seg-000001", 0.0, 6.0, "intro"),
        TranscriptSegment("seg-000002", 8.0, 12.0, "moving average"),
        TranscriptSegment("seg-000003", 24.0, 28.0, "setup"),
        TranscriptSegment("seg-000004", 40.0, 45.0, "later"),
    ]

    links = link_frames_to_transcript(frames, segments, window_seconds=5.0)

    self.assertEqual([link.frame_id for link in links], ["frame-000001", "frame-000002"])
    self.assertEqual(links[0].transcript_segment_ids, ["seg-000002"])
    self.assertEqual(links[0].window_start, 5.0)
    self.assertEqual(links[0].window_end, 15.0)
    self.assertEqual(links[1].transcript_segment_ids, ["seg-000003"])
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_pipeline.test_timeline`
Expected: FAIL because `vbook_pipeline.timeline` does not exist.

- [x] **Step 3: Implement timestamp-window linking**

Add `link_frames_to_transcript(frames, segments, window_seconds, match_strategy="timestamp_window") -> list[TimelineLink]`. Clamp `window_start` to `0.0`, reject negative windows, and match transcript segments whose time range overlaps the frame window.

- [x] **Step 4: Verify timeline tests pass**

Run: `python -m unittest tests.test_pipeline.test_timeline`
Expected: OK.

### Task 2: Manifest Timeline Artifacts

**Files:**
- Modify: `tests/test_export/test_manifest.py`
- Modify: `vbook_export/manifest.py`

- [x] **Step 1: Write the failing manifest timeline test**

```python
def test_build_manifest_can_record_timeline_links(self) -> None:
    links = [
        TimelineLink(
            frame_id="frame-000001",
            transcript_segment_ids=["seg-000001"],
            window_start=0.0,
            window_end=10.0,
        )
    ]

    manifest = build_manifest(
        video_path=Path("course/lesson.mp4"),
        transcript_path=Path("course/transcript.json"),
        output_dir=Path("outputs/lesson"),
        segments=[],
        config={},
        timeline_links=links,
    )

    self.assertEqual(manifest.artifacts["timeline"]["link_count"], 1)
    self.assertEqual(manifest.artifacts["timeline"]["links"], links)
    self.assertEqual(manifest.pipeline_run.stage_status["timeline_alignment"], StageStatus.DONE)
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: FAIL because `build_manifest` does not accept `timeline_links`.

- [x] **Step 3: Extend manifest construction**

Add optional `timeline_links: Sequence[TimelineLink] | None = None`. Stage status should include `timeline_alignment: skipped` by default and `done` when links are provided. Record `artifacts["timeline"]` with `link_count`, `links`, and `match_strategy`.

- [x] **Step 4: Verify manifest tests pass**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: OK.

### Task 3: CLI Timeline Alignment

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Write the failing CLI alignment test**

```python
def test_manifest_command_can_align_selected_frames_to_transcript(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        video = root / "lesson.mp4"
        transcript = root / "transcript.json"
        output = root / "outputs" / "lesson"
        candidate_dir = output / "frames" / "candidates"
        video.write_text("placeholder", encoding="utf-8")
        transcript.write_text(
            json.dumps(
                {
                    "segments": [
                        {"start": 0, "end": 3, "text": "intro"},
                        {"start": 8, "end": 12, "text": "case"},
                    ]
                }
            ),
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
                "--frame-interval-seconds",
                "10",
                "--align-timeline",
                "--alignment-window-seconds",
                "3",
            ]
        )

        data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    self.assertEqual(code, 0)
    self.assertEqual(data["artifacts"]["timeline"]["link_count"], 1)
    self.assertEqual(
        data["artifacts"]["timeline"]["links"][0]["transcript_segment_ids"],
        ["seg-000002"],
    )
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: FAIL because timeline CLI arguments do not exist.

- [x] **Step 3: Implement CLI alignment wiring**

Add `--align-timeline` and `--alignment-window-seconds`. If alignment is requested, require frame metadata. Use selected frames when selection ran, otherwise use discovered candidate frames. Default alignment window comes from config when CLI value is omitted.

- [x] **Step 4: Verify CLI tests pass**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: OK.

### Task 4: Verification and Delivery

**Files:**
- Modify only if verification exposes small consistency issues.

- [x] Run `python -m unittest discover`.
- [x] Run `python -m ruff check .`; if `ruff` is unavailable, record the missing tool.
- [x] Run a temporary CLI manifest command with `--align-timeline` and inspect `timeline.link_count`.
- [x] Run `git status --short --branch`.
- [ ] Commit with `git commit -m "feat: add timeline alignment foundation"`.
- [ ] Push to `origin main`, then verify remote with `git ls-remote --heads origin main`, `git rev-parse HEAD`, and `git rev-parse origin/main`.

## Self-Review

- Spec coverage: this plan covers timestamp-window alignment and manifest traceability for future visual analysis and fusion.
- Scope boundary: no semantic similarity, OCR, multimodal analysis, visual classification, fusion, note generation, or server API.
- Type consistency: the plan uses existing `TimelineLink`, `FrameCandidate`, `TranscriptSegment`, `StageStatus`, and `Manifest` contracts.
