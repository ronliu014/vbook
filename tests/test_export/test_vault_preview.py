from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from vbook_export.vault_preview import (
    PreviewSources,
    load_preview_sources,
    render_enhancement_markdown,
    write_preview_package,
)


class VaultPreviewTest(unittest.TestCase):
    def test_load_preview_sources_reads_vault_note_and_lesson_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_note = root / "vault" / "lesson.md"
            lesson_output = root / "lesson-output"
            vault_note.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            vault_note.write_text("# Existing Note\n\n纯文本笔记。", encoding="utf-8")
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
                        "backend": "qwen-vision-service",
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "visual_type": "slide",
                                "image_path": str(
                                    lesson_output
                                    / "frames"
                                    / "selected"
                                    / "frame_000001.jpg"
                                ),
                                "ocr_text": "量比排行榜",
                                "vision_description": "A slide about stock ranking.",
                                "structured_observations": {"topic": "stock selection"},
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
                        "schema_version": "1",
                        "intent": "fusion_sections_evidence",
                        "section_count": 1,
                        "sections": [
                            {
                                "title": "短线股票池",
                                "summary": "结合量比和盘口信息筛选短线候选。",
                                "source_timestamps": [12.0, 30.0],
                                "image_refs": [
                                    str(
                                        lesson_output
                                        / "frames"
                                        / "selected"
                                        / "frame_000001.jpg"
                                    )
                                ],
                                "key_points": ["画面文字：量比排行榜"],
                                "tags": ["evidence", "visual:slide", "has_ocr"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            sources = load_preview_sources(vault_note, lesson_output)

        self.assertIn("Existing Note", sources.vault_note_markdown)
        self.assertEqual(sources.vision["analysis_count"], 1)
        self.assertEqual(sources.sections["section_count"], 1)
        self.assertEqual(sources.manifest["stage_status"]["vision_analysis"], "done")

    def test_render_enhancement_markdown_keeps_original_note_and_adds_visual_evidence(
        self,
    ) -> None:
        sources = _preview_sources_for_render()

        markdown = render_enhancement_markdown(sources, image_prefix="images")

        self.assertIn("# Existing Note", markdown)
        self.assertIn("## vBook 图文增强预览", markdown)
        self.assertIn("### 短线股票池", markdown)
        self.assertIn("结合量比和盘口信息筛选短线候选。", markdown)
        self.assertIn("量比排行榜", markdown)
        self.assertIn("![frame-000001](images/frame_000001.jpg)", markdown)
        self.assertIn("当前文件是预览，不会写回 vault。", markdown)

    def test_write_preview_package_writes_markdown_manifest_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = (
                root
                / "lesson-output"
                / "frames"
                / "selected"
                / "frame_000001.jpg"
            )
            image.parent.mkdir(parents=True)
            image.write_bytes(b"fake image")
            sources = _preview_sources_for_render()
            sources = replace(sources, lesson_output_dir=root / "lesson-output")
            sources.sections["sections"][0]["image_refs"] = [str(image)]
            sources.vision["analyses"][0]["image_path"] = str(image)
            preview_dir = root / "preview"

            result = write_preview_package(sources, preview_dir)

            self.assertTrue((preview_dir / "enhancement.md").is_file())
            self.assertTrue((preview_dir / "manifest.json").is_file())
            self.assertTrue((preview_dir / "images" / "frame_000001.jpg").is_file())
            manifest = json.loads(
                (preview_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_version"], "1")
            self.assertEqual(manifest["status"], "preview")
            self.assertEqual(manifest["outputs"]["enhancement_md"], "enhancement.md")
            self.assertEqual(result.preview_dir, preview_dir)


def _preview_sources_for_render() -> PreviewSources:
    return PreviewSources(
        vault_note_path=Path("F:/vault/20_Learning/投资训练营/demo.md"),
        lesson_output_dir=Path("outputs/demo"),
        vault_note_markdown="# Existing Note\n\n纯文本笔记。",
        manifest={"stage_status": {"vision_analysis": "done"}},
        vision={
            "analysis_count": 1,
            "analyses": [
                {
                    "frame_id": "frame-000001",
                    "image_path": "outputs/demo/frames/selected/frame_000001.jpg",
                    "ocr_text": "量比排行榜",
                    "vision_description": "A slide about stock ranking.",
                }
            ],
        },
        sections={
            "sections": [
                {
                    "title": "短线股票池",
                    "summary": "结合量比和盘口信息筛选短线候选。",
                    "source_timestamps": [12.0, 30.0],
                    "image_refs": ["outputs/demo/frames/selected/frame_000001.jpg"],
                    "key_points": ["画面文字：量比排行榜"],
                    "tags": ["evidence", "visual:slide", "has_ocr"],
                }
            ]
        },
    )


if __name__ == "__main__":
    unittest.main()
