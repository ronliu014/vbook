# 2026-07-10 Note Synthesis Experiment Plan

## Context

The vtext-first vault enhancement workflow has produced useful previews: vtext
summary text remains readable, and vBook can insert relevant high-value images.
However, the route has a structural limitation. Because vtext generates a
text-only summary before vBook inserts visuals, any semantic details lost during
the text-only summary stage may never be recovered.

The new hypothesis is that vBook should test a transcript-and-visual-first
workflow:

1. Start from corrected timestamped text.
2. Add visual evidence from vBook frames, OCR, and vision descriptions.
3. Ask a model to synthesize the note and choose useful image refs.
4. Render a project-local Markdown preview.

## Existing Stable Route

Route label: `vtext_first_vault_enhance`.

Current status:

- Stable checkpoint: `v0.1.0`, commit `78d6015`.
- Preview output root:
  `outputs/post-deploy-vault-enhance/240s/韩珂龙头班：基础篇`.
- Tested lessons:
  - `如何筛选龙头股？`
  - `龙头股的上涨逻辑是什么？`
  - `反抽 反弹 反转`

Findings:

- Images display from copied `assets/` paths.
- Insert placement is usually near the matching vtext section.
- Final/high-information visual pages are preferred.
- Structured Qwen error visuals are skipped.
- Text remains vtext-first and concise.

Risk:

- The main body inherits omissions from the upstream vtext summary.

## New Experimental Route

Route label: `semantic_visual_note`.

Branch:

- `codex-semantic-visual-note-test`

Implemented first slice:

- Added `vbook_export.semantic_visual_note`.
- Added CLI command `semantic-visual-note`.
- Added tests in `tests/test_export/test_semantic_visual_note.py`.

Command shape:

```text
D:/anaconda3/envs/App/python.exe -m vbook_client semantic-visual-note \
  --lesson-output "<lesson-output>" \
  --output "<preview-output>" \
  --transcript-source-label vtext_semantic_verified \
  --max-visuals-per-request 4
```

Smoke output:

```text
outputs/semantic-visual-note-test/240s/韩珂龙头班：基础篇/如何筛选龙头股？
```

Formal experiment workspace:

```text
Input root:  F:/vbook/inputs/investment-camp-hanke-basic-v1
Output root: F:/vbook/experiments
Experiment:  F:/vbook/experiments/E20260710-semantic-visual-note
Vault write: disabled
```

The smoke output predates the formal workspace convention. New request,
response, render, review, comparison, and decision artifacts should be written
under `F:/vbook/experiments/<experiment-id>/`.

Observed request metrics:

```text
status: request_ready
workflow: semantic_visual_note
transcript_source_label: vtext_semantic_verified
transcript_segment_count: 676
visual_evidence_count: 4
skipped_error_visual_count: 0
```

Interpretation:

- The first slice builds a provider-neutral request from timeline transcript
  segments and visual evidence.
- It does not depend on vtext's already-compressed Markdown summary.
- It does not call any model by default.
- It can render a preview Markdown note when supplied with either an external
  model command or an existing structured response JSON.

## Next Experiment Steps

1. Freeze the small evaluation set in `docs/60_operations/experiment-datasets.md`.
2. Generate request-only packages for all three baseline lessons.
3. Run one model backend against the same request payload.
4. Render preview notes and compare against vtext-first output.
5. Record rubric scores and examples.
6. Decide whether to improve prompt, evidence shape, model adapter, or renderer.

## Model Comparison Backlog

Status update on 2026-07-11:

- External OpenAI, Claude, and GLM API calls are paused pending administrator
  coordination for the AI distribution center.
- They should not block current route evaluation.
- Continue with existing local/reproducible capabilities first: Qwen visual
  evidence, vtext-first enhancement, and deterministic semantic+visual
  baselines.
- See
  [2026-07-11-existing-model-baseline-plan.md](./2026-07-11-existing-model-baseline-plan.md).

Candidate APIs:

- Qwen VL: existing visual baseline.
- Claude: long-context synthesis and Chinese note quality comparison.
- GLM: Chinese course-note synthesis comparison.
- OpenAI GPT: structured multimodal/text+vision evidence synthesis comparison.

Open design question:

- Should the model receive raw image pixels, structured OCR/vision JSON, or both?

Initial recommendation:

- Start with structured OCR/vision JSON for reproducibility and cost control.
- Add raw image inputs only for a focused model-adapter evaluation, using the
  same lesson-output and same scoring rubric.
