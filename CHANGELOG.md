# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-23

### Added

- **CLI 命令**
  - `vbook init` - 初始化配置文件
  - `vbook process` - 处理视频文件或目录
  - `vbook status` - 查看处理状态

- **核心功能**
  - 音频提取（AudioExtractStage）- 使用 FFmpeg 从视频提取音频
  - 语音转录（TranscribeStage）- 支持本地和远程 Whisper
  - 内容分析（AnalyzeStage）- 使用 LLM 生成知识大纲
  - 截图提取（ScreenshotStage）- 根据关键时间戳提取视频帧
  - 文档生成（GenerateStage）- 生成 Markdown 格式的知识文档

- **后端支持**
  - WhisperSTTBackend - 本地 Whisper（faster-whisper）
  - WhisperRemoteBackend - 远程 Whisper API
  - LiteLLMBackend - Ollama/Qwen LLM 集成

- **Pipeline 引擎**
  - 模块化 Stage 架构
  - 自动重试机制（指数退避）
  - 断点续处理（跳过已完成阶段）
  - 状态追踪（YAML 持久化）

- **配置系统**
  - 三层配置优先级（全局 < 项目 < CLI）
  - Pydantic 类型验证
  - YAML 格式配置文件
  - 深度合并配置

- **文档**
  - README.md - 项目简介
  - docs/DEPLOYMENT.md - 部署指南
  - docs/USER_GUIDE.md - 用户指南

- **测试**
  - 25 个单元测试
  - 87% 代码覆盖率
  - Mock-based 测试策略

### Technical Details

- **依赖**
  - Python 3.11+
  - click 8.3+ - CLI 框架
  - faster-whisper 1.2+ - 语音识别
  - ffmpeg-python 0.2+ - 音视频处理
  - httpx 0.28+ - HTTP 客户端
  - jinja2 3.1+ - 模板引擎
  - litellm 1.82+ - LLM API 抽象
  - pydantic 2.12+ - 数据验证
  - pyyaml 6.0+ - YAML 解析
  - rich 14.3+ - 终端美化

- **架构**
  - 可插拔 Backend 架构
  - Stage-based Pipeline 设计
  - 配置驱动的后端选择

### Known Limitations

- 仅支持 .mp4 和 .mkv 视频格式
- 输出格式仅支持 Markdown
- 目录结构仅支持 mirror 模式
- 中文语言优先（其他语言需配置）

---

## [Unreleased]

### Planned for v0.2.0

- 思维导图输出（MindMap 格式）
- PPT 生成
- 更多视频格式支持
- 批量处理优化
- Web UI

### Planned for v0.3.0

- 多语言支持优化
- 自定义模板系统
- 视频场景检测优化
- 性能优化

---

## Version History

- **v0.1.0** (2026-03-23) - MVP Release
  - 首个可用版本
  - 核心 Pipeline 完整实现
  - 支持本地和远程模型部署

---

## Links

- [GitHub Repository](https://github.com/ronliu014/vbook)
- [Issue Tracker](https://github.com/ronliu014/vbook/issues)
- [Documentation](docs/)
