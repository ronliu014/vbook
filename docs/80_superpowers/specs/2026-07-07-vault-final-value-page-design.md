# Deprecated: Vault Final Value Page Design

> Status: deprecated on 2026-07-07.
>
> This design captured a useful intermediate idea: selecting the final,
> information-rich frame from a continuous teaching scene. However, its output
> direction is no longer the product direction because it still renders a
> vBook-generated enhancement section after the source note. The current
> direction is vtext-first augmentation: preserve vtext's corrected note as the
> authoritative text and insert only selected images with short captions.
>
> Use this document only as historical context for visual-scene selection.
> For new work, follow
> [2026-07-07-vtext-first-vault-augmentation-design.md](./2026-07-07-vtext-first-vault-augmentation-design.md).

## Goal

Upgrade `vault-preview` from section-by-section image insertion to scene-level
knowledge rendering for online-course notes.

The key product rule is: when a lecturer explains the same board, slide, chart,
or trading-software view over several adjacent transcript sections, vBook should
prefer the final integrated information page rather than repeating process
frames. The output should capture the completed knowledge state of the teaching
block.

## Background

The first real vtext + Qwen + vault-preview run showed that the current preview
mechanism works mechanically:

- it preserves the existing vtext vault note;
- it appends vBook visual enhancement content;
- it copies referenced images into the preview package;
- Qwen OCR and visual descriptions enter the note.

The quality issue is that the same image can be repeated across many nearby
knowledge sections. A simple image de-duplication pass would reduce repetition,
but it would miss the teaching pattern of online courses: visual content often
evolves while the lecturer annotates, scrolls, opens examples, or completes a
board explanation.

## Non-Goals

This design does not:

- write directly to `F:\vault`;
- modify the source vault note in place;
- change the vtext bundle contract;
- change the Qwen Vision Service contract;
- require an LLM for the first implementation;
- solve dense-frame reprocessing or Qwen retry scheduling;
- replace the existing deterministic fusion pipeline.

## Recommended Approach

Use a deterministic scene-level renderer in `vault-preview`, but treat the
source vault as read-only. vBook should first create a staged vault working copy
and apply visual augmentation to files in that copy.

The renderer consumes existing `fusion/sections.json` and `vision/analysis.json`
and produces a smaller set of enhancement scenes. Each scene represents one
continuous teaching block with shared or related visual evidence. The rendered
Markdown displays one primary image for the scene: the final-value frame.

This keeps the first implementation scoped to export quality and avoids
destabilizing the main build pipeline.

## Vault Workcopy Safety

The source vault must remain read-only during preview and automated enrichment.

For course-note enhancement, vBook should use this flow:

```text
F:\vault                       # source vault, read-only
  -> outputs\vault-workcopy\... # staged copy managed by vBook
  -> enhancement preview        # modify only copied files and copied assets
```

The workcopy may be a copy of a single note, a lesson directory, a course
directory, or eventually a full vault mirror. The first implementation should
copy only the target note and generated image assets needed for the preview.
This keeps previews fast and avoids surprising large copies.

Direct writes to `F:\vault` are out of scope for this design. A future
vault-write command must require explicit user confirmation and should operate
from a reviewed workcopy diff, not from raw generated artifacts.

## Data Model

Introduce internal preview-only structures:

```text
PreviewScene
  title: str
  start_timestamp: float | None
  end_timestamp: float | None
  sections: list[dict]
  image_refs: list[str]
  primary_image_ref: str | None
  supporting_image_refs: list[str]
  key_points: list[str]
  summary: str
```

These structures do not need to be serialized in vBook build outputs. They can
be represented as dataclasses or private dictionaries inside
`vbook_export/vault_preview.py`.

## Scene Grouping Rules

`vault-preview` should group adjacent sections into the same scene when at
least one condition is true:

1. They share the same image reference.
2. Their first visual analysis has the same `structured_observations.topic`.
3. Their titles are equal after whitespace normalization.
4. The next section begins within a conservative time gap, such as 180 seconds,
   and both sections have overlapping visual text or visual descriptions.

