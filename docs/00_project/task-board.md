# Project Task Board

Last updated: 2026-07-04

## 如何阅读这个看板

这个看板是 vBook 的当前操作视角，用来回答“现在做到哪里、什么被阻塞、还能继续推进什么、下一步最推荐做什么”。

它不替代其他项目文档：

- [status.md](./status.md) 说明当前项目状态和能力边界。
- [roadmap.md](./roadmap.md) 说明阶段方向。
- [../70_progress/](../70_progress/) 保存 dated progress log。
- [../80_superpowers/](../80_superpowers/) 保存 agent spec、plan、review 和 handoff。

状态标签固定含义：

| Status | 含义 |
| --- | --- |
| `Done` | 已实现、已验证，并且当前可作为项目基础使用。 |
| `Ready` | 不依赖外部条件，可以立即开始推进。 |
| `Partial` | 已有可运行基础，但不是最终形态，仍有明确缺口。 |
| `Blocked` | 被外部服务、数据、权限或决策阻塞，当前不能完成真实验收。 |
| `Planned` | 已纳入计划，但不是当前立即推进项。 |

## 当前阶段

vBook 处于 local MVP pipeline 阶段。本地 pipeline 已经可以从视频和时间戳 transcript 生成 `manifest.json`、`note.md`、`vision/analysis.json`、`fusion/prompt.json`、`fusion/sections.json`，并且具备 external-command 形式的视觉分析和 LLM fusion 接口边界。

当前主线没有偏离：项目正在把“视频课程自动分析成图文证据笔记”的本地闭环做稳，同时等待真实 Qwen 视觉服务和真实 LLM/Qwen 文本综合服务部署。等待服务期间，继续推进不冲突的文档入口、smoke runbook、输出体验和批处理说明。

## 阶段总览

| Area | Status | 当前说明 | 下一步 |
| --- | --- | --- | --- |
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、任务看板、reference 文档、本地 smoke runbook、Qwen 联调 runbook 和 pipeline stage docs 已经建立。 | 继续梳理真实 smoke fixture 要求。 |
| Local MVP pipeline | `Done` | CLI 可从 video + transcript 生成 manifest、note、vision、fusion artifacts；本地 smoke runbook 已固化可重复验收路径。 | 等真实服务 ready 后执行联调 smoke。 |
| Vision integration boundary | `Partial` | `placeholder`、`manual-json`、`external-command`、`tools/vision_qwen_adapter.py` 和 Qwen 联调 runbook 已具备边界。 | Qwen 服务 ready 后按 runbook 执行真实 health/analyze-frame smoke。 |
| LLM fusion boundary | `Partial` | `--llm-fusion-command`、stub、request/response parser、contract samples、checker 已具备。 | 真实 LLM/Qwen 文本服务 ready 后做联调 smoke。 |
| Expert note export | `Partial` | `note.md` 已支持增强 section-based expert-note 模板，包含学习目标、回看索引、复习问题和标签索引。 | 后续接入真实 glossary 定义、多格式导出和更高质量 LLM synthesis。 |
| Batch workflow | `Partial` | `build-batch` 已有基础，batch processing runbook 已说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 | 后续根据真实课程批量运行反馈设计 rerun、并发和真实服务参数透传。 |
| Server/runtime | `Planned` | `vbook_server` 仍是未来边界，没有服务运行时。 | 本地 pipeline 稳定后再设计。 |

## 当前阻塞项

| Blocker | Status | 影响 | 当前处理 |
| --- | --- | --- | --- |
| Qwen Vision Service 尚未部署完成 | `Blocked` | 不能执行真实 `/health` 和 `/analyze-frame` smoke，视觉智能质量无法实测。 | 保持 adapter 和需求文档 ready；等待服务组通知。 |
| 真实 LLM/Qwen 文本综合服务尚未接入 | `Blocked` | 不能验证最终模型综合笔记质量。 | 使用 stub、external command contract 和 checker 推进接口准备。 |
| 缺少可长期保留的真实 MP4 + transcript smoke fixture | `Blocked` | 端到端真实样例验收还不能纳入 repo 固定流程。 | 先完善本地 smoke runbook，明确 fixture 要求。 |

## 等待 Qwen 服务期间可推进的任务

