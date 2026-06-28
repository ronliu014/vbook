# vBook 处理流水线

## 端到端数据流

```text
VideoAsset + TranscriptInput
  +-- TranscriptSegment[]
  +-- FrameCandidate[]
        +-- VisualAnalysis[]
              +-- TimelineLink[]
                    +-- KnowledgeSection[]
                          +-- CourseNote
```

## 阶段 1：输入登记

系统记录源视频路径、课程名、章节标题、视频时长和输出工作区。`course_id` 或 `lesson_id` 应从元数据或文件名中稳定生成。

## 阶段 2：音频与转写

MVP 以已有带时间戳 transcript 为标准输入。vBook 内部统一转换为 `TranscriptSegment[]`，不关心来源。可选 adapter 可以调用外部 `vtext` CLI 生成 transcript，但 vBook 不 import vtext、不依赖 vtext 包。

## 阶段 3：视频抽帧

按可配置间隔抽帧，例如每 2 到 5 秒一帧。每个候选帧记录来源视频、时间戳、图片路径、尺寸和抽取配置。

## 阶段 4：帧过滤

过滤重复画面、纯讲师画面、空白画面和低信息量图片。MVP 的保留目标是 PPT/幻灯片和 K 线案例图。初期可使用感知哈希、画面差异、OCR 文本密度和阈值规则。

## 阶段 5：视觉分析

对保留帧识别其类型和内容。MVP 支持两类高优先级视觉类型：`slide` 和 `kline_case`。默认使用多模态模型理解图片语义，OCR 后端作为 PPT 文字提取、调试和 fallback。输出统一为 OCR 文本、视觉描述、结构化观察、后端信息和置信度。

## 阶段 6：时间轴对齐

按时间戳把视觉记录绑定到附近的转写片段。默认策略可使用每张图前后 10 秒的窗口，后续再加入语义相似度匹配。

## 阶段 7：知识融合

当前本地实现先使用确定性 evidence draft：把 transcript、OCR 文本、图像描述、
结构化视觉观察和时间轴关联转换为可审计的 `KnowledgeSection[]`。它会保留图片引用、
来源时间戳、要点和标签，并对相邻同主题或共享视觉证据的片段做保守合并，但还不是
最终 LLM 知识综合。后续 LLM 融合会在这个稳定 artifact 基础上生成去重后的高质量
知识段落。

同时，vBook 已准备 LLM-ready request/response contract 和 deterministic parser，
用于后续接入模型综合；当前默认输出仍使用 evidence draft，不执行模型调用。

显式提供 `--llm-fusion-command` 时，vBook 会把 evidence sections 写成
`fusion/llm_request.json`，调用外部命令生成 `fusion/llm_response.json`，再校验并写出
`fusion/llm_sections.json`。此时 `note.md` 使用 LLM sections 渲染；未提供该参数时默认
仍使用 deterministic evidence draft。

## 阶段 8：导出

导出双核心产物：`note.md` 面向用户阅读，`manifest.json` 面向机器复跑和后续知识库。同步保存图片素材、转写记录、视觉分析 JSON 和融合结果。section-based `note.md` 使用第一版专家笔记 Markdown 模板组织 `课程信息`、`课程总览`、`核心结论` 和 `知识结构`，并保留每个重点对应的原始视频时间点、相关图片和 tags。
