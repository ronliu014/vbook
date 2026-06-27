# vBook 路线图

## P0：规划基础

- 建立业务规划和架构文档。
- 定义模块边界、数据模型、输出行为和 sync 协议。
- 保留 `docs/vBook需求意向.md` 作为原始需求来源。

## P1：项目骨架

- 添加 Python packaging 和 `pyproject.toml`。
- 创建 vtext 风格混合骨架：`vbook_client`、`vbook_common`、`vbook_pipeline`、`vbook_audio`、`vbook_vision`、`vbook_fusion`、`vbook_export` 和空包 `vbook_server`。
- 添加 lint、test 工具和基础单元测试。
- 保持依赖最小化。

## P2：本地 MVP 流水线

- 接收单个股票课程视频和已有带时间戳 transcript。
- 可选通过外部 `vtext` CLI 生成 transcript，但不依赖 vtext 包。
- 按可配置间隔抽帧。
- 过滤明显重复画面，并优先保留 PPT 和 K 线案例图。
- 默认接入多模态视觉分析后端，OCR 作为 fallback 或辅助输入。
- 按时间戳对齐帧和转写片段。
- 导出 `note.md`、`manifest.json`、图片资产和中间 JSON。

## P3：质量提升

- 使用感知哈希和文本密度改进帧过滤。
- 增强 `slide` 和 `kline_case` 的视觉类型判断。
- 增加交割单、收益表和复杂表格作为后续视觉类型。
- 优化融合 Prompt 模板。
- 支持从中间产物复跑。

## P4：vtext 风格服务模式

- 增加可选 `vbook_server`。
- 支持任务提交、队列状态、健康检查和进度流。
- 保持本地 CLI 模式可用。

## P5：知识库能力

- 增加案例标签。
- 导出文本与图片引用的向量索引。
- 支持跨课程搜索和重复案例识别。

## P6：协作与运维

- 将 sync 迁移到方向性单写者信道。
- 增加部署文档。
- 定义 wcodex/lcodex 审查、handoff 和发布协作流程。
