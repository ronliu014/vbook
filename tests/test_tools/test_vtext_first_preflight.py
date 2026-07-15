import json
import tempfile
import unittest
from pathlib import Path

from tools.vtext_first_preflight import run_preflight, write_markdown_report


class VtextFirstPreflightTest(unittest.TestCase):
    def test_passes_when_manifest_and_markdown_images_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "lesson" / "note.md"
            image = root / "lesson" / "assets" / "note" / "frame 240.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"fake image")
            note.write_text(
                "# 如何筛选龙头股？\n\n"
                "![筛选条件](assets/note/frame%20240.jpg)\n",
                encoding="utf-8",
            )
            (note.parent / "manifest.json").write_text(
                json.dumps(
                    {
                        "text_source": "vtext",
                        "source_note": "F:/vault/20_Learning/vtext/投资训练营/note.md",
                        "output_note": str(note),
                        "inserted_image_count": 1,
                        "unmatched_image_count": 0,
                        "safety": {"source_vtext": "read_only"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = run_preflight(root)

        self.assertTrue(report.ok)
        self.assertEqual(report.note_count, 1)
        self.assertEqual(report.manifest_count, 1)
        self.assertEqual(report.image_link_count, 1)
        self.assertEqual(report.missing_image_count, 0)
        self.assertEqual(report.error_count, 0)

    def test_reports_missing_markdown_image_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "lesson" / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                "# 反抽 反弹 反转\n\n![图示](assets/note/missing.jpg)\n",
                encoding="utf-8",
            )
            (note.parent / "manifest.json").write_text(
                json.dumps(
                    {
                        "text_source": "vtext",
                        "output_note": str(note),
                        "inserted_image_count": 1,
                        "safety": {"source_vtext": "read_only"},
                    }
                ),
                encoding="utf-8",
            )

            report = run_preflight(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.missing_image_count, 1)
        self.assertIn("missing_markdown_image", {issue.code for issue in report.issues})

    def test_reports_experiment_output_that_points_to_vault_publication_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "lesson" / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text("# 误写 vault\n", encoding="utf-8")
            (note.parent / "manifest.json").write_text(
                json.dumps(
                    {
                        "text_source": "vtext",
                        "output_note": "F:/vault/20_Learning/vbook/投资训练营/note.md",
                        "inserted_image_count": 0,
                        "safety": {"source_vtext": "read_only"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = run_preflight(root)

        self.assertFalse(report.ok)
        self.assertIn("unsafe_vault_output", {issue.code for issue in report.issues})

    def test_reports_inserted_qwen_error_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "lesson" / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                "# 龙头股的上涨逻辑是什么？\n\n"
                "> qwen_service status=error http_status=504\n",
                encoding="utf-8",
            )
            (note.parent / "manifest.json").write_text(
                json.dumps(
                    {
                        "text_source": "vtext",
                        "output_note": str(note),
                        "inserted_image_count": 1,
                        "inserted_visuals": [
                            {
                                "image_path": "assets/note/frame_000240.jpg",
                                "structured_observations": {
                                    "qwen_service": {
                                        "status": "error",
                                        "http_status": 504,
                                    }
                                },
                            }
                        ],
                        "safety": {"source_vtext": "read_only"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = run_preflight(root)

        self.assertFalse(report.ok)
        self.assertIn("qwen_error_placeholder", {issue.code for issue in report.issues})

    def test_writes_human_readable_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "lesson" / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text("# 无图笔记\n", encoding="utf-8")
            report = run_preflight(root)
            report_path = root / "preflight.md"

            write_markdown_report(report, report_path)

            markdown = report_path.read_text(encoding="utf-8")

        self.assertIn("# vtext-first 预检报告", markdown)
        self.assertIn("- 笔记数量：1", markdown)
        self.assertIn("missing_manifest", markdown)


if __name__ == "__main__":
    unittest.main()
