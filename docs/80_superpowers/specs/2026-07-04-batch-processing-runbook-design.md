# Batch Processing Runbook Design

## 背景

vBook 已经具备 `build-batch` 功能基础，可以从 vtext-compatible 输入目录中发现媒体文件，
匹配 `text/` 下的 transcript，为每节课执行本地 MVP pipeline，并写出批处理层面的
`batch_manifest.json`。

当前 batch 能力已有代码和测试覆盖：

- `vbook_pipeline.batch` 负责媒体发现、transcript 匹配、lesson plan 和 batch manifest 写入。
- `vbook_client.cli` 暴露 `python -m vbook_client build-batch`。
- `tests/test_pipeline/test_batch.py` 覆盖发现规则、忽略目录、嵌套路径、缺失 transcript 和
  manifest 序列化。
- `tests/test_client/test_manifest_cli.py` 覆盖成功 batch、缺失 transcript、unsupported
  transcript failure。
- `README.md` 只有一个简短命令示例。
- `docs/60_operations/smoke-tests.md` 只有 batch smoke，而不是完整 batch operations runbook。

项目任务看板当前推荐任务是“完善 batch workflow 说明”。因此本阶段不扩展 batch runtime，
只补齐运营层文档，让操作者能清楚理解输入、命令、输出、失败和重跑策略。

## 目标

- 新增一份面向操作者的 batch processing runbook。
- 如实说明当前 `build-batch` 能力，不夸大为生产级批处理系统。
- 让用户能独立完成一次本地 batch run，并知道如何检查结果。
- 解释 `batch_manifest.json` 的关键字段和状态含义。
- 说明 `missing_transcript`、`unsupported_transcript_format`、`build_failed: ...` 等失败原因。
- 给出保守的重跑策略，避免旧输出和新输出混淆。
- 把 `docs/60_operations/README.md`、`docs/00_project/task-board.md` 和
  `docs/00_project/status.md` 同步到当前状态。

## 非目标

本阶段不做：

- 不修改 `vbook_pipeline/batch.py`。
- 不修改 `vbook_client/cli.py`。
- 不新增 `--rerun-failed`、`--continue-from-manifest`、`--jobs`、`--skip-done` 等 CLI 参数。
- 不实现并发批处理。
- 不实现断点续跑或增量跳过。
- 不执行真实 Qwen Vision Service batch 性能验证。
- 不执行真实 LLM/Qwen 文本综合质量验证。
- 不加入长期保留的大视频 fixture。
- 不承诺 `.vtt` 或 `.txt` 已具备完整高质量 transcript 支持。
- 不把 README 扩写成完整操作手册。

## 方案选择

### 方案 A：新增 docs-only batch runbook

新增 `docs/60_operations/batch-processing.md`，同步 operations index 和项目状态文档。

优点：

- 与任务看板“完善 batch workflow 说明”完全匹配。
- 不触碰 runtime，风险低。
- 直接补齐用户关心的“怎么跑、怎么看、失败怎么办、怎么重跑”。
- 符合当前文档分层：runbook 放在 `docs/60_operations/`。

缺点：

- 不新增 batch runtime 能力。

### 方案 B：同时增强 `build-batch` runtime

例如新增 `--rerun-failed`、`--jobs`、基于旧 `batch_manifest.json` 的断点续跑。

优点：

- batch 使用体验上限更高。

缺点：

- 会扩大实现范围，需要重新设计和 TDD。
- 真实 Qwen 和 LLM 服务尚未 ready，过早扩展 runtime 容易设计偏离实际失败模式。

### 方案 C：只更新 README

把 batch 操作说明直接写入根目录 README。

优点：

- 改动最少。

缺点：

- README 会变臃肿。
- 不能承载失败排查、manifest 解读和重跑策略。
- 不符合已建立的 `docs/60_operations/` 分层。

## 决策

采用方案 A：新增 docs-only batch runbook。

原因：

- 当前缺口是运营说明，不是 runtime 功能。
- `build-batch` 已有测试覆盖和 smoke 入口，但缺少面向操作者的完整说明。
- 本阶段继续等待 Qwen 服务部署，不应引入真实服务依赖或 batch 并发/重跑复杂度。

## 新增文档

新增：

```text
docs/60_operations/batch-processing.md
```

定位：

- 运营层 runbook。
- 面向要批量跑一组课程的操作者。
- 解释当前本地 MVP batch workflow，而不是未来生产级 batch 系统。

## Runbook 结构

建议结构：

```markdown
# Batch Processing

## 适用范围

## 当前能力边界

## 输入目录结构

## 文件发现规则

## Transcript 匹配规则

## 运行命令

## 输出目录结构

## batch_manifest.json 解读

## 状态说明

## 输出检查清单

## 常见失败与处理

## 重跑策略

## 不覆盖的内容

## 相关文档
```

## 适用范围

Runbook 应说明它覆盖：

- 本地 `build-batch` 命令。
- vtext-compatible 输入目录。
- 本地 MVP pipeline 的 per-lesson 输出。
- `batch_manifest.json` 检查。
- 常见失败定位。
- 保守重跑策略。

