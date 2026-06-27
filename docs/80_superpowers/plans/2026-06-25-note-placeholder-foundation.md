# Note Placeholder Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit Markdown `note.md` placeholder export path so each MVP run can produce both human-readable notes and `manifest.json`.

**Architecture:** Keep note rendering in `vbook_export.note`, keep manifest artifact indexing in `vbook_export.manifest`, and keep CLI orchestration in `vbook_client.cli`. The note is deterministic and uses existing transcript, frame, visual-analysis, and timeline data without LLM fusion.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing vBook dataclasses and CLI.

---

### Task 1: Note Rendering Module

**Files:**
- Create: `vbook_export/note.py`
- Test: `tests/test_export/test_note.py`

- [ ] **Step 1: Write failing render and write tests**

Create tests that call `render_placeholder_note(...)` with a `VideoAsset`, transcript segments, frames, visual analyses, and timeline links. Assert the Markdown includes the lesson heading, course metadata, transcript count, visual counts, timeline references, and transcript lines. Add a `write_note(...)` test that verifies a UTF-8 Markdown file is created.

- [ ] **Step 2: Run target tests to verify RED**

Run: `python -m unittest tests.test_export.test_note`

Expected: fail because `vbook_export.note` does not exist.

- [ ] **Step 3: Implement minimal note rendering**

Create `render_placeholder_note(...)` and `write_note(...)`. Sort transcript segments by start time, frames by timestamp, visual analyses by frame id, and timeline links by frame id. Keep Markdown readable and deterministic.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_export.test_note`

Expected: pass.

### Task 2: Manifest Note Artifact

**Files:**
- Modify: `vbook_export/manifest.py`
- Test: `tests/test_export/test_manifest.py`

- [ ] **Step 1: Write failing manifest test**

Extend manifest tests to call `build_manifest(..., note_path=Path("outputs/lesson/note.md"), note_written=True)` and assert:
- `artifacts["note"]["path"] == Path("outputs/lesson/note.md")`
- `artifacts["note"]["format"] == "markdown"`
- `stage_status["note_export"] == StageStatus.DONE`

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_export.test_manifest`

Expected: fail because `build_manifest` does not accept note export fields yet.

- [ ] **Step 3: Implement manifest note metadata**

Add optional `note_path` and `note_written` parameters. Preserve the default `note_path` of `<output>/note.md`; set `note_export` to `done` only when `note_written=True`, otherwise `skipped`. Add `artifacts["note"]` only when a note was written.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_export.test_manifest`

Expected: pass.

### Task 3: CLI Note Export

**Files:**
- Modify: `vbook_client/cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add a test that runs:

```sh
python -m vbook_client manifest --video lesson.mp4 --transcript transcript.json --output outputs/lesson --write-note
```

Assert `note.md` exists, includes transcript content, and manifest records `artifacts.note` plus `stage_status.note_export == "done"`.

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: fail because `--write-note` does not exist.

- [ ] **Step 3: Implement CLI note flags**

Add `--write-note` and `--note-path`. When `--write-note` is set, render a placeholder note using the data already loaded during the manifest run and write it to the requested path or `<output>/note.md`. Pass `note_path` and `note_written=True` into `build_manifest`.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: pass.

### Task 4: Final Verification and Commit

**Files:**
- All files changed above.

- [ ] **Step 1: Run full unit test suite**

Run: `python -m unittest discover`

Expected: all tests pass.

- [ ] **Step 2: Run lint command**

Run: `python -m ruff check .`

Expected: pass if `ruff` is installed. If unavailable, record the environment error without claiming lint success.

- [ ] **Step 3: Run CLI smoke test**

Run a temporary `manifest --write-note` command with a small transcript and frame fixture. Verify both `note.md` and `manifest.json` are written.

- [ ] **Step 4: Commit and push**

Commit with `feat: add note placeholder export` and push to `origin/main`.

- [ ] **Step 5: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
