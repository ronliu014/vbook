# vtext-Compatible Batch Input Design

## Purpose

vBook must reuse transcript assets produced by the separate vtext project while remaining independent. The goal is to support a vtext-compatible input directory layout for real course testing and future batch processing, without importing, vendoring, or requiring vtext as a runtime dependency.

## Reference Layout

The current local sample set follows this shape:

```text
E:/projects/my_app/temp/
|-- 三分钟学会选短线个股.mp4
|-- 双均线完整操盘体系.mp4
|-- 如何判断个股阶段性高点和低点.mp4
+-- text/
    |-- 三分钟学会选短线个股.srt
    |-- 三分钟学会选短线个股.txt
    |-- 双均线完整操盘体系.srt
    +-- 如何判断个股阶段性高点和低点.srt
```

vtext batch mode also uses `<input_dir>/text/` and may write files such as `<stem>_raw.srt`, `<stem>_clean.txt`, and `<stem>_summary.md`. vBook should treat this as an external artifact convention, not as an internal dependency.

## Proposed CLI Flow

Single lesson import should work first:

```sh
python -m vbook_client build \
  --video E:/projects/my_app/temp/三分钟学会选短线个股.mp4 \
  --transcript E:/projects/my_app/temp/text/三分钟学会选短线个股.srt \
  --output outputs/三分钟学会选短线个股
```

Batch import should follow after SRT support and real frame extraction:

```sh
python -m vbook_client build-batch \
  --input E:/projects/my_app/temp \
  --output outputs/temp-batch
```

`build-batch` should discover media files, match transcripts, and run the existing per-lesson build pipeline for each item.

## Transcript Matching

For a media file at `<input>/<relative_parent>/<stem>.mp4`, vBook should search `<input>/text/<relative_parent>/` in this priority order:

1. `<stem>_raw.srt`
2. `<stem>.srt`
3. `<stem>_raw.vtt`
4. `<stem>.vtt`
5. `<stem>_raw.txt`
6. `<stem>.txt`

SRT and VTT preserve timing and should be preferred. Plain text is a fallback only; it should be imported as one untimed segment, excluded from high-quality timeline alignment, and recorded in the manifest as lower-quality alignment input.

## Batch Discovery Rules

Supported media extensions should initially match vtext's common set:

```text
.mp4 .mkv .avi .mov .wmv .flv .webm .mp3 .wav .m4a .aac .flac .ogg
```

The scanner must ignore generated or coordination directories, including `text/`, `outputs/`, `.git/`, `.pytest_cache/`, `.ruff_cache/`, and `sync/`. Discovery should preserve relative hierarchy so nested course folders map to nested transcript paths and stable output IDs.

## Output Layout

For batch output, each lesson gets its own vBook workspace:

```text
outputs/temp-batch/
|-- batch_manifest.json
|-- 三分钟学会选短线个股/
|   |-- note.md
|   |-- manifest.json
|   |-- frames/
|   |-- vision/
|   +-- fusion/
+-- 双均线完整操盘体系/
    |-- note.md
    +-- manifest.json
```

`batch_manifest.json` should record every discovered media file, matched transcript path, output directory, status, stage failure if any, and whether the transcript came from a vtext-compatible layout.

## Error Handling

Batch processing should be resilient. One missing transcript or failed lesson must not abort other lessons. Each failure should be written to `batch_manifest.json` with a short actionable reason:

```text
missing_transcript
unsupported_transcript_format
build_failed
```

Single-lesson `build` should still fail fast for invalid paths or unsupported transcript formats.

## Implementation Sequence

1. Add SRT transcript import to vBook's own transcript loader.
2. Add real video frame extraction so a real MP4 can run without a prebuilt `frames/candidates` directory.
3. Add vtext-compatible batch discovery and transcript matching.
4. Add `build-batch` as a thin orchestrator over the existing per-lesson build pipeline.

This order allows real MP4 testing before the full batch command exists.

## Independence Boundary

vBook may read vtext-style files and may optionally call a vtext executable in a future adapter, but it must not import `vtext_client`, `vtext_common`, or any other vtext package. If an external vtext command is ever invoked, the per-lesson manifest must record the command, input path, output path, and exit status.