Runbook 应说明它不覆盖：

- 真实 Qwen Vision Service batch 性能。
- 真实 OCR 和 multimodal 质量。
- 真实 LLM/Qwen 文本综合质量。
- 生产并发、队列、调度、断点续跑。
- 长期归档策略。

## 当前能力边界

需要如实说明：

- `build-batch` 是对已有 per-lesson `build` pipeline 的薄编排。
- 每个 lesson 使用当前本地 MVP pipeline。
- 当前默认仍是 placeholder/local intelligence 路径，除非单课 build 能力后来扩展并显式透传。
- 当前 CLI 只支持：
  - `--input`
  - `--output`
  - `--frame-interval-seconds`
  - `--alignment-window-seconds`
- 当前不支持：
  - 并发参数。
  - 只重跑失败项。
  - 从旧 manifest 自动续跑。
  - batch 级真实 Qwen adapter 参数透传。
  - batch 级 LLM fusion command 参数透传。

## 输入目录结构

说明标准 vtext-compatible layout：

```text
input/
  lesson-a.mp4
  lesson-b.mp4
  text/
    lesson-a.srt
    lesson-b.srt
```

说明嵌套 layout：

```text
input/
  course-a/
    lesson-01.mp4
    lesson-02.mp4
  text/
    course-a/
      lesson-01.srt
      lesson-02.srt
```

说明约束：

- 媒体文件位于 input root 或其子目录。
- transcript 位于 `input/text/` 下，并保持与媒体文件相同的相对目录。
- 文件 stem 必须能匹配。
- 生成输出不应放回 input 目录中被误扫；当前 discovery 会忽略名为 `outputs` 的目录，但仍建议输出到 input 外部。

## 文件发现规则

按当前代码记录支持的媒体扩展：

```text
.mp4 .mkv .avi .mov .wmv .flv .webm .mp3 .wav .m4a .aac .flac .ogg
```

记录被忽略的目录名：

```text
.git
.pytest_cache
.ruff_cache
outputs
sync
text
```

说明排序：

- discovery 输出按相对路径稳定排序。
- 嵌套路径会保留到 `lesson_id` 和 output layout。

## Transcript 匹配规则

按当前代码记录 transcript 优先级：

```text
<stem>_raw.srt
<stem>.srt
<stem>_raw.vtt
<stem>.vtt
<stem>_raw.txt
<stem>.txt
```

说明：

- 匹配目录是 `input/text/<relative_parent>/`。
- `*.srt` 是当前稳定推荐格式。
- discovery 会匹配 `.vtt` 和 `.txt`，但当前 loader 未承诺完整支持；batch 执行时可能记录
  `unsupported_transcript_format`。
- 如果找不到 transcript，该 lesson 记录为 `skipped`，原因是 `missing_transcript`。

## 运行命令

标准命令：

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\batch-run
```

带可选参数：

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\batch-run `
  --frame-interval-seconds 30 `
  --alignment-window-seconds 5
```

说明：

- 从仓库根目录执行。
- 输出目录建议每次使用新的 run path，例如 `outputs/batch-YYYYMMDD-HHMM/`。
- 命令返回 `0` 不代表每节课都成功；必须查看 `batch_manifest.json`。

## 输出目录结构

说明顶层输出：

```text
outputs/batch-run/
  batch_manifest.json
  lesson-a/
    manifest.json
    note.md
    frames/
    vision/
    fusion/
```

说明嵌套输出：

```text
outputs/batch-run/
  batch_manifest.json
  course-a/
    lesson-01/
      manifest.json
      note.md
```

说明：

- 每个成功 lesson 都应有自己的 `manifest.json` 和 `note.md`。
- `batch_manifest.json` 是 batch 级汇总，不替代 lesson 级 manifest。
- lesson 级输出结构仍遵循 `docs/20_architecture/output-contracts.md`。

## batch_manifest.json 解读

记录字段：

| Field | 含义 |
| --- | --- |
| `lesson_count` | discovery 发现的 lesson 数。 |
| `done_count` | 完成 per-lesson build 的数量。 |
| `failed_count` | 进入 build 但失败的数量。 |
| `skipped_count` | 未进入 build 的数量。 |
| `lessons[].lesson_id` | lesson 稳定标识，嵌套目录使用 `/`。 |
| `lessons[].media_path` | 源媒体路径。 |
| `lessons[].transcript_path` | 匹配到的 transcript 路径；缺失时为空。 |
| `lessons[].output_dir` | 该 lesson 的输出目录。 |
| `lessons[].status` | `done`、`failed` 或 `skipped`。 |
| `lessons[].manifest_path` | 成功 lesson 的 `manifest.json` 路径。 |
| `lessons[].failure_reason` | skipped/failed 的原因。 |
| `lessons[].vtext_compatible` | 是否匹配到 vtext-compatible transcript。 |

## 状态说明

### `done`

含义：

- 该 lesson 已完成 per-lesson pipeline。
- 通常应有 `manifest.json`、`note.md`、`vision/analysis.json`、`fusion/sections.json`。

检查：

- 打开 `lessons[].manifest_path`。
- 检查 lesson manifest 的 `stage_status`。
- 打开 lesson `note.md` 做人工抽查。

