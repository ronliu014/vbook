# vBook

vBook is a project for automatic video-course analysis and knowledge organization. Its target pipeline is:

1. Extract and filter key video frames, especially PPT slides and practical case screenshots.
2. Convert audio to timestamped text.
3. Recognize visual content with OCR or multimodal models.
4. Align screenshots with transcript segments by timeline.
5. Fuse speech, slide text, and visual case descriptions into structured Markdown notes and a searchable knowledge base.

Start documentation from [`docs/README.md`](docs/README.md). For a quick project
orientation, read [`docs/00_project/overview.md`](docs/00_project/overview.md),
[`docs/00_project/glossary.md`](docs/00_project/glossary.md), and
[`docs/00_project/status.md`](docs/00_project/status.md). The original product
intent remains available at [`docs/vBook需求意向.md`](docs/vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md).

## Project Status

vBook is in the local MVP pipeline stage. The current pipeline can run from a
video plus timestamped transcript into `manifest.json`, `note.md`,
`vision/analysis.json`, `fusion/prompt.json`, and `fusion/sections.json`.
Some stages are still placeholders or partial foundations. See
[`docs/00_project/status.md`](docs/00_project/status.md) for the current project
dashboard.

## Repository Layout

- `docs/` - numbered documentation layers; start at `docs/README.md`.
- `sync/` - Git-backed coordination directory for Windows and Linux Codex agents.
- `AGENTS.md` - contributor and agent guidelines.
- `vbook_common/` - shared data contracts, config, version, and serialization.
- `vbook_client/` - CLI entry point.
- `vbook_server/` - future server boundary, currently an empty placeholder.

## Development Commands

```sh
python -m unittest discover
python -m vbook_client --version
python -m vbook_client check
python -m vbook_client config --show
python -m vbook_client build \
  --video lesson.mp4 \
  --transcript transcript.json \
  --output outputs/lesson
```

Editable install for local command testing:

```sh
python -m pip install -e ".[dev]"
vbook check
```

The `build` command runs the current MVP pipeline using an imported timestamped transcript. `--transcript` accepts timestamped JSON or SRT files. By default, `build` extracts candidate frames from `--video` into `<output>/frames/candidates`; pass `--frame-candidates-dir` to reuse an existing candidate directory. It writes:

- `manifest.json`
- `note.md`
- `vision/analysis.json`
- `fusion/prompt.json`
- `fusion/sections.json`

## Sync Roles

- `wcodex` - Windows-side Codex agent.
- `lcodex` - Linux-side Codex agent.

See [`sync/README.md`](sync/README.md) for the message protocol.
