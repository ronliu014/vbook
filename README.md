# vBook

vBook is a project for automatic video-course analysis and knowledge organization. Its target pipeline is:

1. Extract and filter key video frames, especially PPT slides and practical case screenshots.
2. Convert audio to timestamped text.
3. Recognize visual content with OCR or multimodal models.
4. Align screenshots with transcript segments by timeline.
5. Fuse speech, slide text, and visual case descriptions into structured Markdown notes and a searchable knowledge base.

The original product intent is documented in [`docs/vBook需求意向.md`](docs/vBook需求意向.md). The planning index starts at [`docs/README.md`](docs/README.md).

## Project Status

This repository is in initial setup. The video-to-audio-to-text-to-knowledge workflow may reference design ideas from `vtext`, but vBook must remain an independent project and must not depend on or vendor vtext code.

## Repository Layout

- `docs/` - business plan, architecture, pipeline, module, data model, and roadmap documents.
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
  --output outputs/lesson \
  --frame-candidates-dir outputs/lesson/frames/candidates
```

Editable install for local command testing:

```sh
python -m pip install -e ".[dev]"
vbook check
```

The `build` command runs the current MVP pipeline using an imported timestamped transcript and an existing frame candidate directory. It writes:

- `manifest.json`
- `note.md`
- `vision/analysis.json`
- `fusion/prompt.json`
- `fusion/sections.json`

## Sync Roles

- `wcodex` - Windows-side Codex agent.
- `lcodex` - Linux-side Codex agent.

See [`sync/README.md`](sync/README.md) for the message protocol.
