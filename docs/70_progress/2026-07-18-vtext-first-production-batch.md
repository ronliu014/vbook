# 2026-07-18 Vtext-First Production Batch Preview

## Scope

- Route: `vtext_first_vault_enhance`
- Mode: preview-only
- Dataset: `invest-training-production-batch-001`
- Input manifest: `F:/vbook/inputs/invest-training-production-batch-001/batch-input.json`
- Output root: `F:/vbook/experiments/E20260718-vtext-first-production-batch-preview`
- Vault write: disabled
- Source vtext policy: read-only

## Dataset

The user requested a 10-20 lesson production preview batch. Current local
`F:/vault/20_Learning/vtext/投资训练营` only has four source Markdown notes, and
three of them currently have matching 240s vBook lesson outputs with
`manifest.json`, `vision/analysis.json`, and `fusion/sections.json`.

This first production-batch smoke therefore ran the three matched lessons:

- `反抽 反弹 反转`
- `如何筛选龙头股？`
- `龙头股的上涨逻辑是什么？`

The remaining vtext source note, `如何高效选股，构建自己的短线股票池`, should be
added to a later batch after a matching 240s lesson-output package is available
or confirmed.

## Commands

```powershell
D:/anaconda3/envs/App/python.exe -m vbook_client production-batch-preview `
  --batch-input "F:/vbook/inputs/invest-training-production-batch-001/batch-input.json" `
  --output-root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --max-images-per-note 3 `
  --min-image-gap-seconds 240
```

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_preflight.py `
  --root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline" `
  --json-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.json" `
  --markdown-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.md"
```

## Results

- Batch status: `preview_ready`
- Lessons requested: 3
- Lessons done: 3
- Lessons failed: 0
- Lessons skipped: 0
- Preflight: `ok: true`
- Notes: 3
- Manifests: 3
- Markdown image links: 3
- Missing images: 0
- Errors: 0
- Warnings: 0

## Outputs

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/batch-preview-manifest.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/batch-preview-manifest.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline/
```

## Review Round

Formal user review package:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/reviews/round-001/review-manifest.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/reviews/round-001/review-sheet.csv
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/reviews/round-001/user-review.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/reviews/round-001/decision-template.md
```

Review manifest summary:

- Review round: `round-001`
- Candidate count: 3
- Candidate route: `vtext_first_vault_enhance`
- Candidate variant: `baseline`
- Readable note candidate: `yes`
- Preflight status: `pass`
- Review status: awaiting user scoring and decision

Preview notes to inspect:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline/反抽 反弹 反转/note.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline/如何筛选龙头股？/note.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline/龙头股的上涨逻辑是什么？/note.md
```

## Findings

- Batch orchestration works through `vbook_client production-batch-preview`.
- Generated previews stay under `F:/vbook/experiments`; no vault write occurred.
- vtext source notes remain read-only.
- Preflight confirms Markdown image links resolve and no Qwen error placeholders
  were inserted.
- Review package was generated successfully and gives the user a stable scoring
  entry point before any vault publication plan is created.
- The main blocker for larger 10-20 lesson batches is dataset availability:
  more vtext Markdown notes and matching 240s lesson-output directories are
  needed.

## Decision

- Status: continue.
- Next: user reviews `reviews/round-001/user-review.md` and the three preview
  notes. After explicit approval, create a publication plan; otherwise generate
  or locate additional matched lesson-output packages and rerun a larger batch.

## Follow-Up: 4-Lesson Expansion Preview

After the first 3-lesson review package, the remaining local vtext source note
was expanded into a comparable 240s lesson output:

```text
outputs/production-batch-expansion-qwen-240s/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池
```

Build input:

- Video: `F:/downloads/allwin/投资训练营/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池.mp4`
- Transcript: `outputs/vtext-bundles/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池/transcript.raw.srt`
- Frame interval: `240`
- Minimum selected frame interval: `240`
- Vision backend: `external-command`
- Qwen profile: `vbook_visual_analysis_v1`
- Qwen error mode: `--continue-on-error`

Generated 240s lesson-output facts:

