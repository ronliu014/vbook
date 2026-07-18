# Production Batch Workflow

This runbook is the controlled production workflow for the accepted
`vtext_first_vault_enhance` route.

## Status

- Route: `vtext_first_vault_enhance`
- Stage: production candidate
- Preview output root: `F:/vbook/experiments`
- Vault target root: `F:/vault/20_Learning/vbook`
- Source vtext root: `F:/vault/20_Learning/vtext`
- Source vtext policy: read-only

## Safety Rules

- Do not write generated previews directly to `F:/vault`.
- Do not modify `F:/vault/20_Learning/vtext`.
- Do not publish without a reviewed `publication-plan.json`.
- Do not overwrite existing `vbook` vault files without `--backup-existing`.
- Treat `vtext_first_preflight` and `vault_publication_postcheck` failures as
  publication blockers.

## Phase 1: Batch Input

Create an explicit batch input JSON. Keep it outside the repository under
`F:/vbook/inputs`:

```json
{
  "schema_version": "1",
  "kind": "vtext_first_batch_input",
  "dataset_id": "invest-training-small-batch-001",
  "lessons": [
    {
      "lesson": "如何筛选龙头股？",
      "vtext_note": "F:/vault/20_Learning/vtext/投资训练营/韩珂龙头班：基础篇/如何筛选龙头股？.md",
      "lesson_output": "F:/vbook/experiments/E20260711-existing-model-baselines/lesson-outputs/如何筛选龙头股？"
    }
  ]
}
```

Each lesson must point to:

- one vtext Markdown source note;
- one existing vBook lesson output directory with `manifest.json`,
  `vision/analysis.json`, and `fusion/sections.json`.

## Phase 2: Preview Batch

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_batch_preview.py `
  --batch-input "F:/vbook/inputs/invest-training-small-batch-001/batch-input.json" `
  --output-root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --max-images-per-note 3 `
  --min-image-gap-seconds 180
```

Expected outputs:

```text
F:/vbook/experiments/<experiment-id>/batch-preview-manifest.json
F:/vbook/experiments/<experiment-id>/batch-preview-manifest.md
F:/vbook/experiments/<experiment-id>/renders/vtext_first_vault_enhance/baseline/<lesson>/note.md
F:/vbook/experiments/<experiment-id>/renders/vtext_first_vault_enhance/baseline/<lesson>/note.manifest.json
```

## Phase 3: Preflight

```powershell
D:/anaconda3/envs/App/python.exe tools/vtext_first_preflight.py `
  --root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/renders/vtext_first_vault_enhance/baseline" `
  --json-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.json" `
  --markdown-output "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/comparisons/vtext-first-preflight.md"
```

Expected gate:

```text
ok: true
missing_image_count: 0
error_count: 0
```

## Phase 4: Human Review

Create or update a review round before publication. The user must inspect:

- whether images display in Markdown preview;
- whether image placement is close to the related vtext section;
- whether the screenshot is a final high-value teaching page;
- whether Qwen error placeholders are absent;
- whether vtext remains the main body and is not replaced by long AI rewrite.

## Phase 5: Publication Plan

Only after preflight and review pass:

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_plan.py `
  --experiment-root "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview" `
  --route vtext_first_vault_enhance `
  --variant baseline `
  --target-vault-root "F:/vault/20_Learning/vbook/投资训练营/韩珂龙头班：基础篇" `
  --plan-id "vtext_first_vault_enhance-production-batch-001"
```

## Phase 6: Conflict Report

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_publish.py `
  --plan "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/publication-plans/vtext_first_vault_enhance-production-batch-001/publication-plan.json" `
  --conflict-report
```

Review `publication-conflicts.json` and `publication-conflicts.md` before
asking for approval to publish.

## Phase 7: Apply With Backup

Only run this phase after explicit user approval for the exact plan id.

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_publish.py `
  --plan "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/publication-plans/vtext_first_vault_enhance-production-batch-001/publication-plan.json" `
  --apply `
  --confirm-plan-id vtext_first_vault_enhance-production-batch-001 `
  --overwrite `
  --backup-existing
```

The publish tool writes:

```text
publication-result.json
publication-result.md
publication-backups/<timestamp>/publication-backup.json
publication-backups/<timestamp>/publication-backup.md
```

## Phase 8: Postcheck

```powershell
D:/anaconda3/envs/App/python.exe tools/vault_publication_postcheck.py `
  --publication-result "F:/vbook/experiments/E20260718-vtext-first-production-batch-preview/publication-plans/vtext_first_vault_enhance-production-batch-001/publication-result.json"
```

Expected gate:

```text
status: pass
hash_mismatch_count: 0
missing_markdown_image_count: 0
```

Publication is accepted only when the postcheck status is `pass`.

## Phase 9: Progress Record

Write a dated progress note under `docs/70_progress/` with:

- dataset id;
- lesson count;
- preview manifest path;
- preflight path and status;
- review outcome;
- publication plan id;
- conflict summary;
- backup path;
- postcheck status;
- decision and next batch.
