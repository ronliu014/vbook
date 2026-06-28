# Project Task Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a stable project task board and link it from the root and project documentation entry points so users can quickly see current phase, blockers, available work, next recommendation, and verification status.

**Architecture:** Keep the task board as a human-maintained Markdown document under `docs/00_project/`, where project-level status and terminology already live. `status.md` remains the narrative current-state page, while `task-board.md` becomes the operational view for blockers, ready work, and next action; entry documents link to both instead of duplicating the board.

**Tech Stack:** Markdown documentation, existing numbered docs hierarchy, Git diff checks, `unittest` full-suite verification.

---

## File Structure

- Create: `docs/00_project/task-board.md`
  - Operational project board with current phase, stage summary, blockers, ready tasks, recent completions, next recommendation, verification snapshot, communication links, and update rules.
- Modify: `README.md`
  - Root documentation entry links to the new task board from the project status section and orientation sentence.
- Modify: `docs/README.md`
  - Fast reading path includes the task board immediately after current status.
- Modify: `docs/00_project/README.md`
  - Project-layer read-first list includes the task board.
- Modify: `docs/00_project/status.md`
  - Narrative status page points readers to the operational board and removes the obsolete “status dashboard” next-work wording.

No runtime source, CLI behavior, pipeline output, model integration, Qwen service call, LLM service call, or test fixture is included.

---

## Task 1: Add the Project Task Board

**Files:**
- Create: `docs/00_project/task-board.md`

- [ ] **Step 1: Create the board document**

Create `docs/00_project/task-board.md` with:

```markdown
# Project Task Board

Last updated: 2026-06-28

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
| Documentation foundation | `Partial` | 文档分层、术语库、状态页、reference 文档已经建立；任务看板是当前补齐项。 | 完成任务看板后推进 smoke runbook。 |
| Local MVP pipeline | `Done` | CLI 可从 video + transcript 生成 manifest、note、vision、fusion artifacts。 | 用 smoke runbook 固化可重复验收路径。 |
| Vision integration boundary | `Partial` | `placeholder`、`manual-json`、`external-command`、`tools/vision_qwen_adapter.py` 已具备边界。 | Qwen 服务 ready 后执行真实 health/analyze-frame smoke。 |
| LLM fusion boundary | `Partial` | `--llm-fusion-command`、stub、request/response parser、contract samples、checker 已具备。 | 真实 LLM/Qwen 文本服务 ready 后做联调 smoke。 |
| Expert note export | `Partial` | `note.md` 已支持第一版 section-based expert-note 模板。 | 增加 review questions、glossary、learning objectives。 |
| Batch workflow | `Partial` | `build-batch` 已有基础，可按 vtext-compatible 输入批量生成 lesson outputs。 | 补批处理 runbook、失败报告和输出检查。 |
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
| 完善本地 smoke test runbook | `Ready` | 文档能串起 CLI check、stub、sample、checker、manifest 和 note 输出检查。 |
| 编写 Qwen 视觉服务上线后的联调 runbook | `Ready` | 文档说明服务 ready 后如何设置 endpoint、运行 adapter、检查成功和失败输出。 |
| 增强专家笔记模板 | `Ready` | `note.md` 增加 review questions、glossary、learning objectives 的稳定结构。 |
| 完善 batch workflow 说明 | `Ready` | 文档说明输入目录、输出目录、失败报告、manifest 检查和重跑策略。 |
| 扩展 pipeline stage documents | `Ready` | `docs/30_pipeline/` 下关键阶段拥有输入、输出、状态、测试和限制说明。 |

## 最近完成

| Work | Status | 说明 |
| --- | --- | --- |
| LLM fusion contract samples and checker | `Done` | 外部服务组可用样例 request/response 和 `tools/check_llm_fusion_contract.py` 自测 contract。 |
| LLM fusion smoke command | `Done` | `tools/llm_fusion_stub.py` 可在无真实模型时跑通 LLM fusion external-command 闭环。 |
| Expert note Markdown template | `Done` | `note.md` 支持第一版 section-based 专家笔记结构。 |
| Qwen Vision adapter boundary | `Done` | `tools/vision_qwen_adapter.py` 可通过 `external-command` 调用兼容 HTTP 服务。 |
| External vision backend | `Done` | vBook core 可把 frame input JSON 交给用户命令，并复用 manual-json 校验路径。 |

## 下一步推荐任务

推荐下一步：完善本地 smoke test runbook。

理由：

- 不依赖真实 Qwen 服务部署。
- 能把已有 CLI、stub、sample、checker、manifest、note 输出串成固定验收路径。
- 能降低后续真实 Qwen 视觉服务和 LLM/Qwen 文本服务上线后的联调成本。

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
```

