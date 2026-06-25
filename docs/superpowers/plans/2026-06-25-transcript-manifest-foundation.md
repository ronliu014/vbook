# vBook Transcript Manifest Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the P2 foundation that imports timestamped transcripts and writes a minimal `manifest.json` for a local vBook run.

**Architecture:** Keep this step as a local CLI foundation, not a media-processing pipeline. `vbook_audio` owns transcript parsing, `vbook_export` owns manifest construction and JSON writing, and `vbook_client` wires the two modules into a small command.

**Tech Stack:** Python 3.11+, stdlib `json`, `argparse`, `dataclasses`, `pathlib`, `unittest`.

---

## File Structure

- Create `vbook_audio/transcript.py` for JSON transcript import into `TranscriptSegment` values.
- Create `vbook_export/manifest.py` for deterministic `Manifest` construction and JSON writing.
- Modify `vbook_client/cli.py` to add `manifest --video --transcript --output` with optional course and lesson metadata.
- Create `tests/test_audio/test_transcript.py`, `tests/test_export/test_manifest.py`, and `tests/test_client/test_manifest_cli.py`.

### Task 1: Transcript Import

**Files:**
- Create: `tests/test_audio/__init__.py`
- Create: `tests/test_audio/test_transcript.py`
- Create: `vbook_audio/transcript.py`

- [x] **Step 1: Write the failing transcript import test**

```python
def test_loads_object_wrapped_segments_with_stable_ids(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "transcript.json"
        path.write_text(
            json.dumps(
                {
                    "segments": [
                        {"start": 0, "end": 4.2, "text": "课程开场", "language": "zh"},
                        {"start": 4.2, "end": 9.0, "text": "讲解均线支撑", "confidence": 0.92},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        segments = load_transcript(path)

    self.assertEqual([segment.id for segment in segments], ["seg-000001", "seg-000002"])
    self.assertEqual(segments[0].text, "课程开场")
    self.assertEqual(segments[0].source, TranscriptSourceType.IMPORTED)
    self.assertEqual(segments[1].confidence, 0.92)
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_audio.test_transcript`
Expected: FAIL because `vbook_audio.transcript` does not exist.

- [x] **Step 3: Implement transcript import**

Add `load_transcript(path, source=TranscriptSourceType.IMPORTED)` that accepts either a JSON object with `segments` or a JSON list. Validate each segment has numeric `start`, numeric `end`, and non-empty `text`; reject `end < start`.

- [x] **Step 4: Verify transcript import passes**

Run: `python -m unittest tests.test_audio.test_transcript`
Expected: OK.

### Task 2: Manifest Construction and Writing

**Files:**
- Create: `tests/test_export/__init__.py`
- Create: `tests/test_export/test_manifest.py`
- Create: `vbook_export/manifest.py`

- [x] **Step 1: Write the failing manifest tests**

```python
def test_build_manifest_records_inputs_outputs_and_stage_status(self) -> None:
    segments = [TranscriptSegment(id="seg-000001", start=0, end=4, text="intro")]
    manifest = build_manifest(
        video_path=Path("course/lesson.mp4"),
        transcript_path=Path("course/transcript.json"),
        output_dir=Path("outputs/lesson"),
        segments=segments,
        config={"vision_backend": "multimodal"},
        course_title="Stock Course",
        lesson_title="MA Support",
    )

    self.assertEqual(manifest.video_asset.id, "lesson")
    self.assertEqual(manifest.video_asset.course_title, "Stock Course")
    self.assertEqual(manifest.artifacts["transcript"]["segment_count"], 1)
    self.assertEqual(manifest.pipeline_run.stage_status["transcript_import"], StageStatus.DONE)
    self.assertEqual(manifest.note_path, Path("outputs/lesson/note.md"))
```

```python
def test_write_manifest_creates_json_file(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "lesson"
        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=output_dir,
            segments=[],
            config={},
        )

        written = write_manifest(manifest, output_dir / "manifest.json")
        data = json.loads(written.read_text(encoding="utf-8"))

    self.assertEqual(data["schema_version"], "1")
    self.assertEqual(data["transcript_source"], "imported")
    self.assertEqual(data["stage_status"]["manifest"], "done")
```

- [x] **Step 2: Verify the tests fail**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: FAIL because `vbook_export.manifest` does not exist.

- [x] **Step 3: Implement manifest functions**

Add `build_manifest(...) -> Manifest` and `write_manifest(manifest, path) -> Path`. Use `to_jsonable` and formatted UTF-8 JSON. Do not create `note.md` yet; only record the planned path.

- [x] **Step 4: Verify manifest tests pass**

Run: `python -m unittest tests.test_export.test_manifest`
Expected: OK.

### Task 3: CLI Manifest Command

**Files:**
- Modify: `vbook_client/cli.py`
- Create: `tests/test_client/test_manifest_cli.py`

- [x] **Step 1: Write the failing CLI test**

```python
def test_manifest_command_writes_manifest_json(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        video = root / "lesson.mp4"
        transcript = root / "transcript.json"
        output = root / "outputs" / "lesson"
        video.write_text("placeholder", encoding="utf-8")
        transcript.write_text(
            json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
            encoding="utf-8",
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            code = main(
                [
                    "manifest",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--course-title",
                    "Stock Course",
                    "--lesson-title",
                    "MA Support",
                ]
            )

        manifest_path = output / "manifest.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

    self.assertEqual(code, 0)
    self.assertIn(str(manifest_path), stdout.getvalue())
    self.assertEqual(data["artifacts"]["transcript"]["segment_count"], 1)
    self.assertEqual(data["video_asset"]["lesson_title"], "MA Support")
```

- [x] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: FAIL because the CLI has no `manifest` command.

- [x] **Step 3: Implement the CLI command**

Add `manifest` subparser with `--video`, `--transcript`, `--output`, optional `--course-title`, `--lesson-title`, and optional `--config`. Load config, import transcript, build manifest, write `manifest.json`, then print the manifest path.

- [x] **Step 4: Verify CLI test passes**

Run: `python -m unittest tests.test_client.test_manifest_cli`
Expected: OK.

### Task 4: Full Verification and Commit

**Files:**
- Modify as needed only if verification exposes small consistency gaps.

- [x] Run `python -m unittest discover`.
- [x] Run `python -m vbook_client manifest --video sample.mp4 --transcript sample.json --output outputs/sample` only with temporary files, not committed fixtures.
- [x] Run `git status --short --branch`.
- [x] Commit with `git commit -m "feat: add transcript manifest foundation"`.
- [ ] Push to `origin main`, then verify remote with `git ls-remote --heads origin main`, `git rev-parse HEAD`, and `git rev-parse origin/main`.

## Self-Review

- Spec coverage: P2 foundation covers timestamped transcript input and minimal `manifest.json`; later P2 work still owns frames, visual analysis, alignment, fusion, and `note.md`.
- Scope boundary: no vtext runtime dependency, no media probing, no frame extraction, no OCR, no multi-modal model calls, and no server API.
- Type consistency: tests and implementation use existing `TranscriptSegment`, `TranscriptSourceType`, `Manifest`, `VideoAsset`, `PipelineRun`, and `StageStatus`.
