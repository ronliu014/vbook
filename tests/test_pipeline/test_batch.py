import json
import tempfile
import unittest
from pathlib import Path

from vbook_pipeline.batch import (
    BatchLessonResult,
    discover_batch_lessons,
    write_batch_manifest,
)


class BatchDiscoveryTest(unittest.TestCase):
    def test_discovers_media_and_matches_transcript_by_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            text_dir = input_dir / "text"
            input_dir.mkdir()
            text_dir.mkdir()
            video = input_dir / "lesson.mp4"
            video.write_text("video", encoding="utf-8")
            (text_dir / "lesson.srt").write_text("plain", encoding="utf-8")
            raw = text_dir / "lesson_raw.srt"
            raw.write_text("raw", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].media_path, video)
        self.assertEqual(plans[0].transcript_path, raw)
        self.assertEqual(plans[0].output_dir, output / "lesson")
        self.assertEqual(plans[0].lesson_id, "lesson")
        self.assertTrue(plans[0].vtext_compatible)
        self.assertIsNone(plans[0].skip_reason)

    def test_preserves_nested_relative_paths_for_output_and_transcript_lookup(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            video = input_dir / "course-a" / "lesson one.mp4"
            transcript = input_dir / "text" / "course-a" / "lesson one.srt"
            video.parent.mkdir(parents=True)
            transcript.parent.mkdir(parents=True)
            video.write_text("video", encoding="utf-8")
            transcript.write_text("transcript", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual(len(plans), 1)
        self.assertEqual(
            plans[0].relative_media_path,
            Path("course-a") / "lesson one.mp4",
        )
        self.assertEqual(plans[0].transcript_path, transcript)
        self.assertEqual(plans[0].output_dir, output / "course-a" / "lesson one")
        self.assertEqual(plans[0].lesson_id, "course-a/lesson one")

    def test_ignores_generated_and_coordination_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            real_video = input_dir / "lesson.mp4"
            real_transcript = input_dir / "text" / "lesson.srt"
            ignored_video = input_dir / "outputs" / "old.mp4"
            sync_video = input_dir / "sync" / "handoff.mp4"
            real_transcript.parent.mkdir(parents=True)
            ignored_video.parent.mkdir(parents=True)
            sync_video.parent.mkdir(parents=True)
            real_video.write_text("video", encoding="utf-8")
            real_transcript.write_text("transcript", encoding="utf-8")
            ignored_video.write_text("ignore", encoding="utf-8")
            sync_video.write_text("ignore", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual([plan.media_path for plan in plans], [real_video])

    def test_records_missing_transcript_without_dropping_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs"
            input_dir = root / "input"
            video = input_dir / "lesson.mp4"
            input_dir.mkdir()
            video.write_text("video", encoding="utf-8")

            plans = discover_batch_lessons(input_dir=input_dir, output_dir=output)

        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].media_path, video)
        self.assertIsNone(plans[0].transcript_path)
        self.assertEqual(plans[0].skip_reason, "missing_transcript")

    def test_write_batch_manifest_serializes_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "batch_manifest.json"
            result = BatchLessonResult(
                lesson_id="lesson",
                media_path=Path("lesson.mp4"),
                transcript_path=Path("text/lesson.srt"),
                output_dir=Path("outputs/lesson"),
                status="done",
                vtext_compatible=True,
                manifest_path=Path("outputs/lesson/manifest.json"),
            )

            written = write_batch_manifest([result], manifest_path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(data["lesson_count"], 1)
        self.assertEqual(data["done_count"], 1)
        self.assertEqual(data["failed_count"], 0)
        self.assertEqual(data["skipped_count"], 0)
        self.assertEqual(data["lessons"][0]["status"], "done")
        self.assertEqual(data["lessons"][0]["vtext_compatible"], True)


if __name__ == "__main__":
    unittest.main()
