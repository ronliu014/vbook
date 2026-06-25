# Fusion Prompt Snapshot Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic `fusion/prompt.json` export that captures the exact transcript, visual analysis, and timeline context intended for later knowledge fusion.

**Architecture:** Keep prompt snapshot construction in `vbook_fusion.snapshot`, manifest indexing in `vbook_export.manifest`, and CLI orchestration in `vbook_client.cli`. This stage writes audit input only; it does not call an LLM or produce final `KnowledgeSection` records.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing vBook dataclasses and JSON serialization helpers.

---

### Task 1: Fusion Snapshot Module

**Files:**
- Create: `vbook_fusion/snapshot.py`
- Test: `tests/test_fusion/test_snapshot.py`

- [ ] **Step 1: Write failing snapshot tests**

Create tests for `build_fusion_prompt_snapshot(...)` and `write_fusion_prompt_snapshot(...)`. The payload should include:
- `schema_version: "1"`
- `intent: "fusion_prompt_snapshot"`
- `video` metadata
- sorted `transcript_segments`
- sorted `visual_analyses`
- sorted `timeline_links`
- `inputs` counts for transcript, visual analysis, and timeline links

- [ ] **Step 2: Run target tests to verify RED**

Run: `python -m unittest tests.test_fusion.test_snapshot`

Expected: fail because `vbook_fusion.snapshot` does not exist.

- [ ] **Step 3: Implement minimal snapshot builder and writer**

Use existing dataclasses and `to_jsonable(...)`. Sort transcript segments by `(start, end, id)`, visual analyses by `frame_id`, and timeline links by `frame_id`. Write formatted UTF-8 JSON with a trailing newline.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_fusion.test_snapshot`

Expected: pass.

### Task 2: Manifest Fusion Artifact

**Files:**
- Modify: `vbook_export/manifest.py`
- Test: `tests/test_export/test_manifest.py`

- [ ] **Step 1: Write failing manifest test**

Extend manifest tests to call `build_manifest(..., fusion_prompt_path=Path("outputs/lesson/fusion/prompt.json"), fusion_prompt_written=True)` and assert:
- `artifacts["fusion"]["prompt_path"] == Path("outputs/lesson/fusion/prompt.json")`
- `artifacts["fusion"]["prompt_format"] == "json"`
- `stage_status["fusion_prompt"] == StageStatus.DONE`

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_export.test_manifest`

Expected: fail because `build_manifest` does not accept fusion prompt fields yet.

- [ ] **Step 3: Implement manifest fusion metadata**

Add optional `fusion_prompt_path` and `fusion_prompt_written` parameters. Default path is `<output>/fusion/prompt.json`. Set `fusion_prompt` to `done` only when written, otherwise `skipped`. Add the artifact only when written.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_export.test_manifest`

Expected: pass.

### Task 3: CLI Fusion Prompt Export

**Files:**
- Modify: `vbook_client/cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add a test that runs `manifest --write-fusion-prompt` with transcript, frame candidates, timeline alignment, and placeholder visual analysis enabled. Assert `fusion/prompt.json` exists, contains the expected input counts, and manifest records `artifacts.fusion` plus `stage_status.fusion_prompt == "done"`.

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: fail because `--write-fusion-prompt` does not exist.

- [ ] **Step 3: Implement CLI flags and orchestration**

Add `--write-fusion-prompt` and `--fusion-prompt-path`. When enabled, write the snapshot to the requested path or `<output>/fusion/prompt.json`. If timeline links or visual analyses were not requested, include empty lists; do not auto-run additional stages.

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

Run a temporary `manifest --write-fusion-prompt` command. Verify `fusion/prompt.json` and `manifest.json` are written and `fusion_prompt` is `done`.

- [ ] **Step 4: Commit and push**

Commit with `feat: add fusion prompt snapshot export` and push to `origin/main`.

- [ ] **Step 5: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
