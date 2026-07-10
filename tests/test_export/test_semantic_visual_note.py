from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vbook_export.semantic_visual_note import (
    build_semantic_visual_request,
    write_semantic_visual_note_package,
)


class SemanticVisualNoteTest(unittest.TestCase):
    def test_build_request_uses_timeline_text_and_skips_qwen_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lesson_output, _ = _write_lesson_output_fixture(Path(tmp))

            request, metrics = build_semantic_visual_request(
                lesson_output_dir=lesson_output,
                transcript_source_label="vtext_semantic_verified",
            )

        self.assertEqual(request["intent"], "semantic_visual_note_request")
        self.assertEqual(request["task"], "semantic_visual_course_note_synthesis")
        self.assertEqual(request["transcript_source"]["label"], "vtext_semantic_verified")
        self.assertEqual(metrics["transcript_segment_count"], 2)
        self.assertEqual(metrics["visual_evidence_count"], 1)
        self.assertEqual(metrics["skipped_error_visual_count"], 1)
        self.assertEqual(request["visual_evidence"][0]["frame_id"], "frame-000002")
        self.assertEqual(
            request["visual_evidence"][0]["linked_transcript_segment_ids"],
            ["seg-000002"],
        )
        self.assertIn("Use the timestamped transcript", request["instructions"][0])

    def test_request_only_package_writes_manifest_without_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output, _ = _write_lesson_output_fixture(root)
            output_dir = root / "semantic-preview"

            package = write_semantic_visual_note_package(
                lesson_output_dir=lesson_output,
                output_dir=output_dir,
            )
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
            request_exists = package.request_path.is_file()

        self.assertTrue(request_exists)
        self.assertIsNone(package.note_path)
        self.assertEqual(manifest["status"], "request_ready")
        self.assertEqual(manifest["workflow"], "semantic_visual_note")
        self.assertEqual(manifest["request_metrics"]["visual_evidence_count"], 1)
        self.assertEqual(manifest["safety"]["source_lesson_output"], "read_only")

    def test_existing_model_response_renders_markdown_with_copied_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output, final_image = _write_lesson_output_fixture(root)
            response_path = root / "response.json"
            response_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "title": "如何选取龙头",
                        "overview": "整合时序文本和完成态画面。",
                        "sections": [
                            {
                                "title": "龙头股筛选口诀",
                                "summary": "讲师说明超级热点龙头股的筛选条件。",
                                "key_points": ["股价位置优先", "实体涨停是关键"],
                                "source_timestamps": [12.0, 42.0],
                                "image_refs": [str(final_image)],
                                "tags": ["semantic_visual", "visual:slide"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output_dir = root / "semantic-preview"

            package = write_semantic_visual_note_package(
                lesson_output_dir=lesson_output,
                output_dir=output_dir,
                llm_response_path=response_path,
            )
            note = package.note_path.read_text(encoding="utf-8") if package.note_path else ""
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
            copied_image = output_dir / "assets" / "note" / final_image.name
            copied_image_exists = copied_image.is_file()

        self.assertEqual(manifest["status"], "preview")
        self.assertEqual(manifest["asset_count"], 1)
        self.assertTrue(copied_image_exists)
        self.assertIn("# 如何筛选龙头股？", note)
        self.assertIn("![龙头股筛选口诀](assets/note/frame_000002.jpg)", note)
        self.assertIn("讲师说明超级热点龙头股的筛选条件。", note)
        self.assertIn("- 时间：12.00s - 42.00s", note)


def _write_lesson_output_fixture(root: Path) -> tuple[Path, Path]:
    lesson_output = root / "lesson-output"
    selected_dir = lesson_output / "frames" / "selected"
    final_image = selected_dir / "frame_000002.jpg"
    error_image = selected_dir / "frame_000001.jpg"
    selected_dir.mkdir(parents=True)
    (lesson_output / "vision").mkdir(parents=True)
    error_image.write_bytes(b"error image")
    final_image.write_bytes(b"final image")
    manifest = {
        "video_asset": {
            "id": "lesson-001",
            "path": "F:/downloads/allwin/lesson.mp4",
            "course_title": "投资训练营",
            "lesson_title": "如何筛选龙头股？",
            "duration_seconds": 120.0,
        },
        "artifacts": {
            "transcript": {
                "path": "outputs/vtext-bundles/lesson/transcript.raw.srt",
                "segments": [
                    {
                        "id": "seg-000001",
                        "start": 0.0,
                        "end": 12.0,
                        "text": "今天讲如何筛选龙头股。",
                    },
                    {
                        "id": "seg-000002",
                        "start": 12.0,
                        "end": 42.0,
                        "text": "超级热点龙头选，股价位置要优先。",
                    },
                ],
            },
            "timeline": {
                "links": [
                    {
                        "frame_id": "frame-000001",
                        "transcript_segment_ids": ["seg-000001"],
                        "window_start": 0.0,
                        "window_end": 12.0,
                    },
                    {
                        "frame_id": "frame-000002",
                        "transcript_segment_ids": ["seg-000002"],
                        "window_start": 12.0,
                        "window_end": 42.0,
                    },
                ]
            },
            "vision": {
                "analysis_path": str(lesson_output / "vision" / "analysis.json"),
            },
        },
    }
    vision = {
        "analysis_count": 2,
        "analyses": [
            {
                "frame_id": "frame-000001",
                "visual_type": "slide",
                "image_path": str(error_image),
                "timestamp": 12.0,
                "ocr_text": "",
                "vision_description": "",
                "structured_observations": {
                    "qwen_service": {
                        "status": "error",
                        "http_status": 504,
                    }
                },
            },
            {
                "frame_id": "frame-000002",
                "visual_type": "slide",
                "image_path": str(final_image),
                "timestamp": 42.0,
                "ocr_text": "如何选取龙头\n超级热点龙头选\n股价位置要优先",
                "vision_description": "完成态PPT页面，列出龙头股筛选口诀。",
                "structured_observations": {
                    "topic": "如何选取龙头股",
                    "key_points": ["超级热点龙头选", "股价位置要优先"],
                    "quality": {"readability": "high"},
                },
                "confidence": 0.99,
            },
        ],
    }
    (lesson_output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )
    (lesson_output / "vision" / "analysis.json").write_text(
        json.dumps(vision, ensure_ascii=False),
        encoding="utf-8",
    )
    return lesson_output, final_image


if __name__ == "__main__":
    unittest.main()
