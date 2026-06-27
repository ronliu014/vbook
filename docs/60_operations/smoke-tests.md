# Smoke Tests

This page lists small local checks for verifying that vBook pipeline boundaries
are wired correctly. Smoke tests are not quality benchmarks; they confirm that
commands run, expected artifacts are written, and contracts are readable.

## Placeholder Build Smoke

Use the default `build` path when you only need to verify the local MVP pipeline:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson
```

Expected artifacts:

- `outputs\lesson\manifest.json`
- `outputs\lesson\vision\analysis.json`
- `outputs\lesson\fusion\prompt.json`
- `outputs\lesson\fusion\sections.json`
- `outputs\lesson\note.md`

## Manual JSON Vision Smoke

Use `manual-json` when visual analysis has already been prepared by a person or
external process:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-manual `
  --vision-backend manual-json `
  --visual-analysis-input path\to\manual-vision.json
```

The manual JSON must contain an `analyses` list or be a list itself. Each record
must reference a `frame_id` selected or discovered in the current build.

## External Command Vision Smoke

Use `tools\vision_stub.py` to verify the `external-command` contract without
installing OCR, model runtimes, or API credentials:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-external `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

Expected external-command artifacts:

- `outputs\lesson-external\vision\external\frames.json`
- `outputs\lesson-external\vision\external\analysis.json`
- `outputs\lesson-external\vision\analysis.json`
- `outputs\lesson-external\manifest.json`

`tools\vision_stub.py` does not perform OCR or multimodal visual understanding.
It writes deterministic smoke analysis so the command contract, paths, JSON
validation, manifest stage status, and downstream fusion inputs can be checked.

## Direct Vision Stub Check

You can also run the tool directly against an existing frame input JSON:

```powershell
python tools\vision_stub.py `
  --input outputs\lesson-external\vision\external\frames.json `
  --output outputs\lesson-external\vision\external\analysis.json
```

The output is compatible with the `manual-json` visual analysis contract.
