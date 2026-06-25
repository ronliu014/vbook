# Section-Aware Note Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `note.md` use generated `KnowledgeSection` data when available, while preserving the existing transcript placeholder fallback.

**Architecture:** Add a section-aware Markdown renderer in `vbook_export.note`, then adjust CLI ordering so `--write-fusion-sections --write-note` writes sections first and renders the note from those in-memory sections. Manifest behavior remains unchanged because `note_export` and `fusion_sections` already record their own artifacts.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing vBook dataclasses and CLI.

---

### Task 1: Section Markdown Renderer

**Files:**
- Modify: `vbook_export/note.py`
- Test: `tests/test_export/test_note.py`

- [ ] **Step 1: Write failing renderer test**

Add a test for `render_sections_note(video, sections)` that asserts the Markdown includes:
- lesson title as H1
- course metadata
- section count
- each section title
- section summary
- source timestamps
- image references
- key points when present

- [ ] **Step 2: Run target tests to verify RED**

Run: `python -m unittest tests.test_export.test_note`

Expected: fail because `render_sections_note` does not exist.

- [ ] **Step 3: Implement renderer**

Implement `render_sections_note(video, sections)` in `vbook_export.note`. Sort sections by first source timestamp, then title. Keep formatting deterministic and readable.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_export.test_note`

Expected: pass.

### Task 2: CLI Section-Aware Note Path

**Files:**
- Modify: `vbook_client/cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add a test that runs `manifest --write-fusion-sections --write-note` with aligned vision data. Assert `note.md` contains a `## Knowledge Sections` section, includes `Segment seg-000001`, includes the transcript summary text, and includes a referenced frame path. Assert manifest records both `note_export == "done"` and `fusion_sections == "done"`.

- [ ] **Step 2: Run target test to verify RED**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: fail because `note.md` still uses transcript placeholder rendering.

- [ ] **Step 3: Implement CLI ordering**

Store generated fusion sections in a local variable. Move fusion section generation before note writing. When `--write-note` is set and generated fusion sections exist, call `render_sections_note(...)`; otherwise keep using `render_placeholder_note(...)`.

- [ ] **Step 4: Run target tests to verify GREEN**

Run: `python -m unittest tests.test_client.test_manifest_cli`

Expected: pass.

### Task 3: Final Verification and Commit

**Files:**
- All files changed above.

- [ ] **Step 1: Run full unit test suite**

Run: `python -m unittest discover`

Expected: all tests pass.

- [ ] **Step 2: Run lint command**

Run: `python -m ruff check .`

Expected: pass if `ruff` is installed. If unavailable, record the environment error without claiming lint success.

- [ ] **Step 3: Run CLI smoke test**

Run a temporary command with `--write-fusion-sections --write-note`. Verify `note.md`, `fusion/sections.json`, and `manifest.json` are written and the note contains section content.

- [ ] **Step 4: Commit and push**

Commit with `feat: render notes from fusion sections` and push to `origin/main`.

- [ ] **Step 5: Verify remote alignment**

Run:

```sh
git ls-remote --heads origin main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Expected: local and remote `main` point to the same commit, with a clean worktree.
