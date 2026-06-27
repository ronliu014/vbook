import json
import sys
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import FrameCandidate, VisualAnalysis, VisualType
from vbook_vision.analysis import (
    analyze_frames,
    analyze_frames_placeholder,
    write_visual_analysis,
)


class VisualAnalysisTest(unittest.TestCase):
    def _frame(self, image: Path, frame_id: str = "frame-000001") -> FrameCandidate:
        image.write_bytes(b"image")
        return FrameCandidate(
            id=frame_id,
            video_id="lesson",
            timestamp=0.0,
            image_path=image,
            width=1280,
            height=720,
        )

    def test_analyze_frames_placeholder_creates_visual_analysis_records(self) -> None:
        frames = [
            FrameCandidate("frame-000001", "lesson", 0.0, Path("frame_000001.jpg"), 0, 0)
        ]

        analyses = analyze_frames_placeholder(frames)

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
        self.assertEqual(analyses[0].image_path, Path("frame_000001.jpg"))
        self.assertEqual(analyses[0].backend, "placeholder")
        self.assertIn("pending", analyses[0].vision_description)

    def test_write_visual_analysis_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vision" / "analysis.json"
            analyses = [
                VisualAnalysis(
                    frame_id="frame-000001",
                    visual_type=VisualType.OTHER,
                    image_path=Path("frame.jpg"),
                    backend="placeholder",
                )
            ]

            written = write_visual_analysis(analyses, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(data["analysis_count"], 1)
        self.assertEqual(data["analyses"][0]["visual_type"], "other")
        self.assertEqual(data["backend"], "placeholder")

    def test_analyze_frames_dispatches_placeholder_backend(self) -> None:
        frames = [
            FrameCandidate("frame-000001", "lesson", 0.0, Path("frame_000001.jpg"), 0, 0)
        ]

        analyses = analyze_frames(frames, backend="placeholder")

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].backend, "placeholder")

    def test_manual_json_loads_object_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps(
                    {
                        "backend": "manual-json",
                        "analyses": [
                            {
                                "frame_id": "frame-000001",
                                "visual_type": "slide",
                                "ocr_text": "entry signal",
                                "vision_description": "A short-term stock selection slide.",
                                "structured_observations": {"topic": "stock selection"},
                                "confidence": 0.9,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            analyses = analyze_frames(
                frames,
                backend="manual-json",
                visual_analysis_input=manual,
            )

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].visual_type, VisualType.SLIDE)
        self.assertEqual(analyses[0].image_path, image)
        self.assertEqual(analyses[0].ocr_text, "entry signal")
        self.assertEqual(
            analyses[0].vision_description,
            "A short-term stock selection slide.",
        )
        self.assertEqual(analyses[0].structured_observations["topic"], "stock selection")
        self.assertEqual(analyses[0].confidence, 0.9)
        self.assertEqual(analyses[0].backend, "manual-json")

    def test_manual_json_loads_list_format_and_defaults_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000002.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps(
                    [
                        {
                            "frame_id": "frame-000002",
                            "vision_description": "A chart example.",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000002", "lesson", 5.0, image, 0, 0)]

            analyses = analyze_frames(
                frames,
                backend="manual-json",
                visual_analysis_input=manual,
            )

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
        self.assertEqual(analyses[0].image_path, image)
        self.assertEqual(analyses[0].ocr_text, "")
        self.assertEqual(analyses[0].structured_observations, {})
        self.assertEqual(analyses[0].backend, "manual-json")

    def test_manual_json_allows_partial_frame_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_a = root / "frame_000001.jpg"
            image_b = root / "frame_000002.jpg"
            manual = root / "manual.json"
            image_a.write_bytes(b"a")
            image_b.write_bytes(b"b")
            manual.write_text(
                json.dumps(
                    [
                        {
                            "frame_id": "frame-000002",
                            "visual_type": "kline_case",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            frames = [
                FrameCandidate("frame-000001", "lesson", 0.0, image_a, 0, 0),
                FrameCandidate("frame-000002", "lesson", 5.0, image_b, 0, 0),
            ]

            analyses = analyze_frames(
                frames,
                backend="manual-json",
                visual_analysis_input=manual,
            )

        self.assertEqual([analysis.frame_id for analysis in analyses], ["frame-000002"])
        self.assertEqual(analyses[0].visual_type, VisualType.KLINE_CASE)

    def test_manual_json_rejects_invalid_visual_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps([{"frame_id": "frame-000001", "visual_type": "chart"}]),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "visual_type"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_manual_json_rejects_duplicate_frame_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps(
                    [
                        {"frame_id": "frame-000001"},
                        {"frame_id": "frame-000001"},
                    ]
                ),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "Duplicate frame_id"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_manual_json_rejects_unknown_frame_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(
                json.dumps([{"frame_id": "frame-999999"}]),
                encoding="utf-8",
            )
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "Unknown frame_id"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_manual_json_rejects_malformed_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            manual = root / "manual.json"
            image.write_bytes(b"image")
            manual.write_text(json.dumps({"items": []}), encoding="utf-8")
            frames = [FrameCandidate("frame-000001", "lesson", 0.0, image, 0, 0)]

            with self.assertRaisesRegex(ValueError, "analyses"):
                analyze_frames(
                    frames,
                    backend="manual-json",
                    visual_analysis_input=manual,
                )

    def test_external_command_writes_frame_input_and_loads_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "vision_stub.py"
            input_capture = root / "input_capture.json"
            script.write_text(
                (
                    "import argparse, json\n"
                    "from pathlib import Path\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "args = parser.parse_args()\n"
                    "data = json.loads(Path(args.input).read_text(encoding='utf-8'))\n"
                    f"Path({str(input_capture)!r}).write_text(json.dumps(data), encoding='utf-8')\n"
                    "frame = data['frames'][0]\n"
                    "Path(args.output).write_text(json.dumps({\n"
                    "    'analyses': [{\n"
                    "        'frame_id': frame['frame_id'],\n"
                    "        'visual_type': 'slide',\n"
                    "        'image_path': frame['image_path'],\n"
                    "        'ocr_text': 'entry signal',\n"
                    "        'vision_description': 'A slide generated by an external command.',\n"
                    "        'structured_observations': {'source': 'fake-script'},\n"
                    "        'confidence': 0.86,\n"
                    "    }]\n"
                    "}), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )
            frame = self._frame(root / "frame_000001.jpg")
            work_dir = root / "vision" / "external"

            analyses = analyze_frames(
                [frame],
                backend="external-command",
                vision_command=f"{sys.executable} {script} --input {{input}} --output {{output}}",
                work_dir=work_dir,
            )
            input_data = json.loads(input_capture.read_text(encoding="utf-8"))

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].visual_type, VisualType.SLIDE)
        self.assertEqual(analyses[0].ocr_text, "entry signal")
        self.assertEqual(analyses[0].backend, "external-command")
        self.assertEqual(input_data["backend"], "external-command")
        self.assertEqual(input_data["frames"][0]["frame_id"], "frame-000001")
        self.assertEqual(input_data["frames"][0]["video_id"], "lesson")
        self.assertEqual(input_data["frames"][0]["timestamp"], 0.0)
        self.assertEqual(input_data["frames"][0]["image_path"], frame.image_path.as_posix())
        self.assertEqual(input_data["frames"][0]["width"], 1280)
        self.assertEqual(input_data["frames"][0]["height"], 720)

    def test_external_command_accepts_quoted_script_path_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_dir = root / "vision tools"
            script_dir.mkdir()
            script = script_dir / "vision stub.py"
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
                    "    'analyses': [{'frame_id': frame['frame_id']}]\n"
                    "}), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )
            frame = self._frame(root / "frame_000001.jpg")

            analyses = analyze_frames(
                [frame],
                backend="external-command",
                vision_command=f'{sys.executable} "{script}" --input {{input}} --output {{output}}',
                work_dir=root / "vision" / "external",
            )

        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].frame_id, "frame-000001")
        self.assertEqual(analyses[0].backend, "external-command")

    def test_external_command_requires_vision_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = self._frame(root / "frame_000001.jpg")

            with self.assertRaisesRegex(
                ValueError,
                "external-command backend requires vision_command",
            ):
                analyze_frames(
                    [frame],
                    backend="external-command",
                    work_dir=root / "vision" / "external",
                )

    def test_external_command_requires_input_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = self._frame(root / "frame_000001.jpg")

            with self.assertRaisesRegex(ValueError, r"vision_command must contain \{input\}"):
                analyze_frames(
                    [frame],
                    backend="external-command",
                    vision_command=f"{sys.executable} script.py --output {{output}}",
                    work_dir=root / "vision" / "external",
                )

    def test_external_command_requires_output_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = self._frame(root / "frame_000001.jpg")

            with self.assertRaisesRegex(ValueError, r"vision_command must contain \{output\}"):
                analyze_frames(
                    [frame],
                    backend="external-command",
                    vision_command=f"{sys.executable} script.py --input {{input}}",
                    work_dir=root / "vision" / "external",
                )

    def test_external_command_reports_nonzero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "fail.py"
            script.write_text(
                "import sys\nprint('bad command', file=sys.stderr)\nsys.exit(7)\n",
                encoding="utf-8",
            )
            frame = self._frame(root / "frame_000001.jpg")

            with self.assertRaisesRegex(
                ValueError,
                "external vision command failed with exit code 7",
            ):
                analyze_frames(
                    [frame],
                    backend="external-command",
                    vision_command=f"{sys.executable} {script} --input {{input}} --output {{output}}",
                    work_dir=root / "vision" / "external",
                )

    def test_external_command_reports_missing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "missing_output.py"
            script.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            frame = self._frame(root / "frame_000001.jpg")

            with self.assertRaisesRegex(
                ValueError,
                "external vision command did not write output",
            ):
                analyze_frames(
                    [frame],
                    backend="external-command",
                    vision_command=f"{sys.executable} {script} --input {{input}} --output {{output}}",
                    work_dir=root / "vision" / "external",
                )


if __name__ == "__main__":
    unittest.main()
