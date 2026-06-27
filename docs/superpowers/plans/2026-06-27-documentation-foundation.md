# Documentation Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first vBook documentation foundation: numbered doc layers, a root documentation entry, a project glossary, and a current status dashboard.

**Architecture:** Follow the approved documentation architecture spec at `docs/superpowers/specs/2026-06-27-documentation-architecture-design.md`. This first pass creates the new structure and entry documents without large-scale migration, so existing links remain usable while the project gains a shared vocabulary and current-state view.

**Tech Stack:** Markdown documentation, Git moves/directories, existing Python unittest suite for no-runtime-regression verification.

---

## File Structure

- Modify `README.md`: add a clear root-level documentation entry section that points readers to the new docs index, glossary, status, and roadmap.
- Replace `docs/README.md`: make it the new documentation layer index and reading guide while preserving links to legacy documents during migration.
- Create `docs/00_project/README.md`: project-layer entry.
- Create `docs/00_project/overview.md`: concise project positioning.
- Create `docs/00_project/glossary.md`: initial shared terminology.
- Create `docs/00_project/status.md`: current project status dashboard.
- Create `docs/00_project/scope.md`: current scope, non-goals, and vtext boundary.
- Create `docs/00_project/roadmap.md`: project roadmap summary that links to the existing roadmap.
- Create `docs/10_product/README.md`: product layer placeholder index with concrete responsibility.
- Create `docs/20_architecture/README.md`: architecture layer index that links to current legacy docs.
- Create `docs/30_pipeline/README.md`: pipeline layer stage index and current stage statuses.
- Create `docs/40_development/README.md`: development layer index.
- Create `docs/50_modules/README.md`: module layer index.
- Create `docs/60_operations/README.md`: operations layer index.
- Create `docs/70_progress/README.md`: progress layer index that links to current progress logs.
- Create `docs/80_superpowers/README.md`: agent planning layer index that links to existing `docs/superpowers/` during migration.
- Create `docs/90_reference/README.md`: reference layer index.

This plan intentionally does not move existing files such as `docs/business-plan.md`, `docs/pipeline.md`, or `docs/superpowers/`. The first pass makes the new navigation and shared language available without breaking current references.

---

### Task 1: Documentation Layer Skeleton and Index READMEs

**Files:**
- Create: `docs/00_project/README.md`
- Create: `docs/10_product/README.md`
- Create: `docs/20_architecture/README.md`
- Create: `docs/30_pipeline/README.md`
- Create: `docs/40_development/README.md`
- Create: `docs/50_modules/README.md`
- Create: `docs/60_operations/README.md`
- Create: `docs/70_progress/README.md`
- Create: `docs/80_superpowers/README.md`
- Create: `docs/90_reference/README.md`

- [ ] **Step 1: Create layer directories and README files**

Create the files with this content:

`docs/00_project/README.md`

```markdown
# 00 Project

Project-level documents answer what vBook is, what it is not, which terms mean
what, and where the project currently stands.

## Read First

1. [overview.md](./overview.md)
2. [glossary.md](./glossary.md)
3. [status.md](./status.md)
4. [scope.md](./scope.md)
5. [roadmap.md](./roadmap.md)

## Layer Responsibility

Use this layer for stable project-level context that both users and developers
need before reading implementation details.
```

`docs/10_product/README.md`

```markdown
# 10 Product

Product-level documents describe user scenarios, expected workflows, feature
requirements, and acceptance criteria.

## Planned Documents

- `user-scenarios.md`
- `mvp-requirements.md`
- `output-experience.md`
- `workflow.md`

## Current Source Material

- [../business-plan.md](../business-plan.md)
- [../vBook需求意向.md](../vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md)
```

`docs/20_architecture/README.md`

```markdown
# 20 Architecture

Architecture-level documents describe system design, data contracts, module
boundaries, output contracts, and durable technical decisions.

## Current Source Documents

- [../architecture.md](../architecture.md)
- [../design.md](../design.md)
- [../data-model.md](../data-model.md)
- [../modules.md](../modules.md)
- [../output-behavior.md](../output-behavior.md)

## Planned Documents

- `module-boundaries.md`
- `output-contracts.md`
- `decisions.md`
```

`docs/30_pipeline/README.md`

