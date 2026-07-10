# Experiment Datasets

This document defines the current local test data used to compare vBook note
synthesis workflows.

## Canonical Local Paths

| Purpose | Path |
| --- | --- |
| vBook repo | `E:/projects/my_app/vbook` |
| Experiment workspace root | `F:/vbook` |
| Experiment input registries | `F:/vbook/inputs` |
| Formal experiment outputs | `F:/vbook/experiments` |
| Video source root | `F:/downloads/allwin/投资训练营` |
| vtext original notes | `F:/vault/20_Learning/vtext/投资训练营` |
| vBook development preview outputs | `E:/projects/my_app/vbook/outputs` |
| vBook vault target | `F:/vault/20_Learning/vbook` |

Rules:

- Treat vtext original notes as read-only.
- Write formal experiment previews under `F:/vbook/experiments`.
- Use repository-local `outputs/` for development smoke runs only.
- Do not write to the vBook vault target until a preview has been reviewed.

## Current Evaluation Set

The current small real-course set is from `韩珂龙头班：基础篇`.

| Lesson | vtext note | 240s lesson-output | Existing preview route |
| --- | --- | --- | --- |
| `如何筛选龙头股？` | `F:/vault/20_Learning/vtext/投资训练营/韩珂龙头班：基础篇/如何筛选龙头股？.md` | `outputs/interval-sweep-qwen/240s/韩珂龙头班：基础篇/如何筛选龙头股？` | `outputs/post-deploy-vault-enhance/240s/韩珂龙头班：基础篇/如何筛选龙头股？.md` |
| `龙头股的上涨逻辑是什么？` | `F:/vault/20_Learning/vtext/投资训练营/韩珂龙头班：基础篇/龙头股的上涨逻辑是什么？.md` | `outputs/interval-sweep-qwen/240s/韩珂龙头班：基础篇/龙头股的上涨逻辑是什么？` | `outputs/post-deploy-vault-enhance/240s/韩珂龙头班：基础篇/龙头股的上涨逻辑是什么？.md` |
| `反抽 反弹 反转` | `F:/vault/20_Learning/vtext/投资训练营/韩珂龙头班：基础篇/反抽 反弹 反转.md` | `outputs/post-deploy-controlled-qwen/240s/韩珂龙头班：基础篇/反抽 反弹 反转` | `outputs/post-deploy-vault-enhance/240s/韩珂龙头班：基础篇/反抽 反弹 反转.md` |

## Baseline A: vtext-first Visual Enhancement

Route label: `vtext_first_vault_enhance`.

Intent:

- preserve vtext summary as the main note body;
- select high-value vBook visuals;
- insert copied assets into a preview Markdown note.

Strengths observed:

- preserves the vtext writing style;
- adds useful visual anchors;
- avoids writing to source vault notes;
- skips structured Qwen error visuals.

Known limitation:

- vtext summary is already compressed before images are added, so information
  lost during text-only summarization cannot be recovered reliably.

Representative output:

- `outputs/post-deploy-vault-enhance/240s/韩珂龙头班：基础篇`

## Baseline B: Semantic + Visual Note Synthesis

Route label: `semantic_visual_note`.

Intent:

- use corrected timestamped transcript as the primary semantic source;
- use vBook visual OCR, visual descriptions, and linked timestamps as visual
  evidence;
- ask the model to synthesize sections and choose image refs in one pass;
- render a project-local preview note.

Current branch:

- `codex-semantic-visual-note-test`

Current request-only smoke output:

- `outputs/semantic-visual-note-test/240s/韩珂龙头班：基础篇/如何筛选龙头股？`

Observed request metrics for `如何筛选龙头股？`:

- transcript segments: `676`
- visual evidence records: `4`
- skipped structured Qwen errors: `0`
- status: `request_ready`

The first smoke run only writes the provider-neutral request. It does not call a
model and does not write a final note unless `--llm-fusion-command` or
`--llm-response` is provided.

## Model Candidates

Candidate model families:

| Provider | Possible role |
| --- | --- |
| Qwen VL | Local or service-side visual understanding baseline. |
| Claude Code / Claude API | Long-context transcript reasoning and note synthesis. |
| GLM API | Chinese finance-course synthesis comparison. |
| OpenAI GPT API | Structured multimodal or text+vision evidence synthesis comparison. |

Comparison policy:

- Use the same request payload when possible.
- Record whether a model consumed raw image pixels, OCR/vision JSON, or both.
- Validate responses against the same sections contract before rendering notes.
- Keep provider credentials outside the repository.

## Review Checklist

For every generated preview:

- Open Markdown preview and confirm images display.
- Confirm selected images are useful completed pages.
- Confirm section text is grounded in transcript and visual evidence.
- Confirm unsupported financial claims are not invented.
- Confirm timestamps and image refs are present.
- Confirm output is concise enough for a learning vault note.
