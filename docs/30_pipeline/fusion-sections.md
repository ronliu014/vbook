# Fusion Sections

## 阶段目标

把 transcript、视觉证据和 timeline links 转换为 `KnowledgeSection[]`，供 `note.md` 和后续知识库使用。

## 当前状态

Status: `Partial`

默认路径使用 deterministic evidence draft，并会保守合并相邻同主题或共享视觉证据的片段。显式提供 `--llm-fusion-command` 时，vBook 会执行 external-command LLM fusion contract。

## 输入

- `TranscriptSegment[]`
- `VisualAnalysis[]`
- `TimelineLink[]`
- CLI `--llm-fusion-command`
- CLI `--llm-fusion-request-path`
- CLI `--llm-fusion-response-path`
- CLI `--llm-fusion-sections-path`

## 输出

- `KnowledgeSection[]`
- `fusion/sections.json`
- `fusion/llm_request.json`
- `fusion/llm_response.json`
- `fusion/llm_sections.json`

## 关键代码

- `vbook_fusion/sections.py::build_evidence_sections`
- `vbook_fusion/sections.py::write_fusion_sections`
- `vbook_fusion/llm_contract.py::build_llm_fusion_request`
- `vbook_fusion/llm_contract.py::parse_llm_fusion_response`
- `vbook_fusion/llm_external.py::run_llm_fusion_command`
- `vbook_common/types.py::KnowledgeSection`
- `tools/llm_fusion_stub.py`
- `tools/check_llm_fusion_contract.py`

## CLI 与配置入口

- `python -m vbook_client build`
- `python -m vbook_client build --llm-fusion-command "<command with input and output slots>"`

`build-batch` 当前不透传 batch-level LLM fusion command 参数。

## 产物路径

- `outputs/<lesson_id>/fusion/sections.json`
- `outputs/<lesson_id>/fusion/llm_request.json`
- `outputs/<lesson_id>/fusion/llm_response.json`
- `outputs/<lesson_id>/fusion/llm_sections.json`
- `outputs/<lesson_id>/manifest.json` 中的 `artifacts.fusion`

## 失败边界

- `--llm-fusion-command` 缺少输入或输出插槽时 CLI 直接报错。
- 外部 LLM fusion command 非零退出时 build 失败。
- `llm_response.json` 不符合 parser contract 时 build 失败。
- 未提供 `--llm-fusion-command` 时不会调用真实模型，仍使用 deterministic evidence sections。

## 验收与测试

```powershell
python -m unittest tests.test_fusion.test_sections
python -m unittest tests.test_fusion.test_llm_contract
python -m unittest tests.test_fusion.test_llm_external
python -m unittest tests.test_tools.test_llm_fusion_stub
python -m unittest tests.test_tools.test_check_llm_fusion_contract
python -m unittest tests.test_client.test_manifest_cli
```

## 当前限制

- deterministic evidence draft 不是最终高质量模型综合。
- vBook core 不内置 LLM SDK 或模型 provider。
- contract samples 只验证 shape 和 parser compatibility，不评价笔记质量。

## 后续任务

- 真实 LLM/Qwen 文本综合服务 ready 后执行 contract smoke。
- 根据真实输出决定是否扩展 response fields。
- 后续可设计 glossary、learning objectives 或 review questions 的模型字段。

## 相关文档

- [fusion-prompt.md](./fusion-prompt.md)
- [note-export.md](./note-export.md)
- [../90_reference/llm-fusion-command-requirements.md](../90_reference/llm-fusion-command-requirements.md)
- [../90_reference/llm-fusion-service-integration-request.md](../90_reference/llm-fusion-service-integration-request.md)
