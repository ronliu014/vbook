import json
from pathlib import Path
from unittest.mock import patch
from vbook.pipeline.stage import StageStatus


def test_scene_detect_stage_outputs_changes(tmp_path):
    from vbook.stages.scene_detect import SceneDetectStage

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake")

    fake_changes = [10.5, 30.0, 65.2]

    with patch("vbook.stages.scene_detect.detect_scene_changes", return_value=fake_changes):
        stage = SceneDetectStage(
            video_path=video_file,
            cache_dir=cache_dir,
            sample_interval=5.0,
            threshold=0.3,
        )
        result = stage.run(context={"video_path": str(video_file)})

    assert result.status == StageStatus.SUCCESS
    assert result.output["scene_changes"] == [10.5, 30.0, 65.2]

    scene_file = cache_dir / "scene_changes.json"
    assert scene_file.exists()
    data = json.loads(scene_file.read_text(encoding="utf-8"))
    assert data["timestamps"] == [10.5, 30.0, 65.2]


def test_scene_detect_stage_empty_result(tmp_path):
    from vbook.stages.scene_detect import SceneDetectStage

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake")

    with patch("vbook.stages.scene_detect.detect_scene_changes", return_value=[]):
        stage = SceneDetectStage(
            video_path=video_file,
            cache_dir=cache_dir,
        )
        result = stage.run(context={"video_path": str(video_file)})

    assert result.status == StageStatus.SUCCESS
    assert result.output["scene_changes"] == []
