# Current Project Status

Last updated: 2026-06-27

## Current Phase

vBook is in the local MVP pipeline stage. The project can run an end-to-end
local build from video plus timestamped transcript into Markdown and JSON
artifacts, but intelligent visual understanding and final knowledge synthesis
are not complete yet.

## Current Branch State

Local `main` contains the current implementation work and is ahead of
`origin/main` by local commits. Check the live state with:

```powershell
git status --short --branch
```

## What Works Now

- CLI entry points: `python -m vbook_client --version`, `check`, `config --show`,
  `manifest`, and `build`.
- Transcript import from timestamped JSON and SRT.
- Frame candidate discovery and ffmpeg-based frame extraction.
- Basic frame selection into selected and rejected frame records.
- Visual analysis through the default `placeholder` backend.
- Visual analysis through explicit `manual-json` input.
- Timeline alignment between frames and transcript segments.
- Fusion prompt snapshot export.
- Deterministic placeholder fusion sections.
- Markdown note export from transcript or fusion sections.
- `manifest.json` output with stage statuses and artifact summaries.

## What Is Still Placeholder or Partial

- Visual intelligence is partial: `manual-json` can ingest external analysis,
  but vBook does not yet run OCR or multimodal model analysis itself.
- Fusion sections are deterministic placeholders, not final knowledge synthesis.
- `note.md` is structurally useful, but not yet a polished expert-level course
  note.
- `vbook_server` is only a future boundary and has no service runtime.
- Batch processing is designed in prior specs but is not part of the current
  main execution path.

## Most Important Next Work

1. Finish the documentation foundation: glossary, status dashboard, and layer
   indexes.
2. Decide whether the next product milestone is real visual analysis
   integration or batch input workflow.
3. Add a real smoke-test sample path once both local MP4 and transcript files
   are available.
4. Expand pipeline-stage documents under `docs/30_pipeline/`.
5. Keep `manifest.json` and `note.md` as the primary output contract while
   intelligence improves behind the same artifacts.

## Verification Snapshot

Latest full suite run after the vision backend work:

```powershell
python -m unittest discover
```

Expected current result:

```text
Ran 60 tests
OK
```
