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
from vbook.backends.base import TranscriptResult, TranscriptSegment
from vbook.stages.transcribe import TranscribeStage

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
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b", base_url="http://localhost:7866")
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
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b")
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
            base_url="http://gpu-server:7867",
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
    assert "gpu-server:7867/v1/audio/transcriptions" in call_args[0][0]


def test_whisper_remote_backend_http_error(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")

    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.text = "Internal Server Error"
    fake_response.raise_for_status.side_effect = Exception("HTTP 500")

    with patch("httpx.post", return_value=fake_response):
        backend = WhisperRemoteBackend(
            base_url="http://gpu-server:7867",
            model="medium",
            language="zh",
        )
        with pytest.raises(Exception):
            backend.transcribe(str(audio_file))


from vbook.stages.screenshot import ScreenshotStage


def test_screenshot_stage_extracts_frames(tmp_path):
    """Mock ffmpeg, verify frames extracted per key_timestamps, output screenshots map."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    analysis = {
        "title": "测试视频",
        "outline": [
            {"title": "第一节", "summary": "内容", "key_timestamps": [10.0, 30.5]},
            {"title": "第二节", "summary": "更多内容", "key_timestamps": [60.0]},
        ],
        "keywords": ["测试"],
    }
    analysis_path = cache_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake video")

    with patch("vbook.stages.screenshot.ffmpeg_lib") as mock_ffmpeg, \
         patch("vbook.stages.screenshot._get_video_duration", return_value=3600.0):
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = ScreenshotStage(video_path=video_file, cache_dir=cache_dir)
        result = stage.run(context={
            "video_path": str(video_file),
            "analysis_path": str(analysis_path),
        })

    assert result.status == StageStatus.SUCCESS
    assert "screenshots_dir" in result.output
    assert "screenshots_map" in result.output

    # New implementation uses flat structure: frame_000_10.0s.jpg, frame_001_30.5s.jpg, etc.
    screenshots_map = result.output["screenshots_map"]
    assert len(screenshots_map) == 3  # 3 screenshots total
    assert mock_ffmpeg.input.call_count == 3


def test_screenshot_stage_no_timestamps(tmp_path):
    """Sections without key_timestamps now use fallback (0.0)."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    analysis = {
        "title": "测试视频",
        "outline": [
            {"title": "第一节", "summary": "内容"},
            {"title": "第二节", "summary": "更多", "key_timestamps": []},
        ],
        "keywords": ["测试"],
    }
    analysis_path = cache_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake video")

    with patch("vbook.stages.screenshot.ffmpeg_lib") as mock_ffmpeg, \
         patch("vbook.stages.screenshot._get_video_duration", return_value=3600.0):
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = ScreenshotStage(video_path=video_file, cache_dir=cache_dir)
        result = stage.run(context={
            "video_path": str(video_file),
            "analysis_path": str(analysis_path),
        })

    assert result.status == StageStatus.SUCCESS
    # New behavior: fallback to 0.0 when no timestamps exist
    assert len(result.output["screenshots_map"]) == 1
    assert mock_ffmpeg.input.call_count == 1


from vbook.stages.generate import GenerateStage


def test_generate_stage_copies_screenshots_and_injects(tmp_path):
    """GenerateStage should copy screenshots to assets/ and inject filenames into sections."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    screenshots_dir = cache_dir / "screenshots"
    screenshots_dir.mkdir()

    # Create real screenshot files (needed for PPT generation)
    from PIL import Image
    for filename in ["section_0_frame_0.jpg", "section_0_frame_1.jpg", "section_1_frame_0.jpg"]:
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(str(screenshots_dir / filename))

    analysis = {
        "title": "测试视频",
        "outline": [
            {"title": "第一节", "summary": "内容", "key_timestamps": [10.0, 30.5]},
            {"title": "第二节", "summary": "更多内容", "key_timestamps": [60.0]},
        ],
        "keywords": ["测试"],
    }
    analysis_path = cache_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "output"

    stage = GenerateStage(output_dir=output_dir, cache_dir=cache_dir)
    result = stage.run(context={
        "analysis_path": str(analysis_path),
        "screenshots_dir": str(screenshots_dir),
        "screenshots_map": {
            "0": ["section_0_frame_0.jpg", "section_0_frame_1.jpg"],
            "1": ["section_1_frame_0.jpg"],
        },
    })

    assert result.status == StageStatus.SUCCESS

    # Verify screenshots copied to assets/
    assets_dir = output_dir / "assets"
    assert (assets_dir / "section_0_frame_0.jpg").exists()
    assert (assets_dir / "section_0_frame_1.jpg").exists()
    assert (assets_dir / "section_1_frame_0.jpg").exists()

    # Verify markdown contains image references
    md_content = Path(result.output["markdown_path"]).read_text(encoding="utf-8")
    assert "![第一节](assets/section_0_frame_0.jpg)" in md_content
    assert "![第一节](assets/section_0_frame_1.jpg)" in md_content
    assert "![第二节](assets/section_1_frame_0.jpg)" in md_content


def test_generate_stage_without_screenshots(tmp_path):
    """GenerateStage should work normally when no screenshots are provided."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    analysis = {
        "title": "测试视频",
        "outline": [
            {"title": "第一节", "summary": "内容", "key_timestamps": [10.0]},
        ],
        "keywords": ["测试"],
    }
    analysis_path = cache_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "output"

    stage = GenerateStage(output_dir=output_dir, cache_dir=cache_dir)
    result = stage.run(context={"analysis_path": str(analysis_path)})

    assert result.status == StageStatus.SUCCESS
    md_content = Path(result.output["markdown_path"]).read_text(encoding="utf-8")
    assert "第一节" in md_content
    assert "![" not in md_content


