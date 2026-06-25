# vBook 架构决策记录

本文记录 vBook 后续实现应遵守的重要架构决策。

## ADR-001：vBook 独立于 vtext

**决策：** vBook 可以学习 vtext 的架构，但不能在运行时 import、vendor 或依赖 vtext 代码。

**原因：** vtext 与 vBook 当前设计思路接近，但后续会独立演进。运行时依赖会耦合发布节奏，并限制 vBook 的多模态范围。

**影响：** 需要复用的行为应通过 vBook 自有接口重新实现，或通过明确的外部命令和协议调用。

## ADR-002：采用 vtext 风格的包边界

**决策：** vBook 学习 vtext 的 client/server/common 分层方式。

**原因：** 该结构清晰地区分用户命令、长任务服务和共享数据契约。

**影响：** 即使 MVP 先做本地 CLI，也应保留未来服务化的模块边界。

## ADR-003：文档和业务架构优先

**决策：** 项目第一阶段先建设规划文档，再写实现代码。

**原因：** vBook 同时涉及音频、视频帧、OCR、多模态模型、时间轴对齐、LLM 融合和知识导出，复杂度高于普通脚本。

**影响：** 早期提交以文档为主，这些文档是项目资产，不是临时说明。

## ADR-004：中间产物是一等对象

**决策：** 每个流水线阶段都必须保存可检查的中间产物。

**原因：** 抽帧、过滤、OCR、对齐和 LLM 融合都需要调参。黑盒式从视频到笔记会导致排错困难。

**影响：** 输出目录和 manifest 是核心设计的一部分。

## ADR-005：sync 采用单写者纪律

**决策：** wcodex/lcodex 协作应使用只追加、单写者的方向信道。

**原因：** vtext 的 sync 协议证明，每个路径只有一个写入者时，Git 冲突会显著减少。

**影响：** vBook 应从当前 inbox/outbox 脚手架逐步演进到方向目录和 owner state 文件。

## ADR-006：生成媒体不进入 Git

**决策：** 视频、音频、抽帧图片、转写文本、模型文件和生成输出都应被 Git 忽略。

**原因：** 这些文件体积大、可能包含隐私，并且通常可以从原始输入重新生成。

**影响：** Git 只跟踪源码、文档、协议和小型测试 fixture。

## ADR-007：股票课程优先，架构保持可扩展

**决策：** vBook 第一阶段优先服务股票/交易课程。

**原因：** 股票课程高度依赖 K 线图、买卖点标注、均线形态和 PPT 框架，视觉信息缺失会直接降低笔记价值。

**影响：** MVP 优先识别 PPT 和 K 线案例图；通用课程、交割单、收益表和复杂表格放入后续阶段。

## ADR-008：混合骨架起步，server 空包占位

**决策：** 第一版创建 vtext 风格的包边界，但 `vbook_server` 只作为空包占位。

**原因：** 项目需要继承 vtext 的结构经验，但 MVP 应先验证本地 pipeline 闭环，不应过早引入 FastAPI、任务队列和服务端运维复杂度。

**影响：** 可运行能力先集中在 CLI 和 pipeline；服务端后续再扩展为 job queue、health API 和进度流。

## ADR-009：transcript 输入优先，vtext CLI 可选

**决策：** MVP 标准输入是已有带时间戳 transcript；可选通过外部 `vtext` CLI 生成 transcript。

**原因：** vBook 的差异化核心是视觉抽取、图文对齐和知识融合，不应在第一阶段重复实现完整 ASR 系统。

**影响：** vBook 内部统一使用 `TranscriptSegment[]`；vtext 是可选外部工具，不是 Python 包依赖。

## ADR-010：多模态视觉优先，OCR fallback

**决策：** MVP 默认使用多模态模型做视觉理解，OCR 作为 fallback 或辅助输入。

**原因：** PPT 文字可由 OCR 提供，但 K 线案例图的核心价值在图形语义和交易逻辑，需要多模态理解。

**影响：** `VisualAnalysis` 同时保留 `ocr_text`、`vision_description` 和 `structured_observations`。

## ADR-011：note.md 与 manifest.json 双核心输出

**决策：** MVP 输出以 `note.md` 和 `manifest.json` 为双核心。

**原因：** `note.md` 保证用户立即可读，`manifest.json` 保证复跑、审计、后续知识库和自动化处理。

**影响：** exporter 必须同时维护人类可读结果和机器可读索引。
