import tempfile
import unittest
from pathlib import Path

from vbook_common.types import (
    FilterStatus,
    FrameCandidate,
    KnowledgeSection,
    TimelineLink,
    TranscriptSegment,
    VideoAsset,
    VisualAnalysis,
    VisualType,
)
from vbook_export.note import render_placeholder_note, render_sections_note, write_note


class NoteExportTest(unittest.TestCase):
    def test_render_placeholder_note_includes_run_context_and_artifacts(self) -> None:
        video = VideoAsset(
            id="lesson",
            path=Path("course/lesson.mp4"),
            course_title="Stock Course",
            lesson_title="MA Support",
        )
        segments = [
            TranscriptSegment(id="seg-000002", start=8.0, end=12.0, text="case detail"),
            TranscriptSegment(id="seg-000001", start=0.0, end=3.0, text="intro"),
        ]
        frames = [
            FrameCandidate(
                id="frame-000001",
                video_id="lesson",
                timestamp=0.0,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                width=1280,
                height=720,
                filter_status=FilterStatus.SELECTED,
            )
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.OTHER,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                vision_description="Visual analysis pending backend implementation.",
                backend="placeholder",
            )
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=3.0,
            )
        ]

        markdown = render_placeholder_note(
            video=video,
            segments=segments,
            frames=frames,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertIn("# MA Support", markdown)
        self.assertIn("- Course: Stock Course", markdown)
        self.assertIn("- Lesson: MA Support", markdown)
        self.assertIn("- Segments: 2", markdown)
        self.assertIn("- Candidate Frames: 1", markdown)
        self.assertIn("- Selected Frames: 1", markdown)
        self.assertIn("- Visual Analyses: 1", markdown)
        self.assertIn("- frame-000001: seg-000001", markdown)
        self.assertLess(
            markdown.index("[0.00s - 3.00s] intro"),
            markdown.index("[8.00s - 12.00s] case detail"),
        )

    def test_write_note_creates_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note_path = Path(tmp) / "outputs" / "lesson" / "note.md"

            written = write_note("# Lesson\n", note_path)
            content = written.read_text(encoding="utf-8")

        self.assertEqual(written.name, "note.md")
        self.assertEqual(content, "# Lesson\n")

    def test_render_sections_note_uses_knowledge_sections(self) -> None:
        video = VideoAsset(
            id="lesson",
            path=Path("course/lesson.mp4"),
            course_title="Stock Course",
            lesson_title="MA Support",
        )
        sections = [
            KnowledgeSection(
                title="Segment seg-000002",
                summary="case detail",
                source_timestamps=[8.0, 12.0],
                image_refs=["outputs/lesson/frames/selected/frame_000002.jpg"],
                key_points=["Watch volume confirmation"],
                tags=["placeholder"],
            ),
            KnowledgeSection(
                title="Segment seg-000001",
                summary="intro",
                source_timestamps=[0.0, 3.0],
                image_refs=["outputs/lesson/frames/selected/frame_000001.jpg"],
                key_points=[],
                tags=["placeholder"],
            ),
        ]

        markdown = render_sections_note(video=video, sections=sections)

        self.assertIn("# MA Support", markdown)
        self.assertIn("- Course: Stock Course", markdown)
        self.assertIn("- Sections: 2", markdown)
        self.assertLess(
            markdown.index("### Segment seg-000001"),
            markdown.index("### Segment seg-000002"),
        )
        self.assertIn("intro", markdown)
        self.assertIn("- Source: 0.00s - 3.00s", markdown)
        self.assertIn("- Image: outputs/lesson/frames/selected/frame_000001.jpg", markdown)
        self.assertIn("- Watch volume confirmation", markdown)


if __name__ == "__main__":
    unittest.main()
