# Documentation Architecture Design

## Purpose

vBook needs a shared documentation structure before the project grows further.
The immediate problem is not only missing documentation, but missing shared
language. Without a terminology layer and a current-status layer, project
updates become hard to evaluate: readers cannot tell which parts are real,
which are placeholders, which are future goals, and which tasks are next.

This design defines a vBook-specific `docs/` hierarchy inspired by numbered
documentation layers from another project, but adapted to vBook's actual
domain: video-course analysis, visual understanding, knowledge fusion,
reproducible outputs, and agent-assisted development.

## Design Goals

- Give project owners a fast path to understand current project state.
- Give developers and agents a stable path to understand terminology,
  architecture, pipeline stages, commands, and handoff context.
- Separate durable product and architecture documents from implementation
  planning artifacts.
- Make the pipeline a first-class documentation layer because vBook's core
  complexity is stage-by-stage media and knowledge processing.
- Avoid a disruptive one-shot migration; create the structure first, then move
  existing documents gradually.

## Proposed Directory Layout

```text
docs/
  00_project/          Project layer: positioning, goals, scope, glossary, status, roadmap
  10_product/          Product layer: user scenarios, workflows, requirements, acceptance
  20_architecture/     Architecture layer: system design, module boundaries, data contracts
  30_pipeline/         Pipeline layer: stage-by-stage inputs, outputs, status, and tasks
  40_development/      Development layer: setup, commands, testing, Git, agent collaboration
  50_modules/          Module layer: package-level documentation for vbook_* modules
  60_operations/       Operations layer: local runs, samples, smoke tests, troubleshooting
  70_progress/         Progress layer: status snapshots, backlog, milestones, dated logs
  80_superpowers/      Agent planning layer: specs, plans, reviews, handoffs
  90_reference/        Reference layer: original requirements, external tools, vtext boundary
```

## Layer Responsibilities

### `00_project/`

The project entry layer. It answers what vBook is, what it is not, which words
mean what, and where the project currently stands.

Initial files:

- `README.md`: reading order and layer index.
- `overview.md`: one-page project positioning and value.
- `glossary.md`: shared terminology for business, pipeline, data, output, and
  status terms.
- `scope.md`: current scope, non-goals, and vtext boundary.
- `roadmap.md`: stage roadmap.
- `status.md`: current project state for non-implementation readers.

### `10_product/`

The product layer. It explains the user-facing workflow and acceptance criteria
without requiring code knowledge.

Expected files:

- `user-scenarios.md`
- `mvp-requirements.md`
- `output-experience.md`
- `workflow.md`

### `20_architecture/`

The technical design layer. It owns durable architecture, data, module, and
output contracts.

Existing documents that fit here:

- `architecture.md`
- `design.md`
- `data-model.md`
- `modules.md` as `module-boundaries.md`
- `output-behavior.md` as `output-contracts.md`

Expected additional file:

- `decisions.md` for architecture decision records or an ADR index.

### `30_pipeline/`

The vBook-specific pipeline layer. This replaces the game-config layer from
the reference project because vBook's core complexity is its media-to-knowledge
pipeline.

Expected files:

- `README.md`
- `transcript-import.md`
- `frame-extraction.md`
- `frame-selection.md`
- `vision-analysis.md`
- `timeline-alignment.md`
- `fusion-prompt.md`
- `fusion-sections.md`
- `note-export.md`
- `manifest.md`

Each stage document should use the same structure:

- stage purpose;
- current implementation status;
- inputs;
- outputs;
- core data structures;
- CLI or API entry points;
- owning module;
- tests;
- known limitations;
- next tasks.

### `40_development/`

The engineering workflow layer. It explains how to work on the project.

Expected files:

- `README.md`
- `setup.md`
- `commands.md`
- `coding-style.md`
- `testing.md`
- `git-workflow.md`
- `agent-collaboration.md`
- `release-checklist.md`

The root `AGENTS.md` remains the top-level agent instruction file. This layer
can provide longer-form supporting guidance.

### `50_modules/`

The code module layer. It documents package responsibilities and public
interfaces.

Expected files:

- `README.md`
- `vbook_client.md`
- `vbook_common.md`
- `vbook_audio.md`
- `vbook_vision.md`
- `vbook_pipeline.md`
- `vbook_fusion.md`
- `vbook_export.md`
- `vbook_server.md`

### `60_operations/`

The runbook layer. It explains how to run, inspect, debug, and clean generated
artifacts.

Expected files:

- `local-run.md`
- `sample-inputs.md`
- `smoke-tests.md`
- `batch-processing.md`
- `troubleshooting.md`
- `outputs-cleanup.md`

### `70_progress/`

The progress layer. It is designed to prevent the project state from being
trapped in chat history or dated logs only.

Expected files:

- `README.md`
- `status.md`: current status snapshot or a pointer to `00_project/status.md`.
- `backlog.md`
- `milestones.md`
- dated progress logs such as `2026-06-25.md`.

### `80_superpowers/`

The agent planning layer. It keeps implementation-process artifacts separate
from durable project docs.

Expected directories:

- `specs/`
- `plans/`
- `reviews/`
- `handoffs/`

Existing `docs/superpowers/specs/` and `docs/superpowers/plans/` should move
here during migration.

### `90_reference/`

The reference layer. It stores source material and external constraints that
are useful but should not be the primary reading path.

Expected files:

- `original-requirements.md`
- `vtext-boundary.md`
- `external-tools.md`
- `sample-json.md`

Existing `docs/vBook需求意向.md` belongs here as the original requirements
source, with the original wording preserved.

## Recommended Reading Order

For project owners:

```text
1. docs/00_project/overview.md
2. docs/00_project/glossary.md
3. docs/00_project/status.md
4. docs/00_project/roadmap.md
```

For developers and agents:

```text
1. docs/00_project/glossary.md
2. docs/00_project/status.md
3. docs/30_pipeline/README.md
4. docs/20_architecture/data-model.md
5. docs/40_development/commands.md
```

## Migration Strategy

Use an incremental migration instead of moving all documents at once.

1. Create the new directory skeleton and update the root `docs/README.md`.
2. Add `docs/00_project/glossary.md`.
3. Add `docs/00_project/status.md`.
4. Add minimal `README.md` files for the new top-level layers.
5. Move existing durable docs into their target layers in small commits.
6. Move `docs/superpowers/` to `docs/80_superpowers/` after links are updated.
7. Move dated logs from `docs/progress/` to `docs/70_progress/`.

## Initial Implementation Scope

The first implementation should not reorganize every existing file.

It should:

- create the directory skeleton;
- create `docs/00_project/glossary.md`;
- create `docs/00_project/status.md`;
- update `docs/README.md` as the new documentation entry;
- leave existing documents in place unless a small move is clearly needed.

This keeps links stable while giving the project a shared vocabulary and a
readable status dashboard immediately.

## Out of Scope

- Rewriting all existing architecture documents in one pass.
- Renaming every old file immediately.
- Introducing generated documentation tooling.
- Changing runtime code or CLI behavior.
- Changing the `AGENTS.md` instruction contract.

## Success Criteria

- A new reader can find the project overview, glossary, status, and roadmap
  from `docs/README.md`.
- The glossary defines the terms needed to discuss current vBook work without
  ambiguity.
- The status document explains completed, placeholder, partial, blocked, and
  next-step work in shared terminology.
- Existing implementation specs and plans remain accessible during migration.
- The repository test suite still passes because no runtime behavior changes.
