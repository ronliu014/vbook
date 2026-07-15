# Experiment Artifact Layout

This document defines how vBook stores experiment inputs, outputs, reviews, and
comparisons. The goal is to make each route or model attempt reproducible and
reviewable by both developers and users.

Use this layout together with:

- [experiment-workspace.md](./experiment-workspace.md)
- [experiment-workflow.md](./experiment-workflow.md)
- [experiment-datasets.md](./experiment-datasets.md)
- [../40_development/experiment-protocol.md](../40_development/experiment-protocol.md)

## Root Layout

Formal experiment artifacts should live under the user-provided workspace root:

```text
F:/vbook/experiments/
```

Repository-local `outputs/experiments/` remains available for short development
smoke runs, but route and model comparisons intended for user review should use
`F:/vbook/experiments/`.

```text
F:/vbook/experiments/<experiment-id>/
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

The experiment id should be stable and descriptive:

```text
E20260710-semantic-visual-note
E20260710-model-adapter-eval-openai
E20260710-vtext-first-baseline
```

## Input and Output Roots

The user only needs to provide the workspace root, currently `F:/vbook`.
Agents derive standard roots from it:

```text
input_root:  F:/vbook/inputs/<dataset-id>
output_root: F:/vbook/experiments
experiment:  F:/vbook/experiments/<experiment-id>
```

If the input set is not yet packaged, `input_root` acts as a registry that
points to existing videos, vtext notes, transcripts, lesson-output directories,
and baseline previews. Agents must not rewrite original source notes or course
media while creating this registry.

## Top-Level Files

### `manifest.json`

Machine-readable experiment index.

Required fields:

```json
{
  "schema_version": "1",
  "experiment_id": "E20260710-semantic-visual-note",
  "route_label": "semantic_visual_note",
  "branch": "codex-semantic-visual-note-test",
  "baseline_ref": "v0.1.0",
  "dataset_id": "investment-camp-hanke-basic-240s-v1",
  "input_root": "F:/vbook/inputs/investment-camp-hanke-basic-v1",
  "output_root": "F:/vbook/experiments",
  "experiment_root": "F:/vbook/experiments/E20260710-semantic-visual-note",
  "status": "request_ready",
  "created_at": "2026-07-10",
  "vault_write": "disabled",
  "lessons": []
}
```

### `README.md`

Human-readable overview:

- hypothesis;
- route/model under test;
- dataset;
- commands;
- output locations;
- review status.

### `decision.md`

Final or current decision:

- `continue`;
- `revise`;
- `compare`;
- `abandon`;
- later, `candidate_for_production`.

Include why the decision was made and what evidence supports it.

## Inputs

`inputs/` stores small pointers and normalized metadata, not large media copies.

```text
inputs/
  dataset.json
  lessons/
    lesson-001.json
    lesson-002.json
```

Each lesson input record should include:

- lesson id and title;
- source video path;
- transcript source path or manifest segment source;
- lesson-output path;
- vtext note path, if used;
- frame interval;
- known visual/model error notes.

Do not copy course videos, extracted frames, or vtext original notes here.
Reference their paths.

## Requests

`requests/` stores model/provider-neutral inputs.

```text
requests/
  semantic_visual_note/
    如何筛选龙头股？.request.json
    龙头股的上涨逻辑是什么？.request.json
  vtext_first_vault_enhance/
    如何筛选龙头股？.request.json
```

Rules:

- Store exact request JSON used for a model run.
- Include prompt/instruction version inside the request or adjacent metadata.
- If request files are too large for Git, keep them under `outputs/` only and
  summarize them in docs.

## Responses

`responses/` stores raw model outputs and structured error records.

```text
responses/
  openai/
    如何筛选龙头股？.response.json
    如何筛选龙头股？.error.json
  glm/
  claude/
  qwen/
