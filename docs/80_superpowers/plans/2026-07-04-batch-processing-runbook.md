# Batch Processing Runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an operations runbook for the existing `build-batch` workflow so users can organize inputs, run batch builds, inspect `batch_manifest.json`, handle failures, and rerun conservatively without changing runtime behavior.

**Architecture:** Keep this as a docs-only change. Create `docs/60_operations/batch-processing.md` as the detailed runbook, promote it in the operations index, and update project status/task-board documents so the next recommended work moves to pipeline stage documentation.

**Tech Stack:** Markdown documentation, existing vBook CLI semantics, Git diff checks, Python `unittest`.

---

## File Structure

- Create: `docs/60_operations/batch-processing.md`
  - Full batch operations runbook for current `build-batch` behavior.
- Modify: `docs/60_operations/README.md`
  - Promote `batch-processing.md` to current operations entry point and remove it from planned documents.
- Modify: `docs/00_project/task-board.md`
  - Mark batch workflow documentation done and set next recommendation to pipeline stage documents.
- Modify: `docs/00_project/status.md`
  - Record that batch processing has a runbook and adjust most important next work.

Do not modify runtime source, tests, CLI arguments, batch discovery logic, manifest schema, README command examples, Qwen adapter code, LLM fusion code, or any real-service runbook.

---

## Task 1: Create the Batch Processing Runbook

**Files:**
- Create: `docs/60_operations/batch-processing.md`

- [ ] **Step 1: Create `docs/60_operations/batch-processing.md`**

Create the file with this exact content:

````markdown
# Batch Processing

This runbook explains how to use vBook's current `build-batch` command for a
vtext-compatible input directory. It is an operations guide for the local MVP
pipeline, not a production batch scheduler or quality benchmark.

## 适用范围

Use this runbook when you need to:

- Run vBook over multiple local media files.
- Reuse transcript files arranged in a vtext-compatible `text/` directory.
- Inspect per-lesson outputs plus the batch-level `batch_manifest.json`.
- Understand `done`, `skipped`, and `failed` batch statuses.
- Diagnose common batch failures.
- Rerun conservatively without mixing old and new outputs.

This runbook assumes commands are executed from the repository root.

## 当前能力边界

`build-batch` is a thin orchestration layer over the existing per-lesson
`build` pipeline. Each discovered lesson runs the same local MVP pipeline used
by:

```powershell
python -m vbook_client build
```

Current batch CLI arguments:

```text
--input
--output
--frame-interval-seconds
--alignment-window-seconds
```

Current limitations:

- No concurrency or worker pool option.
- No automatic resume from an existing `batch_manifest.json`.
- No `--rerun-failed` or `--skip-done` option.
- No batch-level Qwen Vision Service adapter arguments.
- No batch-level LLM fusion command arguments.
- No production queueing, scheduling, or archive policy.
- No real-service quality validation.

The command can return exit code `0` even when individual lessons are skipped
or failed. Always inspect `batch_manifest.json`.

## 输入目录结构

The expected layout is vtext-compatible: media files are placed under the input
root, while matching transcript files are placed under `text/`.

Flat layout:

```text
input/
  lesson-a.mp4
  lesson-b.mp4
  text/
    lesson-a.srt
    lesson-b.srt
```

Nested layout:

```text
input/
  course-a/
    lesson-01.mp4
    lesson-02.mp4
  text/
    course-a/
      lesson-01.srt
      lesson-02.srt
```

Rules:

- The transcript directory is always `input/text/`.
- Nested transcripts must preserve the same relative parent directory as the
  media file.
- Media and transcript file stems must match.
- Keep batch outputs outside the input directory when possible. The scanner
  ignores directories named `outputs`, but a separate output location keeps
  runs easier to inspect and compare.

## 文件发现规则

`build-batch` discovers files with these media extensions:

```text
.mp4 .mkv .avi .mov .wmv .flv .webm .mp3 .wav .m4a .aac .flac .ogg
```

The scanner ignores media files under directories with these names:

```text
.git
.pytest_cache
.ruff_cache
outputs
sync
text
```

Discovery is sorted by relative path, so repeated runs over the same input
layout produce stable lesson ordering.

Nested media paths are preserved in the lesson id and output layout. For
example:

```text
input/course-a/lesson-01.mp4
```

maps to:

