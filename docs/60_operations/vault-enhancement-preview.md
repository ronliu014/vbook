# Deprecated: Vault Enhancement Preview

> Status: deprecated on 2026-07-07.
>
> This runbook describes the old preview workflow that appends a vBook-generated
> visual enhancement section after an existing note. It is useful only for
> historical reproduction of that preview package. It should not be used as the
> current workflow for vault-quality notes.
>
> The current direction is vtext-first: use vtext's Markdown note as the
> authoritative source text, preserve its headings/lists/emphasis, and have
> vBook insert selected screenshots plus short captions into a separate
> lowercase `vbook` output directory.
>
> Current design:
> [../80_superpowers/specs/2026-07-07-vtext-first-vault-augmentation-design.md](../80_superpowers/specs/2026-07-07-vtext-first-vault-augmentation-design.md).

## Purpose

This workflow creates a preview package that combines an existing vtext-created
vault note with vBook visual evidence. It does not modify `F:\vault`.

Use it before any controlled write-back design. The preview output is meant to
answer whether the image evidence, OCR, and visual explanations actually
increase the knowledge density of an existing note.

## Inputs

- Existing note:
  `F:\vault\20_Learning\投资训练营\<series>\<lesson>.md`
- vBook lesson output:
  `outputs/<run>/<lesson>/`
- Preview output:
  `outputs/vault-enhancement-preview/<series>/<lesson>/`

The vBook lesson output must already contain:

```text
manifest.json
vision/analysis.json
fusion/sections.json
frames/selected/
```

## Step 1: Produce vBook Lesson Output

Use the existing `build` command with a transcript and a vision backend. For a
real Qwen Vision Service run, use the `external-command` adapter described in
[qwen-vision-integration.md](./qwen-vision-integration.md).

The first investment-training fixture can use:

```text
video:
F:\downloads\allwin\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.mp4

existing vault note:
F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md
```

## Step 2: Write Preview Package

```powershell
python -m vbook_client vault-preview `
  --vault-note "F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\<run>\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output "outputs\vault-enhancement-preview\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池"
```

Expected command output:

```text
outputs\vault-enhancement-preview\...\manifest.json
```

## Expected Output

```text
enhancement.md
manifest.json
images/
```

`enhancement.md` contains the original note content followed by
`## vBook 图文增强预览`. Each evidence section may include:

- section title and summary;
- key points from fusion sections;
- copied image embeds;
- OCR text;
- visual description.

`manifest.json` records:

- source vault note path;
- source vBook lesson output path;
- preview output files;
- copied image count and relative image paths.

## Safety Rules

- Do not write to `F:\vault` in this workflow.
- Do not copy preview images into the vault assets directory yet.
- Review `enhancement.md` before designing any write-back command.
- Keep copied images inside the preview output directory.
- If the existing vault note is dirty in Git, leave it untouched.

## Verification

Run focused tests:

```powershell
python -m unittest tests.test_export.test_vault_preview tests.test_client.test_vault_preview_cli
```

Run full tests:

```powershell
python -m unittest discover
```

For a real fixture smoke:

- command exits `0`;
- preview manifest path is printed;
- `enhancement.md` contains the original note plus `## vBook 图文增强预览`;
- copied image files exist under `images/`;
- no files under `F:\vault` are modified.
