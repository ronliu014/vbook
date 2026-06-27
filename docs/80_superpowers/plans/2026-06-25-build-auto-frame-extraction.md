# Build Auto Frame Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `python -m vbook_client build` extract candidate frames from `--video` when `--frame-candidates-dir` is not provided.

**Architecture:** Reuse the existing `vbook_vision.frames.extract_frame_candidates()` function. Keep `manifest` unchanged as a low-level command that only records an explicit frame candidate directory; make `build` the high-level command that fills `<output>/frames/candidates` automatically.

**Tech Stack:** Python 3.11 standard library, existing ffmpeg command builder, `unittest`, `unittest.mock`.

---

### Task 1: CLI Auto Extraction Test

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`

- [x] **Step 1: Write failing build test**

Add a test named `test_build_command_extracts_frames_when_candidate_dir_omitted`. Patch `vbook_client.cli.extract_frame_candidates` so the test does not call ffmpeg:

```python
with patch("vbook_client.cli.extract_frame_candidates") as extract:
    extract.side_effect = lambda video_path, candidate_dir, video_id, interval_seconds: [
        FrameCandidate(
            id="frame-000001",
            video_id=video_id,
            timestamp=0.0,
            image_path=Path(candidate_dir) / "frame_000001.jpg",
            width=0,
            height=0,
        )
    ]
```

Run `main(["build", "--video", ..., "--transcript", ..., "--output", ...])` without `--frame-candidates-dir`. Assert:
- exit code is `0`
- extractor was called once
- `candidate_dir` equals `<output>/frames/candidates`
- manifest frame candidate count is `1`
- timeline, vision, fusion, note, and manifest stages are `done`

- [x] **Step 2: Run RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: failure because `build` still requires frame metadata and never calls `extract_frame_candidates`.

### Task 2: CLI Pipeline Wiring

**Files:**
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Import extractor**

Change the frames import to include `extract_frame_candidates`.

- [x] **Step 2: Add build default**

In the `build` dispatch defaults, add:

```python
"extract_frames": True,
```

- [x] **Step 3: Auto-extract frames in helper**

In `_run_manifest_pipeline`, compute `video_id = Path(args.output).name or Path(args.video).stem`. Then:
- If `args.frame_candidates_dir` is present, keep existing discovery behavior.
- Else if `_flag(args, "extract_frames", defaults)` is true, call `extract_frame_candidates()` with:
  - `video_path=args.video`
  - `candidate_dir=Path(args.output) / "frames" / "candidates"`
  - `video_id=video_id`
  - `interval_seconds=args.frame_interval_seconds`

Do not enable this default for `manifest`.

- [x] **Step 4: Run GREEN**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: all CLI manifest/build tests pass.

### Task 3: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: this plan file

- [x] **Step 1: Update README command**

Show the main build example without `--frame-candidates-dir`, then mention the flag can still point at an existing candidate directory.

- [x] **Step 2: Run full verification**

Run:

```sh
python -m unittest discover
git diff --check
python -m ruff check .
```

Expected: unit tests pass and whitespace check passes. If `ruff` is unavailable, record `No module named ruff`.

- [x] **Step 3: Run real MP4 smoke when ffmpeg is available**

Run:

```sh
python -m vbook_client build \
  --video E:/projects/my_app/temp/三分钟学会选短线个股.mp4 \
  --transcript E:/projects/my_app/temp/text/三分钟学会选短线个股.srt \
  --output <temp-output> \
  --frame-interval-seconds 30 \
  --alignment-window-seconds 5
```

Then verify `frames/candidates`, `manifest.json`, `note.md`, `vision/analysis.json`, `fusion/prompt.json`, and `fusion/sections.json` exist. If ffmpeg is unavailable, record the exact error and do not claim smoke success.

- [ ] **Step 4: Commit and push**

Commit with:

```sh
git add docs/superpowers/plans/2026-06-25-build-auto-frame-extraction.md README.md tests/test_client/test_manifest_cli.py vbook_client/cli.py
git commit -m "feat: extract frames during build"
git push origin main
```

- [ ] **Step 5: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