```markdown
# 30 Pipeline

Pipeline-level documents describe each vBook processing stage: purpose, input,
output, owning module, current status, limitations, and next tasks.

## Current Pipeline Stages

| Stage | Current status | Current source |
| --- | --- | --- |
| Transcript import | Functional foundation | [../pipeline.md](../pipeline.md) |
| Frame extraction | Functional foundation | [../pipeline.md](../pipeline.md) |
| Frame selection | Functional foundation | [../pipeline.md](../pipeline.md) |
| Vision analysis | Partial: placeholder and manual-json | [../pipeline.md](../pipeline.md) |
| Timeline alignment | Functional foundation | [../pipeline.md](../pipeline.md) |
| Fusion prompt | Placeholder snapshot | [../pipeline.md](../pipeline.md) |
| Fusion sections | Deterministic placeholder | [../pipeline.md](../pipeline.md) |
| Note export | Functional placeholder/section note | [../output-behavior.md](../output-behavior.md) |
| Manifest | Functional foundation | [../output-behavior.md](../output-behavior.md) |

## Planned Stage Documents

- `transcript-import.md`
- `frame-extraction.md`
- `frame-selection.md`
- `vision-analysis.md`
- `timeline-alignment.md`
- `fusion-prompt.md`
- `fusion-sections.md`
- `note-export.md`
- `manifest.md`
```

`docs/40_development/README.md`

```markdown
# 40 Development

Development-level documents explain how to set up, test, change, review, and
ship vBook work.

## Current Entry Points

- [../../AGENTS.md](../../AGENTS.md)
- [../sync-protocol.md](../sync-protocol.md)
- [../../README.md](../../README.md#development-commands)

## Planned Documents

- `setup.md`
- `commands.md`
- `coding-style.md`
- `testing.md`
- `git-workflow.md`
- `agent-collaboration.md`
- `release-checklist.md`
```

`docs/50_modules/README.md`

```markdown
# 50 Modules

Module-level documents describe package responsibilities and public interfaces.

## Current Modules

- `vbook_client`
- `vbook_common`
- `vbook_audio`
- `vbook_vision`
- `vbook_pipeline`
- `vbook_fusion`
- `vbook_export`
- `vbook_server`

## Current Source Material

- [../modules.md](../modules.md)
- [../data-model.md](../data-model.md)
```

`docs/60_operations/README.md`

```markdown
# 60 Operations

Operations-level documents explain how to run vBook locally, inspect outputs,
perform smoke tests, troubleshoot failures, and clean generated artifacts.

## Current Entry Points

- [../../README.md](../../README.md#development-commands)
- [../output-behavior.md](../output-behavior.md)

## Planned Documents

- `local-run.md`
- `sample-inputs.md`
- `smoke-tests.md`
- `batch-processing.md`
- `troubleshooting.md`
- `outputs-cleanup.md`
```

`docs/70_progress/README.md`

```markdown
# 70 Progress

Progress-level documents make project state visible without requiring readers
to reconstruct it from chat history or dated logs.

## Current Status

- [../00_project/status.md](../00_project/status.md)

## Current Progress Logs

- [../progress/2026-06-25.md](../progress/2026-06-25.md)

## Planned Documents

- `backlog.md`
- `milestones.md`
```

`docs/80_superpowers/README.md`

```markdown
# 80 Superpowers

Agent planning documents store design specs, implementation plans, reviews, and
handoffs. These are process artifacts, not the primary project reading path.

## Current Planning Documents

- [../superpowers/specs/](../superpowers/specs/)
- [../superpowers/plans/](../superpowers/plans/)

## Planned Directories

- `specs/`
- `plans/`
- `reviews/`
- `handoffs/`
```

`docs/90_reference/README.md`

```markdown
# 90 Reference

Reference documents preserve source material, external constraints, and related
project context that are useful but not part of the main reading path.

## Current Source Material

- [../vBook需求意向.md](../vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md)
- [../sync-protocol.md](../sync-protocol.md)

## Planned Documents

- `original-requirements.md`
- `vtext-boundary.md`
- `external-tools.md`
- `sample-json.md`
```

- [ ] **Step 2: Verify files are present**

Run:

```powershell
Get-ChildItem docs -Directory | Sort-Object Name
```

Expected: output includes `00_project`, `10_product`, `20_architecture`, `30_pipeline`, `40_development`, `50_modules`, `60_operations`, `70_progress`, `80_superpowers`, and `90_reference`.

- [ ] **Step 3: Commit skeleton**

Run:

```powershell
git add docs/00_project/README.md docs/10_product/README.md docs/20_architecture/README.md docs/30_pipeline/README.md docs/40_development/README.md docs/50_modules/README.md docs/60_operations/README.md docs/70_progress/README.md docs/80_superpowers/README.md docs/90_reference/README.md
git commit -m "docs: add documentation layer skeleton"
```

---

### Task 2: Project Glossary, Status, Scope, Roadmap, and Overview

