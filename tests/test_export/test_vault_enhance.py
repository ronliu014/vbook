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

    def test_anchors_case_visual_by_stock_code_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output = root / "lesson-output"
            image = lesson_output / "frames" / "selected" / "frame_000004.jpg"
            vtext_note = root / "vault" / "20_Learning" / "vtext" / "lesson.md"
            image.parent.mkdir(parents=True)
            vtext_note.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            image.write_bytes(b"annotated kline image")
            vtext_note.write_text(
                "# Golden Ratio\n\n"
                "## How to draw golden ratio\n\n"
                "Open the drawing tool and draw from high to low.\n\n"
                "## Case Two: Yunnan Germanium 002428\n\n"
                "Use the completed chart to confirm the support line.\n\n"
                "## Summary\n\n"
                "Different methods use different ranges.\n",
                encoding="utf-8",
            )
            (lesson_output / "manifest.json").write_text(
                json.dumps({"stage_status": {"vision_analysis": "done"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (lesson_output / "vision" / "analysis.json").write_text(
                json.dumps(
                    {
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000004",
                                "image_path": str(image),
                                "timestamp": 720.0,
                                "ocr_text": "Yunnan Germanium 002428\nFibonacci 61.8",
                                "vision_description": (
                                    "Completed K-line case board for Yunnan Germanium "
                                    "002428 with final support line."
                                ),
                                "structured_observations": {"topic": "K-line case"},
                                "confidence": 0.95,
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
                                "title": "How to draw golden ratio",
                                "summary": "Teacher explains how to draw golden ratio.",
                                "source_timestamps": [600.0, 720.0],
                                "image_refs": [str(image)],
                                "key_points": [],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertLess(
            enhanced.index("## Case Two: Yunnan Germanium 002428"),
            enhanced.index("![How to draw golden ratio]"),
        )
        self.assertLess(
            enhanced.index("![How to draw golden ratio]"),
            enhanced.index("## Summary"),
        )

    def test_anchors_chinese_case_visual_by_stock_name_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lesson_output = root / "lesson-output"
            image = lesson_output / "frames" / "selected" / "frame_000004.jpg"
            vtext_note = root / "vault" / "20_Learning" / "vtext" / "lesson.md"
            image.parent.mkdir(parents=True)
            vtext_note.parent.mkdir(parents=True)
            (lesson_output / "vision").mkdir(parents=True)
            (lesson_output / "fusion").mkdir(parents=True)
            image.write_bytes(b"annotated kline image")
            vtext_note.write_text(
                "# 黄金分割线绘制指南\n\n"
                "## 一、核心原则与工具准备\n\n"
                "交易软件里打开画线工具，选择黄金分割线，从高点往低点画。\n\n"
                "## 案例二：云南锗业（三连板一字板）\n\n"
                "从第三个涨停板最高价连到最后一个涨停板最低价，确认0.618支撑位。\n\n"
                "## 四、注意事项\n\n"
                "战法不同，画法不同。\n",
                encoding="utf-8",
            )
            (lesson_output / "manifest.json").write_text(
                json.dumps({"stage_status": {"vision_analysis": "done"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (lesson_output / "vision" / "analysis.json").write_text(
                json.dumps(
                    {
                        "analysis_count": 1,
                        "analyses": [
                            {
                                "frame_id": "frame-000004",
                                "image_path": str(image),
                                "timestamp": 720.0,
                                "ocr_text": "股票交易软件界面 展示云南锗业 K线图 画线工具 黄金分割线",
                                "vision_description": (
                                    "股票交易软件界面，展示云南锗业的K线图，已经画出黄金分割线支撑位。"
                                ),
                                "structured_observations": {"topic": "股票交易分析"},
                                "confidence": 0.95,
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
                                "title": "我给你讲明白黄金分割线怎幺画。首先，",
                                "summary": "讲师讲解交易软件和黄金分割线画线工具。",
                                "source_timestamps": [600.0, 720.0],
                                "image_refs": [str(image)],
                                "key_points": [],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertLess(
            enhanced.index("## 案例二：云南锗业（三连板一字板）"),
            enhanced.index("![我给你讲明白黄金分割线怎幺画。首先，]"),
        )
        self.assertLess(
            enhanced.index("![我给你讲明白黄金分割线怎幺画。首先，]"),
            enhanced.index("## 四、注意事项"),
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

    def test_url_encodes_markdown_image_paths_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output, _ = _write_lesson_fixture(root)
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson with spaces.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertIn(
            "![构建股票池之前的准备](assets/lesson%20with%20spaces/frame_000002.jpg)",
            enhanced,
        )
        self.assertNotIn("](assets/lesson with spaces/frame_000002.jpg)", enhanced)

    def test_keeps_final_visual_within_min_gap_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output = _write_multi_scene_fixture(
                root,
                [
                    _SceneFixture("起势观察", 60.0, "frame_000001.jpg", "板书刚开始"),
                    _SceneFixture("买点确认", 110.0, "frame_000002.jpg", "完成态买点确认页"),
                    _SceneFixture("复盘执行", 360.0, "frame_000003.jpg", "复盘执行页"),
                ],
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            package = write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
                min_image_gap_seconds=120.0,
            )

            enhanced = output_note.read_text(encoding="utf-8")
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))

        self.assertNotIn("frame_000001.jpg", enhanced)
        self.assertIn("frame_000002.jpg", enhanced)
        self.assertIn("frame_000003.jpg", enhanced)
        self.assertEqual(manifest["inserted_image_count"], 2)
        self.assertEqual(manifest["image_selection"]["min_image_gap_seconds"], 120.0)

    def test_honors_max_images_per_note_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output = _write_multi_scene_fixture(
                root,
                [
                    _SceneFixture("起势观察", 60.0, "frame_000001.jpg", "起势观察页"),
                    _SceneFixture("买点确认", 240.0, "frame_000002.jpg", "买点确认页"),
                    _SceneFixture("复盘执行", 420.0, "frame_000003.jpg", "复盘执行页"),
                ],
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            package = write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
                max_images_per_note=2,
            )

            enhanced = output_note.read_text(encoding="utf-8")
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(enhanced.count("![起势观察]"), 0)
        self.assertEqual(enhanced.count("![买点确认]"), 1)
        self.assertEqual(enhanced.count("![复盘执行]"), 1)
        self.assertEqual(manifest["inserted_image_count"], 2)
        self.assertEqual(manifest["image_selection"]["max_images_per_note"], 2)

    def test_skips_structured_qwen_error_visuals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output = _write_multi_scene_fixture(
                root,
                [
                    _SceneFixture(
                        "起势观察",
                        60.0,
                        "frame_000001.jpg",
                        "起势观察页",
                        qwen_error=True,
                    ),
                    _SceneFixture("买点确认", 240.0, "frame_000002.jpg", "买点确认页"),
                ],
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            package = write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))

        self.assertNotIn("frame_000001.jpg", enhanced)
        self.assertIn("frame_000002.jpg", enhanced)
        self.assertEqual(manifest["image_selection"]["skipped_error_image_count"], 1)

    def test_prefers_dense_completed_board_over_later_transition_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output = _write_multi_scene_fixture(
                root,
                [
                    _SceneFixture(
                        "反抽反弹反转",
                        180.0,
                        "frame_000001.jpg",
                        "完成态板书，包含反抽、反弹、反转的定义、区别、位置和操作要点",
                    ),
                    _SceneFixture(
                        "反抽反弹反转",
                        240.0,
                        "frame_000002.jpg",
                        "过渡页，准备进入下一节",
                    ),
                ],
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertIn("frame_000001.jpg", enhanced)
        self.assertNotIn("frame_000002.jpg", enhanced)

    def test_prefers_later_same_topic_frame_when_ocr_density_is_only_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note, lesson_output = _write_multi_scene_fixture(
                root,
                [
                    _SceneFixture(
                        "反抽反弹反转",
                        180.0,
                        "frame_000001.jpg",
                        "行情面板和风险提示文字很多，但讲解还在普通观察阶段",
                    ),
                    _SceneFixture(
                        "反抽反弹反转",
                        240.0,
                        "frame_000002.jpg",
                        "继续讲解反抽反弹反转",
                    ),
                ],
            )
            output_note = root / "vault" / "20_Learning" / "vbook" / "lesson.md"

            write_vtext_first_package(
                vtext_note_path=vtext_note,
                lesson_output_dir=lesson_output,
                output_note_path=output_note,
            )

            enhanced = output_note.read_text(encoding="utf-8")

        self.assertNotIn("frame_000001.jpg", enhanced)
        self.assertIn("frame_000002.jpg", enhanced)


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


class _SceneFixture:
    def __init__(
        self,
        title: str,
        timestamp: float,
        image_name: str,
        description: str,
        *,
        qwen_error: bool = False,
    ) -> None:
        self.title = title
        self.timestamp = timestamp
        self.image_name = image_name
        self.description = description
        self.qwen_error = qwen_error


def _write_multi_scene_fixture(
    root: Path,
    scenes: list[_SceneFixture],
) -> tuple[Path, Path]:
    lesson_output = root / "lesson-output"
    selected_dir = lesson_output / "frames" / "selected"
    vtext_note = root / "vault" / "20_Learning" / "vtext" / "lesson.md"
    selected_dir.mkdir(parents=True)
    vtext_note.parent.mkdir(parents=True)
    (lesson_output / "vision").mkdir(parents=True)
    (lesson_output / "fusion").mkdir(parents=True)
    vtext_note.write_text(
        "# 龙头战法\n\n"
        + "\n\n".join(
            f"## {scene.title}\n\n{scene.description}。" for scene in scenes
        )
        + "\n",
        encoding="utf-8",
    )
    analyses = []
    sections = []
    for index, scene in enumerate(scenes, start=1):
        image = selected_dir / scene.image_name
        image.write_bytes(f"image {index}".encode("utf-8"))
        analysis = {
            "frame_id": f"frame-{index:06d}",
            "image_path": str(image),
            "timestamp": scene.timestamp,
            "ocr_text": scene.title + "\n" + scene.description,
            "vision_description": scene.description,
            "structured_observations": {
                "topic": scene.title,
                "qwen_service": {
                    "request_id": f"vbook-frame-{index:06d}",
                },
            },
            "confidence": 0.9,
        }
        if scene.qwen_error:
            analysis["structured_observations"]["qwen_service"] = {
                "status": "error",
                "error_kind": "service_error",
                "http_status": 504,
                "service_error_code": "timeout",
            }
        analyses.append(analysis)
        sections.append(
            {
                "title": scene.title,
                "summary": scene.description,
                "source_timestamps": [scene.timestamp - 30.0, scene.timestamp],
                "image_refs": [str(image)],
                "key_points": [scene.description],
            }
        )
    (lesson_output / "manifest.json").write_text(
        json.dumps({"stage_status": {"vision_analysis": "done"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (lesson_output / "vision" / "analysis.json").write_text(
        json.dumps({"analysis_count": len(analyses), "analyses": analyses}, ensure_ascii=False),
        encoding="utf-8",
    )
    (lesson_output / "fusion" / "sections.json").write_text(
        json.dumps({"sections": sections}, ensure_ascii=False),
        encoding="utf-8",
    )
    return vtext_note, lesson_output


if __name__ == "__main__":
    unittest.main()
