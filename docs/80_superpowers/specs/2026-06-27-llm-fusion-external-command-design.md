# LLM Fusion External Command Design

## 背景

vBook 当前已经具备三层基础能力：

- 视觉分析可以通过 `placeholder`、`manual-json`、`external-command` 以及
  `tools/vision_qwen_adapter.py` 进入统一的 `VisualAnalysis[]`。
- 知识融合可以通过 deterministic evidence draft，把 transcript、OCR、视觉描述、
  结构化视觉观察和 timeline link 转成可审计的 `KnowledgeSection[]`。
- `vbook_fusion.llm_contract` 已经提供 provider-neutral 的 LLM request / response
  contract：
  - `build_llm_fusion_request()`
  - `parse_llm_fusion_response()`
  - `write_llm_fusion_request()`
  - `write_llm_fusion_sections()`

但这个 LLM contract 目前还没有进入 CLI pipeline。用户无法在 `build` 或 `manifest`
命令中生成 `fusion/llm_request.json`，也无法用外部模型命令产出的 JSON response 生成
`fusion/llm_sections.json` 和最终 `note.md`。

下一阶段应该补上“外部 LLM 融合执行入口”，同时继续保持 vBook core 不绑定任何具体
LLM provider。

## 目标

- 为 LLM fusion 增加类似视觉 `external-command` 的可测试执行入口。
- 默认 `build` 行为保持不变：不提供 LLM fusion 参数时仍使用 deterministic
  evidence sections 生成 `note.md`；`manifest` 命令仍由显式写入 flag 控制。
- 显式提供 LLM fusion command 时：
  - 先生成 evidence sections。
  - 写出 `fusion/llm_request.json`。
  - 执行外部 command。
  - 读取并校验外部 command 写出的 `fusion/llm_response.json`。
  - 写出 `fusion/llm_sections.json`。
  - `note.md` 使用 LLM sections 渲染。
- 所有新增行为都能用本地 fake command 和 `unittest` 验证，不访问网络。
- manifest 明确记录 LLM fusion artifacts 和 stage status，用户能判断 note 来源。

## 非目标

本阶段不做：

- 不接入 OpenAI、Qwen、Ollama 或任何模型 SDK。
- 不直接调用 HTTP LLM 服务。
- 不设计 prompt tuning 或模型质量评估。
- 不改变 `KnowledgeSection` dataclass。
- 不改变已有 `fusion/sections.json` schema。
- 不移除 deterministic evidence draft。
- 不让 batch pipeline 支持独立配置不同 LLM command；`build-batch` 可继续沿用默认
  build 行为，不在本阶段展开复杂批量配置。
- 不实现交互式人工编辑器。

## 方案选择

### 方案 A：`external-command` 执行入口

新增 LLM fusion command，命令读取 request JSON 并写 response JSON。

```text
evidence sections
  -> fusion/llm_request.json
  -> external command
  -> fusion/llm_response.json
  -> parse_llm_fusion_response()
  -> fusion/llm_sections.json
  -> note.md
```

优点：

- provider-neutral，不引入模型 SDK。
- 可用 fake script 做完整集成测试。
- 与当前视觉 `external-command` 心智模型一致。
- 未来可以包装 OpenAI、Qwen、本地模型或人工处理脚本。

缺点：

- 需要用户或外部项目提供 command。
- command 协议比内置 provider 多一步文件交接。

### 方案 B：只写 request，不执行 command

CLI 只生成 `fusion/llm_request.json`，用户手工调用模型后再通过另一个命令导入 response。

优点：

- 实现最小。
- 风险低。

缺点：

- pipeline 不闭环，用户仍然需要手工拼接。
- 无法验证 `note.md` 从 LLM sections 生成的完整路径。

### 方案 C：内置 HTTP provider

直接新增 `--llm-endpoint`，由 vBook 调 HTTP。

优点：

- 用户体验更直接。

缺点：

- 过早绑定网络协议、认证、重试和 provider 差异。
- 与当前“provider-neutral core”的边界冲突。

## 决策

采用方案 A：新增 LLM fusion `external-command` 执行入口。

原因：

