from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vbook_export.vault_enhance import write_vtext_first_package


class VaultEnhanceTest(unittest.TestCase):
    def test_preserves_vtext_note_and_inserts_matching_visual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, final_image = _write_lesson_fixture(root)
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"
            original_text = vtext_note.read_text(encoding="utf-8")

            package = write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
            source_after = vtext_note.read_text(encoding="utf-8")
            asset_exists = (
                output_note.parent / "assets" / "lesson" / final_image.name
            ).is_file()

        self.assertEqual(source_after, original_text)
        self.assertIn("# 如何高效选股", enhanced)
        self.assertIn("## 构建股票池之前的准备", enhanced)
        self.assertIn("- **聚焦龙头**，不要什么票都放进来。", enhanced)
        self.assertIn("## 复盘执行", enhanced)
        self.assertIn(
            "![构建股票池之前的准备](assets/lesson/frame_000002.jpg)",
            enhanced,
        )
        self.assertIn("> 图示补充：完成态PPT页面", enhanced)
        self.assertLess(
            enhanced.index("![构建股票池之前的准备]"),
            enhanced.index("## 复盘执行"),
        )
        self.assertTrue(asset_exists)
        self.assertEqual(manifest["text_source"], "vtext")
        self.assertEqual(manifest["source_note"], str(vtext_note))
        self.assertEqual(manifest["output_note"], str(output_note))
        self.assertEqual(manifest["inserted_image_count"], 1)
        self.assertEqual(manifest["unmatched_image_count"], 0)
        self.assertEqual(manifest["safety"], {"source_vtext": "read_only"})

    def test_places_uncertain_visuals_in_confirmation_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, final_image = _write_lesson_fixture(
                root,
                note_markdown="# 如何高效选股\n\n## 完全不同的主题\n\n这里只讲仓位管理。\n",
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")
            manifest = json.loads(
                output_note.with_suffix(".manifest.json").read_text(encoding="utf-8")
            )
            asset_exists = (
                output_note.parent / "assets" / "lesson" / final_image.name
            ).is_file()

        self.assertIn("## 图示补充待确认", enhanced)
        self.assertIn(
            "![构建股票池之前的准备](assets/lesson/frame_000002.jpg)",
            enhanced,
        )
        self.assertTrue(asset_exists)
        self.assertEqual(manifest["inserted_image_count"], 0)
        self.assertEqual(manifest["unmatched_image_count"], 1)

    def test_matches_section_body_when_heading_is_general(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, _ = _write_lesson_fixture(
                root,
                note_markdown=(
                    "# 如何高效选股\n\n"
                    "## 核心原则\n\n"
                    "构建股票池时必须关注近期热点、频繁涨停和上升趋势。\n\n"
                    "## 复盘执行\n\n"
                    "收盘后更新候选池。\n"
                ),
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertLess(
            enhanced.index("## 核心原则"),
            enhanced.index("![构建股票池之前的准备]"),
        )
        self.assertLess(
            enhanced.index("![构建股票池之前的准备]"),
            enhanced.index("## 复盘执行"),
        )

    def test_ignores_source_quote_block_when_matching_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, _ = _write_lesson_fixture(
                root,
                note_markdown=(
                    "# 如何高效选股\n\n"
                    "## 筛选标准\n\n"
                    "构建股票池时必须关注近期热点、频繁涨停和上升趋势。\n\n"
                    "## 集合竞价选股（预告）\n\n"
                    "此处只是预告后续课程。\n\n"
                    "> [!quote]- 原文（纠错全文）\n"
                    "> 构建股票池之前的准备，聚焦龙头，近期热点，频繁涨停。\n"
                ),
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertLess(
            enhanced.index("## 筛选标准"),
            enhanced.index("![构建股票池之前的准备]"),
        )
        self.assertLess(
            enhanced.index("![构建股票池之前的准备]"),
            enhanced.index("## 集合竞价选股（预告）"),
        )

    def test_matches_stock_cultivation_visual_to_raising_stock_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, _ = _write_lesson_fixture(
                root,
                note_markdown=(
                    "# 如何高效选股\n\n"
                    "## 股票池的日常维护（养股）\n\n"
                    "### 3. 养股策略\n\n"
                    "等待启动信号，严禁提前入场。\n\n"
                    "## 集合竞价选股（预告）\n\n"
                    "此处只是预告后续课程。\n"
                ),
            )
            _rewrite_single_visual(
                lesson_output,
                title="股票养殖方法",
                description="PPT教学页面，主题为股票养殖方法。",
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertLess(enhanced.index("### 3. 养股策略"), enhanced.index("![股票养殖方法]"))
        self.assertLess(
            enhanced.index("![股票养殖方法]"),
            enhanced.index("## 集合竞价选股（预告）"),
        )

    def test_honors_explicit_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, _ = _write_lesson_fixture(root)
            output_note = root / "enhanced" / "lesson.md"
            manifest_path = root / "manifests" / "lesson.vbook.json"

            package = write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
                manifest_path=manifest_path,
            )
            manifest_exists = manifest_path.is_file()

        self.assertEqual(package.manifest_path, manifest_path)
        self.assertTrue(manifest_exists)


def _write_lesson_fixture(
    root: Path,
    note_markdown: str | None = None,
) -> tuple[Path, Path, Path]:
    lesson_output = root / "lesson-output"
    first_image = lesson_output / "frames" / "selected" / "frame_000001.jpg"
    final_image = lesson_output / "frames" / "selected" / "frame_000002.jpg"
    vtext_note = root / "vault" / "20_Learning" / "vtext" / "lesson.md"
    vtext_note.parent.mkdir(parents=True)
    first_image.parent.mkdir(parents=True)
    (lesson_output / "vision").mkdir(parents=True)
    (lesson_output / "fusion").mkdir(parents=True)
    vtext_note.write_text(
        note_markdown
        or (
            "# 如何高效选股\n\n"
            "## 构建股票池之前的准备\n\n"
            "- **聚焦龙头**，不要什么票都放进来。\n"
            "- 结合近期热点和频繁涨停筛选。\n\n"
            "## 复盘执行\n\n"
            "收盘后更新候选池。\n"
        ),
        encoding="utf-8",
    )
    first_image.write_bytes(b"first image")
    final_image.write_bytes(b"final image")
    (lesson_output / "manifest.json").write_text(
        json.dumps({"stage_status": {"vision_analysis": "done"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (lesson_output / "vision" / "analysis.json").write_text(
        json.dumps(
            {
                "analysis_count": 2,
                "analyses": [
                    {
                        "frame_id": "frame-000001",
                        "image_path": str(first_image),
                        "timestamp": 60.0,
                        "ocr_text": "构建股票池之前的准备",
                        "vision_description": "板书刚开始，只有标题。",
                        "structured_observations": {
                            "topic": "构建股票池之前的准备"
                        },
                    },
                    {
                        "frame_id": "frame-000002",
                        "image_path": str(final_image),
                        "timestamp": 180.0,
                        "ocr_text": "构建股票池之前的准备\n聚焦龙头\n近期热点\n频繁涨停",
                        "vision_description": "完成态PPT页面，包含股票池筛选清单。",
                        "structured_observations": {
                            "topic": "构建股票池之前的准备"
                        },
                    },
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
                        "title": "构建股票池之前的准备",
                        "summary": "讲师开始说明股票池需要层层筛选。",
                        "source_timestamps": [0.0, 90.0],
                        "image_refs": [str(first_image)],
                        "key_points": ["讲解：股票池不是越多越好"],
                    },
                    {
                        "title": "构建股票池之前的准备",
                        "summary": "讲师补全股票池筛选条件。",
                        "source_timestamps": [90.0, 210.0],
                        "image_refs": [str(final_image)],
                        "key_points": ["讲解：必须聚焦龙头"],
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return vtext_note, lesson_output, final_image


def _rewrite_single_visual(
    lesson_output: Path,
    *,
    title: str,
    description: str,
) -> None:
    image = lesson_output / "frames" / "selected" / "frame_000002.jpg"
    (lesson_output / "vision" / "analysis.json").write_text(
        json.dumps(
            {
                "analysis_count": 1,
                "analyses": [
                    {
                        "frame_id": "frame-000002",
                        "image_path": str(image),
                        "timestamp": 180.0,
                        "ocr_text": title,
                        "vision_description": description,
                        "structured_observations": {"topic": title},
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
                        "title": title,
                        "summary": description,
                        "source_timestamps": [120.0, 180.0],
                        "image_refs": [str(image)],
                        "key_points": [],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
