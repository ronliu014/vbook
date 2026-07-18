# Allwin Production Patrol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run vBook as a queue-driven production coordinator for all videos under the five Allwin source libraries while preserving review, preview, and publication gates.

**Architecture:** vBook owns queue auditing, preview generation, user review packaging, publication planning, and postcheck. vtext owns text source notes and semantic/temporal text artifacts; vision owns visual service compatibility when vBook cannot self-generate or validate lesson outputs. Codex patrols every 30 minutes, regenerates queue state, and only escalates to users or partner projects when a gate requires external action.

**Tech Stack:** Python `D:/anaconda3/envs/App/python.exe`, vBook CLI/tools, `F:/vbook` production workspace, `F:/vault/20_Learning/vtext` read-only source vault, `F:/vault/20_Learning/vbook` publication vault, vsync mailbox, Codex heartbeat automation.

---

### Task 1: Maintain Full-Library Queue Audit

**Files:**
- Use: `tools/production_queue_audit.py`
- Output: `F:/vbook/production-queues/Q20260718-allwin-all-libraries/production-library-audit.json`
- Output: `F:/vbook/production-queues/Q20260718-allwin-all-libraries/production-library-audit.md`

- [ ] **Step 1: Regenerate the full audit**

Run from `E:/projects/my_app/vbook`:

```powershell
D:/anaconda3/envs/App/python.exe tools/production_queue_audit.py `
  --video-library-root "F:/downloads/allwin/读书会" `
  --video-library-root "F:/downloads/allwin/基础教学" `
  --video-library-root "F:/downloads/allwin/量化模式" `
  --video-library-root "F:/downloads/allwin/牛股实战班" `
  --video-library-root "F:/downloads/allwin/投资训练营" `
  --vtext-vault-root "F:/vault/20_Learning/vtext" `
  --lesson-output-root outputs `
  --published-vbook-root "F:/vault/20_Learning/vbook" `
  --output-dir "F:/vbook/production-queues/Q20260718-allwin-all-libraries"
```

Expected current baseline:

```text
lesson_count: 963
published: 4
waiting_vtext_and_lesson_output: 959
ready_for_preview: 0
```

- [ ] **Step 2: Inspect status deltas**

Read `production-library-audit.json` and compare `status_counts` with the prior patrol.

Notify the user when:

- `ready_for_preview` becomes greater than 0;
- `published` changes without a matching vBook publication record;
- any status indicates missing files after a publish;
- a tool fails to regenerate the audit.

- [ ] **Step 3: Keep reports out of source control**

Do not commit generated queue JSON/Markdown from `F:/vbook` or `outputs/production-queues`. Commit only reusable tools, tests, and durable docs.

### Task 2: Coordinate vtext Source Backlog

**Files:**
- Use: `E:/projects/my_app/vsync/mailbox/messages/2026-07-18-vbook-vtext-allwin-library-source-backlog-request.md`
- Use: `E:/projects/my_app/vsync/mailbox/inbox/vbook/README.md`
- Use: `E:/projects/my_app/vsync/mailbox/inbox/vtext/README.md`

- [ ] **Step 1: Check vtext responses**

Every patrol, inspect vsync inboxes for replies to the Allwin source backlog request.

Relevant request:

```text
mailbox/messages/2026-07-18-vbook-vtext-allwin-library-source-backlog-request.md
```

- [ ] **Step 2: Bind newly available vtext outputs**

When vtext reports completed notes, verify that each note exists under:

```text
F:/vault/20_Learning/vtext/<library>/<course>/<lesson>.md
```

Regenerate the full audit. Items should move from `waiting_vtext_and_lesson_output` to either `waiting_lesson_output` or `ready_for_preview`.

- [ ] **Step 3: Request clarification for uncertain notes**

If vtext reports semantic uncertainty, transcript gaps, or failed lessons, keep those lessons out of preview batches and request per-lesson clarification through vsync.

### Task 3: Generate vBook Visual Lesson Outputs

**Files:**
- Input: vtext notes from `F:/vault/20_Learning/vtext`
- Input: videos from `F:/downloads/allwin`
- Output: `E:/projects/my_app/vbook/outputs` or `F:/vbook/lesson-outputs`

- [ ] **Step 1: Select a small ready group**

Only select lessons that have vtext source notes. Prefer batches of 3-10 lessons until postcheck history is stable for multiple runs.

- [ ] **Step 2: Generate or locate 240s lesson output**

For each selected lesson, produce a lesson-output directory that contains:

```text
manifest.json
vision/analysis.json
fusion/sections.json
```

Use the accepted visual baseline:

```text
frame interval: 240s
minimum selected frame interval: 240s
```

- [ ] **Step 3: Regenerate audit**

After lesson-output generation, rerun the full audit and confirm selected items become `ready_for_preview`.

### Task 4: Build Preview Batches

**Files:**
- Create: `F:/vbook/inputs/<dataset-id>/batch-input.json`
- Output: `F:/vbook/experiments/<experiment-id>/`

- [ ] **Step 1: Create a batch input for ready items**

Use only `ready_for_preview` lessons. Each entry must include:

```json
{
  "lesson": "<lesson>",
  "vtext_note": "F:/vault/20_Learning/vtext/<library>/<course>/<lesson>.md",
  "lesson_output": "<ready lesson-output directory>"
}
```

- [ ] **Step 2: Generate previews**

Run:

```powershell
D:/anaconda3/envs/App/python.exe -m vbook_client production-batch-preview `
  --batch-input "F:/vbook/inputs/<dataset-id>/batch-input.json" `
  --output-root "F:/vbook/experiments/<experiment-id>" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --max-images-per-note 3 `
  --min-image-gap-seconds 240
```

