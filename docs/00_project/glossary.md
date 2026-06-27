# vBook Glossary

This glossary defines the shared vocabulary used in vBook discussions, docs,
code reviews, and progress reports.

## Status Terms

### Functional foundation

A working deterministic implementation that is useful for pipeline integration
and regression testing, but may not yet represent final product intelligence.

### Placeholder

An intentional simple implementation that preserves data shape and pipeline
flow while postponing real semantic work. A placeholder is not a bug, but it
must be named clearly.

### Partial

A stage has more than placeholder behavior but is not complete. For example,
visual analysis now supports `manual-json`, but it does not yet call OCR or
multimodal models.

### Done

The stage ran and produced its expected output artifact during a pipeline run.
In `manifest.json`, this appears as a stage status such as `"done"`.

### Skipped

The stage was not requested or could not run because its prerequisites were not
provided. In `manifest.json`, this appears as `"skipped"`.

## Project Terms

### vBook

The project in this repository. vBook automates video-course analysis into
image-aware notes and a searchable knowledge base.

### vtext

A related reference project for video-to-audio-to-text-to-knowledge workflow
ideas. vBook may learn from vtext design but must not import, vendor, or depend
on vtext code.

### MVP

The minimum useful local pipeline: transcript import, frame extraction, frame
selection, visual analysis output, timeline alignment, fusion artifacts, note
export, and manifest export.

## Input Terms

### Video

The source lesson media file, usually an MP4. It is the source for extracted
frames and, in future stages, audio transcription.

### Transcript

Timestamped text for the lesson. Current supported input formats are JSON and
SRT. vBook normalizes transcripts into `TranscriptSegment[]`.

### TranscriptSegment

The normalized data object for one timestamped transcript segment. It records
start time, end time, text, source, and optional metadata.

## Vision Terms

### FrameCandidate

The normalized data object for one extracted or discovered frame. It records
frame id, video id, timestamp, image path, dimensions, and filter state.

### Candidate frame

A frame extracted from video or discovered from an existing frame directory
before final selection.

### Selected frame

A candidate frame kept for downstream stages such as vision analysis, timeline
alignment, fusion, and note export.

### Rejected frame

A candidate frame excluded by frame selection. Rejected frame records are still
useful for auditability.

### VisualAnalysis

The normalized data object for visual understanding output. It records frame id,
visual type, image path, OCR text, visual description, structured observations,
confidence, and backend name.

### VisualType

The category of a visual analysis record. Current values are `slide`,
`kline_case`, and `other`.

### Vision backend

The implementation that produces `VisualAnalysis[]` from frames. Current
backends are `placeholder` and `manual-json`.

### placeholder backend

The default no-service backend. It creates deterministic `VisualAnalysis`
records so the pipeline can run without OCR or model services.

### manual-json backend

A backend that loads externally prepared or manually written visual analysis
from JSON and normalizes it into `VisualAnalysis[]`.

## Pipeline Terms

### Timeline alignment

The stage that links frame timestamps to nearby transcript segments and returns
`TimelineLink[]`.

### Fusion prompt snapshot

A JSON artifact that records the transcript, visual analysis, and timeline
alignment context that would be used for later knowledge fusion.

### Fusion sections

Structured `KnowledgeSection[]` output. Current implementation is deterministic
placeholder construction, not final LLM summarization.

### KnowledgeSection

The normalized data object for one note section. It can include title, summary,
timestamps, image references, key points, and tags.

## Output Terms

### note.md

The human-readable Markdown note exported by vBook.

### manifest.json

The machine-readable run index. It records inputs, stage statuses, output paths,
and artifact summaries.

### vision/analysis.json

The normalized visual analysis artifact.

### fusion/prompt.json

The fusion prompt snapshot artifact.

### fusion/sections.json

The structured fusion sections artifact.