- Selected frames: 10
- Visual analysis records: 10
- Manifest stage status: all build stages `done`, with `llm_fusion` skipped
- Notable visual record: `frame-000003` returned `visual_type = other`, empty
  OCR, and `vision_description = 模型返回格式错误`; it should not be treated as a
  high-value note image.
- Tooling note: the observed PTY command session reported exit code `1` after
  printing `manifest.json`, but the written manifest and downstream preflight
  confirmed usable artifacts.

The 4-lesson batch input is:

```text
F:/vbook/inputs/invest-training-production-batch-002/batch-input.json
```

The 4-lesson preview output is:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/batch-preview-manifest.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/comparisons/vtext-first-preflight.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/renders/vtext_first_vault_enhance/baseline/
```

4-lesson preview result:

- Batch status: `preview_ready`
- Lessons requested: 4
- Lessons done: 4
- Lessons failed: 0
- Lessons skipped: 0
- Preflight: `ok: true`
- Notes: 4
- Manifests: 4
- Markdown image links: 4
- Missing images: 0
- Errors: 0
- Warnings: 0

4-lesson review package:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/review-manifest.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/review-sheet.csv
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/user-review.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/decision-template.md
```

4-lesson review manifest summary:

- Review round: `round-001`
- Dataset: `invest-training-production-batch-002`
- Candidate count: 4
- Candidate route: `vtext_first_vault_enhance`
- Candidate variant: `baseline`
- Readable note candidate: `yes`
- Preflight status: `pass`
- Review status: awaiting user scoring and decision

Important review finding for the new fourth lesson:

- The generated enhanced note inserted one image:
  `assets/note/frame_000007.jpg`.
- The inserted image is not the Qwen malformed `frame_000003` record.
- The note remains vtext-first and readable.
- Because the lesson contains several visual topics, including stock-pool
  preparation, selection time, and stock-pool maintenance, the single inserted
  image should be reviewed for whether it is sufficient or whether this lesson
  needs multiple scene images in a later tuning pass.

## User Acceptance And Publication Prep

The user accepted the current notes on 2026-07-18:

```text
我认为目前的笔记可以
```

The 4-lesson review round was finalized as the production candidate:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/review-manifest.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/review-sheet.csv
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/user-review.md
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/reviews/round-001/decision-template.md
```

Review decision summary:

- Review status: `winner_selected`
- Selected route: `vtext_first_vault_enhance`
- Decision status: `candidate_for_production`
- User review summary: `User said the current notes are acceptable.`

The dry-run publication plan was generated:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/publication-plans/vtext_first_vault_enhance-production-batch-002/publication-plan.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/publication-plans/vtext_first_vault_enhance-production-batch-002/publication-plan.md
```

Publication plan summary:

- Plan id: `vtext_first_vault_enhance-production-batch-002`
- Dry run: `true`
- Vault write: `disabled`
- Target vault root:
  `F:/vault/20_Learning/vbook/投资训练营/韩珂龙头班：基础篇`
- Items: 4
- Assets: 4
- Markdown images: 4
- Missing images: 0

The read-only conflict report was generated:

```text
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/publication-plans/vtext_first_vault_enhance-production-batch-002/publication-conflicts.json
F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/publication-plans/vtext_first_vault_enhance-production-batch-002/publication-conflicts.md
```

Conflict summary:

- Status: `conflicts_detected`
- Existing target notes: 4
- Existing target assets: 3
- All 4 target notes exist and have different hashes from the current preview
  notes, so an apply without overwrite must remain blocked.
- Existing assets for `反抽 反弹 反转`, `如何筛选龙头股？`, and
  `龙头股的上涨逻辑是什么？` have the same hashes as the current preview assets.
- The new fourth lesson asset
  `assets/如何高效选股，构建自己的短线股票池/frame_000007.jpg` is missing in
  the target vault and would be copied on apply.

Required next gate before any vault write:

1. Confirm applying plan id `vtext_first_vault_enhance-production-batch-002`.
2. Because all target notes already exist and differ, apply must use
   `--overwrite --backup-existing`.
3. After apply, run `tools/vault_publication_postcheck.py` against
   `publication-result.json` and accept publication only when status is `pass`.
