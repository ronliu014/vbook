import logging
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

from vbook.pipeline.engine import PipelineEngine

class MockStage(Stage):
    name = "mock_stage"
    call_count = 0

    def run(self, context: dict) -> StageResult:
        self.call_count += 1
        return StageResult(status=StageStatus.SUCCESS, output={"done": True})

class FailThenSucceedStage(Stage):
    name = "flaky_stage"
    call_count = 0

    def run(self, context: dict) -> StageResult:
        self.call_count += 1
        if self.call_count < 3:
            raise RuntimeError("Transient error")
        return StageResult(status=StageStatus.SUCCESS, output={"done": True})

def test_engine_runs_stages(tmp_path):
    stage = MockStage()
    engine = PipelineEngine(cache_dir=tmp_path / ".vbook_cache", max_retries=1)
    results = engine.run([stage], context={})
    assert results["mock_stage"].status == StageStatus.SUCCESS

def test_engine_skips_completed(tmp_path):
    cache_dir = tmp_path / ".vbook_cache"
    tracker = ProcessingTracker(cache_dir)
    tracker.mark_complete("mock_stage", {"done": True})

    stage = MockStage()
    engine = PipelineEngine(cache_dir=cache_dir, max_retries=1)
    engine.run([stage], context={})
    assert stage.call_count == 0

def test_engine_retries_on_failure(tmp_path):
    stage = FailThenSucceedStage()
    engine = PipelineEngine(cache_dir=tmp_path / ".vbook_cache", max_retries=3)
    results = engine.run([stage], context={})
    assert results["flaky_stage"].status == StageStatus.SUCCESS
    assert stage.call_count == 3

def test_engine_logs_stage_start_and_complete(tmp_path, caplog):
    class FakeStage(Stage):
        name = "fake"
        def run(self, context):
            return StageResult(status=StageStatus.SUCCESS, output={})
        def can_skip(self, tracker):
            return False

    with caplog.at_level(logging.DEBUG, logger="vbook"):
        engine = PipelineEngine(cache_dir=tmp_path, max_retries=1)
        engine.run([FakeStage()], context={})

    messages = [r.message for r in caplog.records]
    assert any("fake" in m for m in messages)

def test_retry_logs_on_failure(caplog):
    from vbook.utils.retry import with_retry

    attempts = []
    def flaky():
        attempts.append(1)
        if len(attempts) < 2:
            raise ValueError("transient error")
        return "ok"

    with caplog.at_level(logging.WARNING, logger="vbook"):
        result = with_retry(flaky, max_retries=3, base_delay=0)

    assert result == "ok"
    assert any("transient error" in r.message for r in caplog.records)