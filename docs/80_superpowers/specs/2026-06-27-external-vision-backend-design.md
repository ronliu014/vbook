# External Command Vision Backend Design

## 目的

vBook 当前已经有 `placeholder` 和 `manual-json` 两个视觉 backend。下一步需要进入
真实视觉理解，但不应该在第一步就绑定某个 OCR 引擎、多模态模型厂商或 vtext
代码。

本设计新增 `external-command` backend：vBook 负责准备 frame 输入 JSON、调用用户
提供的外部命令、读取外部命令输出，并继续把结果规范化为 `VisualAnalysis[]`。
外部命令可以是本地 OCR 脚本、多模态模型脚本、人工标注转换脚本，或未来的服务
适配器。

## 当前行为

`vbook_vision.analysis.analyze_frames()` 当前支持：

- `placeholder`：生成确定性的占位 `VisualAnalysis[]`。
- `manual-json`：读取用户提供的 JSON，并通过 `frame_id` 匹配当前 frame 集合。

`build` 默认运行 `placeholder`，也可以通过：

```powershell
--vision-backend manual-json
--visual-analysis-input path\to\manual-vision.json
```

接入外部准备好的视觉分析结果。

## 设计选择

新增 backend：

```powershell
--vision-backend external-command
```

新增 CLI 参数：

```powershell
--vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

其中：

- `{input}` 由 vBook 替换为 frame input JSON 路径。
- `{output}` 由 vBook 替换为外部命令应写入的 visual analysis JSON 路径。
- 命令模板必须同时包含 `{input}` 和 `{output}`。
- `manual-json` 继续使用 `--visual-analysis-input`，两者职责不混用。

第一版不做专用 OCR backend、不接特定模型 API、不实现重试、并发或流式进度。
这些能力可以在 `external-command` 契约稳定后作为外部脚本或后续 backend 增加。

## CLI 示例

```powershell
python -m vbook_client build `
  --video lesson.mp4 `
  --transcript text\lesson.srt `
  --output outputs\lesson `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

`build-batch` 第一版不新增 batch 级别的 vision 参数。后续如果需要 batch 使用
`external-command`，应复用同一个 per-lesson 参数集合，而不是为 batch 单独设计
一套视觉契约。

## 输入契约

运行外部命令前，vBook 写入一个 frame input JSON。该文件只描述当前需要分析的
frames，不包含 transcript、fusion 或 manifest 全量上下文。

示例：

```json
{
  "backend": "external-command",
  "frames": [
    {
      "frame_id": "frame-000001",
      "video_id": "lesson",
      "timestamp": 0.0,
      "image_path": "outputs/lesson/frames/selected/frame_000001.jpg",
      "width": 1280,
      "height": 720
    }
  ]
}
```

字段规则：

- `frame_id` 对应 `FrameCandidate.id`。
- `video_id` 对应 `FrameCandidate.video_id`。
- `timestamp` 使用秒。
- `image_path` 使用 JSON 序列化后的路径字符串。
- `width` 和 `height` 来自 `FrameCandidate`，没有探测到尺寸时可为 `0`。

## 输出契约

外部命令必须写出兼容 `manual-json` 的 JSON。推荐 object 格式：

```json
{
  "backend": "external-command",
  "analyses": [
    {
      "frame_id": "frame-000001",
      "visual_type": "slide",
      "ocr_text": "课程标题",
      "vision_description": "一页讲解短线选股条件的幻灯片。",
      "structured_observations": {
        "topic": "短线选股",
        "signals": ["均线", "成交量"]
      },
      "confidence": 0.86
    }
  ]
}
```

vBook 不信任外部命令输出。读取 output JSON 后，仍然通过现有
`load_manual_visual_analysis()` 的验证与规范化逻辑生成 `VisualAnalysis[]`。

这意味着 `external-command` 继承 `manual-json` 的验证规则：

- `analyses` 必须是 list，或根对象本身可以是 list。
- 每条记录必须是 object。
- `frame_id` 必须存在且非空。
- `frame_id` 不能重复。
- `frame_id` 必须属于当前 frame 集合。
- `visual_type` 必须是 `slide`、`kline_case` 或 `other`。
- `structured_observations` 如果存在，必须是 object。
- `confidence` 如果存在，必须是 number。