- [ ] **Step 3: Run preflight**

Run:

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_preflight.py `
  --root "F:/vbook/experiments/<experiment-id>/renders/vtext_first_vault_enhance/baseline" `
  --json-output "F:/vbook/experiments/<experiment-id>/comparisons/vtext-first-preflight.json" `
  --markdown-output "F:/vbook/experiments/<experiment-id>/comparisons/vtext-first-preflight.md"
```

Required gate:

```text
ok: true
missing images: 0
Qwen error placeholders skipped
```

### Task 5: Review And Publish

**Files:**
- Review: `F:/vbook/experiments/<experiment-id>/reviews/`
- Plan: `F:/vbook/experiments/<experiment-id>/publication-plans/`
- Target: `F:/vault/20_Learning/vbook`

- [ ] **Step 1: Generate user review package**

Create a review round for preview candidates and wait for explicit user acceptance.

- [ ] **Step 2: Create dry-run publication plan**

Create a publication plan only after user acceptance. Publication planning must stage notes and rewrite Markdown image links to vault-stable relative paths.

- [ ] **Step 3: Run conflict report**

If target notes exist, apply must be blocked unless the user explicitly approves overwrite and backup.

- [ ] **Step 4: Apply only with explicit approval**

Use `--backup-existing` for overwrites. Do not write into `F:/vault/20_Learning/vtext`.

- [ ] **Step 5: Postcheck publication**

Accept publication only when:

```text
status: pass
hash_mismatch_count: 0
missing_markdown_image_count: 0
```

### Task 6: Patrol Behavior

**Automation:**
- Name: `vBook production patrol`
- ID: `vbook-production-patrol`
- Cadence: every 30 minutes
- Destination: current Codex task

- [ ] **Step 1: Start each patrol with repository status**

Run:

```powershell
git status -sb
```

- [ ] **Step 2: Rebuild queue state**

Regenerate the full audit and summarize only deltas.

- [ ] **Step 3: Take autonomous action when safe**

Safe autonomous actions:

- regenerate audits;
- run tests;
- create preview-only outputs under `F:/vbook/experiments`;
- write vsync requests;
- fix local tooling bugs with tests and commits.

Actions requiring user approval:

- publish to `F:/vault/20_Learning/vbook`;
- overwrite existing vault notes/assets;
- change accepted production route;
- switch external model provider for production;
- modify `F:/vault/20_Learning/vtext`.

### Self-Review

- Spec coverage: The plan covers all five requested directories, queue auditing, 30-minute patrols, vtext/vision collaboration, preview-only generation, user review, publication approval, and postcheck.
- Placeholder scan: No task relies on unspecified paths or hidden gates.
- Type consistency: Status names match `tools/production_queue_audit.py`; route names match the accepted `vtext_first_vault_enhance` pipeline.
