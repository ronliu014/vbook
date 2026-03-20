# vbook 项目文档体系设计

> 创建日期: 2026-03-20

## 1. 目标

为 vbook 项目创建完整的文档体系，服务于4类受众：终端用户、开发者、测试人员、项目管理者。

## 2. 文档结构

```
docs/
├── README.md                    # 文档索引/导航页
├── PROJECT_OVERVIEW.md          # 项目概述：愿景、目标、用户、用例
├── ARCHITECTURE.md              # 技术架构：组件设计、数据流、决策记录
├── USER_GUIDE.md                # 用户指南：安装、配置、CLI参考、故障排查
├── DEVELOPER_GUIDE.md           # 开发指南：代码结构、扩展方法、规范约定
├── PROJECT_PLAN.md              # 项目规划：阶段目标、里程碑、版本规划
├── TESTING.md                   # 测试方案：策略、测试用例、覆盖率、E2E/性能测试
└── CHANGELOG.md                 # 版本记录：变更历史
```

## 3. 受众矩阵

| 文档 | 终端用户 | 开发者 | 测试人员 | 项目管理 |
|------|---------|--------|---------|---------|
| PROJECT_OVERVIEW.md | ✓ | ✓ | | ✓ |
| ARCHITECTURE.md | | ✓ | ✓ | |
| USER_GUIDE.md | ✓ | | | |
| DEVELOPER_GUIDE.md | | ✓ | | |
| PROJECT_PLAN.md | | | | ✓ |
| TESTING.md | | ✓ | ✓ | ✓ |
| CHANGELOG.md | ✓ | ✓ | | ✓ |

## 4. 版本管理

采用 Living documents + changelog 模式：

- 每个文档包含内部版本标记
- 格式: `> 版本: v0.1.0 | 最后更新: 2026-03-20 | 状态: MVP`
- CHANGELOG.md 记录所有变更历史
- 不做版本化文件名，保持文档路径稳定

## 5. 各文档内容规划

### 5.1 docs/README.md — 文档索引

- 文档导航表（文档名 + 描述 + 适用受众）
- 快速入门链接
- 文档版本状态概览

### 5.2 PROJECT_OVERVIEW.md — 项目概述

- 项目愿景与核心使命
- 设计目标（功能目标 + 非功能目标）
- 目标用户与使用场景
- 核心功能列表与优先级
- 技术栈选型与理由
- 约束条件

### 5.3 ARCHITECTURE.md — 技术架构

- 系统架构图（ASCII）
- 模块化 Pipeline 设计
- 可插拔 Backend 架构
- 配置系统设计（优先级合并）
- 数据流向图
- 目录结构说明（代码 + 用户数据）
- 错误处理策略
- 关键设计决策记录（ADR）

### 5.4 USER_GUIDE.md — 用户指南

- 系统要求（Python, FFmpeg, Ollama）
- 安装步骤（详细）
- 依赖服务部署（Whisper, Ollama/Qwen, FFmpeg）
- 配置文件详解（每个字段）
- CLI 命令参考（init, process, status）
- 使用示例（单文件、批量、断点续处理）
- 输出文件说明
- 常见问题与故障排查

### 5.5 DEVELOPER_GUIDE.md — 开发指南

- 开发环境搭建
- 代码结构导览（每个模块职责）
- 核心抽象（Stage, Backend, Pipeline）
- 如何添加新的 STT Backend
- 如何添加新的 LLM Backend
- 如何添加新的输出格式
- 编码规范与约定
- 提交规范
- 运行测试

### 5.6 PROJECT_PLAN.md — 项目规划

- 版本规划路线图（v0.1 → v1.0）
- 各阶段目标与里程碑
  - Phase 1: MVP 基础框架（当前已完成）
  - Phase 2: 视觉提取与增强分析
  - Phase 3: 多格式输出（思维导图、PPT）
  - Phase 4: 性能优化与生产就绪
- 各版本功能对应表
- 依赖关系图
- 风险识别与应对

### 5.7 TESTING.md — 测试方案

- 测试策略（分层测试）
  - 单元测试：各模块独立逻辑
  - 集成测试：Pipeline 跨模块协作
  - E2E 测试：完整视频处理流程
  - 性能测试：处理时间基准
- 测试环境要求
- 测试用例矩阵（按模块组织）
  - Config 模块
  - Pipeline 模块
  - Audio Extract 阶段
  - Transcribe 阶段
  - Analyze 阶段
  - Generate 阶段
  - CLI 命令
- 覆盖率目标与当前状态
- 回归测试方案
- 端到端验收测试方案
- Mock/Stub 策略
- CI 集成计划
- 已知问题与限制

### 5.8 CHANGELOG.md — 版本记录

- 使用 Keep a Changelog 格式
- 分类: Added, Changed, Deprecated, Removed, Fixed, Security
- 从 v0.1.0 开始记录
