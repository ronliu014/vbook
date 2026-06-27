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
from vbook_fusion.sections import (
    build_evidence_sections,
    build_placeholder_sections,
    write_fusion_sections,
)


class FusionSectionsTest(unittest.TestCase):
    def test_build_evidence_sections_uses_transcript_and_visual_evidence(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=6.0,
                text="这里讲均线多头排列是短线选股条件。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=8.0,
                end=12.0,
                text="后面进入实战案例。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                ocr_text="短线选股条件\n均线多头排列\n成交量放大",
                vision_description="一页讲解短线选股条件的幻灯片。",
                structured_observations={
                    "topic": "短线选股",
                    "key_points": ["均线多头排列", "成交量放大"],
                    "visible_elements": ["标题", "项目符号"],
                    "language": "zh-CN",
                },
                confidence=0.86,
                backend="manual-json",
            )
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=6.0,
            )
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 2)
        first = sections[0]
        self.assertEqual(first.title, "短线选股")
        self.assertIn("这里讲均线多头排列是短线选股条件。", first.summary)
        self.assertIn("视觉：一页讲解短线选股条件的幻灯片。", first.summary)
        self.assertIn("画面文字：短线选股条件", first.summary)
        self.assertEqual(first.source_timestamps, [0.0, 6.0])
        self.assertEqual(
            first.image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertIn("讲解：这里讲均线多头排列是短线选股条件。", first.key_points)
        self.assertIn("画面文字：短线选股条件\n均线多头排列\n成交量放大", first.key_points)
        self.assertIn("视觉描述：一页讲解短线选股条件的幻灯片。", first.key_points)
        self.assertIn("主题：短线选股", first.key_points)
        self.assertIn("均线多头排列", first.key_points)
        self.assertIn("成交量放大", first.key_points)
        self.assertIn("可见元素：标题、项目符号", first.key_points)
        self.assertEqual(
            first.tags,
            ["evidence", "visual:slide", "has_ocr", "has_image", "lang:zh-CN"],
        )
        self.assertEqual(sections[1].title, "后面进入实战案例。")
        self.assertEqual(sections[1].tags, ["evidence"])

    def test_build_evidence_sections_merges_adjacent_segments_with_shared_frame(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=4.0,
                text="先介绍均线多头排列。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=4.5,
                end=8.0,
                text="这里补充成交量放大。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                ocr_text="短线选股条件\n均线多头排列",
                vision_description="一页短线选股条件幻灯片。",
                structured_observations={
                    "topic": "短线选股",
                    "key_points": ["均线多头排列"],
                    "language": "zh-CN",
                },
                confidence=0.9,
                backend="manual-json",
            )
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001", "seg-000002"],
                window_start=0.0,
                window_end=8.0,
            )
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "短线选股")
        self.assertEqual(section.source_timestamps, [0.0, 8.0])
        self.assertIn("讲解：先介绍均线多头排列。 这里补充成交量放大。", section.summary)
        self.assertIn("视觉：一页短线选股条件幻灯片。", section.summary)
        self.assertIn("画面文字：短线选股条件", section.summary)
        self.assertEqual(
            section.image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertIn("讲解：先介绍均线多头排列。", section.key_points)
        self.assertIn("讲解：这里补充成交量放大。", section.key_points)
        self.assertIn("画面文字：短线选股条件\n均线多头排列", section.key_points)
        self.assertIn("视觉描述：一页短线选股条件幻灯片。", section.key_points)
        self.assertIn("主题：短线选股", section.key_points)
        self.assertIn("均线多头排列", section.key_points)
        self.assertEqual(
            section.tags,
            ["evidence", "visual:slide", "has_ocr", "has_image", "lang:zh-CN"],
        )

    def test_build_evidence_sections_merges_adjacent_segments_with_same_heading(self) -> None:
        segments = [
            TranscriptSegment(
                id="seg-000001",
                start=0.0,
                end=6.0,
                text="第一张图说明买点条件。",
            ),
            TranscriptSegment(
                id="seg-000002",
                start=9.0,
                end=14.0,
                text="第二张图继续解释买点条件。",
            ),
        ]
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                vision_description="买点条件第一页。",
                structured_observations={"topic": "买点条件"},
                backend="manual-json",
            ),
            VisualAnalysis(
                frame_id="frame-000002",
                visual_type=VisualType.SLIDE,
                image_path=Path("outputs/lesson/frames/selected/frame_000002.jpg"),
                vision_description="买点条件第二页。",
                structured_observations={"heading": "买点条件"},
                backend="manual-json",
            ),
        ]
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=6.0,
            ),
            TimelineLink(
                frame_id="frame-000002",
                transcript_segment_ids=["seg-000002"],
                window_start=9.0,
                window_end=14.0,
            ),
        ]

        sections = build_evidence_sections(
            segments=segments,
            visual_analyses=analyses,
            timeline_links=links,
        )

        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "买点条件")
        self.assertEqual(section.source_timestamps, [0.0, 14.0])
        self.assertEqual(
            section.image_refs,
            [
                "outputs/lesson/frames/selected/frame_000001.jpg",
                "outputs/lesson/frames/selected/frame_000002.jpg",
            ],
        )
        self.assertIn("视觉描述：买点条件第一页。", section.key_points)
        self.assertIn("视觉描述：买点条件第二页。", section.key_points)

    def test_build_evidence_sections_handles_transcript_without_visuals(self) -> None:
        sections = build_evidence_sections(
            segments=[
                TranscriptSegment(
                    id="seg-000001",
                    start=3.0,
                    end=5.0,
                    text="没有图片时仍然输出讲解主线。",
                )
            ],
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "没有图片时仍然输出讲解主线。")
        self.assertEqual(sections[0].summary, "讲解：没有图片时仍然输出讲解主线。")
        self.assertEqual(sections[0].source_timestamps, [3.0, 5.0])
        self.assertEqual(sections[0].image_refs, [])
        self.assertEqual(sections[0].key_points, ["讲解：没有图片时仍然输出讲解主线。"])
        self.assertEqual(sections[0].tags, ["evidence"])

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

    def test_write_fusion_sections_marks_evidence_intent(self) -> None:
        sections = build_evidence_sections(
            segments=[
                TranscriptSegment(id="seg-000001", start=0.0, end=3.0, text="intro")
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs" / "lesson" / "fusion" / "sections.json"

            written = write_fusion_sections(sections, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(data["intent"], "fusion_sections_evidence")
        self.assertEqual(data["section_count"], 1)
        self.assertEqual(data["sections"][0]["tags"], ["evidence"])


if __name__ == "__main__":
    unittest.main()
