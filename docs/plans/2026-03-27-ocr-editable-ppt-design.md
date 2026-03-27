# OCR 可编辑 PPT 功能设计文档

> 创建日期: 2026-03-27
> 目标版本: v0.3.0-alpha (实验性)
> 状态: 设计阶段

## 1. 需求背景

**当前问题**：
- 截图作为图片插入 PPT，文字无法编辑、搜索、复制
- 降低了 PPT 的可用性和可访问性

**目标**：
- 识别截图中的文字内容
- 生成可编辑的文本框
- 保留原图作为参考
- 作为可选的实验性功能

## 2. 技术方案

### 2.1 架构设计

```
┌─────────────┐
│ Screenshot  │
│   Stage     │
└──────┬──────┘
       │ 截图文件
       ▼
┌─────────────┐
│ OCR Stage   │ ← 新增阶段（可选）
│ (optional)  │
└──────┬──────┘
       │ OCR结果
       ▼
┌─────────────┐
│  Generate   │
│   Stage     │ → PPT (文本框 + 图片)
└─────────────┘
```

### 2.2 OCR 引擎选择

| 引擎 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **PaddleOCR** | 中文准确率高、开源、活跃维护 | 依赖体积大(~500MB) | ⭐⭐⭐⭐⭐ |
| EasyOCR | 多语言支持、易用 | 中文准确率略低 | ⭐⭐⭐⭐ |
| Tesseract | 轻量、传统方案 | 需要额外配置、准确率一般 | ⭐⭐⭐ |

**推荐**：PaddleOCR（中文场景最优）

### 2.3 PPT 布局设计

**方案 A：左图右文**
```
┌─────────────────────────────┐
│  章节标题                    │
├─────────────────────────────┤
│  摘要文字                    │
├──────────┬──────────────────┤
│          │  OCR识别的文字    │
│  原始    │  • 可编辑         │
│  截图    │  • 可搜索         │
│ (缩略)   │  • 保留格式       │
└──────────┴──────────────────┘
```

**方案 B：上图下文**
```
┌─────────────────────────────┐
│  章节标题                    │
├─────────────────────────────┤
│  摘要文字                    │
├─────────────────────────────┤
│      原始截图（缩略）         │
├─────────────────────────────┤
│  OCR识别的文字               │
│  • 可编辑                    │
│  • 可搜索                    │
└─────────────────────────────┘
```

**推荐**：方案 A（左图右文），更符合阅读习惯

### 2.4 智能场景分类

```python
def classify_screenshot(image_path: Path) -> str:
    """
    分类截图类型：
    - "text": 纯文字（如PPT文字页、文档）
    - "chart": 图表为主（如K线图、流程图）
    - "mixed": 混合内容
    """
```

**处理策略**：
- **text**: 全部转文本框，原图作为小缩略图
- **chart**: 保留大图，提取关键标注文字
- **mixed**: 图片 + 文字说明

## 3. 实现计划

### Phase 1: OCR 基础设施

**新增文件**：
- `src/vbook/stages/ocr.py` - OCR 处理阶段
- `src/vbook/utils/ocr_engine.py` - OCR 引擎封装
- `src/vbook/utils/layout_analyzer.py` - 布局分析

**核心接口**：
```python
class OCRStage(Stage):
    name = "ocr"

    def run(self, context: dict) -> StageResult:
        """
        对截图运行 OCR，输出：
        {
            "ocr_results": {
                "frame_001.jpg": {
                    "text": "完整文字",
                    "blocks": [...],
                    "layout": "text|chart|mixed"
                }
            }
        }
        """
```

### Phase 2: PPT 生成增强

**修改文件**：
- `src/vbook/output/pptx_generator.py`

**新增函数**：
```python
def generate_pptx_with_ocr(
    analysis: dict,
    assets_dir: Path,
    ocr_results: dict,
    output_path: Path,
    layout_mode: str = "left_image_right_text"
):
    """
    根据 OCR 结果生成可编辑 PPT
    """
```

### Phase 3: 配置与开关

**配置文件**：`vbook.yaml`
```yaml
processing:
  enable_ocr: false  # 默认关闭

backends:
  ocr: paddleocr
  paddleocr:
    use_gpu: false
    lang: ch
    det_model_dir: null  # 自动下载
    rec_model_dir: null

output:
  ppt:
    ocr_mode: auto  # auto | text_only | image_only
    layout: left_image_right_text  # 布局模式
```

## 4. 依赖管理

### 4.1 可选依赖

**pyproject.toml**：
```toml
[project.optional-dependencies]
ocr = [
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.6.0",
]
```

**安装方式**：
```bash
# 基础安装（不含 OCR）
uv sync

# 安装 OCR 功能
uv sync --extra ocr
```

### 4.2 运行时检查

```python
def check_ocr_available() -> bool:
    try:
        import paddleocr
        return True
    except ImportError:
        return False

# 在 OCRStage 中
if not check_ocr_available():
    logger.warning("OCR 功能未安装，跳过 OCR 阶段")
    return StageResult(status=StageStatus.SKIPPED)
```

## 5. 测试策略

### 5.1 单元测试

- `tests/test_ocr_engine.py` - OCR 引擎测试
- `tests/test_ocr_stage.py` - OCR 阶段测试
- `tests/test_pptx_ocr.py` - OCR PPT 生成测试

### 5.2 集成测试

- 使用真实截图测试 OCR 准确率
- 测试不同场景（纯文字、图表、混合）
- 性能测试（处理时间、内存占用）

### 5.3 用户测试

- 标记为 **alpha** 版本
- 收集用户反馈
- 评估是否进入稳定版

## 6. 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| OCR 准确率不足 | 用户体验差 | 保留原图作为备份，提供开关 |
| 依赖体积大 | 安装困难 | 作为可选依赖，按需安装 |
| 处理时间长 | 用户等待 | 并行处理、缓存结果、进度提示 |
| 复杂布局识别失败 | 文字错乱 | 场景分类，复杂场景降级为图片 |

## 7. 版本路线图

### v0.3.0-alpha (实验性)
- [ ] OCR 基础设施
- [ ] 可编辑 PPT 生成
- [ ] 配置开关
- [ ] 基础测试
- [ ] 文档标注为实验性

### v0.3.0-beta (优化)
- [ ] 根据 alpha 反馈优化
- [ ] 性能优化
- [ ] 更多场景支持
- [ ] 完善测试

### v0.3.0 (稳定版)
- [ ] 功能稳定
- [ ] 文档完善
- [ ] 移除实验性标记（如果效果好）

## 8. 成功标准

**进入稳定版的条件**：
1. OCR 准确率 > 90%（纯文字场景）
2. 处理时间增加 < 50%
3. 用户反馈积极（> 70% 满意度）
4. 无严重 bug

**如果不满足**：
- 保持为可选的实验性功能
- 或移除该功能

## 9. 参考资料

- [PaddleOCR 文档](https://github.com/PaddlePaddle/PaddleOCR)
- [python-pptx 文档](https://python-pptx.readthedocs.io/)
- [OCR 最佳实践](https://github.com/topics/ocr)
