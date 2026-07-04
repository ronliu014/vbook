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
