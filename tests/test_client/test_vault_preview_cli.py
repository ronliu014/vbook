from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vbook_client.cli import main


class VaultPreviewCliTest(unittest.TestCase):
    def test_vault_preview_command_writes_preview_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_note = root / "vault" / "lesson.md"
            lesson_output = root / "lesson-output"
            image = lesson_output / "frames" / "selected" / "frame_000001.jpg"
            preview_dir = root / "preview"
            vault_note.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            vault_note.write_text("# Existing Note\n\n纯文本笔记。", encoding="utf-8")
            image.write_bytes(b"fake image")
            (lesson_output / "manifest.json").write_text(
                json.dumps(
                    {"stage_status": {"vision_analysis": "done"}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (lesson_output / "vision" / "analysis.json").write_text(
                json.dumps(
                    {
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "image_path": str(image),
                                "ocr_text": "量比排行榜",
                                "vision_description": "A slide about stock ranking.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (lesson_output / "fusion" / "sections.json").write_text(
                json.dumps(
                    {
                        "sections": [
                            {
                                "title": "短线股票池",
                                "summary": "结合量比和盘口信息筛选短线候选。",
                                "source_timestamps": [12.0],
                                "image_refs": [str(image)],
                                "key_points": ["画面文字：量比排行榜"],
                                "tags": ["evidence"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "vault-preview",
                    "--vault-note",
                    str(vault_note),
                    "--lesson-output",
                    str(lesson_output),
                    "--output",
                    str(preview_dir),
                ]
            )
            enhancement_exists = (preview_dir / "enhancement.md").is_file()
            manifest_exists = (preview_dir / "manifest.json").is_file()
            image_exists = (preview_dir / "images" / "frame_000001.jpg").is_file()

        self.assertEqual(code, 0)
        self.assertTrue(enhancement_exists)
        self.assertTrue(manifest_exists)
        self.assertTrue(image_exists)

    def test_vault_enhance_command_writes_vtext_first_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note = root / "vault" / "20_Learning" / "vtext" / "lesson.md"
            lesson_output = root / "lesson-output"
            image = lesson_output / "frames" / "selected" / "frame_000001.jpg"
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"
            vtext_note.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            vtext_note.write_text(
                "# Existing Note\n\n## 量比排行榜\n\n- **量比**是短线筛选信号。\n",
                encoding="utf-8",
            )
            image.write_bytes(b"fake image")
            (lesson_output / "manifest.json").write_text(
                json.dumps(
                    {"stage_status": {"vision_analysis": "done"}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (lesson_output / "vision" / "analysis.json").write_text(
                json.dumps(
                    {
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "image_path": str(image),
                                "timestamp": 12.0,
                                "ocr_text": "量比排行榜",
                                "vision_description": "完成态页面，展示量比排行榜。",
                                "structured_observations": {"topic": "量比排行榜"},
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (lesson_output / "fusion" / "sections.json").write_text(
                json.dumps(
                    {
                        "sections": [
                            {
                                "title": "量比排行榜",
                                "summary": "结合量比和盘口信息筛选短线候选。",
                                "source_timestamps": [12.0],
                                "image_refs": [str(image)],
                                "key_points": ["画面文字：量比排行榜"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "vault-enhance",
                    "--vtext-note",
                    str(vtext_note),
                    "--lesson-output",
                    str(lesson_output),
                    "--output-note",
                    str(output_note),
                ]
            )
            note_exists = output_note.is_file()
            manifest_exists = output_note.with_suffix(".manifest.json").is_file()
            asset_exists = (
                output_note.parent / "assets" / "lesson" / "frame_000001.jpg"
            ).is_file()
            enhanced = output_note.read_text(encoding="utf-8") if note_exists else ""

        self.assertEqual(code, 0)
        self.assertTrue(note_exists)
        self.assertTrue(manifest_exists)
        self.assertTrue(asset_exists)
        self.assertIn("## 量比排行榜", enhanced)
        self.assertIn("![量比排行榜](assets/lesson/frame_000001.jpg)", enhanced)
        self.assertIn("- **量比**是短线筛选信号。", enhanced)


if __name__ == "__main__":
    unittest.main()
