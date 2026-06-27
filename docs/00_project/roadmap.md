# Project Roadmap

This page summarizes the active roadmap. The pre-layering roadmap remains
available at [legacy-roadmap.md](./legacy-roadmap.md).

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

Status: interface foundation in progress.

- `external-command` backend lets vBook call a user-supplied visual analysis
  command through a JSON contract.
- Add OCR or multimodal backend integration.
- Preserve the `VisualAnalysis[]` contract.
- Keep `placeholder` and `manual-json` as deterministic testing and smoke paths.

## P4: Batch and Knowledge Workflow

Status: functional foundation for batch input; knowledge workflow still partial.

- Add batch input workflow.
- Improve note quality and knowledge section synthesis.
- Prepare searchable knowledge-base export.

## P5: Service Runtime

Status: future boundary only.

- Add API, job queue, worker lifecycle, progress stream, and health checks when
  local pipeline behavior is stable.
