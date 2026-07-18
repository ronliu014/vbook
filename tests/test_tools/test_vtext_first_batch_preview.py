import json
import tempfile
import unittest
from pathlib import Path

from tools.vtext_first_batch_preview import load_batch_input, run_batch_preview


class VtextFirstBatchPreviewTest(unittest.TestCase):
    def test_load_batch_input_accepts_explicit_lessons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vtext_note = root / "vtext" / "Lesson A.md"
            lesson_output = root / "lesson-output" / "Lesson A"
            vtext_note.parent.mkdir(parents=True)
            vtext_note.write_text("# Lesson A\n", encoding="utf-8")
            lesson_output.mkdir(parents=True)
            batch_input = root / "batch-input.json"
            batch_input.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "kind": "vtext_first_batch_input",
                        "dataset_id": "dataset-a",
                        "lessons": [
                            {
                                "lesson": "Lesson A",
                                "vtext_note": str(vtext_note),
                                "lesson_output": str(lesson_output),
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            loaded = load_batch_input(batch_input)

            self.assertEqual(loaded.dataset_id, "dataset-a")
            self.assertEqual(len(loaded.lessons), 1)
            self.assertEqual(loaded.lessons[0].lesson, "Lesson A")
            self.assertEqual(loaded.lessons[0].vtext_note, vtext_note)
            self.assertEqual(loaded.lessons[0].lesson_output, lesson_output)

    def test_run_batch_preview_writes_preview_manifest_without_vault_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_input, output_root = _write_valid_preview_fixture(root)

            package = run_batch_preview(
                batch_input_path=batch_input,
                output_root=output_root,
                route="vtext_first_vault_enhance",
                variant="baseline",
                max_images_per_note=1,
                min_image_gap_seconds=0,
            )

            self.assertEqual(package.status, "preview_ready")
            self.assertEqual(package.done_count, 1)
            self.assertEqual(package.failed_count, 0)
            self.assertTrue(package.json_path.is_file())
            self.assertTrue(package.markdown_path.is_file())
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["safety"]["vault_write"], "disabled")
            self.assertEqual(payload["route"], "vtext_first_vault_enhance")
            self.assertEqual(payload["variant"], "baseline")
            self.assertEqual(payload["done_count"], 1)
            note = (
                output_root
                / "renders"
                / "vtext_first_vault_enhance"
                / "baseline"
                / "Lesson A"
                / "note.md"
            )
            self.assertTrue(note.is_file())
            self.assertNotIn("F:\\vault", str(note))


def _write_valid_preview_fixture(root: Path) -> tuple[Path, Path]:
    vtext_note = root / "vtext" / "Lesson A.md"
    lesson_output = root / "lesson-output" / "Lesson A"
    output_root = root / "experiment"
    image = lesson_output / "frames" / "selected" / "frame_000001.jpg"
    vtext_note.parent.mkdir(parents=True)
    image.parent.mkdir(parents=True)
    (lesson_output / "vision").mkdir(parents=True)
    (lesson_output / "fusion").mkdir(parents=True)
    vtext_note.write_text(
        "# Lesson A\n\n## 龙头筛选\n\n这里讲筛选条件。\n",
        encoding="utf-8",
    )
    image.write_bytes(b"image")
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
                        "frame_id": "frame-000001",
                        "image_path": str(image),
                        "timestamp": 240.0,
                        "ocr_text": "龙头筛选",
                        "vision_description": "讲师展示龙头筛选条件完成页",
                        "structured_observations": {"topic": "龙头筛选"},
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
                        "title": "龙头筛选",
                        "summary": "讲师展示龙头筛选条件完成页。",
                        "source_timestamps": [180.0, 240.0],
                        "image_refs": [str(image)],
                        "key_points": ["筛选条件要聚焦龙头。"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    batch_input = root / "batch-input.json"
    batch_input.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "kind": "vtext_first_batch_input",
                "dataset_id": "dataset-a",
                "lessons": [
                    {
                        "lesson": "Lesson A",
                        "vtext_note": str(vtext_note),
                        "lesson_output": str(lesson_output),
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return batch_input, output_root


if __name__ == "__main__":
    unittest.main()
