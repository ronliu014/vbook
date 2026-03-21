import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from vbook.stages.audio_extract import AudioExtractStage
from vbook.pipeline.stage import StageStatus

def test_audio_extract_success(tmp_path):
    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake video content")
    output_dir = tmp_path / ".vbook_cache"

    with patch("ffmpeg.input") as mock_input:
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.audio.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = AudioExtractStage(video_path=video_file, cache_dir=output_dir)
        result = stage.run(context={})

    assert result.status == StageStatus.SUCCESS
    assert "audio_path" in result.output

def test_audio_extract_sets_correct_path(tmp_path):
    video_file = tmp_path / "lesson1.mp4"
    video_file.write_bytes(b"fake")
    cache_dir = tmp_path / ".vbook_cache"

    with patch("ffmpeg.input") as mock_input:
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.audio.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = AudioExtractStage(video_path=video_file, cache_dir=cache_dir)
        result = stage.run(context={})

    assert result.output["audio_path"].endswith("audio.wav")

from vbook.backends.stt.whisper import WhisperSTTBackend
from vbook.backends.base import TranscriptResult

def test_whisper_backend_returns_transcript():
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "  你好世界  "

    with patch("vbook.backends.stt.whisper.WhisperModel") as MockModel:
        instance = MockModel.return_value
        instance.transcribe.return_value = ([mock_segment], MagicMock(language="zh"))

        backend = WhisperSTTBackend(model="small", device="cpu")
        result = backend.transcribe("/tmp/audio.wav")

    assert isinstance(result, TranscriptResult)
    assert result.segments[0].text == "你好世界"
    assert result.language == "zh"

from vbook.backends.llm.litellm_backend import LiteLLMBackend
from vbook.stages.analyze import AnalyzeStage
import json

def test_llm_backend_analyze():
    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"outline": []}'))]
        )
        backend = LiteLLMBackend(model="ollama/qwen2.5:14b", base_url="http://localhost:11434")
        result = backend.analyze("some text", "generate outline")
    assert result == '{"outline": []}'

def test_analyze_stage_outputs_json(tmp_path):
    transcript_file = tmp_path / "transcript.json"
    transcript_file.write_text(
        json.dumps({"full_text": "这是测试内容", "segments": [], "language": "zh"}),
        encoding="utf-8"
    )

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                "title": "测试视频",
                "outline": [{"title": "第一节", "summary": "内容", "key_timestamps": [0]}],
                "keywords": ["测试"],
            })))]
        )
        backend = LiteLLMBackend(model="ollama/qwen2.5:14b")
        stage = AnalyzeStage(llm_backend=backend, cache_dir=tmp_path)
        result = stage.run(context={"transcript_path": str(transcript_file)})

    assert result.status == StageStatus.SUCCESS
    assert "analysis_path" in result.output


from vbook.backends.stt.whisper_remote import WhisperRemoteBackend


def test_whisper_remote_backend_returns_transcript(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "language": "zh",
        "segments": [
            {"start": 0.0, "end": 3.5, "text": "你好世界"},
            {"start": 3.5, "end": 7.0, "text": "这是测试"},
        ],
    }

    with patch("httpx.post", return_value=fake_response) as mock_post:
        backend = WhisperRemoteBackend(
            base_url="http://gpu-server:8000",
            model="medium",
            language="zh",
        )
        result = backend.transcribe(str(audio_file))

    assert isinstance(result, TranscriptResult)
    assert len(result.segments) == 2
    assert result.segments[0].text == "你好世界"
    assert result.segments[1].start == 3.5
    assert result.language == "zh"

    call_args = mock_post.call_args
    assert "gpu-server:8000/v1/audio/transcriptions" in call_args[0][0]


def test_whisper_remote_backend_http_error(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")

    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.text = "Internal Server Error"
    fake_response.raise_for_status.side_effect = Exception("HTTP 500")

    with patch("httpx.post", return_value=fake_response):
        backend = WhisperRemoteBackend(
            base_url="http://gpu-server:8000",
            model="medium",
            language="zh",
        )
        with pytest.raises(Exception):
            backend.transcribe(str(audio_file))