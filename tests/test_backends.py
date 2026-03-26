import logging
from unittest.mock import patch, MagicMock
from vbook.backends.base import STTBackend, LLMBackend, TranscriptResult, TranscriptSegment

def test_transcript_result_to_text():
    result = TranscriptResult(segments=[
        TranscriptSegment(start=0.0, end=5.0, text="你好世界"),
        TranscriptSegment(start=5.0, end=10.0, text="这是测试"),
    ])
    assert "你好世界" in result.full_text
    assert "这是测试" in result.full_text

def test_transcript_result_segments():
    result = TranscriptResult(segments=[
        TranscriptSegment(start=0.0, end=5.0, text="Hello"),
    ])
    assert result.segments[0].start == 0.0
    assert result.segments[0].text == "Hello"


def test_litellm_backend_logs_model_and_url(caplog):
    from vbook.backends.llm.litellm_backend import LiteLLMBackend

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"title": "test"}'

    with patch("litellm.completion", return_value=mock_response), \
         caplog.at_level(logging.DEBUG, logger="vbook"):
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b", base_url="http://localhost:7866")
        backend.analyze("some text", "some prompt")

    messages = [r.message for r in caplog.records]
    assert any("qwen3.5:9b" in m or "7866" in m for m in messages)