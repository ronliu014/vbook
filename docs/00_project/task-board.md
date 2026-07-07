# Project Task Board

Last updated: 2026-07-07

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

当前主线没有偏离：项目正在把“视频课程自动分析成图文证据笔记”的本地闭环做稳。Qwen Vision Service 侧已回复服务部署与契约对齐信息，vBook 机器已验证 `/health` 可达，并且真实 adapter build smoke 已通过。用户已确认 vBook 作为总编排方，vtext 作为文本处理模块，vision 作为视觉辅助模块。真实 LLM/Qwen 文本综合服务仍待接入。下一步是先固化跨项目 request/response 协调协议，再推进 vtext 接入与 vault enhancement preview。

## 阶段总览

| Area | Status | 当前说明 | 下一步 |
| --- | --- | --- | --- |
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、任务看板、reference 文档、本地 smoke runbook、Qwen 联调 runbook 和 pipeline stage docs 已经建立。 | 固化真实 smoke fixture 要求和验收记录模板。 |
| Local MVP pipeline | `Done` | CLI 可从 video + transcript 生成 manifest、note、vision、fusion artifacts；本地 smoke runbook 已固化可重复验收路径；Qwen Vision real adapter smoke 已跑通。 | 用更真实 transcript 复测并扩大到更多课程样例。 |
| Vision integration boundary | `Partial` | `placeholder`、`manual-json`、`external-command`、`tools/vision_qwen_adapter.py` 和 Qwen 联调 runbook 已具备边界；服务方已确认 Qwen Vision Service 契约与部署信息；vBook 侧 `/health` 与 adapter build smoke 已通过。 | 固化真实样例验收，并评估抽帧频率、耗时和质量。 |
| LLM fusion boundary | `Partial` | `--llm-fusion-command`、stub、request/response parser、contract samples、checker 已具备。 | 真实 LLM/Qwen 文本服务 ready 后做联调 smoke。 |
| Expert note export | `Partial` | `note.md` 已支持增强 section-based expert-note 模板，包含学习目标、回看索引、复习问题和标签索引。 | 后续接入真实 glossary 定义、多格式导出和更高质量 LLM synthesis。 |
| Batch workflow | `Partial` | `build-batch` 已有基础，batch processing runbook 已说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 | 后续根据真实课程批量运行反馈设计 rerun、并发和真实服务参数透传。 |
| Cross-project coordination | `Ready` | vBook 已新增 vBook/vtext/vision docs request-response 通知和 vBook-to-vtext text integration request；vtext 已回复并提供 `--bundle vbook`。 | 开始消费 vtext bundle，并继续等待 vision 文档对齐。 |
| Vault enhancement preview | `Partial` | 已新增 `vault-preview` CLI，可读取现有 vault note 与 vBook lesson output，生成 `enhancement.md`、图片和 preview manifest，不写回 `F:\vault`；已用现有 Qwen smoke output 跑通真实 vault note preview。 | 用真实 transcript 重新生成 lesson output，再审查 preview 内容质量。 |
| Server/runtime | `Planned` | `vbook_server` 仍是未来边界，没有服务运行时。 | 本地 pipeline 稳定后再设计。 |

## 当前阻塞项

| Blocker | Status | 影响 | 当前处理 |
| --- | --- | --- | --- |
| 真实 LLM/Qwen 文本综合服务尚未接入 | `Blocked` | 不能验证最终模型综合笔记质量。 | 使用 stub、external command contract 和 checker 推进接口准备。 |
| 缺少可长期保留的真实 MP4 + transcript smoke fixture | `Blocked` | 端到端真实样例验收还不能纳入 repo 固定流程。 | 先完善本地 smoke runbook，明确 fixture 要求。 |

## 当前可推进的任务

