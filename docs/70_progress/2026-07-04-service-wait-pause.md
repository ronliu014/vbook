# 2026-07-04 服务等待暂停记录

## 暂停结论

当前阶段可以暂停，等待真实 Qwen Vision Service 和真实 LLM/Qwen 文本综合服务部署完成后再继续真实联调。

暂停前，vBook 主线没有偏离：项目仍围绕“把视频课程自动分析成图文证据笔记”的 local MVP pipeline 做稳。等待服务期间已经完成了一批不依赖真实服务的基础工作，包括专家笔记增强、batch processing runbook 和 pipeline stage documents。

## Git 状态

暂停前已经完成 push，`main` 与 `origin/main` 对齐。

最近同步到远端的阶段性提交包括：

```text
01429af Update project status after pipeline docs
6156c9b Document fusion and export stages
1ebf37f Document vision and timeline stages
dddfaa5 Document transcript and frame stages
fb6a115 Document pipeline stage index
949445f Plan pipeline stage documents
8c6f659 Design pipeline stage documents
a223c96 Document batch processing runbook
01f606e Plan batch processing runbook
836cb59 Design batch processing runbook
```

恢复工作前先运行：

```powershell
git status --short --branch
git pull
```

预期状态：

```text
## main...origin/main
```

## 已完成工作

### Expert note enhancement

`note.md` 已支持增强 section-based expert-note 模板，包含：

- `学习目标`
- `回看索引`
- `复习问题`
- `标签索引`

新增内容来自现有 `KnowledgeSection` 字段和固定模板，不依赖真实 Qwen 或 LLM 服务。

关键文档：

- [../80_superpowers/specs/2026-07-04-expert-note-enhancement-design.md](../80_superpowers/specs/2026-07-04-expert-note-enhancement-design.md)
- [../80_superpowers/plans/2026-07-04-expert-note-enhancement.md](../80_superpowers/plans/2026-07-04-expert-note-enhancement.md)

### Batch processing runbook

`build-batch` 的本地操作说明已经补齐，覆盖：

- vtext-compatible input layout
- nested input layout
- media discovery
- transcript matching
- `batch_manifest.json`
- `done`、`skipped`、`failed` 状态
- `missing_transcript`
- `unsupported_transcript_format`
- `build_failed: ...`
- 保守重跑策略

关键文档：

- [../60_operations/batch-processing.md](../60_operations/batch-processing.md)
- [../80_superpowers/specs/2026-07-04-batch-processing-runbook-design.md](../80_superpowers/specs/2026-07-04-batch-processing-runbook-design.md)
- [../80_superpowers/plans/2026-07-04-batch-processing-runbook.md](../80_superpowers/plans/2026-07-04-batch-processing-runbook.md)

### Pipeline stage documents

`docs/30_pipeline/` 已补齐阶段文档基础版。

入口：

- [../30_pipeline/README.md](../30_pipeline/README.md)
- [../30_pipeline/overview.md](../30_pipeline/overview.md)

阶段页：

- [../30_pipeline/transcript-import.md](../30_pipeline/transcript-import.md)
- [../30_pipeline/frame-extraction.md](../30_pipeline/frame-extraction.md)
- [../30_pipeline/frame-selection.md](../30_pipeline/frame-selection.md)
- [../30_pipeline/vision-analysis.md](../30_pipeline/vision-analysis.md)
- [../30_pipeline/timeline-alignment.md](../30_pipeline/timeline-alignment.md)
- [../30_pipeline/fusion-prompt.md](../30_pipeline/fusion-prompt.md)
- [../30_pipeline/fusion-sections.md](../30_pipeline/fusion-sections.md)
- [../30_pipeline/note-export.md](../30_pipeline/note-export.md)
- [../30_pipeline/manifest.md](../30_pipeline/manifest.md)

关键文档：