**Files:**
- Create: `docs/00_project/overview.md`
- Create: `docs/00_project/glossary.md`
- Create: `docs/00_project/status.md`
- Create: `docs/00_project/scope.md`
- Create: `docs/00_project/roadmap.md`

- [ ] **Step 1: Create `overview.md`**

Use this content:

```markdown
# vBook Overview

vBook turns video courses into image-aware notes and a searchable knowledge
base. The project is currently focused on a local MVP pipeline that can process
a lesson video plus timestamped transcript into reproducible Markdown and JSON
outputs.

## Core Value

Course videos often contain information that is not fully represented in audio
transcripts: slides, K-line chart cases, tables, screenshots, and annotations.
vBook preserves that visual context, aligns it with transcript segments, and
exports structured notes that can later enter a knowledge base.

## Current Execution Path

The current primary command is:

```powershell
python -m vbook_client build --video lesson.mp4 --transcript transcript.json --output outputs/lesson
```

`--transcript` accepts timestamped JSON or SRT files. The build command writes
`manifest.json`, `note.md`, `vision/analysis.json`, `fusion/prompt.json`, and
`fusion/sections.json`.

## Current Emphasis

The project is in the local MVP pipeline stage. The pipeline can run end to end,
but some stages are still deterministic foundations or placeholders rather than
final intelligent implementations.
```

- [ ] **Step 2: Create `glossary.md`**

Use this content:

```markdown
# vBook Glossary

This glossary defines the shared vocabulary used in vBook discussions, docs,
code reviews, and progress reports.

## Status Terms

### Functional foundation

A working deterministic implementation that is useful for pipeline integration
and regression testing, but may not yet represent final product intelligence.

### Placeholder

An intentional simple implementation that preserves data shape and pipeline
flow while postponing real semantic work. A placeholder is not a bug, but it
must be named clearly.

### Partial

A stage has more than placeholder behavior but is not complete. For example,
visual analysis now supports `manual-json`, but it does not yet call OCR or
multimodal models.

### Done

The stage ran and produced its expected output artifact during a pipeline run.
In `manifest.json`, this appears as a stage status such as `"done"`.

### Skipped

The stage was not requested or could not run because its prerequisites were not
provided. In `manifest.json`, this appears as `"skipped"`.

## Project Terms

### vBook

The project in this repository. vBook automates video-course analysis into
image-aware notes and a searchable knowledge base.

### vtext

A related reference project for video-to-audio-to-text-to-knowledge workflow
ideas. vBook may learn from vtext design but must not import, vendor, or depend
on vtext code.

### MVP

The minimum useful local pipeline: transcript import, frame extraction, frame
selection, visual analysis output, timeline alignment, fusion artifacts, note
export, and manifest export.

## Input Terms

### Video

The source lesson media file, usually an MP4. It is the source for extracted
frames and, in future stages, audio transcription.

### Transcript

Timestamped text for the lesson. Current supported input formats are JSON and
SRT. vBook normalizes transcripts into `TranscriptSegment[]`.

### TranscriptSegment

The normalized data object for one timestamped transcript segment. It records
start time, end time, text, source, and optional metadata.

## Vision Terms

### FrameCandidate

The normalized data object for one extracted or discovered frame. It records
frame id, video id, timestamp, image path, dimensions, and filter state.

### Candidate frame

A frame extracted from video or discovered from an existing frame directory
before final selection.

### Selected frame

A candidate frame kept for downstream stages such as vision analysis, timeline
alignment, fusion, and note export.

### Rejected frame

A candidate frame excluded by frame selection. Rejected frame records are still
useful for auditability.

### VisualAnalysis

The normalized data object for visual understanding output. It records frame id,
visual type, image path, OCR text, visual description, structured observations,
confidence, and backend name.

### VisualType

The category of a visual analysis record. Current values are `slide`,
`kline_case`, and `other`.

### Vision backend

The implementation that produces `VisualAnalysis[]` from frames. Current
backends are `placeholder` and `manual-json`.

### placeholder backend

The default no-service backend. It creates deterministic `VisualAnalysis`
records so the pipeline can run without OCR or model services.

### manual-json backend

A backend that loads externally prepared or manually written visual analysis
from JSON and normalizes it into `VisualAnalysis[]`.

## Pipeline Terms

### Timeline alignment

The stage that links frame timestamps to nearby transcript segments and returns
`TimelineLink[]`.

### Fusion prompt snapshot

A JSON artifact that records the transcript, visual analysis, and timeline
alignment context that would be used for later knowledge fusion.

### Fusion sections

Structured `KnowledgeSection[]` output. Current implementation is deterministic
placeholder construction, not final LLM summarization.

### KnowledgeSection

The normalized data object for one note section. It can include title, summary,
timestamps, image references, key points, and tags.

## Output Terms

### note.md

The human-readable Markdown note exported by vBook.

### manifest.json

The machine-readable run index. It records inputs, stage statuses, output paths,
and artifact summaries.

### vision/analysis.json

The normalized visual analysis artifact.

### fusion/prompt.json

The fusion prompt snapshot artifact.

### fusion/sections.json

The structured fusion sections artifact.
```