### `skipped`

当前典型原因：

```text
missing_transcript
```

含义：

- discovery 找到了媒体文件，但找不到匹配 transcript。
- 未进入 per-lesson build。

处理：

- 在 `input/text/<relative_parent>/` 下补齐同 stem 的 `.srt`。
- 使用推荐优先级命名。
- 重新运行 batch 或单课 build。

### `failed`

当前常见原因：

```text
unsupported_transcript_format
build_failed: <message>
```

含义：

- 已匹配 transcript 并尝试执行 per-lesson build，但中途失败。

处理：

- `unsupported_transcript_format`：优先转换为 `.srt` 或 vBook timestamped JSON 单课输入。
- `build_failed: ...`：根据 message 检查视频路径、frame extraction、transcript parse 或输出权限。

## 输出检查清单

Runbook 应给出检查清单：

- `batch_manifest.json` 存在。
- `lesson_count` 与预期媒体数量一致。
- `done_count + failed_count + skipped_count == lesson_count`。
- 每个 `done` lesson 有 `manifest_path`。
- 每个 `done` lesson 的 `manifest.json` 有 `stage_status.manifest == "done"`。
- 每个 `done` lesson 有 `note.md`。
- `skipped` 和 `failed` lesson 有 `failure_reason`。
- 抽查至少一个 `note.md` 的标题、课程信息和知识结构。

## 常见失败与处理

必须覆盖：

### `missing_transcript`

说明匹配路径和命名规则。

### `unsupported_transcript_format`

说明当前推荐转换为 `.srt`，不要误以为 `.txt` 已是高质量 batch 输入。

### `build_failed: ...`

说明这是 per-lesson pipeline 抛出的异常包装，先打开 lesson output 和命令 stderr，必要时单课复现。

### `lesson_count` 不符合预期

说明检查媒体扩展、忽略目录、是否把媒体放在 `text/` 或 `outputs/` 下。

### 旧输出混淆

说明每次 run 建议使用新 output path。

## 重跑策略

保守策略：

### 全量重跑

推荐使用新的 `--output`：

```powershell
python -m vbook_client build-batch `
  --input path\to\vtext-compatible-input `
  --output outputs\batch-run-2
```

### 单课重跑

使用 per-lesson `build`：

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\text\lesson.srt `
  --output outputs\single-lesson-rerun
```

### 修复 transcript 后重跑

建议：

- 修复 transcript 文件。
- 使用新 batch output。
- 对比新旧 `batch_manifest.json`。

### 当前不支持的重跑方式

明确说明当前不支持：

- 自动读取旧 `batch_manifest.json` 只重跑 failed/skipped。
- 自动跳过 done lesson。
- 原地安全清理旧 artifacts。
- 并发重跑。

## 同步更新

### `docs/60_operations/README.md`

更新：

- `batch-processing.md` 从 Planned Documents 移到 Current Entry Points。
- 描述为 batch input、batch manifest、failure handling 和 rerun strategy runbook。

### `docs/00_project/task-board.md`

更新：

- `完善 batch workflow 说明` 从 `Ready` 改为 `Done`。
- `Batch workflow` 当前说明补充 runbook 已完成。
- `最近完成` 增加 `Batch processing runbook`。
- 下一步推荐切换为 `扩展 pipeline stage documents`。

### `docs/00_project/status.md`

更新：

- 说明 batch processing 已有 functional foundation 和 operations runbook。
- Most Important Next Work 中把 batch runbook 移出待办，下一步保留 pipeline stage docs 或真实服务联调。

## 验证策略

本阶段是 docs-only，仍需验证：

```powershell
git diff --check
python -m unittest discover
```

建议追加内容检查：

```powershell
rg -n "build-batch|batch_manifest.json|missing_transcript|unsupported_transcript_format|重跑策略" docs/60_operations/batch-processing.md docs/60_operations/README.md docs/00_project/task-board.md docs/00_project/status.md
```

## 验收口径

本阶段完成后，应满足：

- `docs/60_operations/batch-processing.md` 存在。
- 操作者可以根据 runbook 组织输入、执行命令、检查输出和处理失败。
- 文档解释 `batch_manifest.json` 字段和 `done`/`skipped`/`failed` 状态。
- 文档明确当前不支持并发、断点续跑、自动只重跑失败项和真实服务 batch 验收。
- `docs/60_operations/README.md` 提供 batch runbook 入口。
- `docs/00_project/task-board.md` 标记 batch workflow 说明完成，并推荐下一步 pipeline stage docs。
- `docs/00_project/status.md` 与当前状态一致。
- `git diff --check` 通过。
- `python -m unittest discover` 通过。

## 后续工作

完成 runbook 后，可以继续：

- 扩展 `docs/30_pipeline/` stage documents。
- 在真实 Qwen 服务 ready 后执行 Qwen vision integration runbook。
- 设计 batch runtime 增强，例如 `--rerun-failed`、`--jobs`、读取旧 `batch_manifest.json`
  进行续跑。
- 在有可长期保留 fixture 后补真实 MP4 + transcript batch smoke。
