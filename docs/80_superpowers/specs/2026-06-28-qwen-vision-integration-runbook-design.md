# Qwen Vision Integration Runbook Design

## 背景

vBook 已经完成 Qwen Vision Service 的 adapter 边界：

```text
vBook build
  -> --vision-backend external-command
    -> tools/vision_qwen_adapter.py
      -> POST /analyze-frame
        -> Qwen Vision Service
```

当前本地 smoke runbook 已经覆盖无外部服务的确定性路径：CLI readiness、placeholder build、vision stub、
LLM stub、contract checker 和 batch smoke。它刻意不调用真实 Qwen 服务。

Qwen 服务组已经回复了接口信息、契约对齐情况和目标 endpoint：

```text
Base URL:          http://192.168.0.33:8866
Analyze endpoint: http://192.168.0.33:8866/analyze-frame
Health endpoint:  http://192.168.0.33:8866/health
Auth:             none for current trusted LAN deployment
Prompt profile:   vbook_visual_analysis_v1
Timeout:          120 seconds per frame
Recommended concurrency: 1
```

但服务仍未确认部署完成，性能基线也待实测。因此下一步不是调用服务，而是先准备一份独立的 Qwen
视觉服务联调 runbook：服务 ready 后，vBook 侧可以按固定步骤完成 health、adapter、artifact、manifest
和失败排查。

## 目标

- 新增独立的 Qwen Vision Service integration runbook。
- 明确该 runbook 是服务 ready 后执行的联调手册，不是当前必须执行的本地 smoke。
- 记录服务 ready 前必须确认的信息。
- 记录 `GET /health` 验收步骤。
- 记录通过 `tools/vision_qwen_adapter.py` 调用 `POST /analyze-frame` 的 vBook build 命令。
- 记录 endpoint、timeout、prompt profile 和 token 的设置方式。
- 记录成功后要检查的 artifacts、manifest stage status 和视觉内容字段。
- 记录常见失败与排查口径。
- 明确 adapter 成功不等于视觉质量最终达标。
- 更新 operations 入口和项目任务看板。

## 非目标

本阶段不做：

- 不调用真实 Qwen Vision Service。
- 不验证 `http://192.168.0.33:8866` 当前是否可达。
- 不新增或修改 adapter 代码。
- 不新增 HTTP smoke runner 脚本。
- 不新增真实视频、图片、base64 或 transcript fixture。
- 不做性能基线测试。
- 不做最终 OCR/视觉质量评分。
- 不做真实 LLM fusion。
- 不改变 local smoke runbook 的“无外部服务”边界。
- 不改变 manifest schema、visual analysis schema、note template 或 CLI 行为。

## 方案选择

### 方案 A：新增 `docs/60_operations/qwen-vision-integration.md`

新增独立 runbook，专门描述 Qwen Vision Service ready 后的联调步骤。

优点：

- 与本地 smoke runbook 边界清楚。
- 不会误导读者在服务未部署时执行真实网络调用。
- operations 层入口清晰。
- 后续服务 ready 后可以直接更新同一 runbook 的实测结果和注意事项。

缺点：

- 新增一个 operations 文档，需要维护入口链接。

### 方案 B：追加到 `docs/60_operations/smoke-tests.md`

把 Qwen 联调步骤作为本地 smoke runbook 的后续章节。

优点：

- 文件更少。

缺点：

- 会破坏 `smoke-tests.md` 当前“无外部服务闭环”的定位。
- 读者可能误以为本地 smoke 必须访问 Qwen 服务。

### 方案 C：先做自动化 Qwen smoke script

新增脚本自动执行 health、adapter build 和 artifact 检查。

优点：

- 服务 ready 后更接近 CI/自动化验收。

缺点：

- 当前服务未部署，真实失败形态和性能基线未知。
- 需要 fixture、网络配置和输出清理策略。
- 超出当前“先把联调步骤写清楚”的目标。

## 决策

采用方案 A：新增 `docs/60_operations/qwen-vision-integration.md`。

原因：

