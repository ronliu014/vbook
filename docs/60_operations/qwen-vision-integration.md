# Qwen Vision Integration

This runbook is for the first vBook-side integration check after the Qwen
Vision Service team confirms that the service is deployed and reachable from
the vBook machine. Do not run the live network commands until that readiness is
confirmed.

This page complements [smoke-tests.md](./smoke-tests.md). The local smoke
runbook verifies deterministic no-service paths; this page covers the real
Qwen Vision Service path.

## 适用范围

This runbook verifies:

- `GET /health` is reachable after service deployment.
- `tools/vision_qwen_adapter.py` can receive vBook frame input.
- The adapter can read local frame images and send base64 requests to the service.
- The service response can be normalized into manual-json-compatible analysis.
- vBook `build` writes the expected vision artifacts.
- `manifest.json` records `vision_analysis` as `done`.
- At least one frame has `ocr_text` or `vision_description` related to the image.

This runbook does not verify:

- Final course-note quality.
- Real LLM fusion.
- Production performance.
- Multi-client throughput.
- Long-term service stability.

## 当前服务信息

Current service-team reply:

```text
Base URL:          http://192.168.0.33:8866
Analyze endpoint: http://192.168.0.33:8866/analyze-frame
Health endpoint:  http://192.168.0.33:8866/health
Auth required:    no
Prompt profile:   vbook_visual_analysis_v1
Timeout:          120 seconds per frame
Recommended concurrency: 1
Model:            qwen3-vl:8b
Known pending:    deployment performance baseline
```

If the service team changes endpoint, auth, model, timeout, or image limits,
use the latest service-team reply instead of the values above.

## Ready 前检查

Stop here if any item is not satisfied:

- The service team has explicitly confirmed deployment is complete.
- The vBook machine can access `192.168.0.33:8866`.
- Firewall rules allow inbound TCP `8866` on the service host.
- The service team expects `/health` to return HTTP `200`, or a readable HTTP
  `503` while the model is loading.
- The current trusted-LAN deployment requires no token.
- A local short video and timestamped transcript are available.
- The video contains at least one readable slide, chart, or course screen.

If these conditions are not satisfied, keep the blocker in
[../00_project/task-board.md](../00_project/task-board.md) and do not run the
live adapter command.

## 输入素材要求

Prepare:

```text
path\to\lesson.mp4
path\to\lesson.srt
```

The transcript may also be vBook timestamped JSON. Use a short clip for first
integration. The clip should contain at least one visible slide, PPT page,
chart, or course screen so the visual sanity check is meaningful.

Use a local output directory such as:

```text
outputs/qwen-vision-smoke/
```

Generated outputs should not be committed.

## Step 1: Health Check

Run only after the service team confirms deployment:

```powershell
Invoke-RestMethod -Method Get -Uri http://192.168.0.33:8866/health
```

Expected success checks:

- HTTP status is `200`.
- `status == "ok"`.
- `model_loaded == true`.
- `model.provider == "qwen"`.
- `model.name` is non-empty; current expected value is `qwen3-vl:8b`.

If `/health` returns HTTP `503`, record the response body and ask the service
team whether the model is still loading or the backend is unavailable. Do not
continue to the adapter build until the service is healthy.

## Step 2: vBook Build Through Qwen Adapter

Run only after the health check passes:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\qwen-vision-smoke `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120"
```

The `{input}` and `{output}` placeholders must remain in the command string.
vBook replaces them with the frame input JSON path and external analysis output
path.

The adapter default prompt profile is `vbook_visual_analysis_v1`. To make it
explicit:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\qwen-vision-smoke `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120 --prompt-profile vbook_visual_analysis_v1"
```

## Step 3: Artifact Checks

Expected artifacts:

```text
outputs/qwen-vision-smoke/vision/external/frames.json
outputs/qwen-vision-smoke/vision/external/analysis.json
outputs/qwen-vision-smoke/vision/analysis.json
outputs/qwen-vision-smoke/manifest.json
outputs/qwen-vision-smoke/note.md
```

Check:

- `vision/external/frames.json` exists.
- `vision/external/analysis.json` exists.
- `vision/analysis.json` exists.
- `manifest.json` exists.
- `note.md` exists.

## Step 4: Manifest Checks

Open `outputs/qwen-vision-smoke/manifest.json` and check:

- `stage_status.vision_analysis == "done"`.
- `artifacts.vision.analysis_count > 0`.
- `artifacts.vision.analyses` contains at least one analysis record.

If the build exits with code `0` but these checks fail, keep the output
directory and inspect `manifest.json` plus `vision/external/analysis.json`
before rerunning.

