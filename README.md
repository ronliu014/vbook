# vBook

vBook is a project for automatic video-course analysis and knowledge organization. Its target pipeline is:

1. Extract and filter key video frames, especially PPT slides and practical case screenshots.
2. Convert audio to timestamped text.
3. Recognize visual content with OCR or multimodal models.
4. Align screenshots with transcript segments by timeline.
5. Fuse speech, slide text, and visual case descriptions into structured Markdown notes and a searchable knowledge base.

## Quick Start: Production Status

Run commands from the repository root. The single entry point is:

```powershell
.\vstatus
```

It summarizes the current vBook, vtext, vision, fusion, run, control, and
scheduler state. Use these commands for common inspections:

| Need | Command |
| --- | --- |
| Show the complete current overview | `.\vstatus` |
| Refresh every 30 seconds | `.\vstatus watch` |
| Refresh at a custom interval | `.\vstatus watch 60` |
| Inspect a lesson | `.\vstatus lesson "<lesson-name>"` |
| Inspect a run | `.\vstatus run <run-id>` |
| Inspect a task and its attempts | `.\vstatus task <task-id>` |
| Inspect a stage wave | `.\vstatus wave <stage> <number>` |
| Print JSON | `.\vstatus json` |
| Write a JSON snapshot | `.\vstatus json <output-file>` |
| Fail when blocked, paused, or stale | `.\vstatus check` |
| Show quick commands and all options | `.\vstatus help` |

Aliases `w`, `l`, `r`, `t`, and `j` are accepted for `watch`, `lesson`, `run`,
`task`, and `json`. The command is read-only unless an output file is explicitly
requested. See the
[`production workflow status runbook`](docs/60_operations/production-workflow-status.md)
for report interpretation, exit codes, and automation options.

Start documentation from [`docs/README.md`](docs/README.md). For a quick project
orientation, read [`docs/00_project/overview.md`](docs/00_project/overview.md),
[`docs/00_project/glossary.md`](docs/00_project/glossary.md),
[`docs/00_project/status.md`](docs/00_project/status.md), and
[`docs/00_project/task-board.md`](docs/00_project/task-board.md). The original product
intent remains available at [`docs/90_reference/original-requirements.md`](docs/90_reference/original-requirements.md).

## Project Status

vBook is in the local MVP pipeline stage. The current pipeline can run from a
video plus timestamped transcript into `manifest.json`, `note.md`,
`vision/analysis.json`, `fusion/prompt.json`, and `fusion/sections.json`.
Some stages are still placeholders or partial foundations. See
[`docs/00_project/status.md`](docs/00_project/status.md) for the current project
state and [`docs/00_project/task-board.md`](docs/00_project/task-board.md) for
the operational task board and next recommended work.

## Repository Layout

- `docs/` - numbered documentation layers; start at `docs/README.md`.
- `sync/` - Git-backed coordination directory for Windows and Linux Codex agents.
- `vstatus.cmd` - read-only production workflow status entry point for Windows.
- `AGENTS.md` - contributor and agent guidelines.
- `vbook_common/` - shared data contracts, config, version, and serialization.
- `vbook_client/` - CLI entry point.
- `vbook_server/` - future server boundary, currently an empty placeholder.

## Documentation Rules

vBook uses numbered documentation layers:

- `docs/00_project/` - status, roadmap, task board, scope, and glossary.
- `docs/20_architecture/` - module boundaries, data model, contracts, and design.
- `docs/30_pipeline/` - stage-by-stage video-to-knowledge pipeline docs.
- `docs/40_development/` - setup, commands, testing, Git, and agent workflow.
- `docs/60_operations/` - local runbooks, smoke tests, integration procedures, and troubleshooting.
- `docs/70_progress/` - dated progress logs and milestone records.
- `docs/80_superpowers/` - agent specs, implementation plans, reviews, and handoffs.
- `docs/90_reference/` - external project requests/responses, original requirements, and sample contracts.

When adding an important workflow, contract, or cross-project decision:

1. Put stable reference material under `docs/90_reference/`.
2. Put executable runbooks under `docs/60_operations/`.
3. Put dated implementation or smoke records under `docs/70_progress/`.
4. Update [`docs/00_project/status.md`](docs/00_project/status.md) and
   [`docs/00_project/task-board.md`](docs/00_project/task-board.md) when project
   state, blockers, or next recommended work changes.
