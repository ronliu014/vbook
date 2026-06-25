import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from vbook_client.cli import main


class ManifestCliTest(unittest.TestCase):
    def test_manifest_command_writes_manifest_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = main(
                    [
                        "manifest",
                        "--video",
                        str(video),
                        "--transcript",
                        str(transcript),
                        "--output",
                        str(output),
                        "--course-title",
                        "Stock Course",
                        "--lesson-title",
                        "MA Support",
                    ]
                )

            manifest_path = output / "manifest.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn(str(manifest_path), stdout.getvalue())
        self.assertEqual(data["artifacts"]["transcript"]["segment_count"], 1)
        self.assertEqual(data["video_asset"]["lesson_title"], "MA Support")
        self.assertEqual(data["video_asset"]["course_title"], "Stock Course")

    def test_manifest_command_includes_existing_frame_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            candidate_dir = root / "outputs" / "lesson" / "frames" / "candidates"
            output = root / "outputs" / "lesson"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("image", encoding="utf-8")

            code = main(
                [
                    "manifest",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--frame-candidates-dir",
                    str(candidate_dir),
                    "--frame-interval-seconds",
                    "2",
                ]
            )

            data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["artifacts"]["frames"]["candidate_count"], 1)
        self.assertEqual(data["artifacts"]["frames"]["candidates"][0]["timestamp"], 0.0)
        self.assertEqual(data["pipeline_run"]["stage_status"]["frame_extraction"], "done")

    def test_manifest_command_can_select_existing_frame_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            selected_dir = output / "frames" / "selected"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            (candidate_dir / "frame_000002.jpg").write_text("b", encoding="utf-8")

            code = main(
                [
                    "manifest",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--frame-candidates-dir",
                    str(candidate_dir),
                    "--frame-interval-seconds",
                    "2",
                    "--select-frames",
                    "--selected-frames-dir",
                    str(selected_dir),
                    "--min-selected-frame-interval-seconds",
                    "3",
                ]
            )

            data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            selected_file_exists = (selected_dir / "frame_000001.jpg").exists()

        self.assertEqual(code, 0)
        self.assertEqual(data["artifacts"]["frames"]["selected_count"], 1)
        self.assertEqual(data["artifacts"]["frames"]["rejected_count"], 1)
        self.assertTrue(selected_file_exists)


if __name__ == "__main__":
    unittest.main()