- 它承接任务看板的下一步推荐。
- 它与 local smoke runbook 的范围互补，不互相污染。
- 它不依赖服务当前可用，也不触发网络调用。
- 它能把服务组回复、adapter 参数和 vBook 验收口径落到一份可执行手册中。

## 文件结构

新增：

```text
docs/60_operations/qwen-vision-integration.md
```

修改：

```text
docs/60_operations/README.md
docs/00_project/task-board.md
```

不修改：

```text
tools/vision_qwen_adapter.py
docs/60_operations/smoke-tests.md
docs/90_reference/integration-response.md
docs/90_reference/qwen-vision-service-requirements.md
docs/90_reference/qwen-vision-service-integration-request.md
runtime code
tests
```

## Runbook 结构

`docs/60_operations/qwen-vision-integration.md` 使用固定结构：

```text
# Qwen Vision Integration

## 适用范围
## 当前服务信息
## Ready 前检查
## 输入素材要求
## Step 1: Health check
## Step 2: vBook build through qwen adapter
## Step 3: Artifact checks
## Step 4: Manifest checks
## Step 5: Visual content checks
## Token and auth
## Timeout and performance notes
## Common failures
## 不覆盖的内容
## Completion criteria
## Related documents
```

### `适用范围`

说明本 runbook 用于服务组确认 Qwen Vision Service 已部署并可从 vBook 运行机器访问之后。

它验证：

- health endpoint 可访问；
- adapter 可以读取 vBook frame input；
- adapter 可以把 frame 图片转成 base64 request；
- service response 能被 adapter 归一化为 manual-json-compatible analysis；
- vBook build 能写出 expected artifacts；
- `manifest.json` 中 `vision_analysis` 为 `done`；
- 至少一个 frame 的 `ocr_text` 或 `vision_description` 能反映图片内容。

它不验证：

- 最终课程笔记质量；
- 真实 LLM fusion；
- 服务生产性能；
- 多并发吞吐；
- 长期稳定性。

### `当前服务信息`

从 `docs/90_reference/integration-response.md` 摘取当前已知信息：

```text
Base URL: http://192.168.0.33:8866
Analyze endpoint: http://192.168.0.33:8866/analyze-frame
Health endpoint: http://192.168.0.33:8866/health
Auth required: no
Prompt profile: vbook_visual_analysis_v1
Timeout: 120 seconds per frame
Recommended concurrency: 1
Model: qwen3-vl:8b
Known pending item: deployment performance baseline
```

同时注明：如果服务组后续更新 endpoint、auth 或 timeout，以最新服务组回复为准。

### `Ready 前检查`

列出执行前必须确认：

- 服务组明确通知服务已部署。
- vBook 运行机器能访问 `192.168.0.33:8866`。
- 防火墙已放行入站 TCP `8866`。
- `/health` 预期返回 HTTP `200` 或可读的 `503`。
- 当前 trusted LAN deployment 不需要 token。
- 已准备本地短视频和 transcript。
- 视频中至少应有一帧可读 slide 或课程画面，否则视觉内容检查无法判断。

如果这些条件不满足，runbook 应停在 ready 前检查，不继续真实调用。

### `输入素材要求`

说明需要：

```text
path\to\lesson.mp4
path\to\lesson.srt
```

或 timestamped JSON transcript。

要求：

- 视频较短，适合联调。
- 至少包含清晰 slide、PPT、图表或课程页面。
- transcript 时间轴与视频大致对应。
- 输出目录使用 `outputs/qwen-vision-smoke/` 或类似本地目录，不提交 Git。

### `Step 1: Health check`

PowerShell 命令：

```powershell
Invoke-RestMethod -Method Get -Uri http://192.168.0.33:8866/health
```

成功检查：

- HTTP `200`；
- `status == "ok"`；
- `model_loaded == true`；
- `model.provider == "qwen"`；
- `model.name` 非空，当前预期为 `qwen3-vl:8b`。

如果返回 HTTP `503`：

- 记录错误信息；
- 通知服务组模型未加载或后端不可用；
- 不继续执行 adapter build。

### `Step 2: vBook build through qwen adapter`

