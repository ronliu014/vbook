# Local Smoke Runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the operations smoke-test documentation into a local runbook that validates vBook's current CLI, stub, contract, manifest, note, and batch boundaries without external services.

**Architecture:** Keep this as a docs-only change. Replace the current `docs/60_operations/smoke-tests.md` command list with a structured runbook, update the operations layer index, and update the project task board so the completed runbook changes the next recommended task.

**Tech Stack:** Markdown documentation, existing vBook CLI/tool names, Git diff checks, Python `unittest` full-suite verification.

---

## File Structure

- Modify: `docs/60_operations/smoke-tests.md`
  - Replace the current command list with a structured local smoke runbook.
- Modify: `docs/60_operations/README.md`
  - Promote `smoke-tests.md` from planned/current mixed list to the first operations entry point.
- Modify: `docs/00_project/task-board.md`
  - Mark the local smoke runbook work as done and update the next recommended task.

No runtime source, tests, tools, sample files, CLI arguments, manifest schema, note template, model adapter, Qwen service call, or LLM service call is included.

---

## Task 1: Replace the Smoke Test Document with a Local Runbook

**Files:**
- Modify: `docs/60_operations/smoke-tests.md`

- [ ] **Step 1: Replace `docs/60_operations/smoke-tests.md`**

Replace the entire file with:

````markdown
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
````

- [ ] **Step 2: Verify the runbook contains the required smoke sections**

Run:

```powershell
rg -n "Smoke 0|Smoke 1|Smoke 2|Smoke 3|Smoke 4|Smoke 5|输出检查清单|常见失败与排查|不覆盖的内容|后续真实服务联调" docs/60_operations/smoke-tests.md
```

Expected: output shows one hit for each required section.

- [ ] **Step 3: Verify real services are described as out of scope**

Run:

```powershell
rg -n "does not cover|without calling real|not run unless|Qwen Vision Service network connectivity|Real LLM/Qwen text synthesis quality" docs/60_operations/smoke-tests.md
```

Expected: output shows the scope and boundary statements. Confirm manually that the runbook does not instruct the reader to call real Qwen or real LLM services.

Do not commit yet.

---

## Task 2: Update Operations Entry and Project Task Board

**Files:**
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/task-board.md`

- [ ] **Step 1: Replace `docs/60_operations/README.md`**

Replace the entire file with:

```markdown
# 60 Operations

Operations-level documents explain how to run vBook locally, inspect outputs,
perform smoke tests, troubleshoot failures, and clean generated artifacts.

## Current Entry Points

- [smoke-tests.md](./smoke-tests.md) - local smoke runbook for CLI, stubs,
  contract checker, manifest, and note output.
