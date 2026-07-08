# vtext-first Vault Augmentation Design

> Current direction as of 2026-07-07.
>
> This supersedes the old append-style `vault-preview` workflow and the
> scene-rendered `vault-final-value-page` plan. The useful part retained from
> those documents is visual selection; the note body and structure must come
> from vtext.

## Goal

Define vBook's vault workflow as a vtext-first visual augmentation pipeline.

vtext remains the authoritative text processor. vBook reads vtext's corrected
and summarized Markdown note, keeps that structure intact, and writes a separate
vBook-enhanced note with selected screenshots and concise visual captions.

## Product Rule

The enhanced note should be:

```text
vtext high-quality text note + vBook visual insertions
```

It should not be:

```text
vBook-generated transcript note appended after vtext
```

This means vBook must not re-create headings, emphasis, summaries, or long
knowledge sections when vtext already produced a good note. vBook should add
visual evidence only where it improves the existing note.

## Vault Directory Layout

Use explicit stage directories under `F:\vault\20_Learning`:

```text
F:\vault\
  20_Learning\
    vtext\
      投资训练营\
        韩珂龙头班：基础篇\
          如何高效选股，构建自己的短线股票池.md

    vbook\
      投资训练营\
        韩珂龙头班：基础篇\
          如何高效选股，构建自己的短线股票池.md
          assets\
            如何高效选股，构建自己的短线股票池\
              frame_000001.jpg
              frame_000002.jpg
```

Rules:

- Directory stage names must be lowercase ASCII: use `vtext` and `vbook`.
  Do not create `vText`, `vBook`, or other casing variants.
- `20_Learning\vtext` contains vtext pure-text output.
- `20_Learning\vbook` contains vBook image-enhanced output.
- vBook input is the corresponding note under `vtext`.
- vBook output is the corresponding note under `vbook`.
- vBook may overwrite/regenerate files under `vbook` when explicitly requested.
- vBook must not modify files under `vtext`.
- The existing legacy path `20_Learning\投资训练营\...` should not be modified
  during this migration. It can be copied into `vtext` manually or by an
  explicit migration command later.

## Path Mapping

The vtext source:

```text
F:\vault\20_Learning\vtext\<course>\<series>\<lesson>.md
```

maps to the vBook output:

```text
F:\vault\20_Learning\vbook\<course>\<series>\<lesson>.md
```

Images for that lesson are copied to:

```text
F:\vault\20_Learning\vbook\<course>\<series>\assets\<lesson>\frame_000001.jpg
```

The Markdown image link should be relative from the vBook note:

```markdown
![构建股票池之前的准备](assets/如何高效选股，构建自己的短线股票池/frame_000001.jpg)
```

## Output Style

vBook should preserve the vtext Markdown body as much as possible:

- keep existing headings;
- keep existing lists;
- keep existing bold emphasis;
- keep paragraph order;
- do not create new transcript-derived headings;
- do not append raw transcript summaries;
- do not duplicate vtext's own explanation.

Visual insertions should be compact:

```markdown
![构建股票池之前的准备](assets/如何高效选股，构建自己的短线股票池/frame_000001.jpg)

> 图示补充：讲师在此页列出短线股票池的 8 个准入检查项，包括聚焦龙头、近期热点、频繁涨停、上升趋势、基本面、突破状态、低位低价、符合战法模式。
```

The caption should describe what the image contributes. It should not become a
second note.

## Insert Placement

For each selected visual scene, vBook should choose an insertion point in the
vtext note.

First implementation matching signals:

1. vtext heading text overlaps with visual topic, OCR, or vision description.
2. vtext paragraph/list text overlaps with visual OCR keywords.
3. lesson timeline places the visual scene near the transcript section that
   originally supported the vtext note, when such timing is available.

If confidence is low, vBook should not force an insertion into a random section.
Instead, place the image in a final section:

```markdown
## 图示补充待确认
```

This avoids damaging a high-quality vtext note.

## Visual Selection

The final-value-page work remains useful as the visual selector:

- group adjacent visual evidence into teaching scenes;
- prefer completed board/slide/chart states;
- exclude Qwen error placeholder frames as primary images;
- keep only a few high-value images per lesson unless the user requests dense
  illustration.

This selection is internal. The selected scene should not define the note's
heading structure; the vtext note does that.

## Metadata

The generated vBook note may include YAML front matter if the source note already
uses front matter. If adding front matter would disturb a note that does not
have it, store metadata in the preview/export manifest instead.

Manifest fields should include:

```json
{
  "schema_version": "1",
  "status": "preview",
  "text_source": "vtext",
  "source_note": "F:\\vault\\20_Learning\\vtext\\...",
  "output_note": "F:\\vault\\20_Learning\\vbook\\...",
  "assets_dir": "F:\\vault\\20_Learning\\vbook\\...\\assets\\...",
  "inserted_image_count": 4,
  "unmatched_image_count": 0
}
```

## Safety

The source `vtext` note is read-only for vBook.

For first implementation, prefer a preview command that writes to a requested
output directory or output note under `20_Learning\vbook`. Do not write to
`20_Learning\vtext`, and do not modify legacy notes under
`20_Learning\投资训练营`.

If vBook later supports a migration command, it must:

- copy files from legacy paths or generated vtext output into `vtext`;
- avoid overwriting existing `vtext` notes without explicit confirmation;
- report a dry-run plan before copying many files.

## Command Shape

Proposed command:

```powershell
python -m vbook_client vault-enhance `
  --vtext-note "F:\vault\20_Learning\vtext\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output-note "F:\vault\20_Learning\vbook\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md"
```

For preview-only workflow, the same logic may write under `outputs/` first:

```powershell
python -m vbook_client vault-enhance `
  --vtext-note "<vtext-note>" `
  --lesson-output "<lesson-output>" `
  --output-note "outputs\vbook-vault-preview\<course>\<series>\<lesson>.md"
```

## Testing Strategy

Add focused tests with small Markdown fixtures:

1. vBook preserves vtext headings, lists, and bold text.
2. vBook inserts an image block under the most relevant vtext heading.
3. vBook places uncertain images under `## 图示补充待确认`.
4. vBook copies image assets beside the output note and uses relative links.
5. vBook never writes to the vtext source path.
6. Manifest records source note, output note, assets directory, inserted count,
   and unmatched count.

## Acceptance Criteria

The first vtext-first implementation is acceptable when:

- input is a vtext Markdown note;
- output is a separate vBook Markdown note;
- the vtext note remains unchanged;
- the vBook note largely preserves vtext's original text;
- visual insertions are short and placed near relevant sections;
- generated assets live under the vBook output tree;
- tests pass with deterministic fixtures;
- a real `投资训练营` sample reads more like the vtext note plus helpful images
  than a second generated transcript summary.

## Future Work

1. Add a migration helper from legacy `20_Learning\投资训练营` into
   `20_Learning\vtext\投资训练营`.
2. Add optional LLM-assisted section matching for ambiguous visual scenes.
3. Add user-reviewed diff generation before writing directly under
   `F:\vault\20_Learning\vbook`.
4. Add batch processing for full course directories after single-note quality is
   accepted.