命令：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\qwen-vision-smoke `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120"
```

说明：

- `{input}` 和 `{output}` 必须保留，供 vBook 注入 frame input 和 external analysis output。
- adapter 默认 prompt profile 是 `vbook_visual_analysis_v1`。
- 如需显式指定：

```powershell
--vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://192.168.0.33:8866/analyze-frame --timeout-seconds 120 --prompt-profile vbook_visual_analysis_v1"
```

### `Step 3: Artifact checks`

期望产物：

```text
outputs/qwen-vision-smoke/vision/external/frames.json
outputs/qwen-vision-smoke/vision/external/analysis.json
outputs/qwen-vision-smoke/vision/analysis.json
outputs/qwen-vision-smoke/manifest.json
outputs/qwen-vision-smoke/note.md
```

检查点：

- external frames input 存在；
- external raw analysis 存在；
- normalized analysis 存在；
- manifest 存在；
- note 存在。

### `Step 4: Manifest checks`

检查 `manifest.json`：

- `stage_status.vision_analysis == "done"`；
- `artifacts.vision.analysis_count > 0`；
- `artifacts.vision.analyses` 中至少有一个 analysis；
- 如果后续 manifest 保存 backend/source 信息，应确认其指向 external-command/Qwen adapter 路径。

### `Step 5: Visual content checks`

人工检查 `vision/analysis.json`：

- 每个 analysis 有 `frame_id`；
- `visual_type` 是 `slide`、`kline_case` 或 `other`；
- `ocr_text` 是 string；
- `vision_description` 是 string；
- `structured_observations` 是 object；
- `confidence` 是 `0.0` 到 `1.0` 的 number 或 `null`；
- 至少一个 frame 的 `ocr_text` 或 `vision_description` 与图片内容相关。

说明：

- 这一步是 smoke 级人工质量 sanity check，不是最终模型评分。
- 如果 adapter 成功但内容明显不相关，应记录样例 frame、raw response 和 prompt profile，转交服务组排查。

### `Token and auth`

当前服务组回复 auth required 为 no。

如果未来启用 token，支持两种方式：

```powershell
$env:VBOOK_QWEN_VISION_TOKEN = "<token>"
```

或 command 内显式传：

```powershell
--token "<token>"
```

runbook 说明优先使用环境变量，避免把 token 写进文档或 shell history。

### `Timeout and performance notes`

记录：

- 当前 per-frame timeout 建议是 120 秒；
- 首次请求可能触发模型加载；
- performance baseline 仍待服务部署后补充；
- 第一版 adapter 串行逐帧请求；
- timeout 不一定代表 vBook bug，可能是模型 warmup、GPU 占用或服务端超时。

### `Common failures`

至少覆盖：

- `Invoke-RestMethod` 连接失败；
- `/health` 返回 `503`；
- build 报 `external-command backend requires vision_command`；
- build 报 `{input}`/`{output}` placeholder 缺失；
- adapter 报 `Qwen service returned HTTP 400 ... invalid_request`；
- adapter 报 `Qwen service returned HTTP 503 ... service_unavailable`；
- adapter 报 `Qwen service request timed out for <frame_id>`；
- adapter 报 `Qwen service returned invalid JSON for <frame_id>`；
- adapter 报 `response frame_id mismatch`；
- adapter 报 `invalid visual_type`；
- adapter 报 `confidence ... must be between 0.0 and 1.0`；
- build 成功但 `ocr_text` / `vision_description` 质量差。

每个失败项给出下一步：

- vBook 命令模板问题由 vBook 侧修正；
- network/health/model/timeouts 通知服务组；
- schema mismatch 附上 raw response 和 frame id；
- 视觉质量问题附上 frame image、response 和 prompt profile。

### `不覆盖的内容`

明确：

- 不覆盖 local deterministic smoke，见 `smoke-tests.md`。
- 不覆盖最终 OCR 质量评分。
- 不覆盖最终 LLM fusion。
- 不覆盖 batch Qwen performance。
- 不覆盖 production monitoring。
- 不覆盖长期 benchmark。