The first implementation should prioritize rules 1 and 2 because they are
deterministic and directly address the repeated-image issue seen in the real
sample. Rule 4 can be added conservatively if tests show it is needed.

## Final-Value Frame Selection

For each scene, choose `primary_image_ref` with these rules:

1. Exclude visual analyses whose
   `structured_observations.qwen_service.status == "error"` unless all scene
   images failed.
2. Prefer the latest frame in the scene by timestamp or by frame id order.
3. Prefer frames with non-empty OCR text over frames without OCR.
4. Prefer frames with longer OCR text when timestamps are tied.
5. Fall back to the last image reference in the scene.

The intent is to capture the completed board, slide, or chart state. This is
different from simple de-duplication, which might keep the first frame and lose
later annotations.

## Supporting Frames

Most scenes should render only the primary final-value frame.

Supporting frames may be retained only when they carry distinct teaching value,
for example:

- two different case-study charts are compared in the same scene;
- an early frame shows an explicit wrong example and a later frame shows the
  corrected example;
- OCR text differs substantially and both frames contain non-overlapping
  checklist or formula content.

The first implementation may keep this simple: render only the primary image
and list omitted image count in the scene metadata or manifest. Supporting-frame
selection can be a later quality pass.

## Markdown Rendering

The rendered enhancement section should look like:

```markdown
## vBook 图文增强预览

> 当前文件是预览，不会写回 vault。

### 构建股票池之前的准备

![frame-000001](images/frame_000001.jpg)

**完成态画面**

- OCR：...
- 画面理解：...

**知识要点**

- ...
- ...
```

Rendering rules:

- Preserve the original vault note as the authoritative text.
- Do not rewrite vtext headings, summaries, emphasis, or paragraph structure.
- Insert visual blocks into the staged copy near matching vtext sections.
- Render one scene heading per teaching block.
- Render the primary image before the scene's knowledge points.
- Avoid repeating the same primary image in adjacent scenes.
- Merge repeated key points while preserving order.
- Keep OCR and visual description close to the image they explain.
- Do not add visible instructional text about how to use vBook.

## Manifest Additions

The preview manifest should remain backward compatible and add scene metrics:

```json
{
  "scene_count": 3,
  "image_count": 4,
  "rendered_primary_image_count": 3,
  "omitted_repeated_image_count": 12,
  "source_vault_note": "F:\\vault\\...",
  "workcopy_note": "outputs\\vault-workcopy\\..."
}
```

Existing fields such as `schema_version`, `status`, `vault_note`,
`lesson_output_dir`, `outputs`, and `images` should remain.

## Error Handling

If a scene contains only failed visual analyses, render the section without an
image and include the transcript-derived knowledge points. Do not fail the
preview package.

If an image reference cannot be copied, keep the preview command strict for now:
raise a clear error. Missing local files usually indicate a broken build output
or a manual artifact move.

## Testing Strategy

Add focused unit tests under `tests/test_export/test_vault_preview.py`:

1. Adjacent sections with the same image render that image once.
2. Adjacent sections with the same visual topic form one scene.
3. When multiple frames belong to one scene, the latest frame is rendered as the
   primary image.
4. Failed Qwen placeholder analyses are not selected as primary when a successful
   later frame exists.
5. The preview manifest records scene-level metrics.
6. Existing preview packaging behavior still copies referenced images and does
   not modify the vault note.

Use small JSON fixtures, not real videos.

## Acceptance Criteria

The feature is complete when:

- `vault-preview` treats the source vault as read-only.
- generated or modified Markdown is written to a staged workcopy, not directly
  to `F:\vault`;
- `vault-preview` groups repeated visual evidence into scene-level blocks.
- A scene renders the final-value frame rather than the first repeated frame.
- Real sample preview output no longer repeats the same image across many
  adjacent sections.
- Existing full test suite passes.
- Documentation records that vBook targets completed knowledge pages for
  online-course visual enhancement.

## Future Work

After this deterministic pass is stable:

1. Add optional LLM-assisted scene summarization.
2. Add targeted reprocessing for failed dense frames.
3. Add supporting-frame selection for explicit before/after teaching sequences.
4. Add a reviewed vault-write command once preview quality is accepted.
