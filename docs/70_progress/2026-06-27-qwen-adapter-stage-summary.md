# 2026-06-27 Qwen Adapter 阶段总结

## 阶段结论

本阶段完成的是 vBook 侧的真实视觉服务接入桥，而不是内置 Qwen 模型或新增核心
provider backend。

当前 vBook 已经可以通过现有 `external-command` 机制调用
`tools/vision_qwen_adapter.py`，再由 adapter 调用外部 Qwen Vision Service 的
`POST /analyze-frame` 接口。这样可以在不绑定 Qwen SDK、不引入模型运行时、不破坏
vBook core provider-neutral 边界的前提下，为后续真实视觉理解联调做好准备。

当前成果已合并到本地 `main`，合并后全量测试通过。

## 当前主线是否偏离

没有偏离。

本阶段一直围绕同一条主线推进：

```text
vBook build
  -> external-command backend
    -> tools/vision_qwen_adapter.py
      -> POST /analyze-frame
        -> external Qwen Vision Service
```

关键边界保持不变：

- vBook core 不依赖 Qwen、OpenAI、PaddleOCR、Tesseract 或其他模型 SDK。
- vBook core 没有新增 `qwen-service` backend。
- Qwen 仍是外部服务，vBook 侧只维护一个 adapter。
- 最终进入 vBook pipeline 的视觉结果仍通过 manual-json 兼容结构归一化。
- `manifest.json`、`vision/analysis.json`、`note.md` 仍是当前主要输出契约。

## 已完成工作

### 文档与需求

- 建立并使用分层文档目录：
  - `00_project`
  - `10_product`
  - `20_architecture`
  - `30_pipeline`
  - `40_development`
  - `50_modules`
  - `60_operations`
  - `70_progress`
  - `80_superpowers`
  - `90_reference`
- 增加根文档入口：`docs/README.md`。
- 增加项目状态说明：`docs/00_project/status.md`。
- 增加术语库：`docs/00_project/glossary.md`。
- 完成 Qwen Vision Service 需求书：
  - `docs/90_reference/qwen-vision-service-requirements.md`
- 完成 Qwen adapter 设计与实现计划：
  - `docs/80_superpowers/specs/2026-06-27-qwen-vision-adapter-design.md`
  - `docs/80_superpowers/plans/2026-06-27-qwen-vision-adapter.md`
- 增加 Qwen adapter smoke 文档：
  - `docs/60_operations/smoke-tests.md`

### 代码与测试

- 新增 Qwen adapter：
  - `tools/vision_qwen_adapter.py`
- 新增 adapter 测试：
  - `tests/test_tools/test_vision_qwen_adapter.py`
- adapter 支持：
  - 读取 vBook `frames.json`。
  - 将本地 JPEG/PNG frame 转为 base64 Qwen request。
  - 调用外部 `POST /analyze-frame`。
  - 处理可选 bearer token。
  - 将 Qwen response 转为 manual-json 兼容 output。
  - 将服务调试字段保存在 `structured_observations.qwen_service`。
- adapter 契约硬化：
  - `ocr_text` 必须是 string。
  - `vision_description` 必须是 string。
  - `confidence` 必须是 `null` 或有限数字。
  - `confidence` 数值范围必须为 `0.0` 到 `1.0`。
  - adapter 失败运行会清理旧 output，避免消费 stale `analysis.json`。
  - 输出写入使用 sibling temp 文件再 replace，减少 partial output 风险。
  - 输入、响应、请求、输出均避免非标准 JSON 数值：
    - 拒绝 `NaN`
    - 拒绝 `Infinity`
    - 拒绝 `-Infinity`
    - 拒绝解析后成为非有限数字的值，例如 `1e999`
  - 请求和输出序列化使用 `allow_nan=False`。

### Git 状态

本阶段实现已合并回本地 `main`。

当前本地 `main` 最新相关提交：

```text
8e6fff1 Reject nonstandard Qwen adapter JSON
7f298fc Harden Qwen adapter response validation
1105b8b Update Qwen adapter verification snapshot
2492270 Document Qwen adapter smoke workflow
26248f3 Validate required Qwen confidence field
7a87f9a Add Qwen vision adapter
8851d16 Plan Qwen adapter implementation
36fd08f Document Qwen vision adapter design
```

