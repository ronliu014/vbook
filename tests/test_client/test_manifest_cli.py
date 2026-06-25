import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from vbook_client.cli import main


class ManifestCliTest(unittest.TestCase):
    def test_build_command_writes_default_mvp_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

            code = main(
                [
                    "build",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--frame-candidates-dir",
                    str(candidate_dir),
                    "--alignment-window-seconds",
                    "3",
                ]
            )

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            note = (output / "note.md").read_text(encoding="utf-8")
            vision_exists = (output / "vision" / "analysis.json").exists()
            prompt_exists = (output / "fusion" / "prompt.json").exists()
            sections_exists = (output / "fusion" / "sections.json").exists()

        self.assertEqual(code, 0)
        self.assertTrue(vision_exists)
        self.assertTrue(prompt_exists)
        self.assertTrue(sections_exists)
        self.assertIn("## Knowledge Sections", note)
        self.assertEqual(manifest["stage_status"]["timeline_alignment"], "done")
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_prompt"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_sections"], "done")
        self.assertEqual(manifest["stage_status"]["note_export"], "done")
        self.assertEqual(manifest["stage_status"]["manifest"], "done")

    def test_build_command_accepts_srt_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.srt"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                (
                    "1\n"
                    "00:00:00,000 --> 00:00:02,000\n"
                    "intro\n"
                    "\n"
                    "2\n"
                    "00:00:02,000 --> 00:00:04,000\n"
                    "case setup\n"
                ),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

            code = main(
                [
                    "build",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--frame-candidates-dir",
                    str(candidate_dir),
                    "--alignment-window-seconds",
                    "2",
                ]
            )

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(manifest["artifacts"]["transcript"]["segment_count"], 2)
        self.assertEqual(manifest["stage_status"]["timeline_alignment"], "done")
        self.assertEqual(manifest["stage_status"]["manifest"], "done")

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

    def test_manifest_command_can_align_selected_frames_to_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps(
                    {
                        "segments": [
                            {"start": 0, "end": 3, "text": "intro"},
                            {"start": 8, "end": 12, "text": "case"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            for index in range(1, 7):
                (candidate_dir / f"frame_{index:06d}.jpg").write_text("a", encoding="utf-8")

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
                    "--align-timeline",
                    "--alignment-window-seconds",
                    "3",
                ]
            )

            data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["artifacts"]["timeline"]["link_count"], 6)
        self.assertEqual(
            data["artifacts"]["timeline"]["links"][-1]["transcript_segment_ids"],
            ["seg-000002"],
        )

    def test_manifest_command_can_write_placeholder_visual_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

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
                    "--analyze-vision-placeholder",
                ]
            )

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            vision = json.loads((output / "vision" / "analysis.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)
        self.assertEqual(vision["analyses"][0]["backend"], "placeholder")

    def test_manifest_command_can_write_placeholder_note(self) -> None:
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
                    "--write-note",
                ]
            )

            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# MA Support", note)
        self.assertIn("[0.00s - 3.00s] intro", note)
        self.assertEqual(manifest["artifacts"]["note"]["format"], "markdown")
        self.assertEqual(manifest["stage_status"]["note_export"], "done")

    def test_manifest_command_note_counts_selected_and_rejected_frames(self) -> None:
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
                    "--write-note",
                ]
            )

            note = (output / "note.md").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("- Candidate Frames: 2", note)
        self.assertIn("- Selected Frames: 1", note)

    def test_manifest_command_can_write_fusion_prompt_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps(
                    {
                        "segments": [
                            {"start": 0, "end": 3, "text": "intro"},
                            {"start": 8, "end": 12, "text": "case"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

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
                    "--align-timeline",
                    "--alignment-window-seconds",
                    "3",
                    "--analyze-vision-placeholder",
                    "--write-fusion-prompt",
                ]
            )

            prompt = json.loads((output / "fusion" / "prompt.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(prompt["intent"], "fusion_prompt_snapshot")
        self.assertEqual(prompt["inputs"]["transcript_segment_count"], 2)
        self.assertEqual(prompt["inputs"]["visual_analysis_count"], 1)
        self.assertEqual(prompt["inputs"]["timeline_link_count"], 1)
        self.assertEqual(manifest["artifacts"]["fusion"]["prompt_format"], "json")
        self.assertEqual(manifest["stage_status"]["fusion_prompt"], "done")

    def test_manifest_command_can_write_fusion_sections_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

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
                    "--align-timeline",
                    "--alignment-window-seconds",
                    "3",
                    "--analyze-vision-placeholder",
                    "--write-fusion-sections",
                ]
            )

            sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(sections["intent"], "fusion_sections_placeholder")
        self.assertEqual(sections["section_count"], 1)
        self.assertEqual(len(sections["sections"][0]["image_refs"]), 1)
        self.assertEqual(manifest["artifacts"]["fusion"]["sections_format"], "json")
        self.assertEqual(manifest["stage_status"]["fusion_sections"], "done")

    def test_manifest_command_renders_note_from_fusion_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

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
                    "--align-timeline",
                    "--alignment-window-seconds",
                    "3",
                    "--analyze-vision-placeholder",
                    "--write-fusion-sections",
                    "--write-note",
                ]
            )

            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("## Knowledge Sections", note)
        self.assertIn("### Segment seg-000001", note)
        self.assertIn("intro", note)
        self.assertIn("frame_000001.jpg", note)
        self.assertEqual(manifest["stage_status"]["note_export"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_sections"], "done")


if __name__ == "__main__":
    unittest.main()
