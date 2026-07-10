# Technical Experiment Protocol

This document defines how vBook records and compares technical attempts. Use it
before starting a new note-synthesis, visual-selection, model-adapter, or
pipeline-quality experiment.

## Goals

vBook is now comparing multiple ways to turn video lessons into image-aware
notes. Every attempt must be reproducible, comparable, and easy to review later.

The current question is:

- Can we preserve more course semantics by synthesizing notes from corrected
  timestamped text plus vBook visual evidence, instead of first summarizing with
  vtext and then inserting images?

## Experiment Record Requirements

Every experiment must record:

| Field | Requirement |
| --- | --- |
| Experiment id | Stable short id, for example `E20260710-semantic-visual-note` |
| Branch | Git branch used for code changes |
| Baseline tag | Stable source checkpoint, for example `v0.1.0` |
| Input root | User-provided input registry root, currently under `F:/vbook/inputs/<dataset-id>` |
| Output root | User-provided experiment output root, currently `F:/vbook/experiments` |
| Input data | Course, lesson, transcript source, visual interval, and lesson-output path |
| Workflow | Exact command sequence or script entry point |
| Model | Provider, model name, prompt/request version, timeout, and error policy |
| Output path | Project-local `outputs/...` preview path; do not write to vault during experiments |
| Evaluation | Developer checklist scores, user review scores, and reviewer notes |
| Decision | Continue, revise, compare, or abandon |

Write dated summaries under `docs/70_progress/`. Keep durable runbooks under
`docs/60_operations/`. Keep design decisions under `docs/20_architecture/` or
`docs/80_superpowers/specs/` when they become stable.

## Output Rules

- Formal experiments write to `F:/vbook/experiments/<experiment-id>/` first.
- Repository-local `outputs/experiments/<experiment-id>/` is allowed for short
  development smoke runs only.
- Do not overwrite `F:/vault/20_Learning/vtext` original notes.
- Do not write to `F:/vault/20_Learning/vbook` until a preview is accepted.
- Keep generated videos, frames, OCR dumps, model responses, and large logs out
  of Git.
- Store only small manifests, prompts, summaries, and evaluation notes in docs.

## Standard Workflow

1. Confirm branch and source checkpoint.
2. Record the input root and output root.
3. Select 2-3 representative real lessons from the registered test set.
4. Generate or reuse a stable `lesson-output` directory.
5. Generate preview artifacts under an experiment-specific output path.
6. Inspect Markdown and images locally.
7. Record evaluation against the standard rubric.
8. Summarize findings in a dated progress log before moving on.

## Evaluation Rubric

Use the same rubric across attempts so comparisons are not anecdotal.

| Dimension | Question |
| --- | --- |
| Semantic coverage | Does the note preserve definitions, conditions, exceptions, and reasoning from the full timeline? |
| Visual recovery | Does the workflow recover board/PPT/chart information missing from speech text? |
| Image choice | Are selected images completed, dense, high-value pages rather than cover, transition, or partial pages? |
| Placement | Are images placed next to the matching knowledge section? |
| Error handling | Are Qwen/service error placeholders skipped? |
| Text discipline | Does the output remain concise and evidence-grounded, without unsupported AI rewriting? |
| Traceability | Can each section point back to timestamps and image refs? |
| Preview safety | Are all outputs project-local previews with read-only source notes/transcripts? |
| User preference | Which candidate would the user actually want in the learning vault? |

Suggested scoring:

- `0`: missing or actively wrong.
- `1`: partially works but needs manual repair.
- `2`: acceptable for preview.
- `3`: strong candidate for vault publication.

User review is part of the evaluation, not an optional afterthought. A route
cannot be considered best unless the user has compared same-lesson outputs from
the strongest candidates.

## Route Labels

Use these route labels in manifests, docs, and output directories:

| Label | Meaning |
| --- | --- |
| `vtext_first_vault_enhance` | vtext summary is primary text; vBook inserts selected visuals. |
| `semantic_visual_note` | corrected timestamped text and visual evidence are primary model inputs; model synthesizes sections and chooses image refs. |
| `model_adapter_eval` | same request/evidence set compared across model providers. |

## Model Comparison Rules

Model tests may include Qwen VL, Claude, GLM, and OpenAI GPT-family APIs. Record:

- model provider and exact model name;
- whether the model receives image pixels, OCR/vision JSON only, or both;
- prompt/request file path;
- timeout and retry policy;
- structured error result;
- output contract validation result.

Never commit API keys, account identifiers, or raw credentials. Prefer local
environment variables and provider-neutral request/response JSON files.

## Step Summary Template

Use this short template after every experiment step:

```text
Experiment:
Branch:
Input root:
Output root:
Input lesson-output:
Command:
Output:
Result:
Evidence:
Issues:
Next:
```
