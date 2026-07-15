# Experiment Workflow Runbook

This runbook is the standard execution workflow for vBook technical
experiments. Use it together with:

- [../40_development/experiment-protocol.md](../40_development/experiment-protocol.md)
- [experiment-workspace.md](./experiment-workspace.md)
- [experiment-datasets.md](./experiment-datasets.md)
- [experiment-artifacts.md](./experiment-artifacts.md)

The protocol defines what must be recorded. This runbook defines how each
experiment should be run.

## Principles

- Keep every experiment reproducible.
- Keep source notes and vault targets read-only until review.
- Compare routes using the same lessons and the same rubric.
- Record small evidence summaries in docs; keep formal generated artifacts in
  `F:/vbook/experiments`. Use repository-local `outputs/` only for short
  development smoke runs.
- Do not change the evaluation criteria after seeing a model result. If the
  rubric needs to change, record that as a separate decision first.

## Standard Phases

Every experiment should move through these phases in order.

| Phase | Output |
| --- | --- |
| 0. Scope | Experiment id, route label, hypothesis, branch, input root, output root |
| 1. Baseline | Git status, baseline tag/commit, existing route output paths |
| 2. Dataset | Selected lessons from `experiment-datasets.md` |
| 3. Request | Provider-neutral request or deterministic preview inputs |
| 4. Model run | Structured response, model metadata, error record |
| 5. Render | Project-local Markdown preview and copied assets |
| 6. Review | Developer and user rubric scores, screenshots or image-path evidence, issues |
| 7. Decision | Continue, revise, compare, abandon, or candidate for production |
| 8. Summary | Dated progress log under `docs/70_progress/` |

## Phase 0: Scope

Before running commands, write down:

- experiment id, for example `E20260710-semantic-visual-note-qwen-json`;
- route label, for example `semantic_visual_note`;
- branch name;
- hypothesis;
- model/provider, if any;
- input root;
- output root;
- intended experiment directory.

Canonical workspace roots:

```text
Input root:  F:/vbook/inputs/<dataset-id>
Output root: F:/vbook/experiments
Experiment:  F:/vbook/experiments/<experiment-id>
Vault write: disabled
```

Examples:

```text
F:/vbook/experiments/E20260710-semantic-visual-note/
F:/vbook/experiments/E20260710-model-adapter-eval-openai/
```

Use the subdirectory layout in
[experiment-artifacts.md](./experiment-artifacts.md) for inputs, requests,
responses, renders, reviews, comparisons, and decisions.

## Phase 1: Baseline

Run from the repository root:

```text
git status -sb
git log --oneline --decorate -3
git branch --show-current
D:/anaconda3/envs/App/python.exe -m vbook_client check
```

Record the result in the dated progress note.

Expected safety condition:

- existing stable work is committed or intentionally left in the active
  experiment branch;
- no unrelated worktree changes are mixed into the experiment.

## Phase 2: Dataset Selection

Use the registered evaluation set in
[experiment-datasets.md](./experiment-datasets.md) unless the experiment
explicitly records a new dataset.

Default small set:

- `如何筛选龙头股？`
- `龙头股的上涨逻辑是什么？`
- `反抽 反弹 反转`

For each selected lesson, record:

- vtext source note, if used;
- lesson-output directory;
- frame interval, usually `240s` for the current visual baseline;
- transcript source label;
- whether Qwen/vision errors are present.

## Phase 3: Request Generation

For `semantic_visual_note`, first generate request-only packages. This checks
that the model input is correct before involving a model provider.

Example:

```text
D:/anaconda3/envs/App/python.exe -m vbook_client semantic-visual-note \
  --lesson-output "outputs/interval-sweep-qwen/240s/韩珂龙头班：基础篇/如何筛选龙头股？" \
  --output "F:/vbook/experiments/E20260710-semantic-visual-note/requests/semantic_visual_note/如何筛选龙头股？" \
  --transcript-source-label vtext_semantic_verified \
  --max-visuals-per-request 4
```

Check:

- `manifest.json` has `status: request_ready`;
- request uses timestamped transcript segments, not vtext summary Markdown;
- visual evidence includes high-value frames;
- structured Qwen error frames are skipped;
- no vault paths are written.

Then copy or index the exact request JSON under:

```text
F:/vbook/experiments/<experiment-id>/requests/<route-label>/<lesson>.request.json
```

## Phase 4: Model Run

Model runs must be explicit and provider metadata must be captured.

Allowed comparison candidates:

- Qwen VL;
- Claude / Claude API;
- GLM API;
- OpenAI GPT API.

For each run, record:

- provider and exact model name;
- input mode: OCR/vision JSON only, raw image pixels only, or both;
- command or adapter entry point;
- timeout and retry settings;
- response JSON path;
- validation result.

Store raw responses or structured errors under:

```text
F:/vbook/experiments/<experiment-id>/responses/<provider>/<lesson>.response.json
F:/vbook/experiments/<experiment-id>/responses/<provider>/<lesson>.error.json
```

The output must satisfy the vBook sections contract before rendering:

- `schema_version`;
- top-level `title`, `overview`, `sections`;
- per-section `title`, `summary`, `key_points`, `source_timestamps`,
  `image_refs`, `tags`.

