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