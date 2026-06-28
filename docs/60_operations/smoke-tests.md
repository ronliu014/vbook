# Smoke Tests

This runbook verifies vBook's local pipeline boundaries without calling real
Qwen, OCR, multimodal, or LLM services. Smoke tests are not quality benchmarks;
they confirm that commands run, expected artifacts are written, contracts are
readable, and manifest stage statuses can be inspected.

## 适用范围

This runbook verifies:

- CLI readiness.
- Local MVP pipeline artifact creation.
- `external-command` visual analysis with `tools/vision_stub.py`.
- LLM fusion command execution with `tools/llm_fusion_stub.py`.
- LLM request/response contract compatibility with `tools/check_llm_fusion_contract.py`.
- Basic `build-batch` scheduling and artifact summary.
- `manifest.json` stage status as a quick inspection surface.

This runbook does not verify:

- Real OCR accuracy.
- Real multimodal visual understanding quality.
- Real LLM synthesis quality.
- Qwen Vision Service network connectivity.
- Large-scale batch performance.

## 前置条件

Run commands from the repository root.

Minimum local checks require:

```powershell
python -m vbook_client --version
python -m vbook_client check
```

Build smoke checks require a local short video and a timestamped transcript:

```text
path\to\lesson.mp4
path\to\lesson.srt
```

The transcript may be SRT or vBook timestamped JSON. Generated smoke outputs
belong under `outputs/` or `runs/` and should not be committed.

Not required for this runbook:

- Qwen service.
- LLM service.
- API token.
- GPU.
- Model runtime.

## 输出目录约定

Use isolated output directories so each smoke can be inspected independently:

```text
outputs/smoke-placeholder/
outputs/smoke-vision-stub/
outputs/smoke-llm-stub/
outputs/smoke-batch/
runs/llm_fusion_response.json
```

If a directory already exists from a previous run, remove it manually or choose
a new output path before rerunning the smoke.

## Smoke 0: CLI Readiness

Purpose: verify that the local Python environment can load vBook and print the
current configuration.

Run:

```powershell
python -m vbook_client --version
python -m vbook_client check
python -m vbook_client config --show
```

Expected checks:

- Each command exits with code `0`.
- `check` reports skeleton readiness.
- `config --show` prints the current default configuration.

If this fails:

- Confirm the command is running from the repository root.
- Confirm the active Python environment is the intended environment.
- Install editable development dependencies if needed:

```powershell
python -m pip install -e ".[dev]"
```

## Smoke 1: Placeholder Local Build

Purpose: verify that the local MVP pipeline can create core artifacts using the
default placeholder visual backend.

Run:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\smoke-placeholder
```

Expected artifacts:

```text
outputs/smoke-placeholder/manifest.json
outputs/smoke-placeholder/note.md
outputs/smoke-placeholder/vision/analysis.json
outputs/smoke-placeholder/fusion/prompt.json
outputs/smoke-placeholder/fusion/sections.json
```

Expected manifest checks:

- `stage_status.manifest == "done"`
- `stage_status.vision_analysis == "done"`
- `stage_status.fusion_prompt == "done"`
- `stage_status.fusion_sections == "done"`
- `stage_status.note_export == "done"`

Boundary:

- The default visual backend is placeholder intelligence. Passing this smoke
  proves artifact creation, not real OCR or multimodal quality.

## Smoke 2: External Vision Command with `vision_stub`

Purpose: verify vBook's `external-command` visual-analysis boundary without
installing OCR, model runtimes, or API credentials.

Run:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\smoke-vision-stub `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

Expected artifacts:

```text
outputs/smoke-vision-stub/vision/external/frames.json
outputs/smoke-vision-stub/vision/external/analysis.json
outputs/smoke-vision-stub/vision/analysis.json
outputs/smoke-vision-stub/manifest.json
```

Expected checks:

- `vision/external/frames.json` exists.
- `vision/external/analysis.json` exists.
- Normalized `vision/analysis.json` exists.
- `manifest.json` has `stage_status.vision_analysis == "done"`.
- `vision/analysis.json` includes evidence that the smoke result came from
  `vision_stub`.

Boundary:

- `tools/vision_stub.py` writes deterministic smoke analysis. It does not
  perform OCR or multimodal visual understanding.

## Smoke 3: LLM Fusion Command with `llm_fusion_stub`

Purpose: verify vBook's `--llm-fusion-command` boundary without a real model
provider.

