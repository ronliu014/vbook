import json
import tempfile
import unittest
from pathlib import Path

from tools.production_queue_audit import (
    create_library_production_audit,
    create_production_queue_audit,
)


class ProductionQueueAuditTest(unittest.TestCase):
    def test_audits_course_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            course = "Course A"
            video_dir = root / "videos" / course
            video_dir.mkdir(parents=True)
            for name in ("Lesson A", "Lesson B", "Lesson C"):
                (video_dir / f"{name}.mp4").write_bytes(b"video")
            vtext_dir = root / "vtext" / course
            vtext_dir.mkdir(parents=True)
            (vtext_dir / "Lesson A.md").write_text("# Lesson A\n", encoding="utf-8")
            (vtext_dir / "Lesson B.md").write_text("# Lesson B\n", encoding="utf-8")
            lesson_output = root / "outputs" / "240s" / course / "Lesson A"
            _write_lesson_output(lesson_output)
            published_dir = root / "vault" / course
            published_dir.mkdir(parents=True)
            (published_dir / "Lesson A.md").write_text("# Lesson A\n", encoding="utf-8")

            package = create_production_queue_audit(
                course=course,
                vtext_root=root / "vtext",
                video_root=root / "videos",
                lesson_output_roots=[root / "outputs"],
                published_vault_root=published_dir,
                output_dir=root / "queue",
            )

            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            markdown = package.markdown_path.read_text(encoding="utf-8")

        self.assertEqual(payload["kind"], "vbook_production_queue_audit")
        self.assertEqual(payload["lesson_count"], 3)
        self.assertEqual(payload["status_counts"]["published"], 1)
        self.assertEqual(payload["status_counts"]["waiting_lesson_output"], 1)
        self.assertEqual(
            payload["status_counts"]["waiting_vtext_and_lesson_output"], 1
        )
        statuses = {item["lesson"]: item["status"] for item in payload["lessons"]}
        self.assertEqual(statuses["Lesson A"], "published")
        self.assertEqual(statuses["Lesson B"], "waiting_lesson_output")
        self.assertEqual(statuses["Lesson C"], "waiting_vtext_and_lesson_output")
        self.assertIn("Production Queue Audit: Course A", markdown)

    def test_audits_multiple_video_libraries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            book_course = root / "videos" / "读书会" / "Book Club"
            training_course = root / "videos" / "投资训练营" / "Course A"
            book_course.mkdir(parents=True)
            training_course.mkdir(parents=True)
            (book_course / "Book Lesson.mp4").write_bytes(b"video")
            (training_course / "Lesson A.mp4").write_bytes(b"video")
            vtext_note_dir = root / "vtext" / "投资训练营" / "Course A"
            vtext_note_dir.mkdir(parents=True)
            (vtext_note_dir / "Lesson A.md").write_text("# Lesson A\n", encoding="utf-8")
            _write_lesson_output(root / "outputs" / "240s" / "Course A" / "Lesson A")
            published_note_dir = root / "vbook" / "投资训练营" / "Course A"
            published_note_dir.mkdir(parents=True)
            (published_note_dir / "Lesson A.md").write_text("# Lesson A\n", encoding="utf-8")

            package = create_library_production_audit(
                video_library_roots=[
                    root / "videos" / "读书会",
                    root / "videos" / "投资训练营",
                ],
                vtext_vault_root=root / "vtext",
                lesson_output_roots=[root / "outputs"],
                published_vbook_root=root / "vbook",
                output_dir=root / "library-queue",
            )

            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            markdown = package.markdown_path.read_text(encoding="utf-8")

        self.assertEqual(payload["kind"], "vbook_production_library_audit")
        self.assertEqual(payload["library_count"], 2)
        self.assertEqual(payload["lesson_count"], 2)
        self.assertEqual(payload["status_counts"]["published"], 1)
        self.assertEqual(
            payload["status_counts"]["waiting_vtext_and_lesson_output"], 1
        )
        statuses = {
            f"{item['library']}/{item['course']}/{item['lesson']}": item["status"]
            for item in payload["lessons"]
        }
        self.assertEqual(statuses["投资训练营/Course A/Lesson A"], "published")
        self.assertEqual(
            statuses["读书会/Book Club/Book Lesson"],
            "waiting_vtext_and_lesson_output",
        )
        self.assertIn("Production Library Audit", markdown)


def _write_lesson_output(path: Path) -> None:
    (path / "vision").mkdir(parents=True)
    (path / "fusion").mkdir(parents=True)
    (path / "manifest.json").write_text("{}", encoding="utf-8")
    (path / "vision" / "analysis.json").write_text("[]", encoding="utf-8")
    (path / "fusion" / "sections.json").write_text("[]", encoding="utf-8")
