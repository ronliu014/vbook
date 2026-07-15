# 2026-07-11 Existing-Model Baseline Plan

## Context

External OpenAI, Claude, and GLM API calls are paused. The AI hub configuration
needs administrator coordination, and model availability is not stable enough
to put external model calls on the current critical path.

The experiment continues with existing, locally reproducible capabilities:

- Qwen Vision Service results already generated in vBook lesson-output
  directories;
- vtext semantic-verified timestamped text and vtext summary notes;
- vBook deterministic visual selection, vault enhancement, request generation,
  and Markdown rendering;
- project-local experiment workspace under `F:/vbook`.

No experiment in this stage should require uploading course transcript,
visual-evidence payloads, source videos, or images to an external model API.

## Current Available Baselines

### Baseline A: `vtext_first_vault_enhance`

Status: stable baseline.

Inputs:

- vtext summary Markdown;
- vBook 240s Qwen visual analysis;
- vBook visual selection and Markdown asset-copying logic.

Strength:

- produces readable notes now;
- preserves vtext note style;
- inserts useful visual anchors;
- already skips structured Qwen error placeholders.

Known limitation:

- semantic omissions in the upstream text-only vtext summary cannot be reliably
  recovered after the fact.

### Baseline B: `qwen_visual_evidence_240s`

Status: available visual evidence baseline.

Inputs:

- selected 240s frames;
- Qwen OCR, visual descriptions, structured observations;
- timeline links between frames and transcript windows.

Strength:

- identifies board, slide, chart, and page content not present in text-only
  summaries;
- provides concrete image candidates and timestamps.

Known limitation:

- Qwen Vision is not the final note writer in the current architecture; it is
  evidence, not synthesis.

### Baseline C: `semantic_visual_request_only`

Status: formal request packages generated.

Inputs:

- timestamped transcript segments;
- Qwen visual evidence;
- vBook output contract.

Current experiment root:

```text
F:/vbook/experiments/E20260710-semantic-visual-note
```

Generated request packages:

- `反抽 反弹 反转`
- `龙头股的上涨逻辑是什么？`
- `如何筛选龙头股？`

Strength:

- proves that vBook can assemble the richer semantic+visual input without using
  the compressed vtext summary as the source body.

Known limitation:

- without an external or local note-synthesis model, this route currently stops
  at request generation or requires a manually supplied response JSON.

## New Short-Term Experiment Direction

Use existing capabilities to create comparable outputs before external model
adapters are available.

### Route 1: Formalize the vtext-first baseline in `F:/vbook`

Goal:

- copy or regenerate the current `vtext_first_vault_enhance` previews into the
  formal experiment structure, so later comparisons are same-root and
  same-rubric.

Output target:

```text
F:/vbook/experiments/E20260711-existing-model-baselines/
  renders/vtext_first_vault_enhance/baseline/<lesson>/
  reviews/
  comparisons/
  decision.md
```

Review focus:

- Markdown image paths display;
- image placement is close to matching vtext section;
- Qwen error placeholders are skipped;
- text remains vtext-first and concise.

### Route 2: Build a Qwen visual-evidence inspection pack

Goal:

- make Qwen visual evidence easy to review directly, independent of final note
  synthesis.

Output:

- one Markdown or JSON review page per lesson;
- each selected image;
- timestamp;
- OCR text;
- visual description;
- linked transcript window ids;
- whether it is a completed/high-information page.

Why this matters:

- if Qwen visual evidence is weak, no downstream note synthesis route can be
  trusted;
- if evidence is strong, the remaining problem is fusion/synthesis rather than
  visual understanding.

### Route 3: Add a deterministic `semantic_visual_rule_baseline`

Goal:

- generate a non-LLM comparison note from timestamped transcript plus Qwen
  visual evidence.

Proposed behavior:

- group transcript windows around selected visual frames;
- preserve mostly original transcript wording or lightly normalized excerpts;
- place each image next to the nearest transcript evidence window;
- produce short section titles from visual topic/OCR when available;
- never invent summary content beyond provided transcript and visual evidence.

This route will not be as polished as an LLM-written note, but it gives a
strictly local reference for whether transcript+visual-first preserves more
semantic material than the current vtext-first route.

