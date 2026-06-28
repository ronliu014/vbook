# Project Task Board Design

## 背景

vBook 已经建立了分层文档结构，也有 `docs/00_project/status.md` 用来说明当前项目状态。但随着本地
MVP pipeline、Qwen 视觉服务边界、LLM fusion 外部命令、contract checker、专家笔记模板等工作陆续完成，
单个状态文档开始承担过多职责：

- 它既要说明项目当前阶段；
- 又要列出已完成能力；
- 又要解释 placeholder、partial、blocked 的区别；
- 还要回答“等待 Qwen 服务期间还能做什么”。

用户已经明确提出：项目需要一个能让非实现人员快速理解进度和剩余工作的入口，否则只能依赖聊天记录和零散
progress log，容易出现“两眼一抹黑”的情况。

本阶段要设计一个稳定的项目任务看板，让项目当前阶段、阻塞项、可推进任务和最新验证结果可以从固定入口读取。

## 目标

- 新增一个面向项目管理和协作的任务看板文档。
- 让用户能快速判断 vBook 当前是否偏离主线。
- 明确区分已完成能力、可用但非最终能力、被外部服务阻塞的能力、可立即推进的任务。
- 保留 `docs/00_project/status.md` 作为叙述型状态说明，不把它改成过长 backlog。
- 从根目录 `README.md`、`docs/README.md` 和 `docs/00_project/status.md` 链接到任务看板。
- 使用简体中文解释业务和协作语义，保留英文路径、命令、状态标签和代码术语。

## 非目标

本阶段不做：

- 不引入任务管理系统、Issue tracker 或看板生成工具。
- 不新增 JSON/YAML 结构化任务数据。
- 不改 runtime code、CLI、pipeline、测试逻辑或输出 contract。
- 不调用真实 Qwen 视觉服务。
- 不调用真实 LLM/Qwen 文本综合服务。
- 不重写现有 roadmap、progress log 或 implementation plan。
- 不把所有历史计划迁移成任务条目。

## 方案选择

### 方案 A：独立任务看板 + 状态页和入口链接

新增 `docs/00_project/task-board.md`。`status.md` 继续作为当前状态叙述文档，看板负责更操作化的问题：

- 当前阶段；
- 阶段总览；
- 当前阻塞项；
- 等待服务期间可推进的任务；
- 最近完成；
- 下一步推荐；
- 验证快照；
- 沟通与交接链接；
- 更新规则。

优点：

- 阅读入口明确。
- 不让 `status.md` 继续膨胀。
- 不需要额外工具或依赖。
- 后续每个阶段都可以稳定更新同一文件。

缺点：

- 多一个需要维护的文档。

### 方案 B：全部合并进 `status.md`

把任务看板、阻塞项和待办项都放进现有 `docs/00_project/status.md`。

优点：

- 文件数量少。
- 不需要新增入口文件。

缺点：

- `status.md` 会同时承担状态总结、路线图、backlog、验收快照四类职责。
- 长期会降低可读性，和“快速看清当前阶段”的目标冲突。

### 方案 C：结构化任务数据 + 生成 Markdown

新增 `docs/00_project/task-board.json` 或 YAML，再由脚本生成 Markdown 看板。

优点：

- 后续可以自动化检查和生成。
- 任务状态可以被机器读取。

缺点：

- 当前阶段过重。
- 会引入生成流程和维护规则，而项目现在更需要稳定的人类阅读入口。

## 决策

采用方案 A：独立任务看板 + 状态页和入口链接。

原因：

- 它直接解决用户当前的进度透明度问题。
- 它不依赖 Qwen 服务部署，也不改变任何代码行为。
- 它保持 `status.md` 简洁，让任务级信息沉到专门的看板。
- 它符合当前文档分层：`00_project/` 负责项目定位、术语、范围、路线图和状态。

## 文件结构

新增：

```text
docs/00_project/task-board.md
```

修改：

```text
README.md
docs/README.md
docs/00_project/status.md
```

不修改：