- [ ] **Step 3: Create `status.md`**

Use this content:

```markdown
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
```

- [ ] **Step 4: Create `scope.md`**

Use this content:

```markdown
# Project Scope

## In Scope Now

- Local CLI pipeline.
- Timestamped transcript import from JSON and SRT.
- Frame extraction and frame selection.
- Normalized visual analysis artifacts.
- Timeline alignment.
- Fusion prompt and fusion section artifacts.
- Markdown note export.
- Manifest-based audit and reproducibility.

## Not In Scope Yet

- Production server runtime.
- Job queue or web progress UI.
- Built-in OCR service integration.
- Built-in multimodal model integration.
- Full knowledge-base storage and search service.
- Importing or vendoring vtext code.

## vtext Boundary

vBook can learn from vtext's workflow and documentation style, but vBook must
remain independently runnable. vBook may call external tools in the future, but
it must not depend on vtext packages or copy vtext implementation code.
```

- [ ] **Step 5: Create `roadmap.md`**

Use this content:

```markdown
# Project Roadmap

This page summarizes the active roadmap. The legacy roadmap remains available
at [../roadmap.md](../roadmap.md) until the documentation migration is complete.

## P1: Project Skeleton

Status: functional foundation.

- Python packaging and CLI entry point exist.
- Core dataclasses and serialization exist.
- Initial module boundaries exist.

## P2: Local MVP Pipeline

Status: functional foundation with partial intelligence.

- Transcript import works for JSON and SRT.
- Frame extraction and selection work.
- Vision analysis supports `placeholder` and `manual-json`.
- Timeline alignment works.
- Fusion prompt, fusion sections, note export, and manifest export work.

## P3: Real Visual Understanding

Status: not started.

- Add OCR or multimodal backend integration.
- Preserve the `VisualAnalysis[]` contract.
- Keep `placeholder` and `manual-json` as deterministic testing and smoke paths.

## P4: Batch and Knowledge Workflow

Status: designed in part, not implemented as the main path.

- Add batch input workflow.
- Improve note quality and knowledge section synthesis.
- Prepare searchable knowledge-base export.

## P5: Service Runtime

Status: future boundary only.

- Add API, job queue, worker lifecycle, progress stream, and health checks when
  local pipeline behavior is stable.
```

- [ ] **Step 6: Verify markdown files exist**

Run:

```powershell
Get-ChildItem docs/00_project | Sort-Object Name
```

Expected: output includes `README.md`, `overview.md`, `glossary.md`, `status.md`, `scope.md`, and `roadmap.md`.

- [ ] **Step 7: Commit project layer**

Run:

```powershell
git add docs/00_project/README.md docs/00_project/overview.md docs/00_project/glossary.md docs/00_project/status.md docs/00_project/scope.md docs/00_project/roadmap.md
git commit -m "docs: add project glossary and status"
```

---

### Task 3: Root and Docs Entry Points

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`

- [ ] **Step 1: Update root `README.md` documentation entry**

Replace the existing sentence:

```markdown
The original product intent is documented in [`docs/vBook需求意向.md`](docs/vBook需求意向.md). The planning index starts at [`docs/README.md`](docs/README.md).
```

with:

```markdown
Start documentation from [`docs/README.md`](docs/README.md). For a quick project
orientation, read [`docs/00_project/overview.md`](docs/00_project/overview.md),
[`docs/00_project/glossary.md`](docs/00_project/glossary.md), and
[`docs/00_project/status.md`](docs/00_project/status.md). The original product
intent remains available at [`docs/vBook需求意向.md`](docs/vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md).
```

Replace the existing `## Project Status` section:

```markdown
## Project Status

This repository is in initial setup. The video-to-audio-to-text-to-knowledge workflow may reference design ideas from `vtext`, but vBook must remain an independent project and must not depend on or vendor vtext code.
```

with:

```markdown
## Project Status

vBook is in the local MVP pipeline stage. The current pipeline can run from a
video plus timestamped transcript into `manifest.json`, `note.md`,
`vision/analysis.json`, `fusion/prompt.json`, and `fusion/sections.json`.
Some stages are still placeholders or partial foundations. See
[`docs/00_project/status.md`](docs/00_project/status.md) for the current project
dashboard.
```