## Evaluation Dataset

Use the current three-lesson dataset:

```text
F:/vbook/inputs/investment-camp-hanke-basic-v1/dataset.json
```

Lessons:

- `如何筛选龙头股？`
- `龙头股的上涨逻辑是什么？`
- `反抽 反弹 反转`

Do not add more lessons until the first comparison table is complete.

## Comparison Matrix

Compare same lesson across routes:

| Route | Uses vtext summary | Uses full timestamped text | Uses Qwen visual evidence | Requires external API |
| --- | --- | --- | --- | --- |
| `vtext_first_vault_enhance` | yes | no | yes | no |
| `qwen_visual_evidence_240s` | no | linked windows only | yes | no |
| `semantic_visual_rule_baseline` | no | yes | yes | no |
| `semantic_visual_note_openai/claude/glm` | no | yes | yes | paused |

## Scoring

Use the existing experiment rubric:

- semantic coverage;
- visual recovery;
- image choice;
- image placement;
- error handling;
- text discipline;
- traceability;
- preview safety;
- user preference.

For this stage, mark external model routes as `paused`, not `failed`.

## Next Implementation Steps

1. Create `F:/vbook/experiments/E20260711-existing-model-baselines`.
2. Register the same three-lesson dataset under that experiment.
3. Populate or regenerate formal vtext-first preview artifacts.
4. Generate Qwen visual-evidence inspection packs.
5. Design and implement `semantic_visual_rule_baseline` as a deterministic
   local route.
6. Compare all available local routes before reopening external model adapters.

## Implementation Status

Status on 2026-07-11:

- Created `F:/vbook/experiments/E20260711-existing-model-baselines`.
- Registered the three-lesson dataset under `inputs/dataset.json`.
- Copied the existing `vtext_first_vault_enhance` previews into the formal
  experiment layout and copied per-lesson assets so Markdown image links resolve.
- Added `tools/qwen_visual_evidence_pack.py` to generate Qwen evidence
  inspection Markdown with copied assets.
- Added `tools/semantic_visual_rule_baseline.py` to generate a deterministic
  transcript+visual-first local baseline without external APIs.
- Generated all three local routes for all three registered lessons.
- Checked Markdown image links across rendered outputs: `25` links, `0`
  missing.

Formal output root:

```text
F:/vbook/experiments/E20260711-existing-model-baselines
```

Key route outputs:

```text
renders/vtext_first_vault_enhance/baseline/<lesson>/note.md
renders/qwen_visual_evidence_240s/baseline/<lesson>/visual-evidence.md
renders/semantic_visual_rule_baseline/baseline/<lesson>/note.md
```

## User Review Update

Status on 2026-07-15:

- User reviewed the generated local baseline outputs.
- User concluded that `vtext_first_vault_enhance` gives the best document
  effect among the currently available routes.
- User clarified that compared with pure vtext text-only notes,
  `vtext_first_vault_enhance` is much better in information richness and
  perceived accuracy.
- User clarified that `qwen_visual_evidence_240s` and
  `semantic_visual_rule_baseline` do not read like usable notes.
- The formal experiment decision was updated:

```text
F:/vbook/experiments/E20260711-existing-model-baselines/decision.md
```

Current preferred route:

```text
vtext_first_vault_enhance
```

Implications:

- Treat `vtext_first_vault_enhance` as the current winning baseline for
  near-term hardening and potential preview publication.
- Treat `vtext_first_vault_enhance` as the only current readable-note candidate.
- Keep `qwen_visual_evidence_240s` as a visual evidence/debugging route, not as
  a readable note candidate.
- Keep `semantic_visual_rule_baseline` as a deterministic engineering control,
  not as a user-facing note candidate.
- Keep external OpenAI, Claude, and GLM model routes paused until the AI
  distribution center is ready.

## Decision Rule

Do not wait for OpenAI, Claude, or GLM to become available before improving the
core vBook pipeline. External models should later be tested as provider
candidates, not as blockers for evaluating:

- whether 240s Qwen visual evidence is enough;
- whether image placement is stable;
- whether transcript+visual-first preserves more semantics;
- whether the resulting notes are useful enough for user review.