```text
lesson_id: course-a/lesson-01
output:    outputs/batch-run/course-a/lesson-01/
```

## Transcript 匹配规则

For media file:

```text
input/<relative_parent>/<stem>.mp4
```

vBook searches:

```text
input/text/<relative_parent>/
```

with this priority:

```text
<stem>_raw.srt
<stem>.srt
<stem>_raw.vtt
<stem>.vtt
<stem>_raw.txt
<stem>.txt
```

Operational guidance:

- Use `.srt` for current stable batch runs.
- `*.vtt` and `*.txt` can be discovered by the matcher, but the current
  transcript loader does not promise full high-quality support for them.
- If an unsupported transcript is matched, the lesson can appear as `failed`
  with `failure_reason == "unsupported_transcript_format"`.
- If no matching transcript is found, the lesson appears as `skipped` with
  `failure_reason == "missing_transcript"`.

## 运行命令

Minimal command:

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\batch-run
```

With explicit frame and alignment settings:

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\batch-run `
  --frame-interval-seconds 30 `
  --alignment-window-seconds 5
```

Recommended output naming:

```text
outputs/batch-20260704-1530/
outputs/batch-course-a-smoke/
outputs/batch-run-2/
```

Use a fresh output directory for important reruns. This avoids mixing new
artifacts with stale lesson outputs.

## 输出目录结构

Flat input example:

```text
outputs/batch-run/
  batch_manifest.json
  lesson-a/
    manifest.json
    note.md
    frames/
    vision/
    fusion/
  lesson-b/
    manifest.json
    note.md
    frames/
    vision/
    fusion/
```

Nested input example:

```text
outputs/batch-run/
  batch_manifest.json
  course-a/
    lesson-01/
      manifest.json
      note.md
      frames/
      vision/
      fusion/
```

`batch_manifest.json` is the batch summary. It does not replace each lesson's
own `manifest.json`. For the lesson-level artifact contract, see
`docs/20_architecture/output-contracts.md`.

## batch_manifest.json 解读

Top-level fields:

| Field | Meaning |
| --- | --- |
| `lesson_count` | Number of discovered media lessons. |
| `done_count` | Lessons whose per-lesson build completed. |
| `failed_count` | Lessons that entered build but failed. |
| `skipped_count` | Lessons that did not enter build. |
| `lessons` | Per-lesson result list. |

Per-lesson fields:

| Field | Meaning |
| --- | --- |
| `lesson_id` | Stable lesson id. Nested paths use `/`. |
| `media_path` | Source media path. |
| `transcript_path` | Matched transcript path, or null when missing. |
| `output_dir` | Lesson output directory. |
| `status` | `done`, `failed`, or `skipped`. |
| `vtext_compatible` | Whether a matching transcript was found. |
| `manifest_path` | Lesson manifest path for successful lessons. |
| `failure_reason` | Reason for `failed` or `skipped` lessons. |

Important count check:

```text
done_count + failed_count + skipped_count == lesson_count
```

## 状态说明

### `done`

The lesson completed the per-lesson pipeline.

Expected artifacts:

```text
<lesson-output>/manifest.json
<lesson-output>/note.md
<lesson-output>/vision/analysis.json
<lesson-output>/fusion/sections.json
```

Recommended checks:

- Open `lessons[].manifest_path`.
- Confirm `stage_status.manifest == "done"`.
- Confirm `stage_status.note_export == "done"`.
- Open `note.md` and inspect title, course information, knowledge structure,
  and evidence references.

### `skipped`

The lesson did not enter the per-lesson build.

Current common reason:

```text
missing_transcript
```

Resolution:

- Add a transcript file under `input/text/<relative_parent>/`.
- Match the media file stem.
- Prefer `.srt`.
- Rerun batch with a new output directory, or run the fixed lesson by itself
  with `python -m vbook_client build`.

### `failed`

The lesson entered the per-lesson build and failed.

Current common reasons:

```text
unsupported_transcript_format
build_failed: <message>
```

Resolution:

- For `unsupported_transcript_format`, convert the transcript to `.srt` before
  rerunning.
- For `build_failed: ...`, read the message and inspect the lesson output
  directory. Reproduce the lesson with the single-lesson `build` command when
  the cause is unclear.

## 输出检查清单

After each batch run:

