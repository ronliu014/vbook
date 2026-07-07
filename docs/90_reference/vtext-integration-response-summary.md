# vtext Integration Response Summary

Status: received from vtext  
Date: 2026-07-07  
Source: `E:\projects\my_app\vtext\docs\90_reference\vbook-text-integration-response.md`

## Summary

vtext accepted the vBook integration boundary: vBook should call vtext through
documented CLI/API/artifact contracts, not by importing or vendoring vtext
source code.

The vtext side now documents and exposes a minimal vBook-compatible bundle mode:

```powershell
python -m vtext_client "<video-path>" --bundle vbook --output "<lesson-output-dir>" --format srt --language zh
```

## Bundle Layout

The vBook bundle mode is single-video only for the first implementation pass.
It writes:

```text
<lesson-output-dir>/
|-- transcript.raw.srt
|-- transcript.raw.txt
|-- transcript.clean.txt
|-- summary.md
+-- manifest.json
```

`transcript.clean.txt` and `summary.md` are produced when refine succeeds.
Refine failure is non-fatal: raw transcript artifacts remain available and
`manifest.json` records a `refine` error.

## Manifest

vtext provides `manifest.json` with schema version `1`, including:

- `project: "vtext"`;
- `source_video`;
- inferred `course`, `series`, and `lesson_title`;
- `language`;
- `status`;
- `outputs`;
- `timings`;
- `models`;
- `errors`.

For transcription failure, vtext intends to write a failed manifest when the
output directory can be created.

## Batch Position

Batch-level vBook bundle manifest is not part of the first minimal vtext
implementation. vBook may call vtext once per lesson using `--bundle vbook` and
read each lesson manifest.

## Open Questions

vtext asked vBook to decide:

- whether vBook should pass `course`, `series`, and `lesson_title` explicitly or
  rely on path inference for the first fixture;
- whether one call per lesson is acceptable before batch-level manifest support;
- whether refine failure should mean `done` with a warning or `partial`.

## Current vBook Assumption

For the first integration pass:

- path inference is acceptable;
- one call per lesson is acceptable;
- refine failure should be treated as `done` with a `refine` error when raw
  transcript artifacts are usable.
