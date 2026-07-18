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

## Findings

- Batch orchestration works through `vbook_client production-batch-preview`.
- Generated previews stay under `F:/vbook/experiments`; no vault write occurred.
- vtext source notes remain read-only.
- Preflight confirms Markdown image links resolve and no Qwen error placeholders
  were inserted.
- The main blocker for larger 10-20 lesson batches is dataset availability:
  more vtext Markdown notes and matching 240s lesson-output directories are
  needed.

## Decision

- Status: continue.
- Next: either generate or locate additional matched lesson-output packages for
  the remaining `投资训练营` lessons, then rerun the same production-batch preview
  workflow with a larger input manifest.
