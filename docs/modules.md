# vBook 模块规划

## 包结构方向

vBook 应学习 vtext 清晰的包边界，但按多模态课程处理重新划分职责。

```text
vbook/
|-- vbook_client/
|-- vbook_server/
|-- vbook_common/
|-- vbook_pipeline/
|-- vbook_audio/
|-- vbook_vision/
|-- vbook_fusion/
|-- vbook_export/
+-- tests/
```

第一阶段不必马上创建全部代码包，本文件定义的是职责边界。

## vbook_client

负责 CLI 入口、批处理命令、用户参数、服务端连接和本地输出选择。它应保持轻量，不拥有核心业务逻辑。

## vbook_server

未来的 FastAPI 服务端，负责任务提交、队列、worker 生命周期、健康检查和进度流。可以复用 vtext 中异步 job 与 SSE 进度的架构思想。

## vbook_common

负责共享 dataclass、enum、配置加载、路径工具、输出格式和序列化工具。该包不应依赖大型 OCR、LLM 或视频处理库。

## vbook_pipeline

负责阶段编排。它协调音频、抽帧、视觉分析、时间轴对齐、融合和导出。每个阶段都应可独立运行，并能复用缓存。

## vbook_audio

负责音频抽取和转写适配器。后端可以是本地 Whisper、远程服务或已有转写文件，但对外应暴露 vBook 自己的接口。

## vbook_vision

负责视频抽帧、去重、OCR、图片分类和多模态视觉分析。它拥有视觉中间产物元数据，但不负责最终笔记写出。

## vbook_fusion

负责 Prompt 构造、LLM 调用、图文上下文打包和知识段落生成。它必须保留来源引用，避免生成不可追溯的总结。

## vbook_export

负责 Markdown、JSON、图片索引和未来知识库导出。它拥有输出路径和文件布局规则。

## tests

测试目录应镜像模块边界，例如 `test_common`、`test_pipeline`、`test_audio`、`test_vision`、`test_fusion`、`test_export` 和未来 `test_server`。
