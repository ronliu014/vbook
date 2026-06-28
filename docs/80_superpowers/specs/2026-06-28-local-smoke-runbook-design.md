# Local Smoke Runbook Design

## 背景

vBook 当前已经具备 local MVP pipeline、external vision command、LLM fusion command、stub tools、
contract checker、manifest 和 note 输出。但 `docs/60_operations/smoke-tests.md` 仍更像命令清单：

- 它列出了 placeholder build、manual-json、external-command、Qwen adapter 等片段；
- 但没有形成一条本地可重复执行的 smoke 路径；
- 没有明确“先跑什么、期望产出什么、失败时看哪里”；
- 也没有把本地 contract smoke 和真实 Qwen/LLM 质量验收区分得足够清楚。

项目任务看板已经把下一步推荐任务定为“完善本地 smoke test runbook”。本阶段要把现有 smoke 文档升级成
runbook，使等待 Qwen 服务期间仍能稳定验证 vBook 本地管线和接口边界。

## 目标

- 将 `docs/60_operations/smoke-tests.md` 从命令片段升级为本地 smoke runbook。
- 第一版只覆盖不依赖真实外部服务的本地闭环。
- 让读者知道每个 smoke 的目的、前置条件、命令、期望产物、检查点和失败排查入口。
- 覆盖 CLI readiness、placeholder build、external vision stub、LLM fusion stub、LLM contract checker 和 batch build smoke。
- 明确 smoke tests 只验证管线、文件、contract 和 stage status，不评价 OCR/LLM 输出质量。
- 更新 `docs/60_operations/README.md`，让 operations 层入口指向升级后的 smoke runbook。
- 更新 `docs/00_project/task-board.md`，记录本地 smoke runbook 已完成，并给出下一步推荐。

## 非目标

本阶段不做：

- 不调用真实 Qwen Vision Service。
- 不调用真实 LLM/Qwen 文本综合服务。
- 不新增 HTTP adapter。
- 不新增模型 SDK 或外部依赖。
- 不新增 repo 内大型视频、音频或图片 fixture。
- 不改变 CLI 行为。
- 不改变 manifest schema、note template、fusion contract 或视觉 contract。
- 不新增自动化 smoke runner 脚本。
- 不把 batch workflow 细节扩展成完整 batch operations 文档。

## 方案选择

### 方案 A：升级现有 `docs/60_operations/smoke-tests.md`

直接把现有 smoke test 文档重构成完整 runbook，保留并整理已有 placeholder、vision stub、Qwen adapter
内容，同时新增 LLM fusion stub、contract checker、batch smoke、输出检查和失败排查。

优点：

- 使用现有 operations 入口，不增加读者寻找成本。
- 与 `docs/60_operations/README.md` 当前 planned/current entry 匹配。
- 低风险，纯文档改动。
- 能直接解决任务看板里的“本地 smoke runbook”缺口。

缺点：

- 文件会比现在更长，需要清晰分节。

### 方案 B：新增 `docs/60_operations/local-smoke-runbook.md`

保留现有 `smoke-tests.md`，另建本地 runbook。

优点：

- 新旧内容分离。
- 文件更聚焦。

缺点：

- 两个 smoke 文档容易重复和漂移。
- 现有 `smoke-tests.md` 仍然偏命令清单，入口不够统一。

### 方案 C：新增自动化 smoke runner 脚本

新增 `tools/run_local_smoke.py` 或 PowerShell 脚本，把命令自动串起来。

优点：

- 后续更适合 CI。
- 人工操作更少。

缺点：

- 当前阶段过重。
- 需要引入 fixture、临时文件策略和更细的跨平台命令处理。
- 用户当前最需要的是理解项目状态和可执行 runbook，不是自动化脚本。

## 决策

采用方案 A：升级现有 `docs/60_operations/smoke-tests.md`。

原因：

