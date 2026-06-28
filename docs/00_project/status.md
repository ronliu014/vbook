# Current Project Status

Last updated: 2026-06-27

## Current Phase

vBook is in the local MVP pipeline stage. The project can run an end-to-end
local build from video plus timestamped transcript into Markdown and JSON
artifacts, but intelligent visual understanding and final knowledge synthesis
are not complete yet.

## Progress Log

Detailed dated progress is tracked in [../70_progress/](../70_progress/).
The latest migrated log is [2026-06-25.md](../70_progress/2026-06-25.md).

## Current Branch State

Local `main` is expected to be synchronized with `origin/main` after each
completed stage. Check the live state with:

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
- Visual analysis through `external-command`, where vBook writes frame input
  JSON, runs a user-supplied command, and normalizes the command output through
  the same validation path as `manual-json`.
- Built-in `tools/vision_stub.py` for deterministic `external-command` smoke
  checks without OCR, model runtimes, or API credentials.
- Qwen Vision Service adapter through `tools/vision_qwen_adapter.py`, using
  `external-command` to call a compatible `POST /analyze-frame` HTTP service
  without adding model dependencies to vBook core.
- Timeline alignment between frames and transcript segments.
- Fusion prompt snapshot export.
- Deterministic evidence-based fusion sections from transcript, visual
  analysis, and timeline links, including conservative adjacent-section merge.
- LLM-ready fusion request/response contract and deterministic response parser,
  without model execution.
- LLM fusion through explicit `--llm-fusion-command`, producing request,
  response, parsed LLM sections, manifest records, and `note.md` from LLM
  sections without binding vBook core to a model provider.
- Built-in `tools/llm_fusion_stub.py` for deterministic LLM fusion smoke checks
  without model runtimes, network services, or API credentials.
- LLM fusion contract samples and `tools/check_llm_fusion_contract.py` for
  external service self-tests before real model integration.
- Markdown note export from transcript or fusion sections, including a
  first-version expert-note template for section-based notes.
- `manifest.json` output with stage statuses and artifact summaries.

## What Is Still Placeholder or Partial

- Visual intelligence is partial: `manual-json` can ingest external analysis,
  `external-command` can call a user-supplied analyzer, and
  `tools/vision_qwen_adapter.py` can call a compatible Qwen Vision Service, but
  vBook still does not ship an embedded OCR or multimodal model provider.
- Fusion sections are deterministic evidence drafts with conservative section
  merge, not final LLM knowledge synthesis.
- LLM fusion execution is available through an explicit external command and a
  deterministic smoke stub; vBook still does not ship an embedded model provider
  or model SDK integration.
- LLM fusion contract samples validate file shape and parser compatibility;
  they do not evaluate final model note quality.
- `note.md` has a first-version expert-note structure, but review questions,
  glossary, learning objectives, and multi-format exports are still future work.
- `vbook_server` is only a future boundary and has no service runtime.
- Batch processing has a functional foundation through `build-batch`, but it
  still uses the local MVP placeholder intelligence path for each lesson.

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

Latest full suite run after LLM fusion smoke command integration:

```powershell
python -m unittest discover
```

Expected current result:

```text
Ran 121 tests
OK
```
