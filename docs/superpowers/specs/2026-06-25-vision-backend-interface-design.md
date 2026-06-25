# Vision Backend Interface Design

## Purpose

vBook can now run a real MP4 through frame extraction, frame selection, placeholder visual analysis, timeline alignment, fusion, and note export. The next step is to replace the single placeholder function with a small backend interface that keeps the MVP runnable without external services while allowing real or manually prepared visual analysis to enter the pipeline.

This design does not call OCR engines, multimodal APIs, or vtext code. vBook remains independent and only consumes normalized JSON when visual analysis is supplied externally.

## Current Behavior

`build` enables `analyze_vision_placeholder` by default. `vbook_vision.analysis.analyze_frames_placeholder()` creates one `VisualAnalysis` per selected frame and marks every record as `VisualType.OTHER`. The CLI has `--visual-analysis-path` for output, but it has no backend selector and cannot load precomputed visual analysis.

## Proposed Approach

Add a lightweight function-based backend dispatcher in `vbook_vision.analysis`:

```python
analyze_frames(
    frames: Sequence[FrameCandidate],
    backend: str = "placeholder",
    visual_analysis_input: Path | str | None = None,
) -> list[VisualAnalysis]
```

Supported first-version backends:

- `placeholder`: existing deterministic no-dependency behavior.
- `manual-json`: load normalized visual analysis from a JSON file and match records to the current frame set by `frame_id`.

Avoid abstract base classes for now. With only two simple backends, a function dispatcher is easier to test and keeps the public surface small. Future OCR or multimodal backends can be added behind the same entry point.

## Manual JSON Contract

`manual-json` accepts either an object with `analyses` or a direct list:

```json
{
  "backend": "manual-json",
  "analyses": [
    {
      "frame_id": "frame-000001",
      "visual_type": "slide",
      "image_path": "frames/selected/frame_000001.jpg",
      "ocr_text": "entry signal",
      "vision_description": "A slide describing short-term stock selection.",
      "structured_observations": {"topic": "stock selection"},
      "confidence": 0.9
    }
  ]
}
```

```json
[
  {
    "frame_id": "frame-000002",
    "visual_type": "kline_case",
    "vision_description": "A candlestick chart with a moving average support example."
  }
]
```

Required fields are `frame_id` and a valid `visual_type` when provided. Missing `visual_type` defaults to `other`. Missing `image_path` defaults to the matched frame path. Missing text and observation fields default to empty values.

## Validation Rules

`manual-json` should fail fast with a clear `ValueError` when:

- `visual_analysis_input` is not provided;
- the JSON root is neither an object with `analyses` nor a list;
- a record is not an object;
- `frame_id` is missing or duplicated;
- `frame_id` is not present in the current selected or candidate frame set;
- `visual_type` is not `slide`, `kline_case`, or `other`;
- `structured_observations` is present but not an object.

It may contain analysis for only part of the frame set. This supports incremental manual labeling and small real-video smoke tests.

## CLI Behavior

Add backend selection to shared pipeline arguments:

```powershell
--vision-backend placeholder
--vision-backend manual-json
--visual-analysis-input path\to\manual-vision.json
```

`build` keeps its current default: it runs visual analysis with `placeholder` unless another backend is selected. The low-level `manifest` command remains explicit: it performs visual analysis only when an analysis flag or backend request is provided.

Keep `--analyze-vision-placeholder` for compatibility, but internally treat it as `--vision-backend placeholder`.

Example:

```powershell
python -m vbook_client build `
  --video lesson.mp4 `
  --transcript text\lesson.srt `
  --output outputs\lesson `
  --vision-backend manual-json `
  --visual-analysis-input manual\lesson-vision.json
```

## Outputs and Manifest

Regardless of backend, vBook writes normalized output to `vision/analysis.json` through `write_visual_analysis()`. The JSON should keep:

```json
{
  "backend": "manual-json",
  "analysis_count": 1,
  "analyses": []
}
```

`manifest.json` continues to record `artifacts.vision.analysis_count`, `artifacts.vision.analysis_path`, `artifacts.vision.analyses`, and `stage_status.vision_analysis = done` when visual analysis runs.

## Testing Strategy

Tests should cover:

- the new dispatcher preserves existing placeholder behavior;
- `manual-json` loads object and list input formats;
- missing `image_path` is filled from the matched frame;
- partial frame coverage is allowed;
- invalid visual types, duplicated frame IDs, unknown frame IDs, and malformed roots fail clearly;
- CLI `build --vision-backend manual-json --visual-analysis-input ...` writes normalized analysis and carries it through manifest/fusion/note outputs;
- existing `--analyze-vision-placeholder` tests continue to pass.

## Future Extensions

Later backends can add real OCR and multimodal model calls:

- `ocr-json` for OCR-only external output;
- `external-command` for running a configured analyzer command;
- model-specific backends for local or hosted multimodal services.

Those backends should still return `VisualAnalysis[]` and avoid importing vtext packages.