- 这是当前不依赖 Qwen 部署也能推进的最高价值 operations 工作。
- 它可以复用现有文档路径，不增加入口复杂度。
- 它把已有 CLI、stub、sample、checker、manifest 和 note 输出串成一条可读的验收路径。
- 它保持本阶段为 docs-only，不改变 runtime 行为。

## 文件结构

修改：

```text
docs/60_operations/smoke-tests.md
docs/60_operations/README.md
docs/00_project/task-board.md
```

不修改：

```text
runtime code
tests
tools
docs/90_reference/samples/
docs/90_reference/llm-fusion-command-requirements.md
docs/90_reference/qwen-vision-service-requirements.md
```

## Runbook 结构

`docs/60_operations/smoke-tests.md` 重构为固定结构：

```text
# Smoke Tests

## 适用范围
## 前置条件
## 输出目录约定
## Smoke 0: CLI readiness
## Smoke 1: Placeholder local build
## Smoke 2: External vision command with vision_stub
## Smoke 3: LLM fusion command with llm_fusion_stub
## Smoke 4: LLM contract checker
## Smoke 5: Batch build smoke
## 输出检查清单
## 常见失败与排查
## 不覆盖的内容
## 后续真实服务联调
```

### `适用范围`

说明本 runbook 验证：

- CLI 是否可用；
- local MVP pipeline 是否能写出核心 artifact；
- external-command 视觉边界是否可用；
- LLM fusion command 边界是否可用；
- LLM request/response contract checker 是否可用；
- batch build 基础路径是否可用；
- manifest stage status 是否能作为快速检查入口。

同时明确不验证：

- 真实 OCR 准确率；
- 真实多模态理解质量；
- 真实 LLM synthesis 质量；
- Qwen 服务网络连通性；
- 大规模课程批处理性能。

### `前置条件`

列出最小前置条件：

- 从 repo root 执行命令。
- Python 环境可运行 `python -m vbook_client --version`。
- 如需跑 build smoke，需要准备一个本地短视频和时间戳 transcript。
- transcript 可使用 SRT 或 vBook timestamped JSON。
- 生成输出放在 `outputs/smoke-*` 或用户指定目录，且不提交 Git。

不要求：

- Qwen 服务；
- LLM 服务；
- API token；
- GPU；
- 模型 runtime。

### `输出目录约定`

建议统一使用：

```text
outputs/smoke-placeholder/
outputs/smoke-vision-stub/
outputs/smoke-llm-stub/
outputs/smoke-batch/
runs/llm_fusion_response.json
```

说明这些目录是本地生成物，不应提交。

### `Smoke 0: CLI readiness`

命令：

```powershell
python -m vbook_client --version
python -m vbook_client check
python -m vbook_client config --show
```

检查点：

- 命令 exit code 为 0。
- `check` 输出表示 skeleton readiness。
- `config --show` 能打印当前默认配置。

失败排查：

- Python path 是否在 repo root。
- 是否安装 editable package。
- 是否使用了错误虚拟环境。

### `Smoke 1: Placeholder local build`

命令：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\smoke-placeholder
```

期望产物：

```text
outputs/smoke-placeholder/manifest.json
outputs/smoke-placeholder/note.md
outputs/smoke-placeholder/vision/analysis.json
outputs/smoke-placeholder/fusion/prompt.json
outputs/smoke-placeholder/fusion/sections.json
```

检查点：

- `manifest.json` 存在。
- `note.md` 存在。
- `stage_status.manifest == "done"`。
- `stage_status.vision_analysis == "done"`。
- `stage_status.fusion_prompt == "done"`。
- `stage_status.fusion_sections == "done"`。
- `stage_status.note_export == "done"`。

说明：

- 默认 visual backend 是 placeholder，不代表真实视觉智能。

### `Smoke 2: External vision command with vision_stub`

命令：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\smoke-vision-stub `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

期望产物：

```text
outputs/smoke-vision-stub/vision/external/frames.json
outputs/smoke-vision-stub/vision/external/analysis.json
outputs/smoke-vision-stub/vision/analysis.json
outputs/smoke-vision-stub/manifest.json
```

