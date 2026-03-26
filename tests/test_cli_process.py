from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from vbook.cli.main import cli

def test_process_single_video(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    with patch("vbook.cli.process.PipelineEngine") as MockEngine:
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video), "--output", str(tmp_path)])

    assert result.exit_code == 0

def test_process_missing_video():
    runner = CliRunner()
    result = runner.invoke(cli, ["process", "/nonexistent/video.mp4"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or result.exit_code == 2

def test_process_verbose_flag(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    with patch("vbook.cli.process.PipelineEngine") as MockEngine, \
         patch("vbook.cli.process.setup_logging") as mock_setup:
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video), "--verbose"])

    mock_setup.assert_called_once()
    call_kwargs = mock_setup.call_args
    assert call_kwargs.kwargs.get("verbose") is True or call_kwargs.args[1] is True

def test_process_loads_glossary_and_creates_proofread_stage(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    glossary_file = tmp_path / "glossary.yaml"
    glossary_file.write_text(
        "domain: 投资\nterms:\n  - term: PE比\n    description: 市盈率\n",
        encoding="utf-8",
    )

    config_file = tmp_path / "vbook.yaml"
    config_file.write_text(
        f"processing:\n  glossary: {glossary_file}\n",
        encoding="utf-8",
    )

    with patch("vbook.cli.process.PipelineEngine") as MockEngine, \
         patch("vbook.cli.process.setup_logging"):
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video), "-c", str(config_file)])

    # Verify ProofreadStage was included in stages
    call_args = MockEngine.return_value.run.call_args
    stages = call_args[0][0]
    stage_names = [s.name for s in stages]
    assert "proofread" in stage_names
    # proofread should be after transcribe and before analyze
    assert stage_names.index("proofread") == stage_names.index("transcribe") + 1
    assert stage_names.index("proofread") < stage_names.index("analyze")

def test_process_includes_scene_detect_stage(tmp_path):
    from click.testing import CliRunner
    from unittest.mock import patch, MagicMock
    from vbook.cli.main import cli

    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    with patch("vbook.cli.process.PipelineEngine") as MockEngine:
        MockEngine.return_value.run.return_value = {}
        runner = CliRunner()
        result = runner.invoke(cli, ["process", str(video)])

    call_args = MockEngine.return_value.run.call_args
    stages = call_args[0][0]
    stage_names = [s.name for s in stages]
    assert "scene_detect" in stage_names
    # scene_detect should be after proofread and before analyze
    assert stage_names.index("scene_detect") < stage_names.index("analyze")
    assert stage_names.index("scene_detect") > stage_names.index("transcribe")