## Step 5: Visual Content Checks

Open `outputs/qwen-vision-smoke/vision/analysis.json` and check:

- Each analysis has `frame_id`.
- `visual_type` is `slide`, `kline_case`, or `other`.
- `ocr_text` is a string.
- `vision_description` is a string.
- `structured_observations` is an object.
- `confidence` is a number from `0.0` to `1.0`, or `null`.
- At least one frame has `ocr_text` or `vision_description` related to the
  image content.

This is a smoke-level human sanity check, not a final model-quality score. If
the adapter succeeds but the visual content is clearly unrelated to the image,
record the frame image, `vision/external/analysis.json`, `vision/analysis.json`,
and prompt profile, then send them to the service team.

## Token and Auth

The current service-team reply says auth is not required for the trusted-LAN
deployment.

If token auth is enabled later, prefer an environment variable:

```powershell
$env:VBOOK_QWEN_VISION_TOKEN = "<token>"
```

The adapter also accepts an explicit command argument:

```powershell
--token "<token>"
```

Prefer the environment variable so tokens are not written into docs or shell
history.

## Timeout and Performance Notes

- Current recommended per-frame timeout is `120` seconds.
- First request may be slower if it triggers model loading.
- Deployment performance baseline is still pending from the service team.
- The first adapter version requests frames serially.
- Timeout does not automatically mean a vBook bug; it may indicate model
  warmup, GPU contention, service-side timeout, or network issues.

## Common Failures

### `Invoke-RestMethod` cannot connect

Check network route, service host, port `8866`, and firewall allowlist. Ask the
service team to confirm the process is listening.

### `/health` returns HTTP `503`

The service is reachable but not ready. Record the response body and ask the
service team whether the model is still loading or the backend is unavailable.

### `external-command backend requires vision_command`

The build command used `--vision-backend external-command` without
`--vision-command`. Add the adapter command string.

### `llm-fusion-command requires {input} and {output} placeholders`

This error belongs to LLM fusion, not Qwen vision. Check whether the wrong
command option was edited. Qwen vision uses `--vision-command`, and that command
must include `{input}` and `{output}`.

### Qwen service returned HTTP `400 invalid_request`

Keep `vision/external/frames.json` and the adapter stderr. Check whether the
image path exists, the image suffix is `.jpg`, `.jpeg`, or `.png`, and the
service still supports `vbook_visual_analysis_v1`.

### Qwen service returned HTTP `503 service_unavailable`

The adapter reached the service, but the model backend was unavailable. Send the
frame id and service error message to the service team.

### Qwen service request timed out

Record the frame id, timeout value, and whether this was the first request after
startup. Ask the service team for warmup and latency status. Consider increasing
`--timeout-seconds` only after service-side status is understood.

### Qwen service returned invalid JSON

The adapter requires strict JSON. Save the raw response if available and send it
to the service team with the frame id.

### Response frame id mismatch

The service response `frame_id` must echo the request `frame_id`. Send the raw
response and request frame id to the service team.

### Invalid visual type

`visual_type` must be one of `slide`, `kline_case`, or `other`. Any other value
is a service contract issue.

### Invalid confidence

`confidence` must be a number between `0.0` and `1.0`, or `null`. Boolean,
string, `NaN`, and infinity-like values are invalid.

### Build succeeds but visual content is poor

This is a model or prompt quality issue, not an adapter contract failure. Send
the frame image, raw response, normalized analysis, and prompt profile to the
service team.

## 不覆盖的内容

This runbook does not cover:

- Local deterministic smoke; see [smoke-tests.md](./smoke-tests.md).
- Final OCR quality scoring.
- Final LLM fusion.
- Batch Qwen performance.
- Production monitoring.
- Long-term benchmarks.

## Completion Criteria

The first Qwen Vision integration smoke passes only when:

- Ready checks are satisfied.
- `/health` returns HTTP `200` with `model_loaded == true`.
- The vBook build command exits with code `0`.
- All expected artifacts exist.
- `manifest.json` has `stage_status.vision_analysis == "done"`.
- `vision/analysis.json` contains at least one frame whose `ocr_text` or
  `vision_description` is related to the image.
- There is no unexplained schema mismatch.

## Related Documents

- [smoke-tests.md](./smoke-tests.md)
- [../90_reference/qwen-vision-service-requirements.md](../90_reference/qwen-vision-service-requirements.md)
- [../90_reference/qwen-vision-service-integration-request.md](../90_reference/qwen-vision-service-integration-request.md)
- [../90_reference/integration-response.md](../90_reference/integration-response.md)
- [../../tools/vision_qwen_adapter.py](../../tools/vision_qwen_adapter.py)