检查点：

- external frames input JSON 存在。
- external raw analysis JSON 存在。
- normalized `vision/analysis.json` 存在。
- `manifest.json` 里 `stage_status.vision_analysis == "done"`。
- `vision/analysis.json` 中 backend 或 source 能表明来自 `vision_stub`。

说明：

- `tools/vision_stub.py` 不做 OCR 或多模态理解，只验证 external-command contract。

### `Smoke 3: LLM fusion command with llm_fusion_stub`

命令：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\smoke-llm-stub `
  --llm-fusion-command "python tools\llm_fusion_stub.py --input {input} --output {output}"
```

期望产物：

```text
outputs/smoke-llm-stub/fusion/llm_request.json
outputs/smoke-llm-stub/fusion/llm_response.json
outputs/smoke-llm-stub/fusion/llm_sections.json
outputs/smoke-llm-stub/note.md
outputs/smoke-llm-stub/manifest.json
```

检查点：

- `fusion/llm_request.json` 存在。
- `fusion/llm_response.json` 存在。
- `fusion/llm_sections.json` 存在。
- `manifest.json` 里 `stage_status.llm_fusion == "done"`。
- `note.md` 使用 LLM sections 渲染。

说明：

- `tools/llm_fusion_stub.py` 是 deterministic smoke command，不代表最终 LLM synthesis 质量。

### `Smoke 4: LLM contract checker`

命令：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response docs\90_reference\samples\llm_fusion_response.valid.json
```

期望输出：

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: 2
```

失败样例检查：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response docs\90_reference\samples\llm_fusion_response.invalid_schema.json
```

期望：

- 返回非 0 exit code。
- stderr 包含 `ERROR:`。

说明：

- checker 验证 contract 和 parser compatibility，不验证模型质量。

### `Smoke 5: Batch build smoke`

命令：

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\smoke-batch
```

输入要求：

```text
input/
  lesson.mp4
  text/
    lesson.srt
```

期望产物：

```text
outputs/smoke-batch/batch_manifest.json
outputs/smoke-batch/<lesson-id>/manifest.json
outputs/smoke-batch/<lesson-id>/note.md
```

检查点：

- `batch_manifest.json` 存在。
- `lesson_count` 符合输入数量。
- 至少一个 lesson `status == "done"`。
- 对应 lesson 目录下存在 `manifest.json` 和 `note.md`。

说明：

- batch smoke 只验证批处理基础调度和 artifact 汇总，不验证大规模稳定性。

## 输出检查清单

新增 checklist，方便 smoke 完成后快速验收：

- CLI readiness 命令通过。
- placeholder build 产出 `manifest.json`、`note.md`、vision/fusion artifacts。
- vision stub build 产出 external frames 和 analysis。
- LLM stub build 产出 `llm_request.json`、`llm_response.json`、`llm_sections.json`。
- contract checker valid sample 通过。
- contract checker invalid schema 返回失败。
- batch smoke 产出 `batch_manifest.json`。
- 所有真实服务相关 smoke 均未执行，除非服务组明确通知服务 ready。

## 常见失败与排查

至少覆盖：

- `No module named vbook_client`
  - 检查是否在 repo root；
  - 运行 `python -m pip install -e ".[dev]"`。
- `external-command backend requires vision_command`
  - 检查 `--vision-command` 是否提供；
  - 检查 `{input}` 和 `{output}` placeholder。
- `llm-fusion-command requires {input} and {output} placeholders`
  - 检查 command template。
- transcript 解析失败
  - 检查 SRT 或 timestamped JSON 格式。
- ffmpeg/frame extraction 失败
  - 检查视频路径；
  - 检查 ffmpeg 是否可用。
- contract checker 返回 `ERROR: invalid response JSON`
  - 检查服务输出是否包含 Markdown fence 或解释性文本。

## 不覆盖的内容

