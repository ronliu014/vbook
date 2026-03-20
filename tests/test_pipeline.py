import pytest
from pathlib import Path
from vbook.pipeline.stage import Stage, StageResult, StageStatus
from vbook.pipeline.tracker import ProcessingTracker

def test_stage_result_success():
    result = StageResult(status=StageStatus.SUCCESS, output={"key": "value"})
    assert result.status == StageStatus.SUCCESS
    assert result.output["key"] == "value"

def test_tracker_save_and_load(tmp_path):
    tracker = ProcessingTracker(tmp_path / ".vbook_cache")
    tracker.mark_complete("audio_extract", {"audio_path": "/tmp/audio.wav"})

    tracker2 = ProcessingTracker(tmp_path / ".vbook_cache")
    assert tracker2.is_complete("audio_extract")
    assert tracker2.get_output("audio_extract")["audio_path"] == "/tmp/audio.wav"

def test_tracker_incomplete_stage(tmp_path):
    tracker = ProcessingTracker(tmp_path / ".vbook_cache")
    assert not tracker.is_complete("audio_extract")
    assert tracker.get_output("audio_extract") is None