Run:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\smoke-llm-stub `
  --llm-fusion-command "python tools\llm_fusion_stub.py --input {input} --output {output}"
```

Expected artifacts:

```text
outputs/smoke-llm-stub/fusion/llm_request.json
outputs/smoke-llm-stub/fusion/llm_response.json
outputs/smoke-llm-stub/fusion/llm_sections.json
outputs/smoke-llm-stub/note.md
outputs/smoke-llm-stub/manifest.json
```

Expected checks:

- `fusion/llm_request.json` exists.
- `fusion/llm_response.json` exists.
- `fusion/llm_sections.json` exists.
- `manifest.json` has `stage_status.llm_fusion == "done"`.
- `note.md` is rendered from the parsed LLM sections.

Boundary:

- `tools/llm_fusion_stub.py` is a deterministic smoke command. It does not
  represent final LLM synthesis quality.

## Smoke 4: LLM Contract Checker

Purpose: verify that the reference request/response samples match the current
vBook LLM fusion contract and parser.

Run the valid sample:

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response docs\90_reference\samples\llm_fusion_response.valid.json
```

Expected output:

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: 2
```

Run the invalid schema sample:

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response docs\90_reference\samples\llm_fusion_response.invalid_schema.json
```

Expected checks:

- Command exits with a non-zero status.
- stderr contains `ERROR:`.

Boundary:

- The checker validates file shape and parser compatibility. It does not score
  model note quality.

## Smoke 5: Batch Build Smoke

Purpose: verify that `build-batch` can discover a vtext-compatible input folder,
run lesson builds, and summarize results.

Input layout:

```text
input/
  lesson.mp4
  text/
    lesson.srt
```

Run:

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\smoke-batch
```

Expected artifacts:

```text
outputs/smoke-batch/batch_manifest.json
outputs/smoke-batch/<lesson-id>/manifest.json
outputs/smoke-batch/<lesson-id>/note.md
```

Expected checks:

- `batch_manifest.json` exists.
- `lesson_count` matches the input lesson count.
- At least one lesson has `status == "done"`.
- The corresponding lesson directory has `manifest.json` and `note.md`.

Boundary:

- This smoke verifies basic batch scheduling and artifact summary. It does not
  verify large-scale performance.

## 输出检查清单

Use this checklist after running the relevant smoke commands:

- CLI readiness commands pass.
- Placeholder build writes `manifest.json`, `note.md`, and vision/fusion artifacts.
- Vision stub build writes external frames and analysis artifacts.
- LLM stub build writes `llm_request.json`, `llm_response.json`, and `llm_sections.json`.
- Contract checker accepts the valid sample.
- Contract checker rejects the invalid schema sample.
- Batch smoke writes `batch_manifest.json`.
- Real-service smoke commands are not run unless the service team has confirmed readiness.

## 常见失败与排查

### `No module named vbook_client`

Check that you are running from the repository root and using the intended
Python environment. If needed, install editable development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

### `external-command backend requires vision_command`

Pass `--vision-command` when using `--vision-backend external-command`.

The command template must include both placeholders:

```text
{input}
{output}
```

### `llm-fusion-command requires {input} and {output} placeholders`

Update the command template so vBook can pass the request and response paths:

```powershell
--llm-fusion-command "python tools\llm_fusion_stub.py --input {input} --output {output}"
```

### Transcript parse failure

Check that the transcript is valid SRT or vBook timestamped JSON. Confirm the
transcript path passed to `--transcript` exists.

### Frame extraction or ffmpeg failure

Check that the video path exists and ffmpeg is available on `PATH`. The baseline
frame extraction pattern is:

```powershell
ffmpeg -i lesson.mp4 -vf fps=1/3 frames/frame_%06d.jpg
```

### Contract checker returns `ERROR: invalid response JSON`

Check whether the response file contains Markdown fences, explanatory prose, or
other text around the JSON. vBook expects strict JSON for LLM fusion responses.

## 不覆盖的内容

This local runbook does not cover:

- Qwen Vision Service network connectivity.
- Real OCR accuracy.
- Real LLM/Qwen text synthesis quality.
- Production performance.
- Server runtime.
- Knowledge-base search.

## 后续真实服务联调

When the Qwen service team confirms deployment, use a separate integration
runbook for live service checks. That follow-up should cover:

- Qwen Vision Service health and `/analyze-frame` smoke.
- Real LLM/Qwen fusion command or HTTP adapter smoke.
- Real MP4 + transcript smoke fixture strategy.

Until then, keep this page focused on deterministic local checks.
