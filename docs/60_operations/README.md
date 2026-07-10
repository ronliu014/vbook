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
- [vault-enhance.md](./vault-enhance.md) - current vtext-first workflow that
  writes image-enhanced notes under the lowercase `vbook` output tree.
- [experiment-workspace.md](./experiment-workspace.md) - user-provided
  `F:/vbook` workspace layout for input registries and formal experiment
  outputs.
- [experiment-workflow.md](./experiment-workflow.md) - standard phase-by-phase
  runbook for repeatable route and model experiments.
- [experiment-artifacts.md](./experiment-artifacts.md) - project-local layout
  for experiment inputs, requests, responses, renders, reviews, comparisons,
  and decisions.
- [experiment-datasets.md](./experiment-datasets.md) - canonical local paths,
  real-course sample set, route labels, and review checklist for experiments.
- [../../README.md](../../README.md#development-commands)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)

## Deprecated / Historical

- [vault-enhancement-preview.md](./vault-enhancement-preview.md) - old
  append-style preview workflow. Kept for historical reproduction only; new
  vault-quality work should follow the vtext-first augmentation design in
  [../80_superpowers/specs/2026-07-07-vtext-first-vault-augmentation-design.md](../80_superpowers/specs/2026-07-07-vtext-first-vault-augmentation-design.md).

## Planned Documents

- `local-run.md`
- `sample-inputs.md`
- `troubleshooting.md`
- `outputs-cleanup.md`
