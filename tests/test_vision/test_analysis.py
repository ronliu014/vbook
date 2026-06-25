import json
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import FrameCandidate, VisualAnalysis, VisualType
from vbook_vision.analysis import analyze_frames_placeholder, write_visual_analysis


class VisualAnalysisTest(unittest.TestCase):
    def test_analyze_frames_placeholder_creates_visual_analysis_records(self) -> None:
        frames = [
            FrameCandidate("frame-000001", "lesson", 0.0, Path("frame_000001.jpg"), 0, 0)
        ]

        analyses = analyze_frames_placeholder(frames)

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
        self.assertEqual(analyses[0].image_path, Path("frame_000001.jpg"))
        self.assertEqual(analyses[0].backend, "placeholder")
        self.assertIn("pending", analyses[0].vision_description)

    def test_write_visual_analysis_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vision" / "analysis.json"
            analyses = [
                VisualAnalysis(
                    frame_id="frame-000001",
                    visual_type=VisualType.OTHER,
                    image_path=Path("frame.jpg"),
                    backend="placeholder",
                )
            ]

            written = write_visual_analysis(analyses, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(data["analysis_count"], 1)
        self.assertEqual(data["analyses"][0]["visual_type"], "other")
        self.assertEqual(data["backend"], "placeholder")


if __name__ == "__main__":
    unittest.main()