明确列出：

- 不验证 Qwen Vision Service 网络连通性。
- 不验证真实 OCR 准确率。
- 不验证真实 LLM/Qwen 文本综合质量。
- 不验证 production 性能。
- 不验证服务端 runtime。
- 不验证知识库搜索。

## 后续真实服务联调

说明 Qwen 服务 ready 后的下一步不是修改本地 smoke runbook，而是单独推进：

- Qwen Vision Service integration runbook；
- 真实 LLM/Qwen fusion command 或 HTTP adapter runbook；
- 真实 MP4 + transcript smoke fixture 策略。

## 文档入口更新

### `docs/60_operations/README.md`

把 `smoke-tests.md` 从 planned/current mixed list 提升为第一入口：

- `smoke-tests.md`: local smoke runbook for CLI, stubs, contract checker, manifest, and note output.

保留 planned documents，但不要让读者误以为 smoke-tests 仍只是计划项。

### `docs/00_project/task-board.md`

更新：

- `Documentation foundation` 或 `Local MVP pipeline` 的下一步说明中移除“完成任务看板后推进 smoke runbook”。
- `等待 Qwen 服务期间可推进的任务` 中将“完善本地 smoke test runbook”改为 `Done`。
- `下一步推荐任务` 改为“编写 Qwen 视觉服务上线后的联调 runbook”或“增强专家笔记模板”。

推荐下一步选择：

- 若继续围绕服务接入：Qwen 视觉服务上线后的联调 runbook。
- 若继续不依赖服务：专家笔记模板增强。

本阶段建议将下一步推荐设为 Qwen 联调 runbook，因为它承接本地 smoke runbook，并能在服务部署后直接使用。

## 测试与验证策略

这是 docs-only 阶段，不新增 runtime tests。

实现完成后运行：

```powershell
git diff --check
python -m unittest discover
```

文档自检：

- 扫描目标文档，确认没有未完成占位词。
- 检查 `smoke-tests.md` 中每个 smoke 都包含目的、命令、期望产物或期望输出、检查点、边界说明。
- 检查真实 Qwen 和真实 LLM 服务没有被描述成当前可用。

## 验收口径

本阶段完成后应满足：

- `docs/60_operations/smoke-tests.md` 是可执行 runbook，而不是松散命令清单。
- Runbook 能在没有 Qwen、LLM 服务、token、GPU、模型 runtime 的情况下使用。
- Runbook 覆盖 CLI readiness、placeholder build、vision stub、LLM stub、contract checker、batch smoke。
- Runbook 明确哪些检查需要用户本地短视频和 transcript。
- Runbook 明确 smoke 不是质量评估。
- `docs/60_operations/README.md` 指向 runbook。
- `docs/00_project/task-board.md` 反映本地 smoke runbook 已完成，并给出新的下一步推荐。
- 不访问网络。
- 不新增依赖。
- 不改变 runtime code。
- `python -m unittest discover` 通过。

## 风险与处理

- 风险：Runbook 过长导致读者找不到主路径。
  - 处理：每个 smoke 使用固定结构，并把 checklist 放在后面。
- 风险：读者误以为 vision stub 或 LLM stub 代表真实智能能力。
  - 处理：每个 stub smoke 都明确写出只验证 contract，不验证质量。
- 风险：没有本地视频和 transcript 的读者无法跑 build smoke。
  - 处理：CLI readiness 和 contract checker 不依赖素材；build smoke 明确素材要求。
- 风险：Qwen adapter 内容和“本地无外部服务闭环”混在一起。
  - 处理：真实服务联调移到后续章节，只保留不执行的方向说明。

## 后续工作

- 用户确认本设计后，编写 implementation plan。
- 按 plan 重构 `docs/60_operations/smoke-tests.md`。
- Qwen 服务 ready 后，单独设计 Qwen Vision integration runbook。
- 后续可考虑把 smoke runbook 自动化成脚本，但不在本阶段混入。
