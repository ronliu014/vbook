# Experiment Workspace

This document defines the user-provided experiment workspace root. It lets a
user provide one stable directory while vBook agents create the detailed
experiment structure consistently.

## Canonical Workspace Root

The current user-provided root is:

```text
F:/vbook
```

Use this root for long-running note-generation experiments. The repository's
`outputs/experiments/` directory remains useful for short development smoke
runs, but formal route and model comparisons should prefer `F:/vbook`.

## Top-Level Layout

```text
F:/vbook/
  inputs/
  experiments/
  reviews/
  shared/
  README.md
```

### `inputs/`

User-managed or agent-indexed experiment input sets.

```text
F:/vbook/inputs/
  investment-camp-hanke-basic-v1/
    dataset.json
    lessons/
      lesson-001.json
      lesson-002.json
      lesson-003.json
```

Rules:

- Treat `inputs/` as read-only during experiment runs unless the user explicitly
  asks to curate an input package.
- Do not copy large course videos, extracted frames, or original vtext notes
  into this directory by default.
- Prefer path references to canonical sources such as `F:/downloads/allwin`,
  `F:/vault/20_Learning/vtext`, and existing vBook `outputs/` lesson-output
  directories.

### `experiments/`

Agent-managed experiment outputs.

```text
F:/vbook/experiments/
  E20260710-semantic-visual-note/
    manifest.json
    README.md
    inputs/
    requests/
    responses/
    renders/
    reviews/
    comparisons/
    decision.md
```

Rules:

- Every formal experiment gets one stable `<experiment-id>` directory.
- All generated requests, responses, rendered notes, review files, comparison
  tables, and decisions for that experiment stay inside that directory.
- Never write directly to `F:/vault/20_Learning/vbook` from an experiment.

### `reviews/`

Optional cross-experiment user review material.

Use this for reusable side-by-side exports or user-facing comparison bundles
that span multiple experiment ids. Per-experiment reviews must still be copied
or summarized under each experiment's own `reviews/` directory.

### `shared/`

Reusable small assets and schemas.

Examples:

- scorecard schemas;
- prompt version notes;
- provider adapter notes;
- sample review instructions.

Do not store API keys or provider credentials here.

## Agent Startup Contract

At the start of a formal experiment, the agent must record:

```text
Input root:  F:/vbook/inputs/<dataset-id>
Output root: F:/vbook/experiments
Experiment:  F:/vbook/experiments/<experiment-id>
Vault write: disabled
```

If the input data is still distributed across several existing locations, the
agent may use:

```text
Input root:  F:/vbook/inputs/<dataset-id>
```

as a registry package that points to those locations instead of containing the
source files themselves.

## Loose and Packaged Input Modes

### Loose Mode

Use loose mode during early exploration. The user gives `F:/vbook` as the root,
and the agent creates an input registry that points to existing local paths.

This mode fits the current investment-camp data, which is split across:

- `F:/downloads/allwin/投资训练营`
- `F:/vault/20_Learning/vtext/投资训练营`
- `E:/projects/my_app/vbook/outputs/interval-sweep-qwen/240s`
- `E:/projects/my_app/vbook/outputs/post-deploy-vault-enhance/240s`

### Packaged Mode

Use packaged mode when the dataset becomes stable enough for repeated model
comparison. The input root contains a `dataset.json` plus one lesson metadata
file per lesson. The metadata still references large source files by path.

## Safety Rules

- `F:/vbook/inputs` is an input registry and should not be mutated by a run.
- `F:/vbook/experiments` is the only formal experiment output root.
- `F:/vault/20_Learning/vtext` is read-only source material.
- `F:/vault/20_Learning/vbook` is a publication target, not an experiment
  output directory.
- API keys, provider credentials, and account identifiers must never be written
  under `F:/vbook`.