当前本地 `main` 仍领先 `origin/main`，需要后续 push 到远端。

## 验证结果

合并到 `main` 后，已运行：

```powershell
python -m unittest discover
```

结果：

```text
Ran 93 tests
OK
```

在 adapter 分支开发过程中也验证过：

```powershell
python -m unittest tests.test_tools.test_vision_qwen_adapter
python -m unittest tests.test_tools.test_vision_stub tests.test_client.test_manifest_cli
python -m unittest discover
```

最终结果均通过。

## 当前仍未完成的事情

### 真实服务联调尚未开始

Qwen Vision Service 由外部项目组推进。vBook 侧 adapter 已准备好，但还没有拿到真实
endpoint 做联调。

因此当前只能说明：

- vBook 侧调用边界已实现。
- fake HTTP server 测试已覆盖 adapter contract。
- `external-command` build 集成测试已通过。

还不能说明：

- 真实 Qwen 服务已经可用。
- 真实服务输出质量满足课程笔记需要。
- 真实服务在批量课程场景下具备稳定性。

### Fusion 仍是下一阶段瓶颈

当前视觉输入链路已经具备真实服务接入能力，知识融合也已经从纯 placeholder
推进到 deterministic evidence draft：

- fusion sections 会吸收 transcript、OCR、视觉描述、结构化观察和图片引用，并对相邻
  同主题或共享视觉证据的片段做保守合并。
- `note.md` 能展示 evidence section、key points、tags 和图片引用。
- 这仍然不是最终专家级课程笔记，后续还需要 LLM 知识综合和最终笔记结构设计。

## 后续工作建议

### P0: 推送当前 main

当前本地 `main` 领先 `origin/main`，建议先 push，避免成果只留在本机：

```powershell
git push origin main
```

### P1: 等待 Qwen 服务组提供联调信息

服务组已通过 `docs/90_reference/integration-response.md` 回复第一轮联调信息：

- Base URL: `http://192.168.0.33:8866`
- `POST /analyze-frame`: `http://192.168.0.33:8866/analyze-frame`
- `GET /health`: `http://192.168.0.33:8866/health`
- 当前可信内网 HTTP，无认证。
- 支持 `vbook_visual_analysis_v1`、JPEG、PNG。
- decoded image size 上限 10 MB，per-frame timeout 120 秒，建议并发 1。
- success response、error response 和 strict JSON 约束已对齐。

仍待服务组部署后补充：

- `GET /health` 实测结果。
- slide / K-line 图片自测结果。
- 模型 warmup、平均延迟和 p95 延迟。

对接需求、回复模板和服务组回复见：

- `docs/90_reference/qwen-vision-service-integration-request.md`
- `docs/90_reference/integration-response.md`

### P2: 跑真实 smoke

拿到 endpoint 后，先跑三个层次：

1. `GET /health`
2. 单帧 `POST /analyze-frame`
3. vBook `build --vision-backend external-command`

目标产物：

- `vision/external/frames.json`
- `vision/external/analysis.json`
- `vision/analysis.json`
- `manifest.json`
- `note.md`

### P3: 根据真实失败模式决定 adapter 是否生产化

当前 adapter 是第一阶段 fail-fast 策略。真实联调后再决定是否需要：

- retry
- partial success
- image byte limit
- request delay
- concurrency limit
- richer error manifest

不建议在没有真实失败样本前提前加入这些参数。

### P4: 推进 fusion / note 质量

如果 Qwen 服务部署还需要时间，可以继续推进：

- LLM-ready fusion prompt 和 response parser。
- `note.md` 的最终专家笔记结构。
- 用 `manual-json` 或 fake Qwen output 继续验证融合逻辑。

## 当前阶段交接句

如果需要一句话同步给其他成员，可以这样描述：

```text
vBook 侧已完成 Qwen Vision Service adapter，并已合并到本地 main。
adapter 通过 existing external-command 调用外部 POST /analyze-frame 服务，不引入模型依赖，
并已完成 response validation、strict JSON、防 stale output 等契约硬化。
下一步等待 Qwen 服务组提供 endpoint/token/health/limits 后进行真实 smoke 联调。
```