def test_whisper_backend_passes_hotwords():
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "PE比很高"

    with patch("vbook.backends.stt.whisper.WhisperModel") as MockModel:
        instance = MockModel.return_value
        instance.transcribe.return_value = ([mock_segment], MagicMock(language="zh"))

        backend = WhisperSTTBackend(model="small", device="cpu")
        result = backend.transcribe("/tmp/audio.wav", hotwords=["PE比", "满仓"])

    call_kwargs = instance.transcribe.call_args
    assert call_kwargs.kwargs.get("hotwords") == "PE比 满仓" or "PE比" in str(call_kwargs)


def test_whisper_remote_ignores_hotwords(tmp_path):
    """Remote backend should accept hotwords param without error (graceful ignore)."""
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "language": "zh",
        "segments": [{"start": 0.0, "end": 3.5, "text": "你好"}],
    }

    with patch("httpx.post", return_value=fake_response):
        backend = WhisperRemoteBackend(base_url="http://gpu-server:7867")
        result = backend.transcribe(str(audio_file), hotwords=["PE比"])

    assert result.segments[0].text == "你好"


def test_transcribe_stage_passes_hotwords(tmp_path):
    mock_backend = MagicMock()
    mock_backend.transcribe.return_value = TranscriptResult(
        segments=[TranscriptSegment(start=0, end=5, text="test")],
        language="zh",
    )

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    stage = TranscribeStage(stt_backend=mock_backend, cache_dir=cache_dir, hotwords=["PE比"])
    result = stage.run(context={"audio_path": "/tmp/audio.wav"})

    call_kwargs = mock_backend.transcribe.call_args
    assert call_kwargs.kwargs.get("hotwords") == ["PE比"] or call_kwargs[1].get("hotwords") == ["PE比"]


def test_analyze_stage_parses_visual_cues(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    transcript = {
        "language": "zh",
        "segments": [{"start": 0, "end": 10, "text": "看这张图"}],
        "full_text": "看这张图",
    }
    transcript_path = cache_dir / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")

    llm_response = json.dumps({
        "title": "测试",
        "outline": [{"title": "第一节", "summary": "内容", "key_timestamps": [10.0]}],
        "keywords": ["测试"],
        "visual_cues": [{"timestamp": 5.0, "cue_text": "看这张图", "description": "图表"}],
    }, ensure_ascii=False)

    mock_llm = MagicMock()
    mock_llm.analyze.return_value = llm_response

    from vbook.stages.analyze import AnalyzeStage
    stage = AnalyzeStage(llm_backend=mock_llm, cache_dir=cache_dir)
    result = stage.run(context={"transcript_path": str(transcript_path)})

    assert result.status == StageStatus.SUCCESS
    analysis = json.loads(Path(result.output["analysis_path"]).read_text(encoding="utf-8"))
    assert "visual_cues" in analysis
    assert analysis["visual_cues"][0]["timestamp"] == 5.0


def test_screenshot_fusion_prefers_scene_change_near_cue(tmp_path):
    """When a visual_cue has a nearby scene_change, use the scene_change timestamp."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    analysis = {
        "title": "测试",
        "outline": [
            {"title": "第一节", "summary": "内容", "key_timestamps": [10.0]},
        ],
        "keywords": ["测试"],
        "visual_cues": [
            {"timestamp": 50.0, "cue_text": "看这张图", "description": "图表"},
        ],
    }
    analysis_path = cache_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake")

    with patch("vbook.stages.screenshot.ffmpeg_lib") as mock_ffmpeg, \
         patch("vbook.stages.screenshot._get_video_duration", return_value=3600.0):
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = ScreenshotStage(
            video_path=video_file,
            cache_dir=cache_dir,
            search_window=10.0,
            dedup_window=5.0,
        )
        result = stage.run(context={
            "analysis_path": str(analysis_path),
            "scene_changes": [12.0, 48.5, 100.0],
        })

    assert result.status == StageStatus.SUCCESS
    # Should have screenshots: section 0 uses key_timestamps[10.0] snapped to scene_change[12.0],
    # plus visual_cue[50.0] snapped to scene_change[48.5]
    all_ss_timestamps = [call.kwargs.get("ss") or call.args[0]
                         for call in mock_ffmpeg.input.call_args_list
                         if "ss" in (call.kwargs or {})]
    # Verify scene_change timestamps were used (48.5 near cue 50.0)
    assert any(abs(t - 48.5) < 0.1 for t in all_ss_timestamps)


def test_screenshot_fallback_section_start(tmp_path):
    """Sections with no visual_cues and no scene_changes get a screenshot at key_timestamps[0]."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    analysis = {
        "title": "测试",
        "outline": [
            {"title": "第一节", "summary": "内容", "key_timestamps": [10.0]},
        ],
        "keywords": ["测试"],
    }
    analysis_path = cache_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake")

    with patch("vbook.stages.screenshot.ffmpeg_lib") as mock_ffmpeg, \
         patch("vbook.stages.screenshot._get_video_duration", return_value=3600.0):
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.output.return_value.overwrite_output.return_value.run = MagicMock()

        stage = ScreenshotStage(
            video_path=video_file,
            cache_dir=cache_dir,
        )
        result = stage.run(context={
            "analysis_path": str(analysis_path),
            "scene_changes": [],
        })

    assert result.status == StageStatus.SUCCESS
    # Should still get a screenshot at key_timestamps[0] = 10.0 as fallback
    assert mock_ffmpeg.input.call_count >= 1