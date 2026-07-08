# Historical: 2026-07-07 Real vtext + Qwen Vault Preview

> Status: historical record; superseded for product direction on 2026-07-07.
>
> This log remains valuable for the real vtext + Qwen smoke run, the Qwen
> timeout finding, and adapter resilience evidence. Its old `vault-preview`
> output direction is no longer the target user workflow. New vault-note work
> should be based on the vtext-first design: vBook reads a vtext note, preserves
> its text structure, and inserts selected screenshots with short captions into
> a separate lowercase `vbook` output tree.
>
> Current design:
> [../80_superpowers/specs/2026-07-07-vtext-first-vault-augmentation-design.md](../80_superpowers/specs/2026-07-07-vtext-first-vault-augmentation-design.md).

## Context

This run connected the first real investment-course sample across:

- vtext `--bundle vbook`
- vBook `build`
- Qwen Vision Service through `tools/vision_qwen_adapter.py`
- vBook `vault-preview`

The source lesson was:

```text
F:\downloads\allwin\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.mp4
```

The existing vault note used for preview comparison was:

```text
F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md
```

No files were written to `F:\vault`; only preview outputs were generated under
`outputs/`.

## vtext Bundle

The vtext bundle completed successfully in the Anaconda `App` environment:

```powershell
conda run -n App python -m vtext_client `
  "F:\downloads\allwin\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.mp4" `
  --bundle vbook `
  --output "outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --format srt `
  --language zh `
  --server "http://192.168.0.122:8000"
```

Generated files:

```text
outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\manifest.json
outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\summary.md
outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\transcript.clean.txt
outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\transcript.raw.srt
outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\transcript.raw.txt
```

The manifest reported `status = done`, `duration_seconds = 1357.796`, and
`models.refine = qwen3.5:9b`.

## Qwen Long-Tail Finding

A 120-second frame interval build failed at `frame-000007`:

```text
Qwen service request timed out for frame-000007
```

The frame was a dense stock-chart / trading-software screen. A direct single
frame retry with a 360-second timeout also timed out. A 300-second interval run
later timed out at `frame-000004`.

Conclusion: real course frames can produce long-tail Qwen Vision latency, so
vBook needs resilient per-frame handling for course-length preview runs.

## Adapter Resilience

`tools/vision_qwen_adapter.py` now supports:

```text
--continue-on-error
```

When enabled, failed frames are converted to valid manual-json-compatible
placeholder records:

- `visual_type = other`
- `confidence = null`
- `structured_observations.qwen_service.status = error`
- `structured_observations.qwen_service.message = <adapter error>`

Strict mode remains unchanged when the flag is not provided.

Focused verification:

```text
python -m unittest tests.test_tools.test_vision_qwen_adapter
Ran 13 tests
OK
```

## Successful vBook Build

The first complete real transcript + Qwen build used a conservative 600-second
frame interval:

```powershell
D:\anaconda3\envs\App\python.exe -m vbook_client build `
  --video "F:\downloads\allwin\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.mp4" `
  --transcript "outputs\vtext-bundles\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\transcript.raw.srt" `
  --output "outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --course-title "投资训练营" `
  --lesson-title "如何高效选股，构建自己的短线股票池" `
  --frame-interval-seconds 600 `
  --min-selected-frame-interval-seconds 600 `
  --alignment-window-seconds 180 `
  --vision-backend external-command `
  --vision-command "D:\anaconda3\envs\App\python.exe tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120 --prompt-profile vbook_visual_analysis_v1 --continue-on-error"
```

Generated outputs:

```text
outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\manifest.json
outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\note.md
outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\vision\analysis.json
outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\fusion\sections.json
```

This run selected 4 frames. All 4 Qwen analyses succeeded with
`visual_type = slide` and `confidence = 0.95`.

## Vault Preview

The preview package was generated with:

```powershell
D:\anaconda3\envs\App\python.exe -m vbook_client vault-preview `
  --vault-note "F:\vault\20_Learning\投资训练营\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池.md" `
  --lesson-output "outputs\real-transcript-qwen-resilient-600s\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池" `
  --output "outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池"
```

Generated outputs:

```text
outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\enhancement.md
outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\manifest.json
outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\images\frame_000001.jpg
outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\images\frame_000002.jpg
outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\images\frame_000003.jpg
outputs\vault-enhancement-preview-real\韩珂龙头班：基础篇\如何高效选股，构建自己的短线股票池\images\frame_000004.jpg
```

## Quality Notes

What works:

- vtext real transcript can drive vBook.
- Qwen visual OCR and visual descriptions enter the generated note.
- vault-preview can preserve the original vtext note and append vBook image
  evidence without modifying the vault.
- `--continue-on-error` gives vBook a practical path through long-tail service
  failures.

Observed next quality issue:

- The current enhancement preview can repeat the same image across many nearby
  transcript sections. The next note-quality task should group nearby sections
  by shared visual evidence and render one image block per visual scene instead
  of repeating the image in every section.

## Recommended Next Steps

1. Improve vault enhancement rendering so repeated visual evidence is grouped
   and inserted once per scene.
2. Add a targeted reprocess path for failed Qwen frames recorded through
   `structured_observations.qwen_service.status = error`.
3. Run a denser frame interval after scene-level de-duplication is in place.
4. Only after preview quality is approved, add an explicit vault-write workflow.
