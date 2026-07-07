# Current Project Status

Last updated: 2026-07-07

## Current Phase

vBook is in the local MVP pipeline stage. The project can run an end-to-end
local build from video plus timestamped transcript into Markdown and JSON
artifacts. The first real Qwen Vision Service adapter smoke has passed, but
final knowledge synthesis quality is not complete yet. vBook is also beginning
the cross-project coordination phase where `vtext` supplies the text-processing
module, `vision` supplies visual understanding, and vBook owns orchestration,
evidence fusion, preview output, and future vault integration.

For the operational task board, current blockers, and next recommended work,
see [task-board.md](./task-board.md).

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
  `manifest`, `build`, `build-batch`, and `vault-preview`.
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
- Real Qwen Vision Service smoke against `http://192.168.0.33:8866` using
  `三分钟学会选短线个股.mp4`, proving `/health`, `/analyze-frame`, adapter
  normalization, `vision/analysis.json`, `manifest.json`, and `note.md` output
  through the vBook build path.
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
- Markdown note export from transcript or fusion sections, including an
  enhanced expert-note template with learning objectives, review index,
  review questions, and tag index for section-based notes.
- Batch processing through `build-batch`, including vtext-compatible input
  discovery, per-lesson outputs, batch manifest summary, and an operations
  runbook for failure handling and reruns.
- Pipeline stage documents under `docs/30_pipeline/`, covering transcript
  import, frame extraction, frame selection, vision analysis, timeline
  alignment, fusion prompt, fusion sections, note export, and manifest.
- Cross-project coordination notice for vBook, vtext, and vision
  request/response docs under `docs/90_reference/`, plus a vBook-to-vtext text
  integration request.
- vtext integration response received; App environment vtext CLI exposes
  `--bundle vbook` for a first stable per-lesson artifact bundle.
- Preview-only vault enhancement export through `vault-preview`, which combines
  an existing vault note with vBook visual/fusion artifacts into
  `enhancement.md`, copied images, and a preview manifest without writing back
  to `F:\vault`.
- Real preview smoke using the existing vtext vault note and the Qwen Vision
  smoke output, producing a preview package under
  `outputs/vault-enhancement-preview/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池/`.
- `manifest.json` output with stage statuses and artifact summaries.

## What Is Still Placeholder or Partial

- Visual intelligence is partial: `manual-json` can ingest external analysis,
  `external-command` can call a user-supplied analyzer, and
  `tools/vision_qwen_adapter.py` has passed a real Qwen Vision Service smoke,
  but vBook still does not ship an embedded OCR or multimodal model provider.
- Fusion sections are deterministic evidence drafts with conservative section
  merge, not final LLM knowledge synthesis.
- LLM fusion execution is available through an explicit external command and a
  deterministic smoke stub; vBook still does not ship an embedded model provider
  or model SDK integration.
- LLM fusion contract samples validate file shape and parser compatibility;
  they do not evaluate final model note quality.
- `note.md` now has deterministic learning objectives, review index, review
  questions, and tag index, but true glossary definitions and multi-format
  exports are still future work.
- `vbook_server` is only a future boundary and has no service runtime.
- Batch processing is documented and functional for the local MVP path, but it
  still lacks concurrency, manifest-based resume, automatic rerun of
  failed/skipped lessons, and real-service batch validation.
- Vault enhancement is preview-only. Controlled write-back into `F:\vault` is a
  future step after preview review and vault Git-state checks.

## Most Important Next Work

1. Re-run the Qwen Vision path with a real transcript from vtext
   `--bundle vbook` output so `note.md` and preview enhancement quality can be
   evaluated instead of only adapter/schema correctness.
2. Decide whether vBook should pass `course`, `series`, and `lesson_title`
   explicitly to vtext after the first fixture.
3. Use the real-transcript lesson output to regenerate the vault enhancement
   preview for `F:\vault\20_Learning\投资训练营`.

## Verification Snapshot

Latest full suite run after vault enhancement preview integration:

```powershell
conda run -n App python -m unittest discover
```

Current result:

```text
Ran 133 tests
OK
```
