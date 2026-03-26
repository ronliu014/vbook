# 智能视频截图系统设计

## 目标

替换当前基于 LLM 猜测时间戳的截图机制，改用 OpenCV 场景变化检测 + 转录文本视觉线索 + 智能融合的混合策略，精准捕捉视频中有价值的知识画面。

## 架构

三层策略结合：
1. 场景变化检测层（OpenCV + ffmpeg）：定期采样视频帧，计算直方图差异，标记画面切换点
2. 文本线索分析层（LLM）：分析转录文本，识别"看这张图"等视觉提示词及其时间戳
3. 智能融合层：在提示词时间点附近查找场景变化点，优先选择最接近的变化帧

Pipeline 变更：`audio_extract → transcribe → proofread → **scene_detect** → analyze → screenshot → generate`

## 新增依赖

```toml
"opencv-python>=4.8.0"
"numpy>=1.24.0"
```

## 组件设计

### 1. SceneChangeDetector（新增工具类）

`src/vbook/utils/scene_detector.py`

```python
def detect_scene_changes(
    video_path: str,
    sample_interval: float = 5.0,
    threshold: float = 0.3,
) -> list[float]:
```

- 用 OpenCV 的 VideoCapture 按 sample_interval 采样帧
- 计算相邻帧的 HSV 直方图差异（cv2.compareHist，CORREL 方法）
- 相关性 < (1 - threshold) 时标记为场景变化
- 返回场景变化时间戳列表

### 2. SceneDetectStage（新增 Stage）

`src/vbook/stages/scene_detect.py`

- 位于 proofread 和 analyze 之间
- 调用 SceneChangeDetector 分析视频
- 输出 scene_changes.json 到 cache_dir
- 将 scene_changes 时间戳列表传入 context

### 3. 改进 ANALYZE_PROMPT

在现有 prompt 基础上，要求 LLM 额外输出 visual_cues 字段：

```json
{
  "title": "...",
  "outline": [...],
  "keywords": [...],
  "visual_cues": [
    {"timestamp": 120.5, "cue_text": "看这张图", "description": "讲解图表内容"}
  ]
}
```

LLM 从转录文本中识别暗示视觉内容的语句（如"看这张图"、"PPT上显示"、"这个表格"），
提取对应的时间戳。

### 4. 改进 ScreenshotStage

融合策略：

1. 读取 scene_changes（来自 SceneDetectStage）
2. 读取 visual_cues（来自 AnalyzeStage）
3. 对每个 visual_cue，在其时间戳 ±10 秒范围内查找最近的 scene_change
4. 如果找到 → 在 scene_change 时间点截图
5. 如果未找到 → 直接在 visual_cue 时间点截图
6. 兜底：如果某章节既无 visual_cue 也无 scene_change → 在章节开头截图
7. 去重：合并距离 < 5 秒的截图点

### 5. 配置

`vbook.yaml` 中新增可选配置：

```yaml
processing:
  screenshot:
    sample_interval: 5.0   # 场景检测采样间隔（秒）
    threshold: 0.3          # 场景变化阈值（0-1，越小越敏感）
    search_window: 10.0     # 文本线索搜索窗口（秒）
    dedup_window: 5.0       # 去重窗口（秒）
```

`schema.py` 中新增 `ScreenshotConfig`。

## 数据流

```
视频文件 ──→ SceneDetectStage ──→ scene_changes.json
                                        │
转录文本 ──→ AnalyzeStage ──→ analysis.json (含 visual_cues)
                                        │
                                        ▼
                                 ScreenshotStage（融合）
                                        │
                                        ▼
                                 screenshots/ + screenshots_map
```

## 涉及文件

- 新增: `src/vbook/utils/scene_detector.py`
- 新增: `src/vbook/stages/scene_detect.py`
- 新增: `tests/test_scene_detector.py`
- 修改: `pyproject.toml`（新增 opencv-python, numpy）
- 修改: `src/vbook/config/schema.py`（新增 ScreenshotConfig）
- 修改: `src/vbook/output/prompts.py`（ANALYZE_PROMPT 加 visual_cues）
- 修改: `src/vbook/stages/screenshot.py`（融合策略）
- 修改: `src/vbook/stages/analyze.py`（解析 visual_cues）
- 修改: `src/vbook/cli/process.py`（插入 SceneDetectStage、传入配置）