- [ ] **Step 2: Inspect the board for false completion claims**

Run:

```powershell
rg -n "最终|已完成|Done|Blocked|Partial|Ready|Planned|Qwen|LLM" docs/00_project/task-board.md
```

Expected: output includes the status table and blocker sections. Confirm manually that:

- Qwen live smoke is described as blocked.
- LLM live model quality is described as blocked or partial.
- Local MVP pipeline is the only pipeline area described as done.
- Expert note export and batch workflow are described as partial.

Do not commit yet.

---

## Task 2: Link the Board from Documentation Entrypoints

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/00_project/README.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Update the root README orientation sentence**

In `README.md`, replace:

```markdown
[`docs/00_project/glossary.md`](docs/00_project/glossary.md), and
[`docs/00_project/status.md`](docs/00_project/status.md). The original product
```

with:

```markdown
[`docs/00_project/glossary.md`](docs/00_project/glossary.md),
[`docs/00_project/status.md`](docs/00_project/status.md), and
[`docs/00_project/task-board.md`](docs/00_project/task-board.md). The original product
```

- [ ] **Step 2: Update the root README project status section**

In `README.md`, replace:

```markdown
Some stages are still placeholders or partial foundations. See
[`docs/00_project/status.md`](docs/00_project/status.md) for the current project
dashboard.
```

with:

```markdown
Some stages are still placeholders or partial foundations. See
[`docs/00_project/status.md`](docs/00_project/status.md) for the current project
state and [`docs/00_project/task-board.md`](docs/00_project/task-board.md) for
the operational task board and next recommended work.
```

- [ ] **Step 3: Update `docs/README.md` fast reading path**

In `docs/README.md`, replace:

```markdown
3. [00_project/status.md](./00_project/status.md)
4. [00_project/roadmap.md](./00_project/roadmap.md)
```

with:

```markdown
3. [00_project/status.md](./00_project/status.md)
4. [00_project/task-board.md](./00_project/task-board.md)
5. [00_project/roadmap.md](./00_project/roadmap.md)
```

In the development reading path, replace:

```markdown
2. [00_project/status.md](./00_project/status.md)
3. [30_pipeline/README.md](./30_pipeline/README.md)
```

with:

```markdown
2. [00_project/status.md](./00_project/status.md)
3. [00_project/task-board.md](./00_project/task-board.md)
4. [30_pipeline/README.md](./30_pipeline/README.md)
```

- [ ] **Step 4: Update `docs/00_project/README.md` read-first list**

In `docs/00_project/README.md`, replace:

```markdown
3. [status.md](./status.md)
4. [scope.md](./scope.md)
5. [roadmap.md](./roadmap.md)
```

with:

```markdown
3. [status.md](./status.md)
4. [task-board.md](./task-board.md)
5. [scope.md](./scope.md)
6. [roadmap.md](./roadmap.md)
```

- [ ] **Step 5: Link from `status.md` to the board**

In `docs/00_project/status.md`, after the `Current Phase` paragraph ending with:

```markdown
are not complete yet.
```

add:

```markdown
For the operational task board, current blockers, and next recommended work,
see [task-board.md](./task-board.md).
```

- [ ] **Step 6: Remove obsolete dashboard wording from next work**

