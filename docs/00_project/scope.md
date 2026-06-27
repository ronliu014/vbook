# Project Scope

## In Scope Now

- Local CLI pipeline.
- Timestamped transcript import from JSON and SRT.
- Frame extraction and frame selection.
- Normalized visual analysis artifacts.
- Timeline alignment.
- Fusion prompt and fusion section artifacts.
- Markdown note export.
- Manifest-based audit and reproducibility.

## Not In Scope Yet

- Production server runtime.
- Job queue or web progress UI.
- Built-in OCR service integration.
- Built-in multimodal model integration.
- Full knowledge-base storage and search service.
- Importing or vendoring vtext code.

## vtext Boundary

vBook can learn from vtext's workflow and documentation style, but vBook must
remain independently runnable. vBook may call external tools in the future, but
it must not depend on vtext packages or copy vtext implementation code.
