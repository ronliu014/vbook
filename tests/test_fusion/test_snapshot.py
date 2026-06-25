import json
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import (
    TimelineLink,
    TranscriptSegment,
    VideoAsset,
    VisualAnalysis,
    VisualType,
)
from vbook_fusion.snapshot import (
    build_fusion_prompt_snapshot,
    write_fusion_prompt_snapshot,
)


class FusionSnapshotTest(unittest.TestCase):
    def test_build_fusion_prompt_snapshot_sorts_and_counts_inputs(self) -> None:
        video = VideoAsset(
            id="lesson",
            path=Path("course/lesson.mp4"),
            course_title="Stock Course",
            lesson_title="MA Support",
        )
        segments = [
            TranscriptSegment(id="seg-000002", start=8.0, end=12.0, text="case"),
            TranscriptSegment(id="seg-000001", start=0.0, end=3.0, text="intro"),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000002",
                visual_type=VisualType.OTHER,
                image_path=Path("outputs/lesson/frames/selected/frame_000002.jpg"),
                vision_description="case chart",
                backend="placeholder",
            ),
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                ocr_text="moving average",
                backend="placeholder",
            ),
        ]
        links = [
            TimelineLink(
                frame_id="frame-000002",
                transcript_segment_ids=["seg-000002"],
                window_start=7.0,
                window_end=13.0,
            ),
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=4.0,
            ),
        ]

        snapshot = build_fusion_prompt_snapshot(
            video=video,
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(snapshot["schema_version"], "1")
        self.assertEqual(snapshot["intent"], "fusion_prompt_snapshot")
        self.assertEqual(snapshot["video"]["lesson_title"], "MA Support")
        self.assertEqual(snapshot["inputs"]["transcript_segment_count"], 2)
        self.assertEqual(snapshot["inputs"]["visual_analysis_count"], 2)
        self.assertEqual(snapshot["inputs"]["timeline_link_count"], 2)
        self.assertEqual(snapshot["transcript_segments"][0]["id"], "seg-000001")
        self.assertEqual(snapshot["visual_analyses"][0]["frame_id"], "frame-000001")
        self.assertEqual(snapshot["timeline_links"][0]["frame_id"], "frame-000001")

    def test_write_fusion_prompt_snapshot_creates_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs" / "lesson" / "fusion" / "prompt.json"
            snapshot = {
                "schema_version": "1",
                "intent": "fusion_prompt_snapshot",
                "inputs": {},
            }

            written = write_fusion_prompt_snapshot(snapshot, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written.name, "prompt.json")
        self.assertEqual(data["intent"], "fusion_prompt_snapshot")


if __name__ == "__main__":
    unittest.main()
