# Build Command Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a high-level `build` CLI command that runs the current MVP output pipeline with sensible defaults.

**Architecture:** Extract the existing `manifest` command body into a reusable private pipeline function. Keep `manifest` behavior unchanged by passing its explicit flags as-is. Implement `build` as a thin command wrapper that enables timeline alignment, placeholder vision analysis, fusion prompt, fusion sections, and section-aware note export by default.

**Tech Stack:** Python 3.11 standard library, `argparse`, `unittest`, existing vBook pipeline modules.

---

### Task 1: Build Command Tests

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`

- [x] **Step 1: Write failing build test**

Add a test that runs:

```sh
python -m vbook_client build \
  --video lesson.mp4 \
  --transcript transcript.json \
  --output outputs/lesson \
  --frame-candidates-dir outputs/lesson/frames/candidates \
  --alignment-window-seconds 3
```

Assert it writes `manifest.json`, `note.md`, `vision/analysis.json`, `fusion/prompt.json`, and `fusion/sections.json`. Assert manifest stage statuses for `timeline_alignment`, `vision_analysis`, `fusion_prompt`, `fusion_sections`, `note_export`, and `manifest` are `done`.

- [x] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: fail because the `build` command does not exist.

### Task 2: Pipeline Refactor and Build Command

**Files:**
- Modify: `vbook_client/cli.py`

- [x] **Step 1: Extract reusable pipeline helper**

Create `_run_manifest_pipeline(args, parser, defaults)` where `defaults` supplies booleans for stages such as `align_timeline`, `analyze_vision_placeholder`, `write_fusion_prompt`, `write_fusion_sections`, and `write_note`. Replace direct `args.<flag>` checks with a `_flag(args, name, defaults)` helper.

- [x] **Step 2: Add build parser**

Add a `build` subcommand with the same core arguments as `manifest`:
- `--video`
- `--transcript`
- `--output`
- `--config`
- `--course-title`
- `--lesson-title`
- frame and alignment path/tuning flags
- artifact path override flags

Do not expose `--write-*` flags on `build`; those are defaults.

- [x] **Step 3: Wire command dispatch**

For `manifest`, call `_run_manifest_pipeline(..., defaults={})`.
For `build`, call `_run_manifest_pipeline(...)` with all MVP output defaults enabled.

- [x] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: pass.

### Task 3: Documentation

**Files:**
- Modify: `README.md`

- [x] **Step 1: Document build command**

Add `python -m vbook_client build ...` to development commands and show the expected high-level MVP output paths.

### Task 4: Final Verification and Commit

**Files:**
- All files changed above.

- [x] **Step 1: Run full unit test suite**

Run: `python -m unittest discover`

Expected: all tests pass.

- [x] **Step 2: Run lint command**

Run: `python -m ruff check .`

Expected: pass if `ruff` is installed. If unavailable, record the environment error without claiming lint success.

- [x] **Step 3: Run CLI smoke test**

Run a temporary `build` command and verify all five MVP artifacts are written.

- [ ] **Step 4: Commit and push**

Commit with `feat: add build command for MVP pipeline` and push to `origin/main`.

- [ ] **Step 5: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