## API 设计

扩展 `analyze_frames()`：

```python
def analyze_frames(
    frames: Sequence[FrameCandidate],
    backend: str = "placeholder",
    visual_analysis_input: Path | str | None = None,
    vision_command: str | None = None,
    work_dir: Path | str | None = None,
) -> list[VisualAnalysis]:
    ...
```

新增 helper：

```python
def run_external_vision_command(
    frames: Sequence[FrameCandidate],
    vision_command: str | None,
    work_dir: Path | str | None,
) -> list[VisualAnalysis]:
    ...
```

`work_dir` 用于写入临时输入/输出 JSON。CLI 默认传 `<output>/vision/external`，
这样调试时可以保留外部命令输入和输出，而不是写入系统临时目录。

推荐文件：

```text
<output>/vision/external/frames.json
<output>/vision/external/analysis.json
```

最终规范化输出仍然写到：

```text
<output>/vision/analysis.json
```

## 命令执行

命令模板使用 `shlex.split()` 拆分，并用 token 替换方式填充 `{input}` 和
`{output}`。第一版不通过 shell 执行命令，避免 shell quoting 和注入问题。

示例模板：

```text
python tools\vision_stub.py --input {input} --output {output}
```

执行前验证：

- `vision_command` 不能为空。
- 模板必须包含 `{input}`。
- 模板必须包含 `{output}`。

执行后验证：

- 外部命令退出码必须为 `0`。
- `{output}` 文件必须存在。
- `{output}` 必须能被解析为 JSON。
- JSON 必须能通过 `load_manual_visual_analysis()` 验证。

## CLI 行为

在 shared pipeline 参数中新增：

```powershell
--vision-command
```

`_run_manifest_pipeline()` 在调用 `analyze_frames()` 时传入：

```python
vision_command=args.vision_command
work_dir=Path(args.output) / "vision" / "external"
```

`manifest` 和 `build` 都支持 `external-command`：

- `build` 默认仍然是 `placeholder`。
- `manifest` 只有显式传 `--vision-backend external-command` 时才运行视觉分析。
- 兼容参数 `--analyze-vision-placeholder` 不受影响。

## 错误处理

以下情况应 fail fast，并通过 CLI 的 `parser.error()` 给出可操作信息：

- `external-command backend requires vision_command`
- `vision_command must contain {input}`
- `vision_command must contain {output}`
- `external vision command failed with exit code <code>`
- `external vision command did not write output`
- JSON 格式错误或 `manual-json` 验证错误

外部命令的 stdout/stderr 第一版不写入 manifest。实现可以把 stderr 摘要包含在异常
消息中，但需要避免把长日志塞进主输出。

## 测试策略

不依赖真实 OCR 或模型。测试使用临时 fake script：

1. 读取 `{input}` frame JSON。
2. 取第一个 `frame_id` 和 `image_path`。
3. 写出兼容 `manual-json` 的 `{output}` JSON。

需要覆盖：

- `analyze_frames(..., backend="external-command")` 能调用 fake command。
- fake command 输出会被规范化为 `VisualAnalysis[]`。
- CLI `build --vision-backend external-command --vision-command ...` 写出
  `vision/analysis.json`。
- `manifest.json` 中 `stage_status.vision_analysis = done`。
- 缺少 `--vision-command` 报错。
- 命令模板缺少 `{input}` 报错。
- 命令模板缺少 `{output}` 报错。
- 外部命令非零退出码报错。
- 外部命令未写 output 报错。

## 非目标

第一版明确不做：

- 直接接 OpenAI、Qwen、PaddleOCR、Tesseract 或其他具体 backend。
- 外部命令并发调度。
- 外部命令重试。
- 流式进度。
- 把外部命令 stdout/stderr 写入主 manifest。
- 从 vtext 导入任何包或复制 vtext 代码。

## 后续扩展

当 `external-command` 被真实脚本验证后，可以继续扩展：

- `ocr-command`：约定 OCR-only 输出。
- `multimodal-command`：约定图文理解输出。
- `openai-vision` 或其他模型 backend：直接调用特定服务，但仍返回
  `VisualAnalysis[]`。
- batch 级别的 vision 参数透传，让 `build-batch` 为每个 lesson 使用同一个
  external command。