```text
docs/70_progress/
docs/80_superpowers/plans/
docs/90_reference/
runtime code
tests
```

## 任务看板结构

`docs/00_project/task-board.md` 使用固定结构，方便后续阶段更新。

```text
# Project Task Board

Last updated: 2026-06-28

## 如何阅读这个看板
## 当前阶段
## 阶段总览
## 当前阻塞项
## 等待 Qwen 服务期间可推进的任务
## 最近完成
## 下一步推荐任务
## 验证快照
## 沟通与交接链接
## 更新规则
```

### `如何阅读这个看板`

说明看板的用途和边界：

- 这是项目操作视角，不替代 roadmap、status、progress log。
- `status.md` 负责叙述当前状态。
- `roadmap.md` 负责阶段方向。
- `70_progress/` 负责 dated progress。
- 本看板负责当前阶段、阻塞项、可做任务和下一步建议。

### `当前阶段`

用短段落说明当前项目阶段：

- vBook 处于 local MVP pipeline 阶段；
- 本地 pipeline 可以从视频和时间戳 transcript 产出 `manifest.json`、`note.md`、vision/fusion artifacts；
- Qwen 视觉服务尚未部署完成，真实视觉 smoke 暂不执行；
- 等待服务期间继续推进文档、runbook、输出体验和本地 contract 工作。

### `阶段总览`

使用表格列出主要工作域和状态。

建议列：

| Area | Status | 当前说明 | 下一步 |
| --- | --- | --- | --- |

初始行：

- Documentation foundation
- Local MVP pipeline
- Vision integration boundary
- LLM fusion boundary
- Expert note export
- Batch workflow
- Server/runtime

### `当前阻塞项`

只记录真正阻塞下一类工作的外部条件，不把普通待办混进来。

初始阻塞项：

- Qwen Vision Service 尚未部署完成，不能执行真实 `/health` 和 `/analyze-frame` smoke。
- 真实 LLM/Qwen 文本综合服务尚未接入，只能使用 external command、stub 和 contract checker。
- 尚未提供可长期保留的真实 MP4 + transcript smoke fixture。

### `等待 Qwen 服务期间可推进的任务`

列出不依赖真实服务的任务，让项目不会因为外部服务等待而停住。

初始任务候选：

- 完善本地 smoke test runbook。
- 编写 Qwen 视觉服务上线后的联调 runbook。
- 增强专家笔记模板，例如 review questions、glossary、learning objectives。
- 完善 batch workflow 的运行说明、失败报告和输出检查。
- 扩展 `docs/30_pipeline/` 下的 stage documents。

每一项要带状态和简短验收口径，避免只写模糊标题。

### `最近完成`

记录最近几个已经提交并验证的阶段，帮助用户判断当前工作有没有偏离主线。

初始内容包括：

- LLM fusion contract samples 和 checker。
- LLM fusion smoke command。
- Expert note Markdown template。
- Qwen Vision adapter boundary。
- External vision backend。

### `下一步推荐任务`

只放一个主推任务，避免用户不知道应该选哪个。

初始建议：

- 完成项目任务看板后，优先推进 smoke test runbook。

原因：

- 它不依赖真实 Qwen 服务；
- 它能把已有 CLI、stub、sample、checker 串成可重复验收路径；
- 它能降低后续接入真实服务时的沟通成本。

### `验证快照`

记录最近一次全量测试命令和结果。

初始快照：

```powershell
python -m unittest discover
```

```text
Ran 129 tests
OK
```

看板不要求每次打开都重跑测试，但当实际完成 milestone 或测试数量变化时必须更新。

### `沟通与交接链接`

集中链接外部协作所需文档：

- `docs/90_reference/qwen-vision-service-requirements.md`
- `docs/90_reference/qwen-vision-service-integration-request.md`
- `docs/90_reference/integration-response.md`
- `docs/90_reference/llm-fusion-command-requirements.md`
- `docs/90_reference/llm-fusion-service-integration-request.md`

### `更新规则`

定义什么时候必须更新看板：

