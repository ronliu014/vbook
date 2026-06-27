# Basic Frame Filtering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic first-pass frame filtering so `build` uses selected frames by default and exact duplicate frame files are rejected.

**Architecture:** Extend the existing `vbook_vision.frames.select_frame_candidates()` function rather than adding a new pipeline abstraction. Keep `manifest` explicit, but make `build` default to selecting frames after extraction/discovery so timeline, vision, fusion, and note stages consume selected frames.

**Tech Stack:** Python 3.11 standard library, `hashlib`, existing dataclasses, `unittest`.

---

### Task 1: Exact Duplicate Filtering

**Files:**
- Modify: `tests/test_vision/test_frames.py`
- Modify: `vbook_vision/frames.py`

- [x] **Step 1: Write failing duplicate-content test**

Add this test to `FrameCandidateTest`:

```python
def test_select_frame_candidates_rejects_exact_duplicate_content(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        selected_dir = root / "selected"
        source_a = root / "frame_000001.jpg"
        source_b = root / "frame_000002.jpg"
        source_a.write_bytes(b"same image bytes")
        source_b.write_bytes(b"same image bytes")
        candidates = [
            FrameCandidate("frame-000001", "lesson", 0.0, source_a, 0, 0),
            FrameCandidate("frame-000002", "lesson", 10.0, source_b, 0, 0),
        ]

        selected, rejected = select_frame_candidates(
            candidates,
            selected_dir=selected_dir,
            min_interval_seconds=1.0,
        )

    self.assertEqual([frame.id for frame in selected], ["frame-000001"])
    self.assertEqual([frame.id for frame in rejected], ["frame-000002"])
    self.assertEqual(rejected[0].filter_status, FilterStatus.REJECTED)
    self.assertEqual(rejected[0].filter_reason, "duplicate_content")
```

- [x] **Step 2: Run RED**

Run: `python -m unittest tests.test_vision.test_frames`

Expected: failure because the second frame is currently selected when the timestamp interval allows it.

- [x] **Step 3: Implement exact file hashing**

In `vbook_vision/frames.py`:
- import `hashlib`
- add a private helper:

```python
def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

In `select_frame_candidates`, maintain `selected_hashes: set[str] = set()`. For each frame that passes the interval rule, compute its hash. If the hash is already selected, append a rejected copy with `filter_reason="duplicate_content"`; otherwise copy and select it, then add the hash.

- [x] **Step 4: Run GREEN**

Run: `python -m unittest tests.test_vision.test_frames`

Expected: all frame tests pass.

### Task 2: Build Defaults to Selected Frames

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Write failing build selection test**

Update `test_build_command_extracts_frames_when_candidate_dir_omitted` so the fake extractor returns two frames, both backed by files with different byte content and timestamps `0.0` and `2.5`. Assert:

```python
self.assertEqual(manifest["artifacts"]["frames"]["candidate_count"], 2)
self.assertEqual(manifest["artifacts"]["frames"]["selected_count"], 1)
self.assertEqual(manifest["artifacts"]["frames"]["rejected_count"], 1)
self.assertEqual(manifest["artifacts"]["frames"]["selection_strategy"], "basic_interval_duplicate")
self.assertEqual(manifest["artifacts"]["frames"]["rejected"][0]["filter_reason"], "within_min_interval")
self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)
self.assertEqual(manifest["artifacts"]["timeline"]["link_count"], 1)
```

Use `--min-selected-frame-interval-seconds 10` so the second frame is rejected by the interval rule.

- [x] **Step 2: Run RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: failure because `build` does not select frames by default and manifest has no selected/rejected counts for this path.

- [x] **Step 3: Enable selection by default for build**

In `vbook_client/cli.py`, add `"select_frames": True` to `build` defaults. Change the selection condition from:

```python
if args.select_frames:
```

to:

```python
if _flag(args, "select_frames", defaults):
```

When calling `build_manifest`, pass:

```python
selection_strategy=(
    "basic_interval_duplicate"
    if selected_frames is not None
    else "min_interval"
)
```

Keep `manifest` behavior unchanged by passing `defaults={}`.

- [x] **Step 4: Run GREEN**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: all CLI tests pass.

### Task 3: Verification and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-25-basic-frame-filtering.md`
- Modify: `tests/test_vision/test_frames.py`
- Modify: `tests/test_client/test_manifest_cli.py`
- Modify: `vbook_vision/frames.py`
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Run full verification**

Run:

```sh
python -m unittest discover
git diff --check
python -m ruff check .
```

Expected: unit tests pass and whitespace check passes. If `ruff` is unavailable, record `No module named ruff`.

- [x] **Step 2: Run real MP4 smoke**

Run a real build with the local sample video and SRT:

```sh
python -m vbook_client build \
  --video E:/projects/my_app/temp/三分钟学会选短线个股.mp4 \
  --transcript E:/projects/my_app/temp/text/三分钟学会选短线个股.srt \
  --output <temp-output> \
  --frame-interval-seconds 30 \
  --min-selected-frame-interval-seconds 60 \
  --alignment-window-seconds 5
```

Verify `manifest.json` records candidate, selected, and rejected counts, and that `vision.analysis_count` equals selected count.

- [ ] **Step 3: Commit and push**

Run:

```sh
git add docs/superpowers/plans/2026-06-25-basic-frame-filtering.md tests/test_vision/test_frames.py tests/test_client/test_manifest_cli.py vbook_vision/frames.py vbook_client/cli.py
git commit -m "feat: select filtered frames during build"
git push origin main
```

- [ ] **Step 4: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
