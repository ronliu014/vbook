import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from vbook_client.cli import main
from vbook_common.types import FrameCandidate


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
            sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertTrue(vision_exists)
        self.assertTrue(prompt_exists)
        self.assertTrue(sections_exists)
        self.assertIn("## 课程信息", note)
        self.assertIn("## 课程总览", note)
        self.assertIn("## 核心结论", note)
        self.assertIn("## 知识结构", note)
        self.assertEqual(sections["intent"], "fusion_sections_evidence")
        self.assertEqual(
            sections["sections"][0]["tags"],
            ["evidence", "visual:other", "has_image"],
        )
        self.assertEqual(manifest["stage_status"]["timeline_alignment"], "done")
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_prompt"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_sections"], "done")
        self.assertEqual(manifest["stage_status"]["note_export"], "done")
        self.assertEqual(manifest["stage_status"]["manifest"], "done")

    def test_build_command_can_use_manual_json_visual_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            manual = root / "manual-vision.json"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            manual.write_text(
                json.dumps(
                    {
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "visual_type": "slide",
                                "ocr_text": "buy point",
                                "vision_description": "A slide about a buy point.",
                                "structured_observations": {"topic": "entry"},
                                "confidence": 0.8,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

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
                    "--vision-backend",
                    "manual-json",
                    "--visual-analysis-input",
                    str(manual),
                ]
            )

            vision = json.loads(
                (output / "vision" / "analysis.json").read_text(encoding="utf-8")
            )
            sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )
            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(vision["backend"], "manual-json")
        self.assertEqual(vision["analysis_count"], 1)
        self.assertEqual(vision["analyses"][0]["visual_type"], "slide")
        self.assertEqual(vision["analyses"][0]["ocr_text"], "buy point")
        self.assertEqual(vision["analyses"][0]["backend"], "manual-json")
        self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)
        self.assertEqual(
            manifest["artifacts"]["vision"]["analyses"][0]["structured_observations"][
                "topic"
            ],
            "entry",
        )
        self.assertEqual(sections["sections"][0]["image_refs"][0].endswith("frame_000001.jpg"), True)
        self.assertEqual(sections["intent"], "fusion_sections_evidence")
        self.assertIn("画面文字：buy point", sections["sections"][0]["key_points"])
        self.assertIn(
            "视觉描述：A slide about a buy point.",
            sections["sections"][0]["key_points"],
        )
        self.assertIn("visual:slide", sections["sections"][0]["tags"])
        self.assertIn("has_ocr", sections["sections"][0]["tags"])
        self.assertIn("frame_000001.jpg", note)
        self.assertIn("buy point", note)
        self.assertIn("**元数据**", note)
        self.assertIn("标签：evidence, visual:slide, has_ocr", note)
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")

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

    def test_build_command_extracts_frames_when_candidate_dir_omitted(self) -> None:
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

            with patch("vbook_client.cli.extract_frame_candidates") as extract:

                def fake_extract(
                    video_path: str,
                    candidate_dir: Path,
                    video_id: str,
                    interval_seconds: float,
                ) -> list[FrameCandidate]:
                    directory = Path(candidate_dir)
                    directory.mkdir(parents=True, exist_ok=True)
                    frame_a = directory / "frame_000001.jpg"
                    frame_b = directory / "frame_000002.jpg"
                    frame_a.write_bytes(b"first image")
                    frame_b.write_bytes(b"second image")
                    return [
                        FrameCandidate(
                            id="frame-000001",
                            video_id=video_id,
                            timestamp=0.0,
                            image_path=frame_a,
                            width=0,
                            height=0,
                        ),
                        FrameCandidate(
                            id="frame-000002",
                            video_id=video_id,
                            timestamp=2.5,
                            image_path=frame_b,
                            width=0,
                            height=0,
                        )
                    ]

                extract.side_effect = fake_extract
                code = main(
                    [
                        "build",
                        "--video",
                        str(video),
                        "--transcript",
                        str(transcript),
                        "--output",
                        str(output),
                        "--frame-interval-seconds",
                        "2.5",
                        "--alignment-window-seconds",
                        "3",
                        "--min-selected-frame-interval-seconds",
                        "10",
                    ]
                )
                call_kwargs = extract.call_args.kwargs

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        extract.assert_called_once()
        self.assertEqual(call_kwargs["video_path"], str(video))
        self.assertEqual(call_kwargs["candidate_dir"], output / "frames" / "candidates")
        self.assertEqual(call_kwargs["video_id"], "lesson")
        self.assertEqual(call_kwargs["interval_seconds"], 2.5)
        self.assertEqual(manifest["artifacts"]["frames"]["candidate_count"], 2)
        self.assertEqual(manifest["artifacts"]["frames"]["selected_count"], 1)
        self.assertEqual(manifest["artifacts"]["frames"]["rejected_count"], 1)
        self.assertEqual(
            manifest["artifacts"]["frames"]["selection_strategy"],
            "basic_interval_duplicate",
        )
        self.assertEqual(
            manifest["artifacts"]["frames"]["rejected"][0]["filter_reason"],
            "within_min_interval",
        )
        self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)
        self.assertEqual(manifest["artifacts"]["timeline"]["link_count"], 1)
        self.assertEqual(manifest["stage_status"]["timeline_alignment"], "done")
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_prompt"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_sections"], "done")
        self.assertEqual(manifest["stage_status"]["note_export"], "done")
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

    def test_manifest_command_can_write_evidence_fusion_sections(self) -> None:
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
        self.assertEqual(sections["intent"], "fusion_sections_evidence")
        self.assertEqual(sections["section_count"], 1)
        self.assertEqual(len(sections["sections"][0]["image_refs"]), 1)
        self.assertEqual(
            sections["sections"][0]["tags"],
            ["evidence", "visual:other", "has_image"],
        )
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
        self.assertIn("## 课程信息", note)
        self.assertIn("## 课程总览", note)
        self.assertIn("## 核心结论", note)
        self.assertIn("## 知识结构", note)
        self.assertIn("### 1. intro", note)
        self.assertIn("intro", note)
        self.assertIn("frame_000001.jpg", note)
        self.assertIn("**元数据**", note)
        self.assertIn("标签：evidence, visual:other, has_image", note)
        self.assertEqual(manifest["stage_status"]["note_export"], "done")
        self.assertEqual(manifest["stage_status"]["fusion_sections"], "done")

    def test_build_command_can_use_external_command_visual_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            script = root / "vision_stub.py"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            script.write_text(
                (
                    "import argparse, json\n"
                    "from pathlib import Path\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "args = parser.parse_args()\n"
                    "data = json.loads(Path(args.input).read_text(encoding='utf-8'))\n"
                    "frame = data['frames'][0]\n"
                    "Path(args.output).write_text(json.dumps({\n"
                    "    'analyses': [{\n"
                    "        'frame_id': frame['frame_id'],\n"
                    "        'visual_type': 'slide',\n"
                    "        'ocr_text': 'external text',\n"
                    "        'vision_description': 'External command result.',\n"
                    "        'structured_observations': {'backend': data['backend']},\n"
                    "        'confidence': 0.91,\n"
                    "    }]\n"
                    "}), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )

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
                    "--vision-backend",
                    "external-command",
                    "--vision-command",
                    f"{sys.executable} {script} --input {{input}} --output {{output}}",
                ]
            )

            vision = json.loads(
                (output / "vision" / "analysis.json").read_text(encoding="utf-8")
            )
            external_input = json.loads(
                (output / "vision" / "external" / "frames.json").read_text(
                    encoding="utf-8"
                )
            )
            external_output_exists = (
                output / "vision" / "external" / "analysis.json"
            ).exists()
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(vision["backend"], "external-command")
        self.assertEqual(vision["analysis_count"], 1)
        self.assertEqual(vision["analyses"][0]["backend"], "external-command")
        self.assertEqual(vision["analyses"][0]["ocr_text"], "external text")
        self.assertEqual(external_input["backend"], "external-command")
        self.assertEqual(external_input["frames"][0]["frame_id"], "frame-000001")
        self.assertTrue(external_output_exists)
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
        self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)

    def test_build_command_can_use_repository_vision_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            repo_root = Path(__file__).resolve().parents[2]
            script = repo_root / "tools" / "vision_stub.py"
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
                    "--vision-backend",
                    "external-command",
                    "--vision-command",
                    f"{sys.executable} {script} --input {{input}} --output {{output}}",
                ]
            )

            vision = json.loads(
                (output / "vision" / "analysis.json").read_text(encoding="utf-8")
            )
            external_output = json.loads(
                (output / "vision" / "external" / "analysis.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(external_output["backend"], "vision_stub")
        self.assertEqual(vision["backend"], "external-command")
        self.assertEqual(vision["analyses"][0]["backend"], "external-command")
        self.assertEqual(
            vision["analyses"][0]["vision_description"],
            "External command smoke analysis for frame-000001.",
        )
        self.assertEqual(
            manifest["artifacts"]["vision"]["analyses"][0]["structured_observations"][
                "source"
            ],
            "vision_stub",
        )
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")

    def test_build_command_external_command_requires_vision_command(self) -> None:
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

            with self.assertRaises(SystemExit) as exc:
                main(
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
                        "--vision-backend",
                        "external-command",
                    ]
                )

        self.assertEqual(exc.exception.code, 2)

    def test_build_command_can_run_llm_fusion_external_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            script = root / "fake_llm_fusion.py"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            script.write_text(
                (
                    "import argparse, json\n"
                    "from pathlib import Path\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "args = parser.parse_args()\n"
                    "request = json.loads(Path(args.input).read_text(encoding='utf-8'))\n"
                    "evidence = request['evidence_sections'][0]\n"
                    "Path(args.output).write_text(json.dumps({\n"
                    "    'schema_version': '1',\n"
                    "    'title': 'LLM course note',\n"
                    "    'overview': 'LLM overview.',\n"
                    "    'sections': [{\n"
                    "        'title': 'LLM refined intro',\n"
                    "        'summary': 'LLM summary from evidence.',\n"
                    "        'key_points': ['LLM point'],\n"
                    "        'source_timestamps': evidence['source_timestamps'],\n"
                    "        'image_refs': evidence['image_refs'],\n"
                    "        'tags': ['evidence', 'final'],\n"
                    "    }],\n"
                    "}, ensure_ascii=False), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )

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
                    "--llm-fusion-command",
                    f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                ]
            )

            request = json.loads(
                (output / "fusion" / "llm_request.json").read_text(encoding="utf-8")
            )
            response = json.loads(
                (output / "fusion" / "llm_response.json").read_text(encoding="utf-8")
            )
            llm_sections = json.loads(
                (output / "fusion" / "llm_sections.json").read_text(encoding="utf-8")
            )
            evidence_sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )
            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(request["intent"], "llm_fusion_request")
        self.assertEqual(len(request["evidence_sections"]), 1)
        self.assertEqual(response["title"], "LLM course note")
        self.assertEqual(evidence_sections["intent"], "fusion_sections_evidence")
        self.assertEqual(llm_sections["intent"], "llm_fusion_sections")
        self.assertEqual(llm_sections["section_count"], 1)
        self.assertEqual(llm_sections["sections"][0]["title"], "LLM refined intro")
        self.assertEqual(
            llm_sections["sections"][0]["tags"],
            ["llm", "evidence", "final"],
        )
        self.assertIn("## 知识结构", note)
        self.assertIn("### 1. LLM refined intro", note)
        self.assertIn("LLM summary from evidence.", note)
        self.assertEqual(manifest["stage_status"]["llm_fusion"], "done")
        self.assertEqual(
            manifest["artifacts"]["fusion"]["llm_request_path"],
            (output / "fusion" / "llm_request.json").as_posix(),
        )
        self.assertEqual(
            manifest["artifacts"]["fusion"]["llm_response_path"],
            (output / "fusion" / "llm_response.json").as_posix(),
        )
        self.assertEqual(
            manifest["artifacts"]["fusion"]["llm_sections_path"],
            (output / "fusion" / "llm_sections.json").as_posix(),
        )

    def test_build_command_llm_fusion_command_requires_placeholders(self) -> None:
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

            with self.assertRaises(SystemExit) as exc:
                main(
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
                        "--llm-fusion-command",
                        "python fake_llm.py --input {input}",
                    ]
                )

        self.assertEqual(exc.exception.code, 2)

    def test_build_batch_runs_each_matched_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output = root / "outputs" / "batch"
            video = input_dir / "lesson.mp4"
            transcript = input_dir / "text" / "lesson.srt"
            video.parent.mkdir(parents=True)
            transcript.parent.mkdir(parents=True)
            video.write_text("video", encoding="utf-8")
            transcript.write_text(
                "1\n00:00:00,000 --> 00:00:03,000\nintro\n",
                encoding="utf-8",
            )

            with patch("vbook_client.cli.extract_frame_candidates") as extract:

                def fake_extract(
                    video_path: str,
                    candidate_dir: Path,
                    video_id: str,
                    interval_seconds: float,
                ) -> list[FrameCandidate]:
                    directory = Path(candidate_dir)
                    directory.mkdir(parents=True, exist_ok=True)
                    frame = directory / "frame_000001.jpg"
                    frame.write_bytes(b"image")
                    return [
                        FrameCandidate(
                            id="frame-000001",
                            video_id=video_id,
                            timestamp=0.0,
                            image_path=frame,
                            width=0,
                            height=0,
                        )
                    ]

                extract.side_effect = fake_extract
                code = main(
                    [
                        "build-batch",
                        "--input",
                        str(input_dir),
                        "--output",
                        str(output),
                        "--frame-interval-seconds",
                        "30",
                        "--alignment-window-seconds",
                        "5",
                    ]
                )

            batch_manifest = json.loads(
                (output / "batch_manifest.json").read_text(encoding="utf-8")
            )
            lesson_manifest = json.loads(
                (output / "lesson" / "manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertEqual(batch_manifest["lesson_count"], 1)
        self.assertEqual(batch_manifest["done_count"], 1)
        self.assertEqual(batch_manifest["lessons"][0]["status"], "done")
        self.assertEqual(
            batch_manifest["lessons"][0]["manifest_path"],
            (output / "lesson" / "manifest.json").as_posix(),
        )
        self.assertEqual(lesson_manifest["stage_status"]["manifest"], "done")
        self.assertEqual(lesson_manifest["stage_status"]["vision_analysis"], "done")

    def test_build_batch_records_missing_transcript_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output = root / "outputs" / "batch"
            matched_video = input_dir / "matched.mp4"
            missing_video = input_dir / "missing.mp4"
            transcript = input_dir / "text" / "matched.srt"
            input_dir.mkdir()
            transcript.parent.mkdir(parents=True)
            matched_video.write_text("video", encoding="utf-8")
            missing_video.write_text("video", encoding="utf-8")
            transcript.write_text(
                "1\n00:00:00,000 --> 00:00:03,000\nintro\n",
                encoding="utf-8",
            )

            with patch("vbook_client.cli.extract_frame_candidates") as extract:

                def fake_extract(
                    video_path: str,
                    candidate_dir: Path,
                    video_id: str,
                    interval_seconds: float,
                ) -> list[FrameCandidate]:
                    directory = Path(candidate_dir)
                    directory.mkdir(parents=True, exist_ok=True)
                    frame = directory / "frame_000001.jpg"
                    frame.write_bytes(b"image")
                    return [
                        FrameCandidate(
                            id="frame-000001",
                            video_id=video_id,
                            timestamp=0.0,
                            image_path=frame,
                            width=0,
                            height=0,
                        )
                    ]

                extract.side_effect = fake_extract
                code = main(
                    [
                        "build-batch",
                        "--input",
                        str(input_dir),
                        "--output",
                        str(output),
                    ]
                )

            batch_manifest = json.loads(
                (output / "batch_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertEqual(batch_manifest["lesson_count"], 2)
        self.assertEqual(batch_manifest["done_count"], 1)
        self.assertEqual(batch_manifest["skipped_count"], 1)
        statuses = {lesson["lesson_id"]: lesson for lesson in batch_manifest["lessons"]}
        self.assertEqual(statuses["matched"]["status"], "done")
        self.assertEqual(statuses["missing"]["status"], "skipped")
        self.assertEqual(statuses["missing"]["failure_reason"], "missing_transcript")

    def test_build_batch_records_unsupported_transcript_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output = root / "outputs" / "batch"
            video = input_dir / "lesson.mp4"
            transcript = input_dir / "text" / "lesson.txt"
            input_dir.mkdir()
            transcript.parent.mkdir(parents=True)
            video.write_text("video", encoding="utf-8")
            transcript.write_text("untimed transcript", encoding="utf-8")

            code = main(
                [
                    "build-batch",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(output),
                ]
            )

            batch_manifest = json.loads(
                (output / "batch_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(code, 0)
        self.assertEqual(batch_manifest["lesson_count"], 1)
        self.assertEqual(batch_manifest["failed_count"], 1)
        self.assertEqual(batch_manifest["lessons"][0]["status"], "failed")
        self.assertEqual(
            batch_manifest["lessons"][0]["failure_reason"],
            "unsupported_transcript_format",
        )


if __name__ == "__main__":
    unittest.main()
