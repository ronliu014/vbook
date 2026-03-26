# 专业术语校正系统设计

## 目标

解决视频转录中专业术语（投资领域）识别不准确的问题，通过 Whisper 热词注入 + LLM 后置校正双重机制提高转录质量。

## 架构

两层修正策略：
1. 前置：将术语词表注入 Whisper hotwords 参数，从源头提高识别率
2. 后置：新增 ProofreadStage，用 LLM + 术语词表对转录文本做专业领域纠错

Pipeline 变更：`audio_extract → transcribe → **proofread** → analyze → screenshot → generate`

## 术语词表

### 格式

`glossary/investment.yaml`：

```yaml
domain: 投资
terms:
  - term: PE比
    description: 市盈率，Price-to-Earnings Ratio
  - term: 底背离
    description: 价格创新低但指标未创新低的技术形态
  - term: 满仓
    description: 将全部资金投入持仓
  - term: 止损
    description: 设定亏损上限，达到后卖出以控制风险
```

### 配置引用

`vbook.yaml` 中新增：

```yaml
processing:
  glossary: glossary/investment.yaml
```

`schema.py` 中 `ProcessingConfig` 新增 `glossary: Optional[str] = None` 字段。

## 前置：Whisper 热词注入

### WhisperSTTBackend（本地）

faster-whisper 的 `model.transcribe()` 支持 `hotwords` 参数（字符串，空格分隔）。
将术语列表的 `term` 字段拼接为 hotwords 字符串传入。

### WhisperRemoteBackend（远程）

faster-whisper-server 的 OpenAI 兼容 API 不一定支持 hotwords。
如果 API 不支持，静默跳过（日志记录 WARNING），降级为纯后置校正。

### 接口变更

`STTBackend.transcribe()` 签名新增可选参数 `hotwords: list[str] | None = None`。

## 后置：ProofreadStage

### 位置

插入在 `TranscribeStage` 和 `AnalyzeStage` 之间。

### 输入

- `transcript.json`（来自 TranscribeStage 输出）
- 术语词表（从配置路径加载）

### 处理逻辑

1. 读取 transcript.json 的 segments
2. 将术语词表 + 转录文本发给 LLM，prompt 要求：
   - 识别可能的术语误识别
   - 返回修正后的文本 + 修改记录
3. 解析 LLM 返回，更新 segments 中的 text 字段（保留时间戳不变）
4. 覆盖写入 transcript.json
5. 额外输出 corrections.json 记录所有修改（原文 → 修正，方便人工审查）

### LLM Prompt 设计

```
你是专业的语音转录校对助手。以下是语音识别的转录文本，可能存在专业术语识别错误。

专业术语词表：
{术语: 解释, ...}

请逐段检查转录文本，修正专业术语错误。只修正明显的术语误识别，不要改变原文的表达方式和语序。

返回 JSON 格式：
{
  "segments": [{"index": 0, "text": "修正后的文本"}, ...],
  "corrections": [{"index": 段落序号, "original": "原文", "corrected": "修正后", "reason": "原因"}]
}

只返回有修改的段落。未修改的段落不要包含在 segments 中。
```

### 输出

- 覆盖 `transcript.json`（更新 segments text，保留 start/end 时间戳）
- 新增 `corrections.json`（修改记录，供人工审查）

### 无词表时的行为

如果 `processing.glossary` 未配置或文件不存在，ProofreadStage 跳过（日志记录 INFO）。

## 数据流

```
glossary/investment.yaml
        │
        ├──→ WhisperSTTBackend.transcribe(hotwords=terms)
        │         │
        │         ▼
        │    transcript.json (原始)
        │         │
        └──→ ProofreadStage(llm + glossary)
                  │
                  ▼
             transcript.json (校正后)
             corrections.json (修改记录)
                  │
                  ▼
             AnalyzeStage (使用校正后的文本)
```

## 涉及文件

- 新增: `src/vbook/stages/proofread.py`
- 新增: `src/vbook/output/prompts.py` 中添加 PROOFREAD_PROMPT
- 新增: `glossary/investment.yaml`（示例词表）
- 新增: `tests/test_proofread.py`
- 修改: `src/vbook/config/schema.py`（ProcessingConfig 加 glossary 字段）
- 修改: `src/vbook/backends/base.py`（STTBackend.transcribe 加 hotwords 参数）
- 修改: `src/vbook/backends/stt/whisper.py`（传入 hotwords）
- 修改: `src/vbook/backends/stt/whisper_remote.py`（尝试传入或跳过）
- 修改: `src/vbook/stages/transcribe.py`（传入 hotwords）
- 修改: `src/vbook/cli/process.py`（加载词表、插入 ProofreadStage、传入 hotwords）
