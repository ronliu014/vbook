# Experiment Review Round Design

## Context

vBook now has multiple experiment routes and one current readable-note winner:
`vtext_first_vault_enhance`. The project also has formal experiment roots under
`F:/vbook/experiments`, route renders, user review notes, scorecards, and
automatic preflight output. The next step is to make each user-involved
comparison round repeatable.

## Goal

Create a standard review round package for each experiment comparison. The
package must preserve fixed inputs, candidate outputs, automatic hygiene
evidence, user scoring fields, and a decision template.

## Non-Goals

- Do not rank routes automatically.
- Do not replace user judgment.
- Do not render HTML or build an interactive UI.
- Do not write to `F:/vault`.
- Do not change note generation routes.

## Design

Add a small tool:

```text
tools/experiment_review_round.py
```

The tool scans a formal experiment root and writes:

```text
reviews/<round-id>/
  review-manifest.json
  review-sheet.csv
  user-review.md
  decision-template.md
```

Inputs:

- `--experiment-root`: formal experiment directory under `F:/vbook/experiments`.
- `--round-id`: stable review id such as `round-002`.
- `--dataset-id`: dataset label recorded in outputs.

Route and lesson discovery:

- Read route outputs from `renders/<route>/<variant>/<lesson>/`.
- Prefer note-like files in this order:
  - `note.md`
  - `visual-evidence.md`
  - `enhancement.md`
  - otherwise the first Markdown file in the lesson directory.
- Read preflight summaries from `comparisons/*preflight*.json`.
- Mark a route as preflight `pass`, `fail`, or `not_applicable`.

Review sheet columns:

```text
lesson,route,variant,readable_note_candidate,preview_path,preflight_status,
semantic_coverage,visual_recovery,image_choice,image_placement,
error_handling,text_discipline,traceability,preview_safety,
user_preference,reviewer_notes
```

`readable_note_candidate` defaults to `yes` only for
`vtext_first_vault_enhance`. Other routes default to `no` unless a future
experiment intentionally promotes them.

## Safety

The tool writes only under `<experiment-root>/reviews/<round-id>`. It fails if
the resolved output directory is outside the experiment root.

## Testing

Add tests under:

```text
tests/test_tools/test_experiment_review_round.py
```

The tests use temporary experiment fixtures and verify:

- the four review files are generated;
- route and lesson outputs are discovered;
- preflight status is copied into the sheet and manifest;
- the generated user review groups candidates by lesson;
- unsafe output directories outside the experiment root are rejected.
