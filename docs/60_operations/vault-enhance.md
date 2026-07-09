# Vault Enhance

## Purpose

`vault-enhance` is the current vtext-first workflow for vault-quality notes.

It reads a vtext Markdown note, preserves the note's existing headings, lists,
emphasis, and paragraph order, then writes a separate vBook Markdown note with
selected screenshots and compact visual captions.

This replaces the deprecated append-style `vault-preview` workflow for normal
note production.

## Directory Rule

Use lowercase stage directories under `F:\vault\20_Learning`:

```text
F:\vault\20_Learning\vtext\...
F:\vault\20_Learning\vbook\...
```

Rules:

- `vtext` contains pure text notes.
- `vbook` contains image-enhanced notes and copied image assets.
- vBook reads `vtext` notes as source input.
- vBook must not modify `vtext` notes.
- Do not use `vBook`, `vText`, or other casing variants as directory names.

## Command

```powershell
& "D:\anaconda3\envs\App\python.exe" -m vbook_client vault-enhance `
  --vtext-note "F:\vault\20_Learning\vtext\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output-note "F:\vault\20_Learning\vbook\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --max-images-per-note 3 `
  --min-image-gap-seconds 180
```

By default the manifest is written beside the output note:

```text
<lesson>.manifest.json
```

Use `--manifest-output` to place it somewhere else.

## Image Budget Options

Use the image budget options when converting real Qwen outputs into vault notes:

- `--max-images-per-note N` caps the total images inserted into one Markdown
  note.
- `--min-image-gap-seconds N` prevents nearby screenshots from crowding the
  same teaching block. When multiple scenes fall inside the gap, vBook prefers
  the completed, information-rich teaching page; timestamp is only the fallback
  when visual value is otherwise similar.

The current Qwen smoke results make `240s` a stable visual baseline candidate
for the tested `投资训练营` lesson. `120s` now fails cleanly as structured
`HTTP 504 timeout` instead of client timeouts, but it is too dense for the
current prompt/service budget on K-line-heavy content. Do not use `90s`, `60s`,
or `30s` full-course sweeps as defaults until selection and retry policy are
improved.

## Expected Output

For this output note:

```text
F:\vault\20_Learning\vbook\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md
```

vBook copies images to:

```text
F:\vault\20_Learning\vbook\投资训练营\韩珂龙头班：基础篇\assets\如何高效选股，构建自己的短线股票池\frame_000001.jpg
```

and inserts relative Markdown links:

```markdown
![构建股票池之前的准备](assets/如何高效选股，构建自己的短线股票池/frame_000001.jpg)

> 图示补充：讲师在此页展示股票池筛选条件的完成态页面。
```

## Matching Behavior

The first implementation uses deterministic matching:

- prefer vtext headings that overlap with the scene title, visual topic, OCR, or
  visual description;
- insert matched images near the existing vtext heading;
- place low-confidence images under `## 图示补充待确认`.

The visual scene selector keeps the useful part of the old final-value-page
work: adjacent course frames are grouped and the completed, information-rich
frame is preferred as the primary image, even when a lower-value transition
frame appears slightly later.

Images with structured Qwen service errors are skipped before insertion. This
keeps `HTTP 504 timeout` placeholders out of vault notes while still recording
the selection counts in the generated manifest.

## Safety

`vault-enhance` never writes back to the `--vtext-note` path.

For first review runs, point `--output-note` at an `outputs\...` preview path.
After the generated note is accepted, write to the lowercase `vbook` vault tree.
