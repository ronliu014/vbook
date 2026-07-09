# vBook -> vision: Qwen timeout investigation request

Status: request
Date: 2026-07-08
From: vBook
To: vision
Related:

- `docs/90_reference/qwen-vision-service-integration-request.md`
- `docs/90_reference/integration-response.md`
- `docs/60_operations/qwen-vision-integration.md`
- `tools/vision_qwen_adapter.py`

## Context

vBook is using the vision Qwen service as the external visual-understanding
backend:

```text
POST http://192.168.0.33:8866/analyze-frame
prompt_profile = vbook_visual_analysis_v1
client timeout = 120 seconds per frame
client mode = sequential per-frame requests
adapter flag = --continue-on-error
```

The service was reachable and many frames completed successfully. During a
frame-interval sweep, however, vBook observed repeated per-frame timeout
placeholders. We need vision to help determine whether these failures are:

- service-layer timeout or request handling issues;
- Ollama/Qwen model inference timeout;
- queueing/resource contention inside the vision service;
- specific input-frame content causing pathological model latency;
- another known failure mode.

vBook should not choose the final default frame interval until this is
understood.

## vBook-side observation

The adapter writes a placeholder when a frame request fails:

```json
{
  "structured_observations": {
    "qwen_service": {
      "status": "error",
      "message": "Qwen service request timed out for frame-000003"
    }
  }
}
```

All failures listed below are client-observed request timeouts. vBook did not
observe schema-validation errors such as invalid `visual_type`, invalid
`confidence`, non-finite JSON numbers, or malformed JSON in this batch.

## Reproduction data

Course:

```text
投资训练营 / 韩珂龙头班：基础篇 / 反抽 反弹 反转
```

Video:

```text
F:\downloads\allwin\投资训练营\韩珂龙头班：基础篇\反抽 反弹 反转.mp4
```

vBook output roots:

```text
E:\projects\my_app\vbook\outputs\interval-sweep-qwen\180s\韩珂龙头班：基础篇\反抽 反弹 反转
E:\projects\my_app\vbook\outputs\interval-sweep-qwen\120s\韩珂龙头班：基础篇\反抽 反弹 反转
E:\projects\my_app\vbook\outputs\interval-sweep-qwen\90s\韩珂龙头班：基础篇\反抽 反弹 反转
```

The corresponding request frame list is available in each run at:

```text
vision\external\frames.json
```

The vBook-normalized analysis is available at:

```text
vision\analysis.json
```

## Timeout frames

| Interval | Frame ID | Timestamp | Image | vBook message |
| --- | --- | ---: | --- | --- |
| 180s | `frame-000003` | 360.00 | `frame_000003.jpg` | `Qwen service request timed out for frame-000003` |
| 120s | `frame-000002` | 120.00 | `frame_000002.jpg` | `Qwen service request timed out for frame-000002` |
| 120s | `frame-000003` | 240.00 | `frame_000003.jpg` | `Qwen service request timed out for frame-000003` |
| 120s | `frame-000005` | 480.00 | `frame_000005.jpg` | `Qwen service request timed out for frame-000005` |
| 90s | `frame-000001` | 0.00 | `frame_000001.jpg` | `Qwen service request timed out for frame-000001` |
| 90s | `frame-000002` | 90.00 | `frame_000002.jpg` | `Qwen service request timed out for frame-000002` |
| 90s | `frame-000003` | 180.00 | `frame_000003.jpg` | `Qwen service request timed out for frame-000003` |
| 90s | `frame-000005` | 360.00 | `frame_000005.jpg` | `Qwen service request timed out for frame-000005` |
| 90s | `frame-000006` | 450.00 | `frame_000006.jpg` | `Qwen service request timed out for frame-000006` |
| 90s | `frame-000007` | 540.00 | `frame_000007.jpg` | `Qwen service request timed out for frame-000007` |

Observed run summary:

| Interval | Selected frames | Qwen analyses | Qwen timeout placeholders | Final vBook inserted images |
| --- | ---: | ---: | ---: | ---: |
| 180s | 5 | 5 | 1 | 1 |
| 120s | 7 | 7 | 3 | 1 |
| 90s | 9 | 9 | 6 | 1 |

The `90s` run completed but took about 883.3 seconds. A later `60s` run was
manually terminated after entering the same slow path; it had extracted 14
frames but did not produce `vision/analysis.json`. A `30s` run was also
terminated before analysis completion.

## Question for vision

Please inspect the vision service logs around these requests and answer:

1. Did the service receive each timed-out request?
2. For timed-out requests, did FastAPI return HTTP `504 timeout`, or did the
   client time out before receiving any HTTP response?
3. If the service returned an error, what were the exact HTTP status and
   `error.code` values?
4. Was the timeout caused by model inference exceeding the service-side 120s
   limit, by an Ollama/backend failure, or by service request queueing?
5. Are these frames visually pathological for `qwen3-vl:8b`? If so, please
   identify the likely cause, for example dense K-line UI, tiny text, low
   contrast, too much chart detail, or first-frame warmup.
6. Is the service currently configured with a server-side timeout equal to,
   less than, or greater than the vBook client timeout of 120 seconds?
7. Does vision recommend changing any of the following?
   - server timeout;
   - vBook client timeout;
   - request retry policy;
   - prompt profile;
   - image preprocessing or resizing;
   - per-frame concurrency;
   - logging fields needed for future diagnosis.

## Requested response

Please reply in vision docs, preferably:

```text
docs/90_reference/vbook-vision-qwen-timeout-investigation-response.md
```

The response should include:

- root-cause classification: service / model / input frame / queueing / other;
- evidence from service logs, including request IDs or frame IDs;
- exact error codes or timeout behavior observed by vision;
- recommended vBook adapter behavior;
- whether vBook should keep `180s`, evaluate `120s`, or avoid dense intervals
  until service-side changes are made.

## vBook decision hold

vBook will postpone choosing the final default frame interval until this
investigation is answered. Current provisional stance:

- `180s` remains the safest batch-processing candidate.
- `120s` remains a high-density candidate for valuable lessons.
- `90s`, `60s`, and `30s` should not become default until the timeout behavior
  is explained and mitigated.