- 它把上一阶段的 LLM contract 接入 pipeline，但不绑定具体模型。
- 它能在没有真实模型服务时用 fake command 完成 TDD 和集成测试。
- 它与已存在的视觉 `external-command` 边界一致，用户和后续服务组都容易理解。

## 用户接口

### CLI 参数

在 `manifest` 和 `build` 共用的 pipeline 参数中新增：

```text
--llm-fusion-command
```

含义：

- 外部 LLM fusion command 模板。
- 模板必须包含 `{input}` 和 `{output}` 占位符。
- vBook 会将 `{input}` 替换为 LLM request JSON 路径。
- vBook 会将 `{output}` 替换为 LLM response JSON 路径。

新增路径参数：

```text
--llm-fusion-request-path
--llm-fusion-response-path
--llm-fusion-sections-path
```

默认值：

```text
<output>/fusion/llm_request.json
<output>/fusion/llm_response.json
<output>/fusion/llm_sections.json
```

### CLI 示例

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-command "python tools\llm_fusion_stub.py --input {input} --output {output}"
```

本阶段不要求 `tools/llm_fusion_stub.py` 作为正式工具存在；测试可以在临时目录生成 fake
script。是否保留一个 repo 内 smoke stub 可作为实施时的独立小任务评估。

## 数据流

`build` 不提供 `--llm-fusion-command` 时：

```text
TranscriptSegment[]
  + VisualAnalysis[]
  + TimelineLink[]
    -> build_evidence_sections()
    -> fusion/sections.json
    -> render_sections_note()
    -> note.md
```

`build` 或显式开启对应写入 flag 的 `manifest` 提供 `--llm-fusion-command` 时：

```text
TranscriptSegment[]
  + VisualAnalysis[]
  + TimelineLink[]
    -> build_evidence_sections()
    -> fusion/sections.json
    -> build_llm_fusion_request(video, evidence_sections)
    -> fusion/llm_request.json
    -> external command
    -> fusion/llm_response.json
    -> parse_llm_fusion_response()
    -> fusion/llm_sections.json
    -> render_sections_note(video, llm_sections)
    -> note.md
```

关键点：

- evidence sections 始终保留，作为可审计输入。
- LLM sections 只在显式启用 command 后生成。
- `note.md` 在 LLM command 成功时使用 LLM sections；command 未启用时继续使用
  evidence sections。

## 模块边界

### `vbook_fusion.llm_contract`

继续只负责 provider-neutral JSON contract：

- 构建 request。
- 解析 response。
- 写 request 和 parsed sections artifact。

不在这里执行 command。

### 新模块 `vbook_fusion.llm_external`

新增外部执行 helper，职责集中在文件交接和 command 执行：

```python
def run_llm_fusion_command(
    command_template: str,
    request_path: Path | str,
    response_path: Path | str,
) -> Path:
    ...
