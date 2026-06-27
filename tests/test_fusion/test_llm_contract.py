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


if __name__ == "__main__":
    unittest.main()