- `batch_manifest.json` exists under the batch output directory.
- `lesson_count` matches the expected number of media files.
- `done_count + failed_count + skipped_count == lesson_count`.
- Every `done` lesson has `manifest_path`.
- Every `done` lesson has `note.md`.
- Every `skipped` or `failed` lesson has `failure_reason`.
- At least one `done` lesson has a readable `note.md`.
- At least one `done` lesson manifest has `stage_status.manifest == "done"`.
- The output directory is not inside a source-controlled path that will be
  committed.

## 常见失败与处理

### `missing_transcript`

Cause:

- Media file was found, but no transcript matched the expected name and path.

Check:

```text
input/course-a/lesson-01.mp4
input/text/course-a/lesson-01.srt
```

Fix:

- Add or rename the transcript.
- Prefer `.srt`.
- Preserve the same relative parent directory.

### `unsupported_transcript_format`

Cause:

- A transcript file was matched, but the per-lesson transcript loader could not
  import it.

Fix:

- Convert to `.srt`.
- Run the lesson once with `python -m vbook_client build` to verify transcript
  import before running the full batch again.

### `build_failed: ...`

Cause:

- The per-lesson pipeline raised an exception after batch discovery.

Check:

- The failure message after `build_failed:`.
- The lesson output directory.
- Source video path.
- Transcript parseability.
- Local frame extraction behavior.

Fix:

- Reproduce with a single lesson command.
- Fix the input file or local environment.
- Rerun to a new output directory.

### `lesson_count` is lower than expected

Check:

- Media extension is in the supported list.
- Media was not placed under `text/`, `outputs/`, `sync/`, `.git/`,
  `.pytest_cache/`, or `.ruff_cache/`.
- The input path points at the directory you intended.

### Old outputs make results confusing

Cause:

- A rerun reused an existing output directory.

Fix:

- Prefer a new `--output` path for reruns.
- Compare old and new `batch_manifest.json` manually.

## 重跑策略

### 全量重跑

Use a fresh output path:

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\batch-run-2
```

### 单课重跑

Use the single-lesson pipeline:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\text\lesson.srt `
  --output outputs\single-lesson-rerun
```

### 修复 transcript 后重跑

Recommended sequence:

1. Fix or replace the transcript file.
2. Run a single-lesson `build` if the transcript format is uncertain.
3. Run batch again with a new `--output` directory.
4. Compare old and new `batch_manifest.json`.

### 当前不支持的重跑方式

Current `build-batch` does not support:

- Reading an old `batch_manifest.json` and rerunning only failed or skipped
  lessons.
- Automatically skipping completed lessons.
- In-place cleanup of stale lesson artifacts.
- Concurrent reruns.

## 不覆盖的内容

This runbook does not cover:

- Qwen Vision Service batch performance.
- Real OCR or multimodal quality.
- Real LLM/Qwen text synthesis quality.
- Production queueing or scheduling.
- Multi-machine execution.
- Artifact archival and retention policy.
- Knowledge-base indexing after export.

## 相关文档

- [smoke-tests.md](./smoke-tests.md)
- [qwen-vision-integration.md](./qwen-vision-integration.md)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
- [../00_project/task-board.md](../00_project/task-board.md)
- [../80_superpowers/specs/2026-07-04-batch-processing-runbook-design.md](../80_superpowers/specs/2026-07-04-batch-processing-runbook-design.md)
````

- [ ] **Step 2: Check required runbook sections**

Run:

```powershell
rg -n "适用范围|当前能力边界|输入目录结构|文件发现规则|Transcript 匹配规则|运行命令|输出目录结构|batch_manifest.json 解读|状态说明|输出检查清单|常见失败与处理|重跑策略|不覆盖的内容|相关文档" docs/60_operations/batch-processing.md
```

Expected: output shows one hit for each required section.

- [ ] **Step 3: Check boundary language**

Run:

```powershell
rg -n "No concurrency|No automatic resume|No `--rerun-failed`|No batch-level Qwen|does not cover|does not support|unsupported_transcript_format|missing_transcript" docs/60_operations/batch-processing.md
```

Expected: output shows the current limitations, unsupported transcript behavior, and out-of-scope statements.

Do not commit yet.

---

## Task 2: Update Operations Index and Project Status

**Files:**
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/task-board.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Replace `docs/60_operations/README.md`**

Replace the entire file with:

```markdown
# 60 Operations

