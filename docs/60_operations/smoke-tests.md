# Smoke Tests

This page lists small local checks for verifying that vBook pipeline boundaries
are wired correctly. Smoke tests are not quality benchmarks; they confirm that
commands run, expected artifacts are written, and contracts are readable.

## Placeholder Build Smoke

Use the default `build` path when you only need to verify the local MVP pipeline:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson
```

Expected artifacts:

- `outputs\lesson\manifest.json`
- `outputs\lesson\vision\analysis.json`
- `outputs\lesson\fusion\prompt.json`
- `outputs\lesson\fusion\sections.json`
- `outputs\lesson\note.md`

## Manual JSON Vision Smoke

Use `manual-json` when visual analysis has already been prepared by a person or
external process:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-manual `
  --vision-backend manual-json `
  --visual-analysis-input path\to\manual-vision.json
```

The manual JSON must contain an `analyses` list or be a list itself. Each record
must reference a `frame_id` selected or discovered in the current build.

## External Command Vision Smoke

Use `tools\vision_stub.py` to verify the `external-command` contract without
installing OCR, model runtimes, or API credentials:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-external `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

Expected external-command artifacts:

- `outputs\lesson-external\vision\external\frames.json`
- `outputs\lesson-external\vision\external\analysis.json`
- `outputs\lesson-external\vision\analysis.json`
- `outputs\lesson-external\manifest.json`

`tools\vision_stub.py` does not perform OCR or multimodal visual understanding.
It writes deterministic smoke analysis so the command contract, paths, JSON
validation, manifest stage status, and downstream fusion inputs can be checked.

## Qwen Vision Adapter Smoke

Use `tools\vision_qwen_adapter.py` when a Qwen Vision Service compatible with
`docs/90_reference/qwen-vision-service-requirements.md` is running:

Current service-team reply:

- Reply document: `docs/90_reference/integration-response.md`
- Base URL: `http://192.168.0.33:8866`
- Analyze endpoint: `http://192.168.0.33:8866/analyze-frame`
- Health endpoint: `http://192.168.0.33:8866/health`
- Auth: none for the current trusted-LAN deployment
- Prompt profile: `vbook_visual_analysis_v1`
- Timeout: 120 seconds per frame
- Recommended concurrency: 1
- Current limitation: deployment performance baseline is still pending

Run health check after the service team confirms deployment and firewall access:

```powershell
Invoke-RestMethod -Method Get -Uri http://192.168.0.33:8866/health
```

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-qwen `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120"
```

The current service reply says no token is required. If a future deployment
enables token auth, either pass `--token` inside the command template or set:

```powershell
$env:VBOOK_QWEN_VISION_TOKEN = "your-token"
```

Expected adapter artifacts:

- `outputs\lesson-qwen\vision\external\frames.json`
- `outputs\lesson-qwen\vision\external\analysis.json`
- `outputs\lesson-qwen\vision\analysis.json`
- `outputs\lesson-qwen\manifest.json`

The adapter sends one request per selected frame to `POST /analyze-frame` and
writes manual-json-compatible analysis. vBook still records the normalized final
visual output as `backend = external-command`.

## Direct Vision Stub Check

You can also run the tool directly against an existing frame input JSON:

```powershell
python tools\vision_stub.py `
  --input outputs\lesson-external\vision\external\frames.json `
  --output outputs\lesson-external\vision\external\analysis.json
```

The output is compatible with the `manual-json` visual analysis contract.
