# vbook 测试方案

> 版本: v0.1.0 | 最后更新: 2026-03-23 | 状态: MVP

本文档描述 vbook 的测试策略、测试用例、覆盖率目标和测试执行方法。

---

## 目录

1. [测试策略](#测试策略)
2. [测试环境](#测试环境)
3. [测试用例矩阵](#测试用例矩阵)
4. [覆盖率目标](#覆盖率目标)
5. [测试执行](#测试执行)
6. [CI/CD 集成](#cicd-集成)
7. [已知问题](#已知问题)

---

## 测试策略

### 分层测试策略

```
        ┌─────────────┐
        │  E2E 测试    │  ← 少量（手动）
        │  (手动)      │
        ├─────────────┤
        │  集成测试    │  ← 中等数量
        │  (Pipeline)  │
        ├─────────────┤
        │  单元测试    │  ← 大量
        │  (各模块)    │
        └─────────────┘
```

### 测试类型

| 测试类型 | 目标 | 工具 | 数量 |
|---------|------|------|------|
| **单元测试** | 测试独立模块 | pytest | 25+ |
| **集成测试** | 测试模块协作 | pytest | 10+ |
| **E2E 测试** | 测试完整流程 | 手动 | 3+ |
| **性能测试** | 测试处理速度 | pytest-benchmark | 5+ |

---

## 测试环境

### 开发环境

```bash
# 安装测试依赖
uv sync

# 验证环境
uv run pytest --version
```

### 测试依赖

- `pytest` - 测试框架
- `pytest-cov` - 覆盖率报告
- `pytest-mock` - Mock 工具
- `pytest-benchmark` - 性能测试（未来）

### Mock 策略

**原则：** Mock 外部依赖，不 Mock 内部逻辑

**需要 Mock 的：**
- 外部 API 调用（Whisper API, Ollama API）
- 文件系统操作（大文件读写）
- FFmpeg 调用
- 网络请求

**不需要 Mock 的：**
- 配置加载
- 数据结构转换
- Pipeline 编排逻辑

---

## 测试用例矩阵

### 1. Config 模块测试

**文件：** `tests/test_config.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_load_default_config` | 加载默认配置 | ✅ |
| `test_config_from_yaml` | 从 YAML 加载配置 | ✅ |
| `test_cli_args_override_config` | CLI 参数覆盖配置 | ✅ |
| `test_deep_merge_config` | 深度合并配置 | 📋 TODO |
| `test_invalid_config_validation` | 无效配置验证 | 📋 TODO |

### 2. Pipeline 模块测试

**文件：** `tests/test_pipeline.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_stage_result_success` | Stage 结果创建 | ✅ |
| `test_tracker_save_and_load` | 状态保存和加载 | ✅ |
| `test_tracker_incomplete_stage` | 未完成阶段检测 | ✅ |
| `test_engine_runs_stages` | Engine 执行 Stage | ✅ |
| `test_engine_skips_completed` | 跳过已完成阶段 | ✅ |
| `test_engine_retries_on_failure` | 失败重试机制 | ✅ |
| `test_engine_context_passing` | Context 传递 | 📋 TODO |
| `test_engine_error_handling` | 错误处理 | 📋 TODO |

### 3. Backend 模块测试

**文件：** `tests/test_backends.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_transcript_result_to_text` | TranscriptResult 转文本 | ✅ |
| `test_transcript_result_segments` | TranscriptResult 分段 | ✅ |
| `test_whisper_backend_returns_transcript` | Whisper 本地转录 | ✅ |
| `test_whisper_remote_backend_returns_transcript` | Whisper 远程转录 | ✅ |
| `test_whisper_remote_backend_http_error` | Whisper 远程错误处理 | ✅ |
| `test_llm_backend_analyze` | LLM 分析 | ✅ |

### 4. Stages 模块测试

**文件：** `tests/test_stages.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_audio_extract_success` | 音频提取成功 | ✅ |
| `test_audio_extract_sets_correct_path` | 音频路径正确 | ✅ |
| `test_transcribe_stage` | 转录阶段 | 📋 TODO |
| `test_analyze_stage_outputs_json` | 分析阶段输出 JSON | ✅ |
| `test_screenshot_stage_extracts_frames` | 截图提取 | ✅ |
| `test_screenshot_stage_no_timestamps` | 无时间戳跳过 | ✅ |
| `test_generate_stage_copies_screenshots` | 生成阶段复制截图 | ✅ |
| `test_generate_stage_without_screenshots` | 无截图生成 | ✅ |

### 5. Output 模块测试

**文件：** `tests/test_output.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_markdown_generation` | Markdown 生成 | ✅ |
| `test_generate_stage_creates_file` | 生成文件 | ✅ |
| `test_template_rendering` | 模板渲染 | 📋 TODO |
| `test_image_embedding` | 图片嵌入 | 📋 TODO |

### 6. CLI 模块测试

**文件：** `tests/test_cli.py`, `tests/test_cli_process.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_cli_help` | CLI 帮助信息 | ✅ |
| `test_cli_version` | CLI 版本信息 | ✅ |
| `test_process_single_video` | 处理单个视频 | ✅ |
| `test_process_missing_video` | 视频不存在错误 | ✅ |
| `test_init_command` | init 命令 | 📋 TODO |
| `test_status_command` | status 命令 | 📋 TODO |

### 7. Utils 模块测试

**文件：** `tests/test_utils_path.py`

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `test_mirror_structure` | 镜像目录结构 | ✅ |
| `test_mirror_nested` | 嵌套目录镜像 | ✅ |
| `test_get_cache_dir` | 获取缓存目录 | ✅ |
| `test_retry_mechanism` | 重试机制 | 📋 TODO |

---

## 覆盖率目标

### 当前覆盖率（v0.1.0）

**总体覆盖率：** 87% (369 lines, 49 uncovered)

### 模块覆盖率

| 模块 | 覆盖率 | 目标 | 状态 |
|------|--------|------|------|
| `backends/base.py` | 100% | 100% | ✅ |
| `backends/stt/whisper.py` | 100% | 100% | ✅ |
| `backends/stt/whisper_remote.py` | 100% | 100% | ✅ |
| `backends/llm/litellm_backend.py` | 100% | 100% | ✅ |
| `cli/main.py` | 100% | 100% | ✅ |
| `cli/process.py` | 82% | 90% | ⚠️ |
| `cli/init_cmd.py` | 67% | 80% | ⚠️ |
| `cli/status.py` | 39% | 80% | ❌ |
| `config/schema.py` | 100% | 100% | ✅ |
| `config/loader.py` | 93% | 95% | ✅ |
| `pipeline/engine.py` | 87% | 90% | ⚠️ |
| `pipeline/stage.py` | 95% | 95% | ✅ |
| `pipeline/tracker.py` | 93% | 95% | ✅ |
| `stages/audio_extract.py` | 100% | 100% | ✅ |
| `stages/transcribe.py` | 56% | 90% | ❌ |
| `stages/analyze.py` | 95% | 95% | ✅ |
| `stages/screenshot.py` | 100% | 100% | ✅ |
| `stages/generate.py` | 100% | 100% | ✅ |
| `output/markdown.py` | 100% | 100% | ✅ |
| `utils/path.py` | 100% | 100% | ✅ |
| `utils/retry.py` | 92% | 95% | ✅ |

### 覆盖率提升计划

**v0.2.0 目标：** 90%+

**需要改进的模块：**
1. `cli/status.py` (39% → 80%)
2. `stages/transcribe.py` (56% → 90%)
3. `cli/init_cmd.py` (67% → 80%)
4. `cli/process.py` (82% → 90%)

---

## 测试执行

### 运行所有测试

```bash
# 基本测试
uv run pytest

# 详细输出
uv run pytest -v

# 显示打印输出
uv run pytest -s

# 并行执行（需要 pytest-xdist）
uv run pytest -n auto
```

### 运行特定测试

```bash
# 运行特定文件
uv run pytest tests/test_pipeline.py

# 运行特定测试
uv run pytest tests/test_pipeline.py::test_engine_runs_stages

# 运行匹配模式的测试
uv run pytest -k "test_whisper"
```

### 覆盖率报告

```bash
# 生成终端报告
uv run pytest --cov=src/vbook --cov-report=term-missing

# 生成 HTML 报告
uv run pytest --cov=src/vbook --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### 性能测试

```bash
# 运行性能测试（未来）
uv run pytest tests/test_performance.py --benchmark-only

# 比较性能
uv run pytest --benchmark-compare
```

---

## 回归测试方案

### 回归测试清单

每次发布前必须执行：

- [ ] 所有单元测试通过
- [ ] 覆盖率 > 85%
- [ ] E2E 测试通过（至少 3 个场景）
- [ ] 性能基准测试通过
- [ ] 文档更新

### E2E 测试场景

**场景 1：单个视频处理**

```bash
# 准备测试视频（1-3 分钟）
# 运行处理
vbook process test_video.mp4 --output ./test_output

# 验证输出
ls test_output/test_video/summary.md
cat test_output/test_video/summary.md
```

**预期结果：**
- summary.md 存在
- 包含标题、大纲、关键词
- 截图正确嵌入

**场景 2：批量处理**

```bash
# 准备多个视频
mkdir test_videos
cp video1.mp4 video2.mp4 test_videos/

# 批量处理
vbook process test_videos --output ./test_output

# 验证输出
ls test_output/video1/summary.md
ls test_output/video2/summary.md
```

**预期结果：**
- 所有视频都生成了 summary.md
- 目录结构正确（mirror）

**场景 3：断点续处理**

```bash
# 首次处理（模拟中断）
vbook process test_video.mp4
# 手动中断（Ctrl+C）

# 重新处理
vbook process test_video.mp4

# 验证
vbook status test_output/test_video
```

**预期结果：**
- 跳过已完成的阶段
- 从中断处继续
- 最终生成完整输出

---

## CI/CD 集成

### GitHub Actions 配置（未来）

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --cov=src/vbook --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 测试门禁

**合并到 main 的要求：**
- ✅ 所有测试通过
- ✅ 覆盖率 > 85%
- ✅ 无 linting 错误
- ✅ 代码审查通过

---

## 已知问题与限制

### 测试限制

1. **无真实 GPU 测试**
   - 当前测试都是 Mock
   - 无法测试 GPU 加速效果
   - **缓解：** 手动 E2E 测试

2. **无大视频测试**
   - 测试用例使用小文件
   - 无法测试内存/性能问题
   - **缓解：** 性能测试（未来）

3. **无网络错误模拟**
   - 未测试网络超时、重连
   - **缓解：** 添加网络错误测试

### 已知 Bug

| Bug | 影响 | 优先级 | 状态 |
|-----|------|--------|------|
| 无 | - | - | - |

---

## 测试最佳实践

### 1. 测试命名

```python
# 好的命名
def test_whisper_backend_returns_transcript():
    ...

def test_engine_skips_completed_stages():
    ...

# 不好的命名
def test_1():
    ...

def test_backend():
    ...
```

### 2. Arrange-Act-Assert 模式

```python
def test_my_function():
    # Arrange - 准备测试数据
    input_data = "test"
    expected = "expected"

    # Act - 执行被测试的代码
    result = my_function(input_data)

    # Assert - 验证结果
    assert result == expected
```

### 3. 使用 Fixtures

```python
# conftest.py
@pytest.fixture
def temp_video_file(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    return video

# test_stages.py
def test_audio_extract(temp_video_file):
    stage = AudioExtractStage(video_path=temp_video_file, ...)
    result = stage.run(context={})
    assert result.status == StageStatus.SUCCESS
```

### 4. Mock 外部依赖

```python
def test_whisper_remote_backend():
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"segments": [...]}
        )
        backend = WhisperRemoteBackend(...)
        result = backend.transcribe("/tmp/audio.wav")

    assert isinstance(result, TranscriptResult)
    mock_post.assert_called_once()
```

---

## 下一步

- 了解如何运行测试：[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- 了解项目架构：[ARCHITECTURE.md](ARCHITECTURE.md)
- 查看测试覆盖率：运行 `uv run pytest --cov=src/vbook --cov-report=html`