- [../80_superpowers/specs/2026-07-04-pipeline-stage-documents-design.md](../80_superpowers/specs/2026-07-04-pipeline-stage-documents-design.md)
- [../80_superpowers/plans/2026-07-04-pipeline-stage-documents.md](../80_superpowers/plans/2026-07-04-pipeline-stage-documents.md)

## 当前可运行能力

本地 MVP pipeline 当前可以从视频和 timestamped transcript 生成：

- `manifest.json`
- `note.md`
- `vision/analysis.json`
- `fusion/prompt.json`
- `fusion/sections.json`

当前已有边界：

- `placeholder` vision backend
- `manual-json` vision backend
- `external-command` vision backend
- `tools/vision_stub.py`
- `tools/vision_qwen_adapter.py`
- deterministic evidence sections
- `--llm-fusion-command`
- `tools/llm_fusion_stub.py`
- LLM fusion request/response contract samples and checker
- `build-batch`

## 当前阻塞项

### Qwen Vision Service 尚未部署完成

影响：

- 不能执行真实 `GET /health`。
- 不能执行真实 `POST /analyze-frame`。
- 不能验证真实视觉输出质量。
- 不能验证真实服务延迟、稳定性和失败模式。

暂停期间不要伪造真实联调结果。

### 真实 LLM/Qwen 文本综合服务尚未接入

影响：

- 不能验证最终模型综合笔记质量。
- 不能评价真实 glossary、learning objectives 或 review questions 的模型生成效果。

暂停期间继续使用 deterministic evidence draft 和 stub 作为本地 contract 验证方式。

### 缺少可长期保留的真实 MP4 + transcript smoke fixture

影响：

- 真实端到端样例验收还不能固定到 repo 流程中。
- 服务 ready 后仍需要明确样例文件、路径、授权、大小和保存策略。

## 恢复点

如果 Qwen Vision Service 已部署，优先从这里接：

1. 查看 [../60_operations/qwen-vision-integration.md](../60_operations/qwen-vision-integration.md)。
2. 查看 [../90_reference/integration-response.md](../90_reference/integration-response.md)，确认服务组最新 endpoint、limits 和认证要求。
3. 先跑 `GET /health`。
4. 再跑单帧 `POST /analyze-frame`。
5. 最后跑 vBook `build --vision-backend external-command`。

如果 Qwen 服务仍未部署，推荐下一步从这里接：

1. 梳理真实 smoke fixture 要求。
2. 明确 MP4 + transcript 样例来源、大小、授权、目录位置和是否进入 Git。
3. 更新 [../00_project/task-board.md](../00_project/task-board.md) 与 [../60_operations/smoke-tests.md](../60_operations/smoke-tests.md)。

## 恢复时不要做的事

- 不要在服务未 ready 前调用真实 Qwen endpoint。
- 不要把 `placeholder`、`stub` 或 fake HTTP server 结果写成真实服务质量结论。
- 不要把 `.vtt` 或 `.txt` 说成当前稳定推荐 batch transcript 输入。
- 不要引入 Qwen、OCR 或 LLM SDK 到 vBook core。
- 不要把 batch workflow 描述成已支持并发、resume 或自动 rerun failed。

## 验证快照

暂停前最终验证曾执行：

```powershell
python -m unittest discover
```

结果：

```text
Ran 129 tests in 17.580s
OK
```

如果恢复后先做真实服务联调，仍建议先运行：

```powershell
python -m unittest discover
```

确认本地基线稳定后再调用真实服务。

## 当前交接句

```text
vBook local MVP pipeline、专家笔记增强、batch processing runbook 和 pipeline stage docs 已完成并推送到 origin/main。
当前暂停等待真实 Qwen Vision Service 和真实 LLM/Qwen 文本综合服务部署。
服务 ready 后先按 docs/60_operations/qwen-vision-integration.md 做 health、analyze-frame 和 vBook external-command build smoke。
若服务仍未 ready，下一步先梳理真实 MP4 + transcript smoke fixture 要求。
```
