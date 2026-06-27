# External Command Smoke Tools Design

## 目的

`external-command` backend 已经让 vBook 能调用用户提供的外部视觉分析命令，但当前仓库还没有一个可直接运行的示例命令。用户如果想验证这条接口，需要临时编写脚本，这会增加理解成本，也不利于后续排查真实 OCR 或多模态脚本接入问题。

本设计新增一个仓库内置 smoke 工具：

```text
tools/vision_stub.py
```

它不做真实 OCR 或图像理解，只用于验证 `external-command` 的输入/输出契约、CLI 参数、输出路径和 manifest 贯通是否正常。

## 当前行为

当前可以用如下命令调用外部视觉 backend：

```powershell
python -m vbook_client build `
  --video lesson.mp4 `
  --transcript text\lesson.srt `
  --output outputs\lesson `
  --vision-backend external-command `
  --vision-command "python path\to\script.py --input {input} --output {output}"
```

但 `path\to\script.py` 需要用户自己准备。测试里有临时 fake script，但它只存在于测试临时目录，不是用户可复用工具。

## 设计选择

新增 deterministic smoke script：

```powershell
python tools\vision_stub.py --input path\to\frames.json --output path\to\analysis.json
```

脚本行为：

1. 读取 `--input` 指向的 JSON。
2. 校验根对象包含 `frames` list。
3. 对每个 frame 生成一条兼容 `manual-json` 的 analysis record。
4. 写入 `--output` 指向的 JSON。
5. 输出目录不存在时自动创建。

推荐作为 `external-command` 使用：

```powershell
python -m vbook_client build `
  --video lesson.mp4 `
  --transcript text\lesson.srt `
  --output outputs\lesson `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

## 输入契约

`tools/vision_stub.py` 读取 `external-command` backend 生成的 frame input JSON。

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

脚本只依赖：

- `frames` 是 list。
- 每个 frame 是 object。
- `frame_id` 是非空 string。

其他字段用于生成可读 smoke metadata，不作为必需字段。

## 输出契约

输出 JSON 使用 object 格式：

```json
{
  "backend": "vision_stub",
  "analyses": [
    {
      "frame_id": "frame-000001",
      "visual_type": "other",
      "ocr_text": "",
      "vision_description": "External command smoke analysis for frame-000001.",
      "structured_observations": {
        "source": "vision_stub",
        "video_id": "lesson",
        "timestamp": 0.0,
        "image_path": "outputs/lesson/frames/selected/frame_000001.jpg",
        "width": 1280,
        "height": 720
      },
      "confidence": 0.0
    }
  ]
}
```

注意：`backend` 是脚本输出来源标识。vBook 读取后仍会把归一化后的 `VisualAnalysis.backend` 写成 `external-command`，因为 pipeline backend 是 `external-command`。

## 错误处理

脚本应 fail fast，并向 stderr 输出简短、可操作的信息：

- 缺少 `--input` 或 `--output`：由 `argparse` 报错。
- input 文件不存在：退出码 `1`，信息包含 `input file does not exist`。
- input 不是合法 JSON：退出码 `1`，信息包含 `invalid input JSON`。
- 根对象不是 object：退出码 `1`，信息包含 `input JSON must be an object`。
- 缺少 `frames` list：退出码 `1`，信息包含 `input JSON must contain frames list`。
- frame 不是 object：退出码 `1`，信息包含 `frame at index <n> must be an object`。
- frame 缺少有效 `frame_id`：退出码 `1`，信息包含 `frame at index <n> requires string frame_id`。

## 文档

更新 operations 文档：

```text
docs/60_operations/smoke-tests.md
```

内容包括：

- `placeholder` smoke 的最小命令。
- `manual-json` smoke 的定位说明。
- `external-command` + `tools/vision_stub.py` smoke 命令。
- 运行后应该检查的产物：
  - `<output>/vision/external/frames.json`
  - `<output>/vision/external/analysis.json`
  - `<output>/vision/analysis.json`
  - `<output>/manifest.json`
- 明确 `vision_stub.py` 不是 OCR 或多模态模型，只验证接口。

## 测试策略

新增测试不依赖真实视频、OCR、模型或网络。

测试覆盖：

1. 直接运行 `tools/vision_stub.py --input frames.json --output analysis.json`，能生成兼容 `manual-json` 的输出。
2. `analysis.json` 能被 `load_manual_visual_analysis(..., backend="external-command")` 读取。
3. CLI `build --vision-backend external-command --vision-command "python tools/vision_stub.py --input {input} --output {output}"` 能跑通。
4. input 文件不存在时退出码为 `1`。
5. input JSON 缺少 `frames` list 时退出码为 `1`。

## 非目标

本阶段明确不做：

- 真实 OCR。
- 真实多模态图像理解。
- 模型 API 密钥配置。
- 依赖 PaddleOCR、Tesseract、OpenAI、Qwen 或其他 provider。
- `build-batch` 视觉参数透传。
- 生成长期保存的样例视频、样例图片或大文件。

## 后续扩展

当 smoke 工具链稳定后，下一步可以选择：

1. 新增 `tools/vision_manual_label_template.py` 或文档模板，支持人工标注转 `manual-json`。
2. 新增真实 OCR adapter，例如 `tools/vision_tesseract_adapter.py` 或 `tools/vision_paddleocr_adapter.py`。
3. 新增多模态 adapter，例如 `tools/vision_openai_adapter.py`，仍输出同一个 `manual-json` 兼容契约。
4. 让 `build-batch` 复用 per-lesson `external-command` 参数。

## 自审

- 范围聚焦：只补 smoke script、operations 文档和测试，不接真实 provider。
- 契约一致：输入沿用 `external-command` 的 `frames.json`，输出兼容 `manual-json`。
- 术语一致：继续使用 `external-command`、`manual-json`、`VisualAnalysis[]` 和 smoke test。
- 无占位：错误信息和测试范围已明确。
