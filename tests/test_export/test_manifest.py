import json
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import StageStatus, TranscriptSegment
from vbook_export.manifest import build_manifest, write_manifest


class ManifestExportTest(unittest.TestCase):
    def test_build_manifest_records_inputs_outputs_and_stage_status(self) -> None:
        segments = [TranscriptSegment(id="seg-000001", start=0, end=4, text="intro")]

        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=segments,
            config={"vision_backend": "multimodal"},
            course_title="Stock Course",
            lesson_title="MA Support",
        )

        self.assertEqual(manifest.video_asset.id, "lesson")
        self.assertEqual(manifest.video_asset.path, Path("course/lesson.mp4"))
        self.assertEqual(manifest.video_asset.course_title, "Stock Course")
        self.assertEqual(manifest.video_asset.lesson_title, "MA Support")
        self.assertEqual(manifest.artifacts["transcript"]["segment_count"], 1)
        self.assertEqual(
            manifest.artifacts["transcript"]["path"],
            Path("course/transcript.json"),
        )
        self.assertEqual(manifest.pipeline_run.stage_status["transcript_import"], StageStatus.DONE)
        self.assertEqual(manifest.stage_status["manifest"], StageStatus.DONE)
        self.assertEqual(manifest.note_path, Path("outputs/lesson/note.md"))

    def test_write_manifest_creates_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "lesson"
            manifest = build_manifest(
                video_path=Path("course/lesson.mp4"),
                transcript_path=Path("course/transcript.json"),
                output_dir=output_dir,
                segments=[],
                config={},
            )

            written = write_manifest(manifest, output_dir / "manifest.json")
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written.name, "manifest.json")
        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["transcript_source"], "imported")
        self.assertEqual(data["stage_status"]["manifest"], "done")
        self.assertEqual(data["pipeline_run"]["stage_status"]["manifest"], "done")


if __name__ == "__main__":
    unittest.main()