Operations-level documents explain how to run vBook locally, inspect outputs,
perform smoke tests, troubleshoot failures, and clean generated artifacts.

## Current Entry Points

- [smoke-tests.md](./smoke-tests.md) - local smoke runbook for CLI, stubs,
  contract checker, manifest, and note output.
- [batch-processing.md](./batch-processing.md) - batch input, batch manifest,
  failure handling, and rerun strategy runbook.
- [qwen-vision-integration.md](./qwen-vision-integration.md) - service-ready
  integration runbook for Qwen Vision Service.
- [../../README.md](../../README.md#development-commands)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)

## Planned Documents

- `local-run.md`
- `sample-inputs.md`
- `troubleshooting.md`
- `outputs-cleanup.md`
```

- [ ] **Step 2: Update `docs/00_project/task-board.md` batch workflow row**

Replace:

```markdown
| Batch workflow | `Partial` | `build-batch` 已有基础，可按 vtext-compatible 输入批量生成 lesson outputs。 | 补批处理 runbook、失败报告和输出检查。 |
```

with:

```markdown
| Batch workflow | `Partial` | `build-batch` 已有基础，batch processing runbook 已说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 | 后续根据真实课程批量运行反馈设计 rerun、并发和真实服务参数透传。 |
```

- [ ] **Step 3: Update `docs/00_project/task-board.md` ready task row**

Replace:

```markdown
| 完善 batch workflow 说明 | `Ready` | 文档说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 |
```

with:

```markdown
| 完善 batch workflow 说明 | `Done` | [batch-processing.md](../60_operations/batch-processing.md) 已说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 |
```

- [ ] **Step 4: Add recent completion row in `docs/00_project/task-board.md`**

In the `最近完成` table, add this row immediately before `Expert note enhancement`:

```markdown
| Batch processing runbook | `Done` | `docs/60_operations/batch-processing.md` 记录 `build-batch` 输入、输出、manifest、失败处理和重跑策略。 |
```

- [ ] **Step 5: Replace next recommended task in `docs/00_project/task-board.md`**

Replace the entire `## 下一步推荐任务` section with:

```markdown
## 下一步推荐任务

推荐下一步：扩展 pipeline stage documents。

理由：

- Qwen 服务尚未确认部署完成，真实视觉联调仍保持 blocked。
- batch workflow 说明已经完成，等待服务期间的本地操作路径更清晰。
- `docs/30_pipeline/` 仍缺少关键阶段的输入、输出、状态、测试和限制说明，补齐后可以让后续真实服务联调和批量处理更容易定位问题。
```

- [ ] **Step 6: Update `docs/00_project/status.md` current capabilities**

After this existing bullet:

```markdown
- Markdown note export from transcript or fusion sections, including an
  enhanced expert-note template with learning objectives, review index,
  review questions, and tag index for section-based notes.
```

insert:

```markdown
- Batch processing through `build-batch`, including vtext-compatible input
  discovery, per-lesson outputs, batch manifest summary, and an operations
  runbook for failure handling and reruns.
```

- [ ] **Step 7: Update `docs/00_project/status.md` partial batch statement**

Replace:

```markdown
- Batch processing has a functional foundation through `build-batch`, but it
  still uses the local MVP placeholder intelligence path for each lesson.
```

with:

```markdown
- Batch processing is documented and functional for the local MVP path, but it
  still lacks concurrency, manifest-based resume, automatic rerun of
  failed/skipped lessons, and real-service batch validation.
```

- [ ] **Step 8: Update `docs/00_project/status.md` next work list**

Replace:

```markdown
1. Execute the Qwen Vision Service integration runbook once the service team
   confirms deployment readiness.
2. Add a real smoke-test sample path once both local MP4 and transcript files
   are available.
3. Complete batch workflow runbook and failure-report documentation.
4. Expand pipeline-stage documents under `docs/30_pipeline/`.
5. Keep `manifest.json` and `note.md` as the primary output contract while
   intelligence improves behind the same artifacts.
```

with:

```markdown
1. Execute the Qwen Vision Service integration runbook once the service team
   confirms deployment readiness.
2. Add a real smoke-test sample path once both local MP4 and transcript files
   are available.
3. Expand pipeline-stage documents under `docs/30_pipeline/`.
4. Keep `manifest.json` and `note.md` as the primary output contract while
   intelligence improves behind the same artifacts.
```

- [ ] **Step 9: Check updated status links and task-board language**

Run:

```powershell
rg -n "batch-processing.md|Batch processing runbook|扩展 pipeline stage documents|manifest-based resume|automatic rerun|build-batch" docs/60_operations/README.md docs/00_project/task-board.md docs/00_project/status.md
```

Expected:

- Operations README links to `batch-processing.md`.
- Task board marks batch workflow documentation as `Done`.
- Task board recommends pipeline stage documents next.
- Status mentions batch runbook and current batch limitations.

Do not commit yet.

---

## Task 3: Verify and Commit the Docs-Only Runbook Update

**Files:**
- Create: `docs/60_operations/batch-processing.md`
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/task-board.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Run content checks**

Run:

```powershell
rg -n "build-batch|batch_manifest.json|missing_transcript|unsupported_transcript_format|重跑策略|No concurrency|No automatic resume" docs/60_operations/batch-processing.md docs/60_operations/README.md docs/00_project/task-board.md docs/00_project/status.md
```

Expected: output shows batch command, manifest, failure reasons, rerun strategy, and current limitations.

- [ ] **Step 2: Run placeholder scan**

Run:

```powershell
$placeholderPattern = ('T' + 'BD') + '|待' + '定|' + ('占' + '位') + '|' + ('未' + '完成') + '|' + ('fill' + ' in details') + '|' + ('implement' + ' later')
rg -n $placeholderPattern docs/60_operations/batch-processing.md docs/60_operations/README.md docs/00_project/task-board.md docs/00_project/status.md
```

Expected: exit code `1` with no matches.

- [ ] **Step 3: Run whitespace diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 4: Inspect the final diff**

Run:

```powershell
git diff -- docs/60_operations/batch-processing.md docs/60_operations/README.md docs/00_project/task-board.md docs/00_project/status.md
```

Expected manual checks:

- `docs/60_operations/batch-processing.md` is a runbook, not a future design.
- It documents current `build-batch` behavior without adding unsupported runtime promises.
- It explains input layout, discovery, transcript matching, command usage, output layout, `batch_manifest.json`, statuses, failures, and reruns.
- Operations README promotes the runbook.
- Task board marks the batch workflow documentation task done and recommends pipeline stage documents.
- Status document no longer lists batch runbook completion as future work.

- [ ] **Step 5: Run full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits `0` and prints:

```text
Ran 129 tests
OK
```

If the test count changes while still passing, update any verification snapshot that names the exact count before committing.

- [ ] **Step 6: Commit docs-only update**

Run:

```powershell
git add docs/60_operations/batch-processing.md docs/60_operations/README.md docs/00_project/task-board.md docs/00_project/status.md
git commit -m "Document batch processing runbook"
```

- [ ] **Step 7: Final state check**

Run:

```powershell
git status --short --branch
git log --oneline -3
```

Expected:

- Worktree is clean.
- Branch is ahead of `origin/main` by the new docs commit and the prior design commit if neither has been pushed.
- Recent commits include `Document batch processing runbook` and `Design batch processing runbook`.

Do not push to `origin/main` unless the user explicitly asks for a push.

---

## Self-Review

Spec coverage:

- New runbook path `docs/60_operations/batch-processing.md` is covered by Task 1.
- Scope, current capability boundaries, input layout, discovery rules, transcript matching, commands, output layout, `batch_manifest.json`, statuses, output checks, common failures, rerun strategy, out-of-scope content, and related docs are all included in Task 1 exact content.
- Operations index update is covered by Task 2.
- Project task-board update and next recommendation change are covered by Task 2.
- Project status update is covered by Task 2.
- Content checks, placeholder scan, whitespace check, full suite, commit, and final state check are covered by Task 3.

Scope check:

- This is one docs-only implementation cycle.
- The plan does not modify runtime source, tests, CLI arguments, schemas, README, Qwen adapter code, LLM code, or real-service runbooks.
- The plan does not promise unsupported batch runtime capabilities.

Type and naming consistency:

- Command name is consistently `build-batch`.
- Batch manifest file is consistently `batch_manifest.json`.
- Failure reasons are consistently `missing_transcript`, `unsupported_transcript_format`, and `build_failed: ...`.
- Planned runbook path is consistently `docs/60_operations/batch-processing.md`.
- Verification uses `python -m unittest discover`, matching repository guidelines.
