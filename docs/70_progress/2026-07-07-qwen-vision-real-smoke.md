# 2026-07-07 Qwen Vision Real Smoke

## Summary

The first vBook-side real Qwen Vision adapter smoke passed against the service
at `http://192.168.0.33:8866`.

This validates the real service path from vBook:

- `GET /health`
- frame extraction
- frame selection
- `external-command` vision backend
- `tools/vision_qwen_adapter.py`
- `POST /analyze-frame`
- normalized `vision/analysis.json`
- `manifest.json`
- `note.md`

This does not validate final note quality because the transcript used for this
smoke was a temporary smoke-only transcript.

## Inputs

- Video: `E:\projects\my_app\temp\三分钟学会选短线个股.mp4`
- Duration: about `500` seconds
- Transcript: `outputs/qwen-vision-smoke/input_transcript.json`
- Output: `outputs/qwen-vision-smoke/lesson/`
- Endpoint: `http://192.168.0.33:8866/analyze-frame`
- Model observed in response: `qwen3-vl:8b`

## Command

```powershell
python -m vbook_client build `
  --video E:\projects\my_app\temp\三分钟学会选短线个股.mp4 `
  --transcript outputs\qwen-vision-smoke\input_transcript.json `
  --output outputs\qwen-vision-smoke\lesson `
  --course-title QwenVisionSmoke `
  --lesson-title 三分钟学会选短线个股 `
  --frame-interval-seconds 240 `
  --min-selected-frame-interval-seconds 240 `
  --alignment-window-seconds 180 `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120 --prompt-profile vbook_visual_analysis_v1"
```

## Results

- Build exit code: `0`
- Candidate frames: `2`
- Selected frames: `2`
- `manifest.json`: written
- `note.md`: written
- `vision/external/frames.json`: written
- `vision/external/analysis.json`: written
- `vision/analysis.json`: written
- `manifest.stage_status.vision_analysis`: `done`
- `vision.analysis_count`: `2`

## Visual Checks

Frame `frame-000001`:

- `visual_type`: `other`
- OCR: `这也是我们散户的优势`
- Description matched the talking-head scene with bookshelf background.
- Qwen latency: `23453 ms`
- Confidence: `0.9`

Frame `frame-000002`:

- `visual_type`: `slide`
- OCR extracted the slide content about putting stocks into a watchlist and
  checking the volume-ratio leaderboard.
- Description matched the slide about `量比排行榜`.
- Qwen latency: `17911 ms`
- Confidence: `0.95`

## Follow-Ups

1. Replace the smoke-only transcript with a real transcript for at least one
   sample lesson.
2. Define a reusable fixture policy for local or externally mounted MP4 plus
   transcript samples.
3. Run a broader Qwen Vision sample with more frames to evaluate latency and
   quality distribution.
4. Keep real LLM/Qwen text fusion as a separate integration track.
