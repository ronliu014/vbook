# vision -> vBook: Qwen timeout investigation response

Status: response
Date: 2026-07-08
From: vision
To: vBook
Request:

- [vbook-vision-qwen-timeout-investigation-request.md](./vbook-vision-qwen-timeout-investigation-request.md)

## Summary

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

## Evidence Checked

Vision-side local logs under `vision/logs/` do not contain the July 8 production
interval-sweep requests. `app.log` only contains older validation/smoke entries
up to July 6, and `error.log` / `performance.log` are empty. Because of that,
vision cannot truthfully provide production request IDs, exact service-side
HTTP statuses, or final Ollama attempt logs for the timeout frames from local
logs alone.

What we could verify from repository state and vBook artifacts:

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

## Answers To vBook Questions

1. Did the service receive each timed-out request?

Not confirmed from service logs. The adapter timeout placeholders prove vBook
issued the HTTP calls and waited until its client timeout. Without July 8
service logs from the host at `192.168.0.33`, vision cannot confirm every
timed-out `frame_id` was accepted by FastAPI. The most likely path is that
FastAPI/Ollama did receive the request and continued processing past the client
timeout, but this remains an inference.

2. Did FastAPI return HTTP `504 timeout`, or did the client time out before
receiving any HTTP response?

Most likely the vBook client timed out before receiving a response. If the
service had returned a structured `504` within 120s, the adapter should have
been able to record an HTTP error response rather than a pure request-timeout
placeholder. Current service code may wait up to roughly 3 attempts of 120s
each, plus retry backoff, before returning its own `504`.

3. If the service returned an error, what were the exact HTTP status and
`error.code` values?

No exact production status is available from local logs. The expected service
error after all service-side timeout retries are exhausted is:

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

4. Was the timeout caused by model inference exceeding the service-side 120s
limit, by an Ollama/backend failure, or by service request queueing?

The best current classification is model/input latency plus timeout-budget
mismatch. Direct evidence for a hard Ollama backend failure is absent. Direct
evidence for FastAPI request queueing is also absent, and vBook says requests
were sequential. However, because the client timeout is equal to the per-attempt
Ollama timeout and the service can retry internally, the service can keep work
alive after vBook has already abandoned the request. That can create apparent
backend pressure during dense sweeps.

5. Are these frames visually pathological for `qwen3-vl:8b`?

They are not malformed or oversized, but they are high-complexity frames for
vision analysis. The likely slow factors are:

- dense K-line chart content;
- many small OCR targets across trading UI panels;
- mixed chart, table, indicator, subtitle, and risk-disclaimer text;
- repeated numbers and tick labels that encourage long OCR output;
- possible first-frame or model warmup latency in some runs.

6. Is the service currently configured with a server-side timeout equal to,
less than, or greater than the vBook client timeout of 120 seconds?

Per Ollama attempt, it is equal: `120s`.

End-to-end for one `/analyze-frame` request, it is greater: up to 3 attempts
are configured. In practice the service may not return its own structured
`504` until after the vBook client has already timed out.

7. Does vision recommend changing timeout, retry, prompt, preprocessing,
concurrency, or logging behavior?

Yes. Recommended order:

1. Make the service fail within the vBook client budget.
   Prefer a service-side model-call timeout below the adapter timeout, for
   example 90s service timeout with a 120s vBook client timeout, or keep 120s
   per attempt but set `max_retries: 1` for this endpoint. Do not keep
   `timeout=120` with `max_retries=3` while vBook's client timeout is 120s.

2. Avoid blind vBook retries on client timeout until service budget is aligned.
   A client-side timeout may mean the original server-side Ollama call is still
   running. Retrying immediately can increase backend pressure. After the
   service reliably returns structured `504`/`503` within the client timeout,
   vBook can retry retryable service errors once with short backoff.

3. Keep per-frame concurrency at 1 for now.
   Sequential calls are the safer default until service-side cancellation,
   logging, and latency baselines are improved.

4. Keep the current prompt profile.
   There is no evidence that `vbook_visual_analysis_v1` caused schema failures
   in this batch. Prompt changes should be considered only after timeout budget
   and logging are corrected.

5. Add optional image preprocessing only after measuring dimensions.
   File sizes are not large, but downscaling very dense frames to a bounded
   long edge may reduce latency. The service should record image dimensions and
   decoded size for every request before choosing a resize threshold.

6. Improve service logging before the next sweep.
   Recommended additional fields:
   - `request_id`, `frame_id`, `timestamp`, and optional `image_path`;
   - image width, height, decoded bytes, and MIME type;
   - Ollama attempt number and max attempts;
   - per-attempt latency and total elapsed latency;
   - timeout phase: request decode, model call, JSON parse, response write;
   - Ollama HTTP status or exception type;
   - whether the client disconnected before the service completed, if FastAPI
     exposes it reliably in this route.

## Adapter Guidance

The current vBook adapter is contract-compatible with vision. No API shape
change is required.

Recommended adapter behavior until service-side timeout budget is adjusted:

- Continue writing placeholder observations for client-side timeouts.
- Preserve `frame_id`, timestamp, selected image path, endpoint, model name,
  and prompt profile in the placeholder metadata if available.
- Treat client-side timeout differently from structured service `504`.
  Client-side timeout means response status is unknown and the original request
  may still be executing.
- Do not automatically retry client-side timeouts in dense sweeps unless there
  is a long cooldown or an operator explicitly requests it.
- Once vision returns structured `504 timeout` within the client timeout,
  vBook may retry one time for `retryable=true` errors (`504`, `503`, `429`,
  `500 model_error`) with backoff.

## Interval Recommendation

Until the service timeout policy is changed and re-smoked:

- Keep `180s` as the safest batch-processing candidate.
- Keep `120s` as an evaluation candidate only after service timeout/retry
  alignment.
- Avoid using `90s`, `60s`, or `30s` as defaults. They produce too many slow
  model calls for the current service/client budget and make operator
  termination likely.

After timeout alignment, repeat a small controlled sweep on this same course:

1. Run `180s` and confirm zero or near-zero client-side timeout placeholders.
2. Run `120s` and compare timeout count and successful-frame latency.
3. Only test `90s` after `120s` is stable.

## Proposed vision-side Follow-up

This response does not change the HTTP API. The next vision-side implementation
work should be scoped to operational behavior:

- expose or configure an end-to-end request budget lower than vBook's client
  timeout;
- reduce `/analyze-frame` model-call retries to 1 by default, or make retries
  conditional on failure type;
- add attempt-level latency logging;
- optionally add cancellation/disconnect handling so abandoned client requests
  do not keep consuming model resources longer than necessary.
