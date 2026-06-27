# Basic Frame Filtering Design

## Purpose

vBook can now extract frames from real MP4 files, but raw interval sampling produces repeated and low-value images. The next step is a small, dependency-light filtering layer that improves selected frame quality before placeholder vision analysis and note generation.

This design covers only the first filter pass. It does not add OCR, multimodal classification, perceptual hashing, OpenCV, Pillow, or domain-specific slide/K-line recognition.

## Current Behavior

`build` produces or discovers candidate frames, then the existing `select_frame_candidates()` keeps frames by minimum timestamp interval. It copies selected images into `<output>/frames/selected` when `--select-frames` is enabled. The default `build` path currently does not enable frame selection, so placeholder vision analysis usually receives every candidate frame.

## Proposed Approach

Make `build` select frames by default after extraction or discovery. The first filtering strategy should combine two deterministic rules:

1. **Minimum interval rule**: keep the first frame, then reject nearby frames whose timestamp gap is below `--min-selected-frame-interval-seconds`.
2. **Exact duplicate content rule**: reject a frame when its file hash matches an already selected frame.

Exact hash comparison is intentionally conservative. It catches identical exported frames without pretending to understand visual similarity. Later iterations can add perceptual hash, OCR density, blank-screen detection, and visual-type classification behind the same boundary.

## API Shape

Keep the public entry point in `vbook_vision.frames`:

```python
select_frame_candidates(
    candidates: list[FrameCandidate],
    selected_dir: Path | str,
    min_interval_seconds: float,
    copier: FrameCopier = shutil.copy2,
) -> tuple[list[FrameCandidate], list[FrameCandidate]]
```

Extend its behavior internally so it also tracks selected file hashes. No new public type is required for this first pass. Rejected frames should preserve their original `image_path`, set `filter_status=REJECTED`, and set one of these reasons:

```text
within_min_interval
duplicate_content
```

Selected frames should be copied to `frames/selected` and returned with `filter_status=SELECTED`.

## CLI Behavior

`build` should default to frame selection after candidate frames are available:

```text
extract/discover candidates
-> select frames into <output>/frames/selected
-> timeline alignment uses selected frames
-> placeholder vision analysis uses selected frames
-> note records selected and rejected counts
```

`manifest` should remain explicit: it only selects frames when `--select-frames` is passed.

The user can still tune:

```sh
--min-selected-frame-interval-seconds 10
--selected-frames-dir outputs/lesson/frames/selected
```

## Manifest and Outputs

The existing manifest frame artifact already supports:

```json
{
  "candidate_count": 10,
  "selected_count": 3,
  "rejected_count": 7,
  "selection_strategy": "min_interval"
}
```

For this stage, update `selection_strategy` to:

```text
basic_interval_duplicate
```

Rejected frame entries should include `filter_reason`, allowing later review of why a frame was not used.

## Testing Strategy

Unit tests should avoid real image processing. They can write small byte files and rely on exact file hashes:

- two files with identical bytes should result in one selected and one `duplicate_content` rejection when interval allows both;
- two files with different bytes but close timestamps should reject the later one as `within_min_interval`;
- `build` without `--select-frames` should still select frames by default and use selected frames for timeline, vision, fusion, and note generation;
- `manifest` without `--select-frames` should remain unchanged.

## Future Extensions

Future filter stages can add optional image-aware rules without changing the selected/rejected contract:

- perceptual hash for near-duplicate slides;
- blank or low-information frame detection;
- OCR text density scoring;
- slide and K-line case prioritization;
- manual keep/reject overrides.

Those should be separate designs because they introduce new dependencies or model behavior.
