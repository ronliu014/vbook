# Repository Guidelines

## Project Structure & Module Organization

vBook automates video-course analysis into image-aware notes and a searchable knowledge base. The current repository is lightweight:

- `docs/` stores business planning, architecture, pipeline, data model, and roadmap notes. Start with `docs/README.md`.
- `sync/` is reserved for cross-environment Codex coordination through Git-backed file exchange.
- Future source should be grouped by pipeline stage, for example `src/video/`, `src/audio/`, `src/ocr/`, `src/fusion/`, and `src/export/`.
- Keep generated media, frames, transcripts, and model outputs out of source directories. Prefer ignored paths such as `data/`, `outputs/`, or `runs/`.

## Build, Test, and Development Commands

The project uses Python packaging via `pyproject.toml`. Keep commands reproducible from the repository root:

- `python -m unittest discover` to run the current test suite.
- `python -m vbook_client --version` to verify the CLI entry point.
- `python -m vbook_client check` to verify skeleton readiness.
- `python -m pip install -e ".[dev]"` to install editable development tooling.
- `ffmpeg -i lecture.mp4 -vf fps=1/3 frames/frame_%06d.jpg` as the baseline frame extraction pattern.

## Coding Style & Naming Conventions

Prefer stage-oriented module names matching the pipeline: frame extraction, audio transcription, OCR or visual understanding, timeline alignment, knowledge fusion, and export. Use English names for code, APIs, and paths unless a document is primarily Chinese. For Python, use 4-space indentation, `snake_case` functions and modules, `PascalCase` classes, and typed interfaces for shared data structures.

## Testing Guidelines

Add tests under `tests/` with filenames like `test_frame_extraction.py` or `test_timeline_alignment.py`. Favor small deterministic fixtures over large course videos. For media-heavy behavior, test metadata, timestamps, filtering decisions, and output schemas; keep bulky sample assets outside Git.

## Commit & Pull Request Guidelines

The repository uses `main` with remote `https://github.com/ronliu014/vbook.git`. Use short imperative commits such as `Add frame extraction prototype` or `Document sync protocol`. Pull requests should include purpose, changed stages, test results, and screenshots or sample Markdown output for visual or formatting changes.

## vtext Boundary & Agent Coordination

vBook may borrow design ideas from `vtext` (`https://github.com/ronliu014/vtext.git`), especially the already implemented video-to-audio-to-text-to-knowledge workflow, but it must not depend on or vendor vtext code. Treat the projects as aligned today but independently evolving.

Use `sync/` as the protocol directory for Windows and Linux Codex collaboration. Refer to the Windows-side Codex as `wcodex` and the Linux-side Codex as `lcodex` in sync messages, handoffs, and task files.

## vsync Cross-Project Coordination

vBook participates in `vsync/v1` as the integration hub for the v-series video-note processing cluster. Use vsync as the central mailbox for durable communication with `vtext` and `vision`; do not rely on chat history as the cross-project record.

Canonical protocol:

- `E:/projects/my_app/vsync/PROTOCOL.md`

Mailbox:

- inbox: `E:/projects/my_app/vsync/mailbox/inbox/vbook/README.md`
- outbox: `E:/projects/my_app/vsync/mailbox/outbox/vbook/README.md`
- messages: `E:/projects/my_app/vsync/mailbox/messages/`

When creating, replying to, querying, indexing, or auditing cross-project messages, use:

- `E:/projects/my_app/vsync/skills/cross-project-communication/SKILL.md`

Rules:

- Store canonical cross-project messages in `vsync/mailbox/messages/`.
- Index sent messages in `vsync/mailbox/outbox/vbook/README.md`.
- Check received messages in `vsync/mailbox/inbox/vbook/README.md`.
- Use `Protocol: vsync/v1` and `Mailbox-Path:` in new message envelopes.
- Do not write mailbox copies into `vtext` or `vision` repositories.
- Update vBook docs only when a mailbox message changes durable vBook-owned facts such as contracts, runbooks, operations, compatibility, defaults, latency, risk, or backlog.
- Keep videos, generated notes, extracted frames, large logs, and model artifacts out of vsync messages; link paths and summarize evidence instead.