5. Keep root `README.md` focused on orientation and entry points; link to
   detailed docs instead of duplicating them.

## Cross-Project Coordination

vBook is the orchestrator. Adjacent projects remain independently evolvable:

- `vtext` is the text-processing module for transcript, correction, and summary output.
- `vision` is the visual-understanding module for Qwen Vision Service and similar backends.
- `vBook` owns orchestration, evidence fusion, preview output, and future vault write-back.

Cross-project integration must use stable CLI/API/artifact contracts rather than
source-code imports or vendored code. Requests and replies are documented as
paired files, for example:

- [`docs/90_reference/cross-project-coordination-notice.md`](docs/90_reference/cross-project-coordination-notice.md)
- [`docs/90_reference/vbook-text-integration-request.md`](docs/90_reference/vbook-text-integration-request.md)
- [`docs/90_reference/vtext-integration-response-summary.md`](docs/90_reference/vtext-integration-response-summary.md)
- [`docs/90_reference/integration-response.md`](docs/90_reference/integration-response.md)

The current vtext contract is a per-lesson bundle:

```powershell
conda run -n App python -m vtext_client "<video-path>" --bundle vbook --output "<lesson-output-dir>" --format srt --language zh
```

The current vision contract is the Qwen Vision Service adapter through
`tools/vision_qwen_adapter.py`, documented in
[`docs/60_operations/qwen-vision-integration.md`](docs/60_operations/qwen-vision-integration.md).

## Development Commands

Use the Anaconda `App` environment for local development. See
[`docs/40_development/commands.md`](docs/40_development/commands.md) for the
full command reference.

```sh
conda run -n App python -m unittest discover
conda run -n App python -m vbook_client --version
conda run -n App python -m vbook_client check
conda run -n App python -m vbook_client config --show
conda run -n App python -m vbook_client build \
  --video lesson.mp4 \
  --transcript transcript.json \
  --output outputs/lesson
```

Editable install for local command testing:

```sh
conda run -n App python -m pip install -e ".[dev]"
conda run -n App vbook check
```

The `build` command runs the current MVP pipeline using an imported timestamped transcript. `--transcript` accepts timestamped JSON or SRT files. By default, `build` extracts candidate frames from `--video` into `<output>/frames/candidates`; pass `--frame-candidates-dir` to reuse an existing candidate directory. It writes:

- `manifest.json`
- `note.md`
- `vision/analysis.json`
- `fusion/prompt.json`
- `fusion/sections.json`

Batch input can use a vtext-compatible directory with media files at the input
root and matching transcripts under `text/`:

```powershell
conda run -n App python -m vbook_client build-batch --input E:\projects\my_app\temp --output outputs\temp-batch
```

The command writes one lesson output directory per media file plus
`batch_manifest.json`.

Preview-only vault enhancement can combine an existing vtext-created vault note
with a vBook lesson output without writing back to `F:\vault`:

```powershell
conda run -n App python -m vbook_client vault-preview `
  --vault-note "<existing-vault-note.md>" `
  --lesson-output "<vbook-lesson-output-dir>" `
  --output "outputs\vault-enhancement-preview\<series>\<lesson>"
```

For current vault-quality output, use the vtext-first `vault-enhance` workflow.
It preserves the source vtext note, copies selected screenshots, and writes a
separate vBook note plus manifest:

```powershell
conda run -n App python -m vbook_client vault-enhance `
  --vtext-note "F:\vault\20_Learning\vtext\<series>\<lesson>.md" `
  --lesson-output "outputs\<lesson-output>" `
  --output-note "F:\vault\20_Learning\vbook\<series>\<lesson>.md" `
  --max-images-per-note 3 `
  --min-image-gap-seconds 180
```

See [`docs/60_operations/vault-enhance.md`](docs/60_operations/vault-enhance.md)
for the current image-budget guidance. The tested Qwen baseline is `240s` for
stable visual extraction; denser full-course sweeps should wait for smarter
selection and retry policy.

## Sync Roles

- `wcodex` - Windows-side Codex agent.
- `lcodex` - Linux-side Codex agent.

See [`sync/README.md`](sync/README.md) for the message protocol.
