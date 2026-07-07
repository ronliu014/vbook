# 2026-07-07 Vault Enhancement Preview

## Context

vBook is beginning the preview-first path for enriching vtext-created vault
notes with visual evidence. The workflow must not write back to `F:\vault`
during the first implementation pass.

## Work Done

- Added `vbook_export.vault_preview`.
- Added `python -m vbook_client vault-preview`.
- Added focused export and CLI tests.
- Added [../60_operations/vault-enhancement-preview.md](../60_operations/vault-enhancement-preview.md).
- Kept the workflow preview-only: it reads an existing vault note and vBook
  lesson output, then writes `enhancement.md`, copied `images/`, and
  `manifest.json` under a chosen preview output directory.
- Ran a real preview smoke against the existing `投资训练营` vault note and
  `outputs/qwen-vision-smoke/lesson`.

## Verification

Focused tests run during implementation:

```powershell
python -m unittest tests.test_export.test_vault_preview
python -m unittest tests.test_client.test_vault_preview_cli
```

Both focused commands passed before this log was written. Full-suite results
after implementation:

```powershell
python -m unittest discover
```

Result:

```text
Ran 133 tests
OK
```

Real preview smoke:

```powershell
python -m vbook_client vault-preview `
  --vault-note "F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\qwen-vision-smoke\lesson" `
  --output "outputs\vault-enhancement-preview\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池"
```

Result:

- `enhancement.md` written.
- `manifest.json` written.
- `images/frame_000001.jpg` and `images/frame_000002.jpg` copied.
- `F:\vault` Git status showed no new changes from this workflow; the existing
  unrelated deleted note and untracked `tools/` remained.
- The generated preview contains useful OCR and image evidence, but the lesson
  output used smoke-only transcript text, so final content quality still needs
  a real-transcript rerun.

## Next

1. Produce a real-transcript vBook lesson output for the investment-training
   fixture.
2. Run `vault-preview` again against the existing vault note.
3. Review `outputs/vault-enhancement-preview/.../enhancement.md` before any
   write-back design.
