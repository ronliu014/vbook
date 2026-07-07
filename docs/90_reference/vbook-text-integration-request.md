# vBook Text Integration Request

Status: request from vBook  
Date: 2026-07-07  
From: vBook  
To: vtext  
Related:

- [cross-project-coordination-notice.md](./cross-project-coordination-notice.md)
- [../00_project/task-board.md](../00_project/task-board.md)

## Goal

vBook asks vtext to provide a stable text-processing contract that vBook can
call as one stage of the video-course note pipeline.

vBook will use vtext output as the text backbone, then combine it with selected
frames, OCR, visual descriptions, timeline alignment, and final note export.
The first target course is `投资训练营`, where vtext has already produced
high-quality text notes in the vault.

## Non-Goals

- vBook should not import vtext internal Python modules as the integration
  boundary.
- vBook should not vendor vtext code.
- vtext does not need to own final vBook note layout, image placement, vault
  attachment rules, or knowledge-base write-back.
- vtext does not need to process images or visual evidence.

## Current Compatibility Observed By vBook

vBook can already discover a vtext-style batch input layout:

```text
<input-root>/
|-- <series>/<lesson>.mp4
+-- text/
    +-- <series>/<lesson>_raw.srt
```

vtext currently produces these useful artifacts in its own workflow:

```text
<lesson>_raw.<txt|srt|vtt>
<lesson>_clean.txt
<lesson>_summary.md
```

vtext also has an existing vault archive pattern for:

```text
F:\vault\20_Learning\投资训练营\<series>\<lesson>.md
```

vBook would like to preserve the quality of those text notes while adding
visual evidence and richer knowledge density.

## Requested Stable Contract

Please provide, or document, a stable per-video CLI contract.

Preferred command shape:

```powershell
python -m vtext_client "<video-path>" --output "<lesson-output-dir>" --format srt
```

If vtext prefers another command shape, please document the exact command and
exit-code behavior in the response.

Preferred output bundle:

```text
<lesson-output-dir>/
|-- transcript.raw.srt
|-- transcript.raw.txt
|-- transcript.clean.txt
|-- summary.md
+-- manifest.json
```

The filenames may differ if vtext needs backward compatibility, but vBook needs
the response to identify a stable machine-readable way to find each artifact.

## Requested Manifest

Please include a machine-readable manifest for each lesson.

Preferred shape:

```json
{
  "schema_version": "1",
  "project": "vtext",
  "source_video": "F:/downloads/allwin/投资训练营/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池.mp4",
  "course": "投资训练营",
  "series": "韩珂龙头班：基础篇",
  "lesson_title": "如何高效选股，构建自己的短线股票池",
  "language": "zh",
  "status": "done",
  "outputs": {
    "raw_srt": "transcript.raw.srt",
    "raw_txt": "transcript.raw.txt",
    "clean_txt": "transcript.clean.txt",
    "summary_md": "summary.md"
  },
  "timings": {
    "started_at": "2026-07-07T00:00:00Z",
    "finished_at": "2026-07-07T00:00:00Z",
    "duration_seconds": 0
  },
  "models": {
    "asr": "",
    "refine": ""
  },
  "errors": []
}
```

When processing fails, vBook prefers:

```json
{
  "schema_version": "1",
  "project": "vtext",
  "source_video": "path/to/video.mp4",
  "status": "failed",
  "outputs": {},
  "errors": [
    {
      "stage": "transcription",
      "code": "server_error",
      "message": "Human-readable failure summary"
    }
  ]
}
```

## Batch Contract

For batch processing, vBook can either:

1. call vtext once per lesson; or
2. call a vtext batch command and read a batch manifest.

If vtext supports batch as the preferred path, please document:

- input root structure;
- output root structure;
- how source video paths map to lesson output directories;
- batch manifest path;
- status values;
- retry strategy for failed lessons;
- whether partially completed lessons are safe to reuse.

Preferred batch manifest shape:

```json
{
  "schema_version": "1",
  "project": "vtext",
  "course": "投资训练营",
  "lesson_count": 1,
  "done_count": 1,
  "failed_count": 0,
  "skipped_count": 0,
  "lessons": [
    {
      "lesson_id": "韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池",
      "source_video": "F:/downloads/allwin/投资训练营/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池.mp4",
      "output_dir": "outputs/vtext/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池",
      "manifest_path": "outputs/vtext/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池/manifest.json",
      "status": "done"
    }
  ]
}
```

## Response Requested From vtext

Please reply with a document named:

```text
docs/90_reference/vbook-text-integration-response.md
```

If vtext has not yet adopted numbered docs directories, the response may first
land at:

```text
docs/vbook-text-integration-response.md
```

The response should include:

- exact supported CLI command(s);
- health/check command if available;
- output file layout;
- manifest schema or an alternative discovery mechanism;
- sample success output;
- sample failure output;
- exit codes;
- model/service dependencies;
- known current limitations, including large-file failure modes;
- performance expectations for one lesson and for a course batch;
- whether vtext is willing to adopt the proposed numbered docs layout.

## Initial Fixture

The first integration fixture can use:

```text
video:
F:\downloads\allwin\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.mp4

existing vault note:
F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md
```

vBook will not write back to the vault during the first integration pass. It
will produce preview artifacts under:

```text
outputs/vault-enhancement-preview/
```

## vBook-Side Acceptance

vBook can consume the vtext contract when:

- one command can produce transcript and text-summary artifacts for a single
  lesson;
- vBook can discover raw transcript, clean transcript, summary, and status
  without filename guessing;
- failures are represented in a manifest or stable stderr/exit-code contract;
- a small fixture can be run repeatedly;
- vtext output can be combined with vBook visual evidence without modifying
  vtext internals.
