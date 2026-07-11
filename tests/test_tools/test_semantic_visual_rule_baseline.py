import json
import tempfile
import unittest
from pathlib import Path

from tools.semantic_visual_rule_baseline import write_rule_baseline


class SemanticVisualRuleBaselineTest(unittest.TestCase):
    def test_writes_rule_note_from_transcript_and_visual_evidence(self) -> None:
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
                                "ocr_text": "龙头股筛选条件",
                                "vision_description": "展示筛选龙头股的条件。",
                                "structured_observations": {
                                    "topic": "龙头股筛选",
                                    "key_points": ["趋势", "放量"],
                                },
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
                                "segments": [
                                    {
                                        "id": "s1",
                                        "start": 230.0,
                                        "end": 245.0,
                                        "text": "先看趋势是不是持续向上。",
                                    },
                                    {
                                        "id": "s2",
                                        "start": 245.0,
                                        "end": 260.0,
                                        "text": "再看成交量是不是配合放大。",
                                    },
                                ]
                            },
                            "vision": {"analysis_path": str(vision_path)},
                            "timeline": {
                                "links": [
                                    {
                                        "frame_id": "frame-240",
                                        "transcript_segment_ids": ["s1", "s2"],
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

            summaries = write_rule_baseline(
                dataset_path=dataset,
                output_root=root / "rule",
                max_visuals_per_lesson=4,
            )

            note = root / "rule" / "如何筛选龙头股？" / "note.md"
            copied = root / "rule" / "如何筛选龙头股？" / "assets" / "frame_000240.jpg"
            manifest = root / "rule" / "如何筛选龙头股？" / "manifest.json"

            self.assertEqual(len(summaries), 1)
            self.assertTrue(note.is_file())
            self.assertTrue(copied.is_file())
            markdown = note.read_text(encoding="utf-8")
            self.assertIn("### 1. 龙头股筛选", markdown)
            self.assertIn("![龙头股筛选](assets/frame_000240.jpg)", markdown)
            self.assertIn("先看趋势是不是持续向上。", markdown)
            self.assertIn("再看成交量是不是配合放大。", markdown)
            self.assertIn("展示筛选龙头股的条件。", markdown)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["section_count"], 1)
            self.assertEqual(data["asset_count"], 1)
            self.assertEqual(data["missing_image_count"], 0)

    def test_writes_empty_note_when_no_visual_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output = root / "lesson-output"
            vision_path = lesson_output / "vision" / "analysis.json"
            vision_path.parent.mkdir(parents=True)
            vision_path.write_text(json.dumps({"analyses": []}), encoding="utf-8")
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
                                "title": "Empty Lesson",
                                "lesson_output": str(lesson_output),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            write_rule_baseline(
                dataset_path=dataset,
                output_root=root / "rule",
                max_visuals_per_lesson=4,
            )

            note = (root / "rule" / "Empty Lesson" / "note.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("No non-error visual evidence", note)


if __name__ == "__main__":
    unittest.main()
