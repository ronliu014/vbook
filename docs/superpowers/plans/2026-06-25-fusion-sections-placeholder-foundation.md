# Fusion Sections Placeholder Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic `fusion/sections.json` placeholder export that creates traceable `KnowledgeSection` skeletons from transcript and aligned visual context.

**Architecture:** Keep section construction in `vbook_fusion.sections`, manifest indexing in `vbook_export.manifest`, and CLI orchestration in `vbook_client.cli`. This stage preserves source traceability and does not perform LLM summarization, deduplication, or final note polishing.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing vBook dataclasses and JSON serialization helpers.

---

### Task 1: Fusion Sections Module

**Files:**
- Create: `vbook_fusion/sections.py`
- Test: `tests/test_fusion/test_sections.py`

- [ ] **Step 1: Write failing section builder tests**

Create tests for `build_placeholder_sections(...)` and `write_fusion_sections(...)`. The builder should:
- sort transcript segments by `(start, end, id)`
- create one `KnowledgeSection` per transcript segment
- set `title` to `Segment <id>`
- set `summary` to the transcript text
- set `source_timestamps` to `[segment.start, segment.end]`
- set `image_refs` to visual image paths whose timeline links include that segment id
- keep `key_points` empty
- add tag `placeholder`

- [ ] **Step 2: Run target tests to verify RED**

Run: `python -m unittest tests.test_fusion.test_sections`

Expected: fail because `vbook_fusion.sections` does not exist.

- [ ] **Step 3: Implement minimal section builder and writer**

Use existing `KnowledgeSection`, `VisualAnalysis`, `TimelineLink`, and `TranscriptSegment` dataclasses. Build a frame-id to image-path map from visual analyses and a segment-id to image-ref map from timeline links. Write formatted UTF-8 JSON with `schema_version`, `intent`, `section_count`, and `sections`.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_fusion.test_sections`

Expected: pass.

### Task 2: Manifest Sections Artifact

**Files:**
- Modify: `vbook_export/manifest.py`
- Test: `tests/test_export/test_manifest.py`

- [ ] **Step 1: Write failing manifest test**

Extend manifest tests to call `build_manifest(..., fusion_sections_path=Path("outputs/lesson/fusion/sections.json"), fusion_sections_written=True)` and assert:
- `artifacts["fusion"]["sections_path"] == Path("outputs/lesson/fusion/sections.json")`
- `artifacts["fusion"]["sections_format"] == "json"`
- `stage_status["fusion_sections"] == StageStatus.DONE`

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_export.test_manifest`

Expected: fail because `build_manifest` does not accept fusion section fields yet.

- [ ] **Step 3: Implement manifest sections metadata**

Add optional `fusion_sections_path` and `fusion_sections_written` parameters. Default path is `<output>/fusion/sections.json`. Set `fusion_sections` to `done` only when written, otherwise `skipped`. Merge section metadata into the existing `artifacts["fusion"]` object when a prompt artifact also exists.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_export.test_manifest`

Expected: pass.

### Task 3: CLI Sections Export

**Files:**
- Modify: `vbook_client/cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add a test that runs `manifest --write-fusion-sections` with transcript, frame candidates, timeline alignment, and placeholder visual analysis enabled. Assert `fusion/sections.json` exists, contains section count and image refs, and manifest records `artifacts.fusion.sections_format` plus `stage_status.fusion_sections == "done"`.

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: fail because `--write-fusion-sections` does not exist.

- [ ] **Step 3: Implement CLI flags and orchestration**

Add `--write-fusion-sections` and `--fusion-sections-path`. When enabled, write placeholder sections to the requested path or `<output>/fusion/sections.json`. If visual analyses or timeline links were not requested, generate transcript-only sections with empty image refs; do not auto-run other stages.

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

Run a temporary `manifest --write-fusion-sections` command. Verify `fusion/sections.json` and `manifest.json` are written and `fusion_sections` is `done`.

- [ ] **Step 4: Commit and push**

Commit with `feat: add fusion sections placeholder export` and push to `origin/main`.

- [ ] **Step 5: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