Replace this bullet in `## Repository Layout`:

```markdown
- `docs/` - business plan, architecture, pipeline, module, data model, and roadmap documents.
```

with:

```markdown
- `docs/` - numbered documentation layers; start at `docs/README.md`.
```

- [ ] **Step 2: Replace `docs/README.md` with layered index**

Use this content:

```markdown
# vBook Documentation

This directory uses numbered documentation layers. Start here before reading
implementation code or dated progress logs.

## Fast Reading Path

For project orientation:

1. [00_project/overview.md](./00_project/overview.md)
2. [00_project/glossary.md](./00_project/glossary.md)
3. [00_project/status.md](./00_project/status.md)
4. [00_project/roadmap.md](./00_project/roadmap.md)

For development work:

1. [00_project/glossary.md](./00_project/glossary.md)
2. [00_project/status.md](./00_project/status.md)
3. [30_pipeline/README.md](./30_pipeline/README.md)
4. [20_architecture/README.md](./20_architecture/README.md)
5. [40_development/README.md](./40_development/README.md)

## Documentation Layers

| Layer | Purpose |
| --- | --- |
| [00_project/](./00_project/) | Project positioning, glossary, scope, roadmap, and status |
| [10_product/](./10_product/) | User scenarios, product workflow, requirements, and acceptance criteria |
| [20_architecture/](./20_architecture/) | System architecture, module boundaries, data contracts, and decisions |
| [30_pipeline/](./30_pipeline/) | Stage-by-stage media-to-knowledge pipeline documentation |
| [40_development/](./40_development/) | Setup, commands, testing, Git workflow, and agent collaboration |
| [50_modules/](./50_modules/) | Package-level documentation for `vbook_*` modules |
| [60_operations/](./60_operations/) | Local runs, smoke tests, troubleshooting, and artifact cleanup |
| [70_progress/](./70_progress/) | Status snapshots, backlog, milestones, and dated progress logs |
| [80_superpowers/](./80_superpowers/) | Agent specs, implementation plans, reviews, and handoffs |
| [90_reference/](./90_reference/) | Original requirements, external references, and vtext boundary material |

## Legacy Documents During Migration

The following documents predate the numbered layout and remain valid during
incremental migration:

- [business-plan.md](./business-plan.md)
- [design.md](./design.md)
- [pipeline.md](./pipeline.md)
- [modules.md](./modules.md)
- [data-model.md](./data-model.md)
- [output-behavior.md](./output-behavior.md)
- [architecture.md](./architecture.md)
- [sync-protocol.md](./sync-protocol.md)
- [roadmap.md](./roadmap.md)
- [vBook需求意向.md](./vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md)

vBook can learn from vtext's project structure and workflow ideas, but it must
remain an independent project with independent modules, interfaces, and
evolution.
```

- [ ] **Step 3: Verify root entry mentions new docs**

Run:

```powershell
rg -n "docs/00_project|Project Status|numbered documentation" README.md docs/README.md
```

Expected: output shows matches in both `README.md` and `docs/README.md`.

- [ ] **Step 4: Commit entry points**

Run:

```powershell
git add README.md docs/README.md
git commit -m "docs: update documentation entry points"
```

---

### Task 4: Documentation Verification

**Files:**
- No planned edits unless verification exposes a broken link or typo.

- [ ] **Step 1: Run full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: PASS, currently `Ran 60 tests` and `OK`.

- [ ] **Step 2: Check git status**

Run:

```powershell
git status --short --branch
```

Expected: clean worktree, with `main` ahead of `origin/main` by the new documentation commits.

- [ ] **Step 3: Commit fixes only if needed**

If Task 4 finds a documentation issue that requires edits, commit with:

```powershell
git add <changed-doc-files>
git commit -m "docs: fix documentation foundation"
```

If no edits are needed, skip this step.

---

## Self-Review

- Spec coverage: This plan implements the approved documentation architecture's first-pass scope: layer skeleton, glossary, status dashboard, root entry, and docs entry. It intentionally avoids large migration of existing files.
- Added user requirement: root-level documentation entry is explicitly covered in Task 3 by updating `README.md`.
- Placeholder scan: This plan contains no unresolved placeholder markers. Planned future documents are listed as intentionally planned docs, not implementation gaps for this first pass.
- Type consistency: Paths consistently use `docs/00_project`, `docs/30_pipeline`, `docs/80_superpowers`, `README.md`, and `docs/README.md`.