```

Each response metadata should record:

- provider;
- model name;
- input mode: `structured_json`, `raw_image`, or `json_plus_image`;
- latency;
- token usage, if available;
- timeout/retry result;
- validation status.

Never store API keys or provider account identifiers.

## Renders

`renders/` stores final human-reviewable previews.

```text
renders/
  semantic_visual_note/
    openai/
      如何筛选龙头股？/
        note.md
        manifest.json
        assets/
    glm/
  vtext_first_vault_enhance/
    baseline/
      如何筛选龙头股？/
        note.md
        manifest.json
        assets/
```

Rules:

- Every rendered note must be self-contained enough for Markdown preview.
- Images must be copied under an adjacent `assets/` directory.
- Markdown links must resolve locally.
- Rendered outputs remain previews until a separate vault publication workflow
  is accepted.

## Reviews

`reviews/` stores developer and user evaluations.

```text
reviews/
  rubric.md
  developer-review.md
  user-review-template.md
  user-review-round-001.md
  round-002/
    review-manifest.json
    review-sheet.csv
    user-review.md
    decision-template.md
```

### Standard Review Round

Create a review round package with:

```text
D:/anaconda3/envs/App/python.exe tools/experiment_review_round.py \
  --experiment-root "F:/vbook/experiments/<experiment-id>" \
  --round-id round-002 \
  --dataset-id <dataset-id>
```

Files:

- `review-manifest.json`: machine-readable list of candidates, preview paths,
  route variants, and imported preflight statuses.
- `review-sheet.csv`: fixed scoring table for developer and user review.
- `user-review.md`: human-facing checklist grouped by lesson and route.
- `decision-template.md`: final decision scaffold to fill after review.

The generated sheet uses the standard dimensions:

```text
lesson,route,variant,readable_note_candidate,preview_path,preflight_status,
semantic_coverage,visual_recovery,image_choice,image_placement,
error_handling,text_discipline,traceability,preview_safety,
user_preference,reviewer_notes
```

Automatic preflight status is supporting evidence only. A passing preflight does
not mean the route wins; it only means the preview is mechanically safe enough
for user comparison.

After the user chooses the best route, finalize the round:

```text
D:/anaconda3/envs/App/python.exe tools/experiment_review_round.py \
  --experiment-root "F:/vbook/experiments/<experiment-id>" \
  --round-id round-002 \
  --dataset-id <dataset-id> \
  --selected-route <route-label> \
  --decision-status continue \
  --reason "<short reason>" \
  --user-review-summary "<short user preference summary>"
```

Finalization keeps the user's decision machine-readable in
`review-manifest.json`, fills the standard preference fields in
`review-sheet.csv`, adds a `Review Outcome` section to `user-review.md`, and
writes the final decision into `decision-template.md`.

### User Review Template

Use this template when asking the user to compare outputs:

```text
Lesson:
Candidate A:
Candidate B:
Candidate C:

Scores, 0-3:
- Semantic coverage:
- Visual usefulness:
- Image placement:
- Readability:
- Trust / evidence grounding:
- Overall preference:

Best candidate:
Reason:
Must-fix issues:
Would publish to vault? yes/no
```

The user should compare the same lesson across candidate routes/models. Do not
ask the user to compare different lessons as if they were route quality.

## Comparisons

`comparisons/` stores side-by-side result tables.

```text
comparisons/
  route-comparison.md
  model-comparison.md
  scorecard.csv
```

Required comparison dimensions:

- semantic coverage;
- visual recovery;
- image choice;
- image placement;
- error handling;
- text discipline;
- traceability;
- preview safety;
- user preference.

## Minimal Experiment Example

For a semantic visual note experiment:

```text
F:/vbook/experiments/E20260710-semantic-visual-note/
  manifest.json
  README.md
  inputs/dataset.json
  requests/semantic_visual_note/如何筛选龙头股？.request.json
  responses/openai/如何筛选龙头股？.response.json
  renders/semantic_visual_note/openai/如何筛选龙头股？/note.md
  reviews/user-review-round-001.md
  comparisons/model-comparison.md
  decision.md
```

## Promotion Rule

An experiment can inform implementation decisions only when:

- inputs are registered;
- requests and responses are retained or summarized;
- rendered outputs are inspectable;
- developer review is complete;
- user review has been requested for at least the strongest candidates;
- comparison notes identify why a route/model wins or loses.
