import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import FrameCandidate, VisualType
from vbook_vision.analysis import load_manual_visual_analysis


REPO_ROOT = Path(__file__).resolve().parents[2]
VISION_STUB = REPO_ROOT / "tools" / "vision_stub.py"


class VisionStubToolTest(unittest.TestCase):
    def test_writes_manual_json_compatible_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "frames.json"
            output_path = root / "nested" / "analysis.json"
            image = root / "frame_000001.jpg"
            image.write_bytes(b"image")
            input_path.write_text(
                json.dumps(
                    {
                        "backend": "external-command",
                        "frames": [
                            {
                                "frame_id": "frame-000001",
                                "video_id": "lesson",
                                "timestamp": 12.5,
                                "image_path": image.as_posix(),
                                "width": 1280,
                                "height": 720,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(VISION_STUB),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            data = json.loads(output_path.read_text(encoding="utf-8"))
            analyses = load_manual_visual_analysis(
                [
                    FrameCandidate(
                        id="frame-000001",
                        video_id="lesson",
                        timestamp=12.5,
                        image_path=image,
                        width=1280,
                        height=720,
                    )
                ],
                output_path,
                backend="external-command",
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(data["backend"], "vision_stub")
        self.assertEqual(len(data["analyses"]), 1)
        self.assertEqual(data["analyses"][0]["frame_id"], "frame-000001")
        self.assertEqual(data["analyses"][0]["visual_type"], "other")
        self.assertEqual(data["analyses"][0]["ocr_text"], "")
        self.assertEqual(
            data["analyses"][0]["vision_description"],
            "External command smoke analysis for frame-000001.",
        )
        self.assertEqual(
            data["analyses"][0]["structured_observations"]["source"],
            "vision_stub",
        )
        self.assertEqual(
            data["analyses"][0]["structured_observations"]["image_path"],
            image.as_posix(),
        )
        self.assertEqual(data["analyses"][0]["confidence"], 0.0)
        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
        self.assertEqual(analyses[0].backend, "external-command")

    def test_missing_input_file_exits_with_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(VISION_STUB),
                    "--input",
                    str(root / "missing.json"),
                    "--output",
                    str(root / "analysis.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("input file does not exist", result.stderr)

    def test_missing_frames_list_exits_with_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "frames.json"
            input_path.write_text(json.dumps({"items": []}), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(VISION_STUB),
                    "--input",
                    str(input_path),
                    "--output",
                    str(root / "analysis.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("input JSON must contain frames list", result.stderr)
