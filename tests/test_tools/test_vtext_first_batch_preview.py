import json
import tempfile
import unittest
from pathlib import Path

from tools.vtext_first_batch_preview import load_batch_input


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


if __name__ == "__main__":
    unittest.main()
