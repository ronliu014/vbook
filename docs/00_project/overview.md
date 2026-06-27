# vBook Overview

vBook turns video courses into image-aware notes and a searchable knowledge
base. The project is currently focused on a local MVP pipeline that can process
a lesson video plus timestamped transcript into reproducible Markdown and JSON
outputs.

## Core Value

Course videos often contain information that is not fully represented in audio
transcripts: slides, K-line chart cases, tables, screenshots, and annotations.
vBook preserves that visual context, aligns it with transcript segments, and
exports structured notes that can later enter a knowledge base.

## Current Execution Path

The current primary command is:

```powershell
python -m vbook_client build --video lesson.mp4 --transcript transcript.json --output outputs/lesson
```

`--transcript` accepts timestamped JSON or SRT files. The build command writes
`manifest.json`, `note.md`, `vision/analysis.json`, `fusion/prompt.json`, and
`fusion/sections.json`.

## Current Emphasis

The project is in the local MVP pipeline stage. The pipeline can run end to end,
but some stages are still deterministic foundations or placeholders rather than
final intelligent implementations.