| Task | Status | 验收口径 |
| --- | --- | --- |
| 完善本地 smoke test runbook | `Done` | [smoke-tests.md](../60_operations/smoke-tests.md) 已串起 CLI check、stub、sample、checker、manifest 和 note 输出检查。 |
| 编写 Qwen 视觉服务上线后的联调 runbook | `Done` | [qwen-vision-integration.md](../60_operations/qwen-vision-integration.md) 已说明服务 ready 后如何设置 endpoint、运行 adapter、检查成功和失败输出。 |
| 增强专家笔记模板 | `Done` | `note.md` 已增加学习目标、回看索引、复习问题和标签索引；内容来自现有 section 数据和固定模板。 |
| 完善 batch workflow 说明 | `Done` | [batch-processing.md](../60_operations/batch-processing.md) 已说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 |
| 扩展 pipeline stage documents | `Done` | `docs/30_pipeline/` 下关键阶段已有输入、输出、状态、测试和限制说明。 |
| 执行 Qwen Vision adapter build smoke | `Done` | 2026-07-07 使用 `三分钟学会选短线个股.mp4` + smoke-only transcript 跑通 external-command build，生成 2 条真实 Qwen vision analysis，manifest 中 `vision_analysis == done`。 |
| 固化 vBook/vtext/vision 协调通知 | `Done` | [cross-project-coordination-notice.md](../90_reference/cross-project-coordination-notice.md) 已提出 docs 分层、request/response 文件、vtext 输出契约、vision 响应位置和 vault preview-first 路线。 |
| 编写 vtext integration request | `Done` | [vbook-text-integration-request.md](../90_reference/vbook-text-integration-request.md) 已定义 vBook 期望的单课 CLI、输出 bundle、manifest、batch manifest 和 response 内容。 |
| 接收 vtext integration response | `Done` | vtext 已在 `E:\projects\my_app\vtext\docs\90_reference\vbook-text-integration-response.md` 回复，并在 App 环境 CLI 中暴露 `--bundle vbook`。 |
| 编写 vault enhancement preview 实施计划 | `Done` | [2026-07-07-vault-enhancement-preview.md](../80_superpowers/plans/2026-07-07-vault-enhancement-preview.md) 已拆分 loader、renderer、package writer、CLI、runbook 和真实 fixture smoke。 |
| 实现 vault-preview CLI | `Done` | `python -m vbook_client vault-preview` 已可生成 preview package；聚焦测试覆盖 loader、renderer、图片复制、manifest 和 CLI。 |
| 执行 vault-preview smoke | `Done` | 使用现有 vault note + `outputs/qwen-vision-smoke/lesson` 生成 preview package，包含 `enhancement.md`、2 张图片和 manifest；`F:\vault` 未出现新增修改。 |

## 最近完成

| Work | Status | 说明 |
| --- | --- | --- |
| Qwen Vision real adapter smoke | `Done` | 2026-07-07 从 vBook workspace 调用 `192.168.0.33:8866/analyze-frame` 成功；输出在 `outputs/qwen-vision-smoke/lesson/`，2 帧均有贴合画面的 OCR/description，模型 `qwen3-vl:8b`。 |
| Cross-project coordination notice | `Done` | 2026-07-07 新增 vBook/vtext/vision 协调通知，规定跨项目通过 docs request/response、runbook、progress log 和稳定 artifact contract 协作。 |
| vBook-to-vtext integration request | `Done` | 2026-07-07 新增 vtext 文本模块接入请求，要求 vtext 回复 CLI、输出文件、manifest、失败模型、batch 合约和性能限制。 |
| vtext integration response | `Done` | 2026-07-07 vtext 接受 CLI/artifact contract 边界，并提供首版单课 `--bundle vbook` 输出合约。 |
| Vault enhancement preview plan | `Done` | 2026-07-07 新增 preview-only 实施计划，先消费现有 vBook lesson output 与 vault note，输出预览包，不直接修改知识库。 |
| Vault enhancement preview CLI | `Done` | 2026-07-07 新增 preview-only 导出层和 `vault-preview` 命令，输出 `enhancement.md`、`images/`、`manifest.json`。 |
| Vault enhancement preview smoke | `Done` | 2026-07-07 preview 输出到 `outputs/vault-enhancement-preview/韩珂龙头班：基础篇/如何高效选股，构建自己的短线股票池/`；因 lesson output 使用 smoke-only transcript，内容质量仍需真实 transcript 复测。 |
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

推荐下一步：用 vtext `--bundle vbook` 生成真实 transcript bundle，重跑 Qwen Vision lesson output，并重新生成 `vault-preview`。

理由：

- 用户已确认 vBook 主导、vtext 作为文本模块、vision 作为视觉模块的方向。
- vtext 已回复并提供 `--bundle vbook`，vBook 可以开始消费真实 transcript bundle。
- preview-only CLI 和真实 vault note smoke 已经跑通，机制有效。
- 当前 preview 使用的是 smoke-only transcript，增强段内容不能作为最终质量评估。
- `F:\vault\20_Learning\投资训练营` 已有 vtext 产出的高质量纯文本笔记，适合直接作为图文增强对象。
- 直接写回 vault 风险较高，应该先产出 `outputs/vault-enhancement-preview/.../enhancement.md`、图片和 manifest，让效果可审查。
- Qwen Vision Service blocker 已解除，真实 adapter build smoke 已证明 vBook 到 `/analyze-frame` 的链路可用。

## 验证快照

Latest full suite run after vault enhancement preview integration:

```powershell
conda run -n App python -m unittest discover
```

Current result:

```text
Ran 133 tests
OK
```

## 沟通与交接链接

- [qwen-vision-service-requirements.md](../90_reference/qwen-vision-service-requirements.md)
- [qwen-vision-service-integration-request.md](../90_reference/qwen-vision-service-integration-request.md)
- [integration-response.md](../90_reference/integration-response.md)
- [cross-project-coordination-notice.md](../90_reference/cross-project-coordination-notice.md)
- [vbook-text-integration-request.md](../90_reference/vbook-text-integration-request.md)
- [vtext-integration-response-summary.md](../90_reference/vtext-integration-response-summary.md)
- [vault-enhancement-preview.md](../60_operations/vault-enhancement-preview.md)
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
