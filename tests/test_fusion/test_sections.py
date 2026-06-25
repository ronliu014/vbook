import json
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import (
    TimelineLink,
    TranscriptSegment,
    VisualAnalysis,
    VisualType,
)
from vbook_fusion.sections import build_placeholder_sections, write_fusion_sections


class FusionSectionsTest(unittest.TestCase):
    def test_build_placeholder_sections_links_transcript_to_visual_refs(self) -> None:
        segments = [
            TranscriptSegment(id="seg-000002", start=8.0, end=12.0, text="case"),
            TranscriptSegment(id="seg-000001", start=0.0, end=3.0, text="intro"),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                ocr_text="moving average",
                backend="placeholder",
            )
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=4.0,
            )
        ]

        sections = build_placeholder_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Segment seg-000001")
        self.assertEqual(sections[0].summary, "intro")
        self.assertEqual(sections[0].source_timestamps, [0.0, 3.0])
        self.assertEqual(
            sections[0].image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertEqual(sections[0].key_points, [])
        self.assertEqual(sections[0].tags, ["placeholder"])
        self.assertEqual(sections[1].image_refs, [])

    def test_write_fusion_sections_creates_json_file(self) -> None:
        sections = build_placeholder_sections(
            segments=[
                TranscriptSegment(id="seg-000001", start=0.0, end=3.0, text="intro")
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs" / "lesson" / "fusion" / "sections.json"

            written = write_fusion_sections(sections, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written.name, "sections.json")
        self.assertEqual(data["intent"], "fusion_sections_placeholder")
        self.assertEqual(data["section_count"], 1)
        self.assertEqual(data["sections"][0]["summary"], "intro")


if __name__ == "__main__":
    unittest.main()