### `Completion criteria`

第一轮联调通过，当且仅当：

- 服务 ready 前检查全部满足；
- `/health` 返回 `200` 且 `model_loaded == true`；
- vBook build 命令 exit code 为 `0`；
- expected artifacts 均存在；
- `manifest.json` 中 `stage_status.vision_analysis == "done"`；
- `vision/analysis.json` 中至少一个 frame 有与图片相关的 `ocr_text` 或 `vision_description`；
- 失败排查中没有未解释的 schema mismatch。

### `Related documents`

链接：

- `docs/60_operations/smoke-tests.md`
- `docs/90_reference/qwen-vision-service-requirements.md`
- `docs/90_reference/qwen-vision-service-integration-request.md`
- `docs/90_reference/integration-response.md`
- `tools/vision_qwen_adapter.py`

## 文档入口更新

### `docs/60_operations/README.md`

新增 current entry：

```text
qwen-vision-integration.md - service-ready integration runbook for Qwen Vision Service.
```

### `docs/00_project/task-board.md`

更新：

- `等待 Qwen 服务期间可推进的任务` 中将 Qwen 联调 runbook 标为 `Done`。
- `最近完成` 增加 Qwen Vision integration runbook。
- `下一步推荐任务` 切到“增强专家笔记模板”或“完善 batch workflow 说明”。

推荐下一步：

- 若 Qwen 服务仍未部署：增强专家笔记模板。
- 若 Qwen 服务已部署：执行 Qwen integration runbook 并记录实测结果。

当前根据用户最新状态，Qwen 服务尚未 ready，因此本阶段完成后建议下一步为“增强专家笔记模板”。

## 测试与验证策略

这是 docs-only 阶段，不新增 runtime tests。

实现后运行：

```powershell
git diff --check
python -m unittest discover
```

文档自检：

- 扫描目标文档，确认没有未完成占位词。
- 检查 runbook 明确写出服务未 ready 前不执行真实调用。
- 检查 runbook 没有把 Qwen 服务描述为当前已可用。
- 检查 health、adapter build、artifact、manifest、visual content、failures、completion criteria 均存在。
- 检查 `docs/60_operations/README.md` 和 `docs/00_project/task-board.md` 的链接正确。

## 验收口径

本阶段完成后应满足：

- `docs/60_operations/qwen-vision-integration.md` 存在。
- Runbook 明确依赖服务组 ready 通知，不要求当前执行。
- Runbook 记录当前已知 endpoint、auth、timeout、prompt profile 和 pending performance baseline。
- Runbook 给出 health check 命令和 expected response。
- Runbook 给出 vBook build + `tools/vision_qwen_adapter.py` 命令。
- Runbook 给出 artifact、manifest 和 visual content 检查清单。
- Runbook 给出常见失败与排查路径。
- Runbook 明确 adapter 成功不等于最终视觉质量达标。
- Operations README 指向新 runbook。
- Task board 反映 Qwen 联调 runbook 已完成，并给出新的下一步推荐。
- 不访问网络。
- 不新增依赖。
- 不改变 runtime code。
- `python -m unittest discover` 通过。

## 风险与处理

- 风险：读者误以为现在必须调用 `192.168.0.33:8866`。
  - 处理：ready 前检查写在前面，并明确服务未 ready 时停止。
- 风险：endpoint 或 auth 后续变化。
  - 处理：runbook 标注以服务组最新回复为准，并链接 `integration-response.md`。
- 风险：adapter 成功被误解为模型质量合格。
  - 处理：visual content checks 明确是 smoke sanity check，不是最终质量评分。
- 风险：真实服务 failure shape 和文档不完全一致。
  - 处理：runbook 记录 raw response、frame id、prompt profile 作为服务组排查材料。

## 后续工作

- 用户确认本设计后，编写 implementation plan。
- 按 plan 新增 `docs/60_operations/qwen-vision-integration.md`。
- Qwen 服务部署完成后，按 runbook 执行真实联调，并更新 task board 的 blocker 状态。
- 如果真实联调暴露 adapter 缺口，再单独设计代码变更。
