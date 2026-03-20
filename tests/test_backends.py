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