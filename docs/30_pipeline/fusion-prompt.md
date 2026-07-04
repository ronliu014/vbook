# Fusion Prompt

## 阶段目标

把 video、transcript、visual analysis 和 timeline links 打包成可审计的 prompt snapshot，为后续知识融合和 LLM contract 调试提供输入视图。

## 当前状态

Status: `Partial`

当前会写出 `fusion/prompt.json`。该 artifact 是审计输入，不代表已经调用真实模型。

## 输入

- `VideoAsset`
- `TranscriptSegment[]`
- `VisualAnalysis[]`
- `TimelineLink[]`

## 输出

- `fusion/prompt.json`
- Prompt snapshot JSON

## 关键代码

- `vbook_fusion/snapshot.py::build_fusion_prompt_snapshot`
- `vbook_fusion/snapshot.py::write_fusion_prompt_snapshot`

## CLI 与配置入口

- `python -m vbook_client build`
- `python -m vbook_client manifest --write-fusion-prompt`

## 产物路径

- `outputs/<lesson_id>/fusion/prompt.json`
- `outputs/<lesson_id>/manifest.json` 中的 `artifacts.fusion.prompt_path`

## 失败边界

- 上游 transcript、vision 或 timeline 数据为空时，prompt snapshot 内容也会变弱。
- 当前 prompt snapshot 不负责调用 LLM。
- 当前 prompt snapshot 不评价模型输出质量。

## 验收与测试

```powershell
python -m unittest tests.test_fusion.test_snapshot
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- Prompt snapshot 是本地 artifact，不是最终知识综合。
- 真实 LLM prompt engineering 仍需要基于服务联调结果迭代。

## 后续任务

- 真实 LLM/Qwen 文本综合服务 ready 后，对照 request/response contract 检查 prompt 信息是否足够。
- 根据真实课程输出优化 prompt fields。

## 相关文档

- [fusion-sections.md](./fusion-sections.md)
- [../90_reference/llm-fusion-command-requirements.md](../90_reference/llm-fusion-command-requirements.md)
