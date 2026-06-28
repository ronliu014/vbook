# Qwen Vision Integration Runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a service-ready Qwen Vision integration runbook that tells vBook operators how to validate the Qwen adapter after the external service team confirms deployment.

**Architecture:** Keep this as a docs-only operations update. Add a dedicated `docs/60_operations/qwen-vision-integration.md` runbook, link it from the operations index, and update the project task board so Qwen integration runbook preparation is recorded as done while the actual service remains blocked until deployment.

**Tech Stack:** Markdown documentation, existing `tools/vision_qwen_adapter.py` command interface, existing Qwen reference docs, Git diff checks, Python `unittest` full-suite verification.

---

## File Structure

- Create: `docs/60_operations/qwen-vision-integration.md`
  - Service-ready runbook for Qwen Vision Service health, adapter build, artifact, manifest, and visual sanity checks.
- Modify: `docs/60_operations/README.md`
  - Add the Qwen integration runbook as a current operations entry point.
- Modify: `docs/00_project/task-board.md`
  - Mark Qwen integration runbook preparation as done and update the next recommended task.

No runtime source, adapter code, tests, fixtures, network calls, dependency changes, CLI behavior changes, manifest schema changes, visual schema changes, or note template changes are included.

---

## Task 1: Add the Qwen Vision Integration Runbook

**Files:**
- Create: `docs/60_operations/qwen-vision-integration.md`

- [ ] **Step 1: Create `docs/60_operations/qwen-vision-integration.md`**

Create `docs/60_operations/qwen-vision-integration.md` with:

````markdown
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
````

- [ ] **Step 2: Verify required sections exist**

Run:

```powershell
rg -n "Ready 前检查|Step 1: Health Check|Step 2: vBook Build Through Qwen Adapter|Step 3: Artifact Checks|Step 4: Manifest Checks|Step 5: Visual Content Checks|Common Failures|Completion Criteria" docs/60_operations/qwen-vision-integration.md
```

Expected: output shows one hit for each required section.

- [ ] **Step 3: Verify the runbook does not require current live execution**

Run:

```powershell
rg -n "Do not run|Run only after|Stop here|service team confirms|not required|does not cover" docs/60_operations/qwen-vision-integration.md
```

Expected: output shows readiness and no-current-execution guardrails. Confirm manually that the runbook does not tell the reader to call `192.168.0.33:8866` before service readiness is confirmed.

Do not commit yet.

---

## Task 2: Update Operations Entry and Project Task Board

**Files:**
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/task-board.md`

- [ ] **Step 1: Update `docs/60_operations/README.md`**

In `docs/60_operations/README.md`, replace:

```markdown
- [smoke-tests.md](./smoke-tests.md) - local smoke runbook for CLI, stubs,
  contract checker, manifest, and note output.