- [../../README.md](../../README.md#development-commands)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)

## Planned Documents

- `local-run.md`
- `sample-inputs.md`
- `batch-processing.md`
- `troubleshooting.md`
- `outputs-cleanup.md`
```

- [ ] **Step 2: Update the stage summary in `docs/00_project/task-board.md`**

Replace this table row:

```markdown
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、reference 文档已经建立；任务看板是当前补齐项。 | 完成任务看板后推进 smoke runbook。 |
```

with:

```markdown
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、任务看板、reference 文档和本地 smoke runbook 已经建立。 | 继续补齐 Qwen 联调 runbook 和 pipeline stage docs。 |
```

Replace this table row:

```markdown
| Local MVP pipeline | `Done` | CLI 可从 video + transcript 生成 manifest、note、vision、fusion artifacts。 | 用 smoke runbook 固化可重复验收路径。 |
```

with:

```markdown
| Local MVP pipeline | `Done` | CLI 可从 video + transcript 生成 manifest、note、vision、fusion artifacts；本地 smoke runbook 已固化可重复验收路径。 | 等真实服务 ready 后执行联调 smoke。 |
```

- [ ] **Step 3: Update ready/done task rows in `docs/00_project/task-board.md`**

In the section `等待 Qwen 服务期间可推进的任务`, replace:

```markdown
| 完善本地 smoke test runbook | `Ready` | 文档能串起 CLI check、stub、sample、checker、manifest 和 note 输出检查。 |
```

with:

```markdown
| 完善本地 smoke test runbook | `Done` | [smoke-tests.md](../60_operations/smoke-tests.md) 已串起 CLI check、stub、sample、checker、manifest 和 note 输出检查。 |
```

In the section `最近完成`, add this row immediately before `LLM fusion contract samples and checker`:

```markdown
| Local smoke test runbook | `Done` | `docs/60_operations/smoke-tests.md` 覆盖 CLI readiness、placeholder build、vision stub、LLM stub、contract checker 和 batch smoke。 |
```

- [ ] **Step 4: Update next recommended task in `docs/00_project/task-board.md`**

Replace the section:

```markdown
## 下一步推荐任务

推荐下一步：完善本地 smoke test runbook。

理由：

- 不依赖真实 Qwen 服务部署。
- 能把已有 CLI、stub、sample、checker、manifest、note 输出串成固定验收路径。
- 能降低后续真实 Qwen 视觉服务和 LLM/Qwen 文本服务上线后的联调成本。
```

with:

```markdown
## 下一步推荐任务

推荐下一步：编写 Qwen 视觉服务上线后的联调 runbook。

理由：

- 本地 smoke runbook 已经覆盖无外部服务的可重复验收路径。
- Qwen 服务项目组正在推进部署，联调 runbook 可以提前明确服务 ready 后的 health、adapter、manifest 和失败排查步骤。
- 该 runbook 不需要立即调用真实服务，但能让服务上线后的验收更快进入可执行状态。
```

- [ ] **Step 5: Run entry and board checks**

Run:

```powershell
rg -n "smoke-tests.md|Local smoke test runbook|Qwen 视觉服务上线后的联调 runbook|本地 smoke runbook" docs/60_operations/README.md docs/00_project/task-board.md
```

Expected: output shows:

- `docs/60_operations/README.md` links to `smoke-tests.md`.
- `docs/00_project/task-board.md` marks local smoke runbook as `Done`.
- `docs/00_project/task-board.md` recommends Qwen integration runbook next.

Do not commit yet.

---

## Task 3: Verify and Commit the Runbook Update

**Files:**
- Modify: `docs/60_operations/smoke-tests.md`
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/task-board.md`

- [ ] **Step 1: Run placeholder scan**

Run:

```powershell
$placeholderPattern = ('T' + 'BD') + '|待' + '定|占位' + '未完成|' + ('fill' + ' in details') + '|' + ('implement' + ' later')
rg -n $placeholderPattern docs/60_operations/smoke-tests.md docs/60_operations/README.md docs/00_project/task-board.md
```

Expected: exit code `1` with no matches.

- [ ] **Step 2: Run whitespace diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 3: Inspect the final diff**

Run:

```powershell
git diff -- docs/60_operations/smoke-tests.md docs/60_operations/README.md docs/00_project/task-board.md
```

Expected manual checks:

- `smoke-tests.md` is a runbook with Smoke 0 through Smoke 5.
- `smoke-tests.md` clearly says real Qwen and real LLM services are out of scope.
- `docs/60_operations/README.md` makes `smoke-tests.md` a current entry point.
- `docs/00_project/task-board.md` marks local smoke runbook done and recommends Qwen integration runbook next.

- [ ] **Step 4: Run the full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits `0` and prints:

```text
OK
```

Expected current test count is `129`. If the test count changes while still passing, update the verification snapshot in `docs/00_project/task-board.md` to the exact count before committing.

- [ ] **Step 5: Commit the documentation update**

Run:

```powershell
git add docs/60_operations/smoke-tests.md docs/60_operations/README.md docs/00_project/task-board.md
git commit -m "Document local smoke runbook"
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
- `git log --oneline -1` shows `Document local smoke runbook`.

---

## Self-Review

Spec coverage:

- Upgrade of `docs/60_operations/smoke-tests.md` into a structured runbook is covered by Task 1.
- CLI readiness, placeholder build, vision stub, LLM stub, contract checker, batch smoke, output checklist, failure guide, out-of-scope section, and service-integration follow-up are all included in the exact Task 1 replacement content.
- Operations entry update is covered by Task 2.
- Project task board update, completed local smoke runbook status, and new next recommended task are covered by Task 2.
- Docs-only verification, placeholder scan, `git diff --check`, full suite, commit, push, and remote alignment are covered by Tasks 3 and 4.
- No runtime source, dependency, Qwen service call, LLM service call, fixture addition, CLI behavior change, manifest schema change, note template change, or smoke runner script is included.

Placeholder scan:

- The plan avoids unfinished placeholder markers in content to be written.
- The scan command builds sensitive marker strings through concatenation to avoid matching the plan itself.
- Every document edit step includes complete replacement content or exact replacement text.

Type and naming consistency:

- The runbook path is consistently `docs/60_operations/smoke-tests.md`.
- Tool names are consistently `tools/vision_stub.py`, `tools/llm_fusion_stub.py`, and `tools/check_llm_fusion_contract.py`.
- Output paths are consistently under `outputs/smoke-*` and `runs/`.
- Task-board status labels remain `Done`, `Ready`, `Partial`, `Blocked`, and `Planned`.
