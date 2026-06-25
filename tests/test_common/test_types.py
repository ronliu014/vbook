import json
import unittest
from pathlib import Path

from vbook_common.serialization import to_jsonable
from vbook_common.types import (
    FrameCandidate,
    Manifest,
    PipelineRun,
    StageStatus,
    TranscriptSegment,
    TranscriptSourceType,
    VideoAsset,
    VisualAnalysis,
    VisualType,
)


class CommonTypesTest(unittest.TestCase):
    def test_visual_analysis_serializes_kline_case_as_string(self) -> None:
        analysis = VisualAnalysis(
            frame_id="frame-001",
            visual_type=VisualType.KLINE_CASE,
            image_path=Path("outputs/lesson/frames/selected/frame-001.jpg"),
            ocr_text="MA20",
            vision_description="K line case showing a moving average support entry.",
            structured_observations={"entry": "MA20 support"},
            confidence=0.82,
            backend="qwen-vl",
        )

        data = to_jsonable(analysis)

        self.assertEqual(data["visual_type"], "kline_case")
        self.assertEqual(
            data["image_path"],
            "outputs/lesson/frames/selected/frame-001.jpg",
        )
        json.dumps(data)

    def test_manifest_nested_dataclasses_are_json_safe(self) -> None:
        video = VideoAsset(
            id="lesson-001",
            path=Path("courses/lesson.mp4"),
            course_title="Trading Course",
            lesson_title="Moving Average Support",
            duration_seconds=3600.0,
        )
        transcript = TranscriptSegment(
            id="seg-001",
            start=12.5,
            end=20.0,
            text="Here is a moving average support case.",
            source=TranscriptSourceType.IMPORTED,
        )
        frame = FrameCandidate(
            id="frame-001",
            video_id="lesson-001",
            timestamp=15.0,
            image_path=Path("outputs/lesson/frames/frame-001.jpg"),
            width=1920,
            height=1080,
        )
        run = PipelineRun(
            run_id="run-001",
            config={"vision_backend": "multimodal"},
            stage_status={"frame_extraction": StageStatus.DONE},
            output_paths={"note": Path("outputs/lesson/note.md")},
        )
        manifest = Manifest(
            video_asset=video,
            transcript_source=TranscriptSourceType.IMPORTED,
            pipeline_run=run,
            artifacts={"frames": [frame], "transcript": [transcript]},
            note_path=Path("outputs/lesson/note.md"),
            stage_status={"manifest": StageStatus.DONE},
        )

        data = to_jsonable(manifest)

        self.assertEqual(data["video_asset"]["id"], "lesson-001")
        self.assertEqual(data["transcript_source"], "imported")
        self.assertEqual(data["pipeline_run"]["stage_status"]["frame_extraction"], "done")
        self.assertEqual(data["artifacts"]["frames"][0]["image_path"], "outputs/lesson/frames/frame-001.jpg")
        json.dumps(data)


if __name__ == "__main__":
    unittest.main()