- [../../README.md](../../README.md#development-commands)
```

with:

```markdown
- [smoke-tests.md](./smoke-tests.md) - local smoke runbook for CLI, stubs,
  contract checker, manifest, and note output.
- [qwen-vision-integration.md](./qwen-vision-integration.md) - service-ready
  integration runbook for Qwen Vision Service.
- [../../README.md](../../README.md#development-commands)
```

- [ ] **Step 2: Update task board stage summary**

In `docs/00_project/task-board.md`, replace:

```markdown
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、任务看板、reference 文档和本地 smoke runbook 已经建立。 | 继续补齐 Qwen 联调 runbook 和 pipeline stage docs。 |
```

with:

```markdown
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、任务看板、reference 文档、本地 smoke runbook 和 Qwen 联调 runbook 已经建立。 | 继续补齐 pipeline stage docs。 |
```

In the same table, replace:

```markdown
| Vision integration boundary | `Partial` | `placeholder`、`manual-json`、`external-command`、`tools/vision_qwen_adapter.py` 已具备边界。 | Qwen 服务 ready 后执行真实 health/analyze-frame smoke。 |
```

with:

```markdown
| Vision integration boundary | `Partial` | `placeholder`、`manual-json`、`external-command`、`tools/vision_qwen_adapter.py` 和 Qwen 联调 runbook 已具备边界。 | Qwen 服务 ready 后按 runbook 执行真实 health/analyze-frame smoke。 |
```

- [ ] **Step 3: Update ready task status**

In `docs/00_project/task-board.md`, replace:

```markdown
| 编写 Qwen 视觉服务上线后的联调 runbook | `Ready` | 文档说明服务 ready 后如何设置 endpoint、运行 adapter、检查成功和失败输出。 |
```

with:

```markdown
| 编写 Qwen 视觉服务上线后的联调 runbook | `Done` | [qwen-vision-integration.md](../60_operations/qwen-vision-integration.md) 已说明服务 ready 后如何设置 endpoint、运行 adapter、检查成功和失败输出。 |
```

- [ ] **Step 4: Add recent completion row**

In `docs/00_project/task-board.md`, in the `最近完成` table, add this row immediately before `Local smoke test runbook`:

```markdown
| Qwen Vision integration runbook | `Done` | `docs/60_operations/qwen-vision-integration.md` 记录服务 ready 后的 health、adapter、artifact、manifest 和失败排查步骤。 |
```

- [ ] **Step 5: Update next recommended task**

In `docs/00_project/task-board.md`, replace:

```markdown
## 下一步推荐任务

推荐下一步：编写 Qwen 视觉服务上线后的联调 runbook。

理由：

- 本地 smoke runbook 已经覆盖无外部服务的可重复验收路径。
- Qwen 服务项目组正在推进部署，联调 runbook 可以提前明确服务 ready 后的 health、adapter、manifest 和失败排查步骤。
- 该 runbook 不需要立即调用真实服务，但能让服务上线后的验收更快进入可执行状态。
```

with:

```markdown
## 下一步推荐任务

推荐下一步：增强专家笔记模板。

理由：

- Qwen 服务尚未确认部署完成，真实视觉联调仍保持 blocked。
- 本地 smoke runbook 和 Qwen 联调 runbook 已经把等待服务期间的验收路径准备好。
- 专家笔记模板增强不依赖外部服务，可以继续提升 `note.md` 的用户价值。
```

- [ ] **Step 6: Run entry and board checks**

Run:

```powershell
rg -n "qwen-vision-integration.md|Qwen Vision integration runbook|增强专家笔记模板|真实视觉联调仍保持 blocked" docs/60_operations/README.md docs/00_project/task-board.md
```

Expected: output shows:

- `docs/60_operations/README.md` links to `qwen-vision-integration.md`.
- `docs/00_project/task-board.md` marks the Qwen integration runbook as `Done`.
- `docs/00_project/task-board.md` recommends expert note template enhancement next.

Do not commit yet.

---

## Task 3: Verify and Commit the Runbook Update

**Files:**
- Create: `docs/60_operations/qwen-vision-integration.md`
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/task-board.md`

- [ ] **Step 1: Run placeholder scan**

Run:

```powershell
$placeholderPattern = ('T' + 'BD') + '|待' + '定|占位' + '未完成|' + ('fill' + ' in details') + '|' + ('implement' + ' later')
rg -n $placeholderPattern docs/60_operations/qwen-vision-integration.md docs/60_operations/README.md docs/00_project/task-board.md
```

Expected: exit code `1` with no matches.

- [ ] **Step 2: Run no-live-call guardrail scan**

Run:

```powershell
rg -n "Do not run|Run only after|Stop here|service team confirms|真实视觉联调仍保持 blocked" docs/60_operations/qwen-vision-integration.md docs/00_project/task-board.md
```

Expected: output shows the readiness guardrails and task-board blocked statement.

- [ ] **Step 3: Run whitespace diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 4: Inspect the final diff**

Run:

```powershell
git diff -- docs/60_operations/qwen-vision-integration.md docs/60_operations/README.md docs/00_project/task-board.md
```

Expected manual checks:

- The new Qwen runbook is service-ready, not a current live execution report.
- It includes ready checks, health check, adapter build, artifact checks, manifest checks, visual content checks, common failures, completion criteria, and related docs.
- It does not claim Qwen service is deployed.
- Operations README links to the new runbook.
- Task board marks runbook preparation done while keeping real visual integration blocked until service readiness.

- [ ] **Step 5: Run the full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits `0` and prints:

```text
OK
```

Expected current test count is `129`. If the test count changes while still passing, update the verification snapshot in `docs/00_project/task-board.md` to the exact count before committing.

- [ ] **Step 6: Commit the documentation update**

Run:

```powershell
git add docs/60_operations/qwen-vision-integration.md docs/60_operations/README.md docs/00_project/task-board.md
git commit -m "Document Qwen vision integration runbook"
```

---

## Task 4: Push and Confirm Remote Alignment

**Files:**
- All files committed in Task 3.

- [ ] **Step 1: Push to main**

Run:

```powershell
git push origin main
```

Expected: push updates `main -> main` without force. If the command returns non-zero but prints a successful update, verify with Step 2 before treating it as failed.

- [ ] **Step 2: Verify remote alignment**

Run:

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline -1
```

Expected:

- `git status --short --branch` prints `## main...origin/main`.
- `git rev-parse HEAD` and `git rev-parse origin/main` print the same commit hash.
- `git log --oneline -1` shows `Document Qwen vision integration runbook`.

---

## Self-Review

Spec coverage:

- New `docs/60_operations/qwen-vision-integration.md` runbook is covered by Task 1.
- Scope, service info, ready checks, input requirements, health check, adapter build, artifact checks, manifest checks, visual content checks, auth, timeout, common failures, out-of-scope content, completion criteria, and related documents are included in Task 1 exact content.
- Operations entry update is covered by Task 2.
- Task board update, completed Qwen integration runbook status, and next recommended task change are covered by Task 2.
- Docs-only verification, placeholder scan, no-live-call guardrail scan, `git diff --check`, full suite, commit, push, and remote alignment are covered by Tasks 3 and 4.
- No runtime code, adapter code, dependency, fixture, network call, CLI behavior change, manifest schema change, visual schema change, note template change, or smoke runner script is included.

Placeholder scan:

- The plan avoids unfinished placeholder markers in content to be written.
- The scan command builds sensitive marker strings through concatenation to avoid matching the plan itself.
- Every document edit step includes complete replacement content or exact replacement text.

Type and naming consistency:

- The runbook path is consistently `docs/60_operations/qwen-vision-integration.md`.
- Adapter command uses `tools/vision_qwen_adapter.py --input {input} --output {output} --endpoint ... --timeout-seconds 120`.
- Current endpoint values match `docs/90_reference/integration-response.md`.
- Task-board status labels remain `Done`, `Ready`, `Partial`, `Blocked`, and `Planned`.
