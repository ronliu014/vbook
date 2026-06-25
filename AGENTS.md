# Repository Guidelines

## Project Structure & Module Organization

vBook automates video-course analysis into image-aware notes and a searchable knowledge base. The current repository is lightweight:

- `docs/` stores product intent and technical notes. Start with `docs/vBook需求意向.md`.
- `sync/` is reserved for cross-environment Codex coordination through Git-backed file exchange.
- Future source should be grouped by pipeline stage, for example `src/video/`, `src/audio/`, `src/ocr/`, `src/fusion/`, and `src/export/`.
- Keep generated media, frames, transcripts, and model outputs out of source directories. Prefer ignored paths such as `data/`, `outputs/`, or `runs/`.

## Build, Test, and Development Commands

No build system is committed yet. When adding tooling, document commands in `README.md` and keep them reproducible from the repository root. Expected commands include:

- `python -m pytest` to run Python tests.
- `python -m vbook ...` for local pipeline execution.
- `ffmpeg -i lecture.mp4 -vf fps=1/3 frames/frame_%06d.jpg` as the baseline frame extraction pattern.

## Coding Style & Naming Conventions

Prefer stage-oriented module names matching the pipeline: frame extraction, audio transcription, OCR or visual understanding, timeline alignment, knowledge fusion, and export. Use English names for code, APIs, and paths unless a document is primarily Chinese. For Python, use 4-space indentation, `snake_case` functions and modules, `PascalCase` classes, and typed interfaces for shared data structures.

## Testing Guidelines

Add tests under `tests/` with filenames like `test_frame_extraction.py` or `test_timeline_alignment.py`. Favor small deterministic fixtures over large course videos. For media-heavy behavior, test metadata, timestamps, filtering decisions, and output schemas; keep bulky sample assets outside Git.

## Commit & Pull Request Guidelines

The local directory is not yet initialized as a Git repository. The intended remote is `https://github.com/ronliu014/vbook.git`. Until stronger history exists, use short imperative commits such as `Add frame extraction prototype` or `Document sync protocol`. Pull requests should include purpose, changed stages, test results, and screenshots or sample Markdown output for visual or formatting changes.

## vtext Boundary & Agent Coordination

vBook may borrow design ideas from `vtext` (`https://github.com/ronliu014/vtext.git`), especially the already implemented video-to-audio-to-text-to-knowledge workflow, but it must not depend on or vendor vtext code. Treat the projects as aligned today but independently evolving.

Use `sync/` as the protocol directory for Windows and Linux Codex collaboration. Refer to the Windows-side Codex as `wcodex` and the Linux-side Codex as `lcodex` in sync messages, handoffs, and task files.
