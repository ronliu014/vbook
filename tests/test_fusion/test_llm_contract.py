import json
import math
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import KnowledgeSection, VideoAsset
from vbook_fusion.llm_contract import (
    build_llm_fusion_request,
    parse_llm_fusion_response,
    write_llm_fusion_request,
    write_llm_fusion_sections,
)


class LlmFusionContractTest(unittest.TestCase):
    def test_build_llm_fusion_request_uses_evidence_sections(self) -> None:
        video = VideoAsset(
            id="lesson-001",
            path=Path("lessons/lesson.mp4"),
            course_title="短线课",
            lesson_title="买点条件",
            duration_seconds=120.0,
        )
        sections = [
            KnowledgeSection(
                title="短线选股",
                summary="讲解：均线多头排列。",
                source_timestamps=[0.0, 14.0],
                image_refs=["outputs/lesson/frames/selected/frame_000001.jpg"],
                key_points=["均线多头排列"],
                tags=["evidence", "visual:slide"],
            )
        ]

        request = build_llm_fusion_request(video, sections)

        self.assertEqual(request["schema_version"], "1")
        self.assertEqual(request["intent"], "llm_fusion_request")
        self.assertEqual(request["task"], "course_note_synthesis")
        self.assertEqual(request["video"]["id"], "lesson-001")
        self.assertEqual(request["video"]["course_title"], "短线课")
        self.assertEqual(request["video"]["lesson_title"], "买点条件")
        self.assertEqual(request["video"]["duration_seconds"], 120.0)
        self.assertEqual(
            request["output_contract"]["required_top_level_fields"],
            ["title", "overview", "sections"],
        )
        self.assertIn("Use only provided evidence.", request["instructions"])
        self.assertEqual(len(request["evidence_sections"]), 1)
        self.assertEqual(request["evidence_sections"][0]["title"], "短线选股")
        self.assertEqual(
            request["evidence_sections"][0]["image_refs"],
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )

    def test_parse_llm_fusion_response_returns_knowledge_sections(self) -> None:
        sections = parse_llm_fusion_response(
            {
                "schema_version": "1",
                "title": "短线课",
                "overview": "本节课讲短线选股。",
                "sections": [
                    {
                        "title": "短线选股条件",
                        "summary": "说明均线和成交量条件。",
                        "key_points": ["均线多头排列", "成交量放大"],
                        "source_timestamps": [0.0, 14.0],
                        "image_refs": [
                            "outputs/lesson/frames/selected/frame_000001.jpg",
                            "outputs/lesson/frames/selected/frame_000001.jpg",
                        ],
                        "tags": ["evidence", "visual:slide", "evidence"],
                    }
                ],
            }
        )

        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "短线选股条件")
        self.assertEqual(section.summary, "说明均线和成交量条件。")
        self.assertEqual(section.key_points, ["均线多头排列", "成交量放大"])
        self.assertEqual(section.source_timestamps, [0.0, 14.0])
        self.assertEqual(
            section.image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertEqual(section.tags, ["llm", "evidence", "visual:slide"])


if __name__ == "__main__":
    unittest.main()
