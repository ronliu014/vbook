# vision -> vbook: qwen timeout investigation

Status: response
Date: 2026-07-08
Protocol: vsync/v1
From: vision
To: vbook
Owner: vision
Action Required: yes
In-Reply-To: vbook-vision-qwen-timeout-investigation-request.md
Related:

- vbook-vision-qwen-timeout-investigation-request.md
- vbook-vision-qwen-timeout-investigation-response.md
- ../70_progress/2026-07-08-qwen-timeout-investigation.md
- E:/projects/my_app/vsync/PROTOCOL.md

Supersedes:

- vbook-vision-qwen-timeout-investigation-response.md

## Context

vBook reported repeated Qwen timeout placeholders during interval sweeps for:

```text
投资训练营 / 韩珂龙头班：基础篇 / 反抽 反弹 反转
```

The request asked vision to classify whether the failures came from service
timeout behavior, model inference, input-frame complexity, queueing/resource
pressure, or another known failure mode.

This document is the `vsync/v1` delivery of vision's answer. The earlier
legacy response remains in place for traceability, but new cross-project
references should prefer this file.

## Response

The current evidence points to a timeout-budget mismatch amplified by slow
Qwen/Ollama inference on dense financial-chart frames.

This is not an HTTP contract or schema incompatibility. The `GET /health` and
`POST /analyze-frame` contract remains compatible with the current vBook
adapter. The observed placeholder records were written by the vBook adapter
after its own per-frame HTTP request timeout, not after receiving a structured
vision error response.

Root-cause classification:

- Primary: model/input latency. Dense K-line and trading UI frames can take
  tens of seconds and sometimes approach the 120s client limit.
- Primary: service/client timeout-budget mismatch. The service uses 120s per
  Ollama attempt and currently allows 3 attempts, so the service-side wall-clock
  budget can exceed the vBook client's 120s timeout.
- Secondary: possible backend pressure after client disconnect. vBook sends
  sequential requests, so vBook-side concurrency is not the likely first cause;
  however, if the client times out while FastAPI/Ollama continues processing,
  later dense-interval runs can still feel queued or slowed by leftover work.
- Not indicated by current evidence: invalid request schema, unsupported prompt
  profile, response-schema validation failure, or image-size rejection.

## Evidence

Vision-side local logs under `vision/logs/` do not contain the July 8
production interval-sweep requests. `app.log` only contains older validation
and smoke entries up to July 6, and `error.log` / `performance.log` are empty.
Because of that, vision cannot truthfully provide production request IDs, exact
service-side HTTP statuses, or final Ollama attempt logs for the timeout frames
from local logs alone.

What vision could verify from repository state and vBook artifacts:

- Production config currently sets `ollama.timeout: 120` and
  `ollama.max_retries: 3` in `config/config.prod.yaml`.
- `OllamaClient.analyze_image()` creates an `httpx.AsyncClient` with
  `timeout=self.timeout` for each attempt and retries timeout/request failures
  up to `max_retries`.
- `POST /analyze-frame` maps the service `TimeoutError` to HTTP `504` with
  `error.code == "timeout"`, but that only happens after retries are exhausted.
- vBook artifacts show placeholder records with
  `structured_observations.qwen_service.status == "error"` and messages like
  `Qwen service request timed out for frame-000003`.
- Successful frames in the same interval sweep show Qwen latencies ranging from
  about 8.7s to 99.7s:
  - `180s`: observed successful model latencies include 8.7s, 10.1s, 15.4s,
    and 23.8s.
  - `120s`: observed successful model latencies include 8.8s, 10.8s, 24.5s,
    and 68.3s.
  - `90s`: observed successful model latencies include 15.4s, 38.1s, and
    99.7s.
- The selected JPEG files are modest in byte size, about 99KB to 280KB, so this
  does not look like the service's 10MB image limit or gross file-size pressure.
- The successful visual classifications and OCR show dense K-line/trading UI
  screenshots with many small labels, chart elements, indicators, side panels,
  disclaimers, and overlaid lecture text. Those inputs are plausible slow paths
  for a vision-language model.

## Impact

vBook should treat the current timeout placeholders as client-observed request
timeouts. They should not be interpreted as proof that vision returned a
structured `504 timeout` response.

Expected service-generated error, if the service exhausts its own timeout
retries before the client gives up:

```json
{
  "error": {
    "code": "timeout",
    "message": "Model call timeout after 120s",
    "retryable": true
  },
  "request_id": "..."
}
```

The HTTP status for that service-generated error is `504`.

The current service-side per-attempt timeout is equal to vBook's client timeout
of 120s. The end-to-end service budget is greater because up to 3 attempts are
configured. In practice, vision may not return its own structured `504` until
after the vBook client has already timed out.

## Required Actions

Recommended vision/service actions:

1. Make the service fail within the vBook client budget. Prefer a service-side
   model-call timeout below the adapter timeout, for example 90s service
   timeout with a 120s vBook client timeout, or keep 120s per attempt but set
   `max_retries: 1` for this endpoint.
2. Add attempt-level logging for Ollama calls, including attempt number, max
   attempts, per-attempt latency, total elapsed latency, timeout phase, image
   dimensions, decoded bytes, MIME type, Ollama HTTP status or exception type,
   `request_id`, and `frame_id`.
3. Consider cancellation/disconnect handling so abandoned client requests do
   not keep consuming model resources longer than necessary.

Recommended vBook adapter behavior until service-side timeout budget is
adjusted:

1. Continue writing placeholder observations for client-side timeouts.
2. Preserve `frame_id`, timestamp, selected image path, endpoint, model name,
   and prompt profile in placeholder metadata when available.
3. Treat client-side timeout differently from structured service `504`.
   Client-side timeout means response status is unknown and the original
   request may still be executing.
4. Do not automatically retry client-side timeouts in dense sweeps unless there
   is a long cooldown or an operator explicitly requests it.
5. Once vision reliably returns structured `504 timeout` within the client
   timeout, vBook may retry one time for `retryable=true` errors (`504`, `503`,
   `429`, `500 model_error`) with backoff.

Recommended interval policy:

- Keep `180s` as the safest batch-processing candidate.
- Keep `120s` as an evaluation candidate only after service timeout/retry
  alignment.
- Avoid using `90s`, `60s`, or `30s` as defaults until timeout behavior is
  changed and re-smoked.

## Next

After timeout alignment, repeat a small controlled sweep on the same course:

1. Run `180s` and confirm zero or near-zero client-side timeout placeholders.
2. Run `120s` and compare timeout count and successful-frame latency.
3. Only test `90s` after `120s` is stable.

This response does not change the HTTP API. The next vision-side work should
be scoped to operational behavior: timeout/retry budget alignment, logging,
and optional request cancellation/disconnect handling.

## Delivery Checklist

- [x] Written in responder `docs/90_reference/`.
- [x] Delivered to requester `docs/90_reference/`.
- [x] README indexes updated for requester and responder.
- [x] Progress note already exists:
  `docs/70_progress/2026-07-08-qwen-timeout-investigation.md`.