- 完成一个 milestone。
- 当前推荐任务发生变化。
- 外部服务部署状态变化。
- 新增或解除 blocker。
- 全量测试结果或测试数量变化。
- 新增重要交接文档。

定义什么时候不需要更新看板：

- 只修改实现细节但不改变项目阶段。
- 只改错别字或格式。
- 单个小测试内部重构且对外状态不变。

## 状态标签

看板使用固定状态标签，不使用自由发挥的状态词。

| Status | 含义 |
| --- | --- |
| `Done` | 已实现、已验证，并且当前可作为项目基础使用。 |
| `Ready` | 不依赖外部条件，可以立即开始推进。 |
| `Partial` | 已有可运行基础，但不是最终形态，仍有明确缺口。 |
| `Blocked` | 被外部服务、数据、权限或决策阻塞，当前不能完成真实验收。 |
| `Planned` | 已纳入计划，但不是当前立即推进项。 |

## 入口链接更新

### `README.md`

在 Project Status 段落中增加任务看板链接：

- `docs/00_project/status.md`：当前项目状态说明；
- `docs/00_project/task-board.md`：当前任务看板和下一步建议。

### `docs/README.md`

在 Fast Reading Path 中把 `task-board.md` 放在 `status.md` 后面：

```text
1. 00_project/overview.md
2. 00_project/glossary.md
3. 00_project/status.md
4. 00_project/task-board.md
5. 00_project/roadmap.md
```

### `docs/00_project/status.md`

在 Progress Log 或 Current Phase 附近增加一句：

```text
For the operational task board and next recommended work, see task-board.md.
```

同时可把 `Most Important Next Work` 中的“status dashboard”更新为任务看板已建立后的下一项。

## 测试与验证策略

这是 docs-only 阶段，不需要新增 runtime tests。

实现完成后验证：

```powershell
git diff --check
python -m unittest discover
```

文档自检：

用项目规格自检清单中的常见未完成标记扫描目标文档，确认没有真正的占位内容、矛盾描述或模糊验收项。

验收时要确认：

- `docs/00_project/task-board.md` 存在。
- 根 `README.md` 能指向任务看板。
- `docs/README.md` 的快速阅读路径包含任务看板。
- `docs/00_project/status.md` 指向任务看板。
- 看板清楚说明当前等待 Qwen 服务时还能做什么。
- 看板没有把 placeholder 或 partial 能力描述成最终完成能力。
- 看板包含最近验证快照。

## 验收口径

本阶段完成后应满足：

- 用户从根 `README.md` 两次点击以内能到达任务看板。
- 用户打开任务看板后能在一分钟内知道：
  - 当前阶段是什么；
  - 已完成什么；
  - 哪些被 Qwen 或 LLM 服务阻塞；
  - 等待服务期间还能推进什么；
  - 下一步推荐任务是什么；
  - 最近一次全量测试结果是什么。
- `status.md` 不再承担详细任务看板职责，而是链接到专门看板。
- 文档解释使用简体中文，路径、命令、状态标签保留英文。
- 不访问网络。
- 不新增依赖。
- 不改变 runtime code。

## 风险与处理

- 风险：任务看板和 `status.md` 内容重复。
  - 处理：`status.md` 保留叙述型状态；看板只保留操作视角、阻塞项、下一步和更新规则。
- 风险：看板创建后没人维护。
  - 处理：在 `更新规则` 中写明 milestone、blocker、测试快照变化时必须更新。
- 风险：看板变成长期 backlog。
  - 处理：只放当前阶段相关事项；长期方向继续放 `roadmap.md`。
- 风险：看板把外部服务未完成误写成 vBook 侧失败。
  - 处理：阻塞项要明确区分 vBook 侧边界已完成和外部服务尚未部署。

## 后续工作

- 用户确认本设计后，编写 implementation plan。
- 按 plan 新增 `docs/00_project/task-board.md` 并更新入口链接。
- 看板完成后，优先设计并推进 smoke test runbook。
- Qwen 服务部署完成后，更新看板的 blocker 和下一步推荐任务。