```

行为：

- 校验 `command_template` 同时包含 `{input}` 和 `{output}`。
- 确保 response parent directory 存在。
- 如果 response path 已存在，执行前删除旧文件，避免读取 stale response。
- 使用 `subprocess.run()` 执行命令。
- Windows / PowerShell 下仍使用 `shlex.split()` 解析模板，不调用 shell。
- 与视觉 `external-command` 一致，替换 `{input}` / `{output}` 后剥掉单个参数的外层引号。
- 命令退出码非 0 时抛 `ValueError`，错误中包含退出码。
- 命令成功但未生成 response path 时抛 `ValueError`。
- 返回 response path。

这个模块不解析 LLM response，解析仍由 `llm_contract` 完成。

### `vbook_client.cli`

CLI 只负责 orchestration：

- 建立默认路径。
- 在 evidence sections 写出后，如果有 `--llm-fusion-command`：
  - build request。
  - write request。
  - run command。
  - load response JSON。
  - parse response。
  - write parsed LLM sections。
  - 后续 note 使用 LLM sections。
- 将 manifest 所需 artifact 状态传入 `build_manifest()`。

### `vbook_export.manifest`

manifest 需要能记录新增 artifact：

```json
"fusion": {
  "prompt_path": "...",
  "prompt_format": "json",
  "sections_path": "...",
  "sections_format": "json",
  "llm_request_path": "...",
  "llm_response_path": "...",
  "llm_sections_path": "...",
  "llm_sections_format": "json"
}
```

新增 stage status：

```text
llm_fusion
```

规则：

- 未提供 `--llm-fusion-command`：`llm_fusion = skipped`
- command 成功且 parsed sections 写出：`llm_fusion = done`
- command 失败时 CLI 直接 error，不写成功 manifest。

`pipeline_run.output_paths` 也加入：

```text
llm_fusion_request
llm_fusion_response
llm_fusion_sections
```

## 错误处理

### 缺少占位符

如果 command template 缺 `{input}` 或 `{output}`：

```text
llm-fusion-command requires {input} and {output} placeholders
```

### command 失败

如果外部 command 返回非 0：

```text
llm fusion command failed with exit code <code>
```

CLI 通过 `parser.error()` 输出，并以 SystemExit 2 结束。

### response 缺失

如果 command 成功但没有写 response：

```text
llm fusion command did not create response file: <path>
```

### response JSON 非法

如果 response 不是 JSON object 或 schema 不合法，沿用 `parse_llm_fusion_response()`
的 `ValueError`：

```text
sections[0].source_timestamps[1] must be finite
```

CLI 捕获后通过 `parser.error()` 输出。

### stale output

执行 command 前删除旧 response path。这样 command 失败或没有写文件时，不会误读上一次
结果。

## 测试策略

### Unit tests: `vbook_fusion.llm_external`

新增 `tests/test_fusion/test_llm_external.py`：

- command template 缺 `{input}` 或 `{output}` 时失败。
- fake command 写出 response 后返回 response path。
- command 成功但未写 response 时失败。
- command 失败时删除旧 response，不读取 stale output。

### Manifest tests

扩展 `tests/test_export/test_manifest.py`：

- 未启用 LLM fusion 时 `llm_fusion` 为 skipped。
- 启用并写出 LLM fusion artifacts 时：
  - `stage_status["llm_fusion"] == "done"`
  - `artifacts["fusion"]["llm_request_path"]` 存在于 manifest 数据中。
  - `artifacts["fusion"]["llm_sections_format"] == "json"`。

### CLI integration tests

扩展 `tests/test_client/test_manifest_cli.py`：

- `build --llm-fusion-command <fake script>` 会生成：
  - `fusion/sections.json`
  - `fusion/llm_request.json`
  - `fusion/llm_response.json`
  - `fusion/llm_sections.json`
  - `note.md`
  - `manifest.json`
- `note.md` 使用 LLM response 中的 section title / summary。
- manifest 中 `llm_fusion` 为 done。
- command 缺占位符时 `main()` 抛 `SystemExit(2)`。

### Full verification

```powershell
python -m unittest tests.test_fusion.test_llm_external
python -m unittest tests.test_client.test_manifest_cli
python -m unittest tests.test_export.test_manifest
python -m unittest discover
```

## 文档更新

实现后更新：

- `docs/00_project/status.md`
  - What Works Now 增加 LLM fusion external-command。
  - Placeholder 部分说明仍未内置模型 provider。
  - Verification Snapshot 更新测试数。
- `docs/30_pipeline/overview.md`
  - 阶段 7 增加 LLM external-command 数据流说明。
- `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`
  - P4 将“LLM fusion 执行入口”标记为已完成，剩余为外部模型 command 实例和专家笔记结构。

## 验收口径

本阶段完成后，应满足：

- 默认 `build` 行为不变。
- 显式 `--llm-fusion-command` 可以完整闭环：
  - request artifact
  - external response artifact
  - parsed LLM sections artifact
  - note rendering from LLM sections
  - manifest artifact and stage status
- 所有新增行为都由本地 fake command 测试，不需要真实 LLM 服务。
- `python -m unittest discover` 通过。

## 后续工作

完成本阶段后，后续可以继续：

- 增加 repo 内 `tools/llm_fusion_stub.py` 作为 smoke 工具。
- 设计真实 LLM provider command 的需求书。
- 优化 `note.md` 专家笔记结构。
- 在真实 Qwen 视觉 smoke 输出稳定后，用真实视觉结果跑 LLM fusion。
