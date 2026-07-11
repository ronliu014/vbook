import json
import tempfile
import unittest
from pathlib import Path

from tools.qwen_visual_evidence_pack import write_visual_evidence_pack


class QwenVisualEvidencePackTest(unittest.TestCase):
    def test_writes_markdown_pack_and_copies_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output = root / "lesson-output"
            image = lesson_output / "frames" / "selected" / "frame_000240.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"fake-image")
            vision_path = lesson_output / "vision" / "analysis.json"
            vision_path.parent.mkdir(parents=True)
            vision_path.write_text(
                json.dumps(
                    {
                        "analyses": [
                            {
                                "frame_id": "frame-240",
                                "timestamp": 240.0,
                                "image_path": str(image),
                                "visual_type": "slide",
                                "ocr_text": "龙头股 条件",
                                "vision_description": "讲师展示龙头股筛选条件。",
                                "structured_observations": {
                                    "topic": "龙头股筛选",
                                    "key_points": ["放量", "趋势"],
                                    "quality": "complete",
                                },
                                "confidence": 0.8,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            lesson_output.mkdir(exist_ok=True)
            (lesson_output / "manifest.json").write_text(
                json.dumps(
                    {
                        "video_asset": {
                            "course_title": "韩珂龙头班：基础篇",
                            "lesson_title": "如何筛选龙头股？",
                        },
                        "artifacts": {
                            "transcript": {
                                "path": "transcript.json",
                                "segments": [
                                    {
                                        "id": "s1",
                                        "start": 230.0,
                                        "end": 260.0,
                                        "text": "这里讲龙头股筛选条件。",
                                    }
                                ],
                            },
                            "vision": {"analysis_path": str(vision_path)},
                            "timeline": {
                                "links": [
                                    {
                                        "frame_id": "frame-240",
                                        "transcript_segment_ids": ["s1"],
                                        "window_start": 220.0,
                                        "window_end": 280.0,
                                    }
                                ]
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            dataset = root / "dataset.json"
            dataset.write_text(
                json.dumps(
                    {
                        "lessons": [
                            {
                                "lesson_id": "lesson-001",
                                "title": "如何筛选龙头股？",
                                "course": "韩珂龙头班：基础篇",
                                "lesson_output": str(lesson_output),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output = root / "pack"

            result = write_visual_evidence_pack(
                dataset_path=dataset,
                output_root=output,
                max_visuals_per_lesson=4,
            )

            note = output / "如何筛选龙头股？" / "visual-evidence.md"
            manifest = output / "如何筛选龙头股？" / "manifest.json"
            copied = output / "如何筛选龙头股？" / "assets" / "frame_000240.jpg"

            self.assertEqual(len(result), 1)
            self.assertTrue(note.is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(copied.is_file())
            markdown = note.read_text(encoding="utf-8")
            self.assertIn("# 如何筛选龙头股？", markdown)
            self.assertIn("龙头股 条件", markdown)
            self.assertIn("讲师展示龙头股筛选条件。", markdown)
            self.assertIn("![frame-240](assets/frame_000240.jpg)", markdown)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["visual_evidence_count"], 1)
            self.assertEqual(data["missing_image_count"], 0)

    def test_skips_qwen_error_visuals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output = root / "lesson-output"
            vision_path = lesson_output / "vision" / "analysis.json"
            vision_path.parent.mkdir(parents=True)
            vision_path.write_text(
                json.dumps(
                    {
                        "analyses": [
                            {
                                "frame_id": "frame-error",
                                "timestamp": 240.0,
                                "image_path": str(root / "missing.jpg"),
                                "structured_observations": {
                                    "qwen_service": {"status": "error"}
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (lesson_output / "manifest.json").write_text(
                json.dumps(
                    {
                        "artifacts": {
                            "transcript": {"segments": []},
                            "vision": {"analysis_path": str(vision_path)},
                            "timeline": {"links": []},
                        }
                    }
                ),
                encoding="utf-8",
            )
            dataset = root / "dataset.json"
            dataset.write_text(
                json.dumps(
                    {
                        "lessons": [
                            {
                                "lesson_id": "lesson-001",
                                "title": "Error Lesson",
                                "lesson_output": str(lesson_output),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output = root / "pack"

            write_visual_evidence_pack(
                dataset_path=dataset,
                output_root=output,
                max_visuals_per_lesson=4,
            )

            manifest = json.loads(
                (output / "Error Lesson" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            note = (output / "Error Lesson" / "visual-evidence.md").read_text(
                encoding="utf-8"
            )

            self.assertEqual(manifest["visual_evidence_count"], 0)
            self.assertEqual(manifest["skipped_error_visual_count"], 1)
            self.assertIn("No non-error visual evidence", note)


if __name__ == "__main__":
    unittest.main()