| Task | Status | 验收口径 |
| --- | --- | --- |
| 完善本地 smoke test runbook | `Done` | [smoke-tests.md](../60_operations/smoke-tests.md) 已串起 CLI check、stub、sample、checker、manifest 和 note 输出检查。 |
| 编写 Qwen 视觉服务上线后的联调 runbook | `Done` | [qwen-vision-integration.md](../60_operations/qwen-vision-integration.md) 已说明服务 ready 后如何设置 endpoint、运行 adapter、检查成功和失败输出。 |
| 增强专家笔记模板 | `Done` | `note.md` 已增加学习目标、回看索引、复习问题和标签索引；内容来自现有 section 数据和固定模板。 |
| 完善 batch workflow 说明 | `Done` | [batch-processing.md](../60_operations/batch-processing.md) 已说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 |
| 扩展 pipeline stage documents | `Done` | `docs/30_pipeline/` 下关键阶段已有输入、输出、状态、测试和限制说明。 |

## 最近完成

| Work | Status | 说明 |
| --- | --- | --- |
| Pipeline stage documents | `Done` | `docs/30_pipeline/` 已具备 README matrix、overview 阶段链接，以及 transcript、frame、vision、timeline、fusion、note 和 manifest 阶段页。 |
| Batch processing runbook | `Done` | `docs/60_operations/batch-processing.md` 记录 `build-batch` 输入、输出、manifest、失败处理和重跑策略。 |
| Expert note enhancement | `Done` | `note.md` 新增学习目标、回看索引、复习问题和标签索引，不改变上游 schema 或外部服务 contract。 |
| Qwen Vision integration runbook | `Done` | `docs/60_operations/qwen-vision-integration.md` 记录服务 ready 后的 health、adapter、artifact、manifest 和失败排查步骤。 |
| Local smoke test runbook | `Done` | `docs/60_operations/smoke-tests.md` 覆盖 CLI readiness、placeholder build、vision stub、LLM stub、contract checker 和 batch smoke。 |
| LLM fusion contract samples and checker | `Done` | 外部服务组可用样例 request/response 和 `tools/check_llm_fusion_contract.py` 自测 contract。 |
| LLM fusion smoke command | `Done` | `tools/llm_fusion_stub.py` 可在无真实模型时跑通 LLM fusion external-command 闭环。 |
| Expert note Markdown template | `Done` | `note.md` 支持第一版 section-based 专家笔记结构。 |
| Qwen Vision adapter boundary | `Done` | `tools/vision_qwen_adapter.py` 可通过 `external-command` 调用兼容 HTTP 服务。 |
| External vision backend | `Done` | vBook core 可把 frame input JSON 交给用户命令，并复用 manual-json 校验路径。 |

## 下一步推荐任务

推荐下一步：梳理真实 smoke fixture 要求。

理由：

- Qwen 服务尚未确认部署完成，真实视觉联调仍保持 blocked。
- pipeline stage documents 已补齐，阶段边界和验收入口更清楚。
- 下一步需要明确可长期复用或可外部挂载的 MP4 + transcript 样例要求，方便服务 ready 后执行稳定验收。

## 验证快照

Latest full suite run after LLM fusion contract samples integration:

```powershell
python -m unittest discover
```

Expected current result:

```text
Ran 129 tests
OK
```

## 沟通与交接链接

- [qwen-vision-service-requirements.md](../90_reference/qwen-vision-service-requirements.md)
- [qwen-vision-service-integration-request.md](../90_reference/qwen-vision-service-integration-request.md)
- [integration-response.md](../90_reference/integration-response.md)
- [llm-fusion-command-requirements.md](../90_reference/llm-fusion-command-requirements.md)
- [llm-fusion-service-integration-request.md](../90_reference/llm-fusion-service-integration-request.md)

## 更新规则

必须更新看板的情况：

- 完成一个 milestone。
- 当前推荐任务发生变化。
- 外部服务部署状态变化。
- 新增或解除 blocker。
- 全量测试结果或测试数量变化。
- 新增重要交接文档。

不需要更新看板的情况：

- 只修改实现细节但不改变项目阶段。
- 只改错别字或格式。
- 单个小测试内部重构且对外状态不变。
