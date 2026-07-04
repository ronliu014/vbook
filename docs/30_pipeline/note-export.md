# Note Export

## 阶段目标

把 transcript 或 `KnowledgeSection[]` 渲染成面向用户阅读的 `note.md`，作为 vBook MVP 的核心输出之一。

## 当前状态

Status: `Partial`

当前 section-based note 已使用增强专家笔记模板，包含课程信息、课程总览、学习目标、核心结论、知识结构、回看索引、复习问题和标签索引。

## 输入

- `VideoAsset`
- `TranscriptSegment[]`
- `KnowledgeSection[]`

## 输出

- `note.md`

## 关键代码

- `vbook_export/note.py::render_placeholder_note`
- `vbook_export/note.py::render_sections_note`
- `vbook_export/note.py::write_note`

## CLI 与配置入口

- `python -m vbook_client manifest --write-note`
- `python -m vbook_client build`
- `python -m vbook_client build --llm-fusion-command "<command with input and output slots>"`
- `python -m vbook_client build-batch`

## 产物路径

- `outputs/<lesson_id>/note.md`
- `outputs/<lesson_id>/manifest.json` 中的 `note_path`

## 失败边界

- 上游 sections 为空时，section-based note 只能输出有限课程信息和总览。
- 当前不会生成真实术语解释，因为 `KnowledgeSection` 没有术语定义来源。
- 图片引用保持路径文本，不保证所有 Markdown renderer 都能直接显示本地图片。

## 验收与测试

```powershell
python -m unittest tests.test_export.test_note
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- 当前只输出 Markdown。
- 当前没有 HTML、PDF、Obsidian 或知识库导出。
- 学习目标、复习问题和标签索引由现有 section 字段确定性派生，不是自由模型生成。

## 后续任务

- 接入真实术语库后再生成术语解释章节。
- 设计多格式导出前，先稳定 `CourseNote` 或等价中间模型。

## 相关文档

- [fusion-sections.md](./fusion-sections.md)
- [manifest.md](./manifest.md)
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