If a provider returns Markdown only, treat it as an invalid response for this
workflow unless a parser step is explicitly added and tested.

## Phase 5: Render Preview

Render formal experiment previews into `F:/vbook/experiments`. Repository-local
`outputs/` paths are allowed for short development smoke runs only.

For `semantic_visual_note`, render an existing structured response with:

```text
D:/anaconda3/envs/App/python.exe -m vbook_client semantic-visual-note \
  --lesson-output "<lesson-output>" \
  --output "<preview-output>" \
  --llm-response "<response-json>"
```

Check:

- preview Markdown exists;
- referenced images are copied under `assets/`;
- Markdown image links resolve after URL decoding;
- source transcript/note remains read-only;
- no direct write to `F:/vault/20_Learning/vbook`.

Store rendered previews under:

```text
F:/vbook/experiments/<experiment-id>/renders/<route-label>/<provider-or-baseline>/<lesson>/
```

## Phase 6: Review

Use the rubric in
[../40_development/experiment-protocol.md](../40_development/experiment-protocol.md).

Create a standard review round package before asking the user to compare
candidate outputs:

```text
D:/anaconda3/envs/App/python.exe tools/experiment_review_round.py \
  --experiment-root "F:/vbook/experiments/<experiment-id>" \
  --round-id round-001 \
  --dataset-id <dataset-id>
```

The package is written under:

```text
F:/vbook/experiments/<experiment-id>/reviews/<round-id>/
  review-manifest.json
  review-sheet.csv
  user-review.md
  decision-template.md
```

Use `review-sheet.csv` as the numeric scoring table and `user-review.md` as the
human-facing checklist. Use `decision-template.md` only after the user has
reviewed comparable outputs.

Required checks for every preview:

| Check | Evidence |
| --- | --- |
| Images display | Markdown preview or resolved file path |
| Image choice is high-value | selected frame path and visual description |
| Placement is correct | Markdown heading and line number |
| Semantic coverage improves or regresses | comparison notes against source timeline and vtext-first output |
| No Qwen error placeholders | manifest or request metric |
| Text remains grounded | examples of supported/unsupported claims |
| Traceability exists | timestamps and image refs in sections |

Use numeric scores from `0` to `3` and short reviewer notes.

User review is required before choosing a best implementation route. Use the
standard review round package and ask the user to compare the same lesson
across candidate outputs.

## Phase 7: Decision

End each experiment with one decision:

- `continue`: route is promising, run more lessons or models;
- `revise`: route is promising but needs implementation/prompt changes;
- `compare`: route is ready for side-by-side scoring against another route;
- `abandon`: route does not justify further work now.
- `candidate_for_production`: route has passed the maturity gate and is ready
  for implementation hardening.

Record the reason. Do not delete outputs immediately; keep preview artifacts
until the dated progress note has enough evidence to reconstruct the result.

Finalize the review round after the user chooses a route:

```text
D:/anaconda3/envs/App/python.exe tools/experiment_review_round.py \
  --experiment-root "F:/vbook/experiments/<experiment-id>" \
  --round-id round-001 \
  --dataset-id <dataset-id> \
  --selected-route <route-label> \
  --decision-status continue \
  --reason "<short reason>" \
  --user-review-summary "<short user preference summary>"
```

Finalization updates:

- `review-manifest.json` with `review_status`, `selected_route`, and
  `decision_status`;
- `review-sheet.csv` with route preference scores and reviewer notes;
- `user-review.md` with a `Review Outcome` section;
- `decision-template.md` as the final decision record for the round.

After finalization, run the maturity gate for the selected route:

```text
D:/anaconda3/envs/App/python.exe tools/experiment_maturity_gate.py \
  --experiment-root "F:/vbook/experiments/<experiment-id>" \
  --route <route-label> \
  --round-id round-001 \
  --json-output "F:/vbook/experiments/<experiment-id>/comparisons/maturity-gate-<route-label>.json" \
  --markdown-output "F:/vbook/experiments/<experiment-id>/comparisons/maturity-gate-<route-label>.md"
```

The gate checks that the selected route has at least three rendered lessons,
passed preflight, was selected in a finalized review round, has sufficient user
preference scores, and keeps preview paths inside the experiment root. A passing
gate means the route may be treated as a production-candidate hardening target;
it does not publish anything to vault.

## Phase 8: Summary

Write or update a dated progress log under `docs/70_progress/`.

Minimum summary:

```text
Experiment:
Branch:
Input root:
Output root:
Dataset:
Commands:
Outputs:
Model:
Scores:
Findings:
Decision:
Next:
```

## Strict Safety Rules

- Never overwrite vtext original notes.
- Never write experiment output directly into the vBook vault target.
- Never commit API keys or provider credentials.
- Never compare outputs generated from different datasets as if they were the
  same experiment.
- Never accept a model result that fails the output contract unless the failure
  itself is the recorded result.

## Workflow Maturity Gate

Before calling a route a candidate for production, it must pass:

- at least three registered lessons;
- Markdown preview inspection;
- image-link existence checks;
- route comparison against `vtext_first_vault_enhance`;
- user review on the strongest candidate outputs;
- finalized review round with selected route;
- maturity gate status `pass`;
- dated progress summary with decision and known risks.