In `docs/00_project/status.md`, replace:

```markdown
1. Finish the documentation foundation: glossary, status dashboard, and layer
   indexes.
2. Decide whether the next product milestone is real visual analysis
   integration or batch input workflow.
```

with:

```markdown
1. Finish the documentation foundation by adding the operational task board and
   keeping layer indexes current.
2. Complete a local smoke-test runbook that ties together the current CLI,
   stubs, samples, checker, manifest, and note output.
```

- [ ] **Step 7: Run link and wording checks**

Run:

```powershell
rg -n "task-board.md|task board|任务看板" README.md docs/README.md docs/00_project/README.md docs/00_project/status.md docs/00_project/task-board.md
```

Expected: output shows links or board wording in all five files.

Run:

```powershell
rg -n "status dashboard" README.md docs/README.md docs/00_project/README.md docs/00_project/status.md docs/00_project/task-board.md
```

Expected: exit code 1 with no matches.

Do not commit yet.

---

## Task 3: Verify and Commit the Documentation Update

**Files:**
- Create: `docs/00_project/task-board.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/00_project/README.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Run Markdown placeholder scan**

Run:

```powershell
$placeholderPattern = ('T' + 'BD') + '|待' + '定|占位' + '未完成|' + ('fill' + ' in details') + '|' + ('implement' + ' later')
rg -n $placeholderPattern README.md docs/README.md docs/00_project/README.md docs/00_project/status.md docs/00_project/task-board.md
```

Expected: exit code 1 with no matches.

- [ ] **Step 2: Run whitespace diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 3: Run full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits 0 with:

```text
OK
```

The test count should be `129` unless unrelated tests were added after this plan was written. If the test count differs but the suite exits 0, update `docs/00_project/status.md` and `docs/00_project/task-board.md` verification snapshots to the exact reported count before committing.

- [ ] **Step 4: Inspect changed files**

Run:

```powershell
git diff -- README.md docs/README.md docs/00_project/README.md docs/00_project/status.md docs/00_project/task-board.md
```

Expected manual checks:

- The root README links to both `status.md` and `task-board.md`.
- `docs/README.md` includes `task-board.md` in both reading paths.
- `docs/00_project/README.md` includes `task-board.md`.
- `status.md` points to `task-board.md`.
- `task-board.md` describes Qwen and real LLM service integration as blocked or partial, not final.

- [ ] **Step 5: Commit the task board**

Run:

```powershell
git add README.md docs/README.md docs/00_project/README.md docs/00_project/status.md docs/00_project/task-board.md
git commit -m "Add project task board"
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
- `git log --oneline -1` shows `Add project task board`.

---

## Self-Review

Spec coverage:

- `docs/00_project/task-board.md` creation is covered by Task 1.
- Current phase, stage summary, blockers, ready tasks, recent completions, next recommendation, verification snapshot, communication links, and update rules are all included in Task 1 exact content.
- Root `README.md`, `docs/README.md`, and `docs/00_project/status.md` links are covered by Task 2.
- `docs/00_project/README.md` is included as a layer-index consistency update.
- Docs-only verification, placeholder scan, `git diff --check`, full suite, commit, push, and remote alignment are covered by Tasks 3-4.
- No runtime code, service call, dependency, Qwen smoke, LLM smoke, issue tracker, or generated task data is included.

Placeholder scan:

- The plan avoids unfinished placeholder markers in content to be written.
- The only scan patterns are constructed in commands to avoid matching the plan itself.
- Every file edit step includes exact replacement text or complete new file content.

Type and naming consistency:

- The board path is consistently `docs/00_project/task-board.md`.
- Relative links from `docs/00_project/task-board.md` use `./`, `../70_progress/`, `../80_superpowers/`, and `../90_reference/`.
- Status labels are consistently `Done`, `Ready`, `Partial`, `Blocked`, and `Planned`.
- Verification snapshot matches the current project status expectation of `Ran 129 tests` and `OK`, with an explicit update rule if the count changes.
