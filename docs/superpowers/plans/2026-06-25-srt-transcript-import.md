# SRT Transcript Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow `load_transcript()` and the existing `build` CLI path to accept `.srt` transcript files produced by vtext-compatible workflows.

**Architecture:** Keep transcript loading centralized in `vbook_audio/transcript.py`. Dispatch by file suffix: existing `.json` behavior remains unchanged; `.srt` is parsed into the same `TranscriptSegment` dataclass with stable `seg-000001` IDs.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing vBook dataclasses.

---

### Task 1: SRT Loader Tests

**Files:**
- Modify: `tests/test_audio/test_transcript.py`

- [x] **Step 1: Write failing SRT parsing test**

Add `test_loads_srt_segments_with_stable_ids`, writing a small `.srt` file:

```text
1
00:00:00,000 --> 00:00:02,600
大家好

2
00:00:02,600 --> 00:00:04,919
欢迎来到课程
```

Assert `load_transcript(path)` returns two segments with IDs `seg-000001`, `seg-000002`, start/end seconds `0.0`, `2.6`, `2.6`, `4.919`, and trimmed text.

- [x] **Step 2: Write failing multiline SRT test**

Add `test_loads_multiline_srt_cue_text`, writing one cue with two text lines. Assert the text is joined with a single newline so subtitle line breaks are preserved.

- [x] **Step 3: Run RED**

Run: `python -m unittest tests.test_audio.test_transcript`

Expected: failure because current loader tries to parse `.srt` as JSON.

### Task 2: SRT Parser Implementation

**Files:**
- Modify: `vbook_audio/transcript.py`

- [x] **Step 1: Add suffix dispatch**

In `load_transcript`, branch on `transcript_path.suffix.lower()`. Keep `.json` behavior unchanged and call a new `_load_json_transcript()`. For `.srt`, call `_load_srt_transcript()`. For unsupported suffixes, raise `ValueError("unsupported transcript format: <suffix>")`.

- [x] **Step 2: Implement SRT cue parsing**

Implement helpers:

```python
def _load_srt_transcript(path: Path, source: TranscriptSourceType) -> list[TranscriptSegment]
def _parse_srt_timestamp(value: str) -> float
```

Parsing rules:
- Split cues on blank lines.
- Ignore numeric cue index lines.
- Require a timing line containing `"-->"`.
- Parse `HH:MM:SS,mmm` and tolerate `HH:MM:SS.mmm`.
- Join text lines with `"\n"` and strip surrounding whitespace.
- Skip empty text cues.
- Raise `ValueError` for malformed timing.

- [x] **Step 3: Run GREEN**

Run: `python -m unittest tests.test_audio.test_transcript`

Expected: all transcript tests pass.

### Task 3: CLI SRT Coverage

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`

- [x] **Step 1: Add build test with SRT transcript**

Add a test that writes `transcript.srt`, runs `main(["build", ...])` with an existing frame candidate directory, and asserts `manifest["artifacts"]["transcript"]["segment_count"] == 2` plus `timeline_alignment` is `done`.

- [x] **Step 2: Run target tests**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: pass after Task 2 implementation.

### Task 4: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: this plan file

- [x] **Step 1: Document SRT support**

Add a short note under the build command description: `--transcript` accepts timestamped JSON or SRT files.

- [x] **Step 2: Run full verification**

Run:

```sh
python -m unittest discover
git diff --check
python -m ruff check .
```

Expected: unit tests pass and whitespace check passes. If `ruff` is unavailable, record `No module named ruff`.

- [ ] **Step 3: Commit and push**

Commit with:

```sh
git add docs/superpowers/plans/2026-06-25-srt-transcript-import.md README.md tests/test_audio/test_transcript.py tests/test_client/test_manifest_cli.py vbook_audio/transcript.py
git commit -m "feat: import SRT transcripts"
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
