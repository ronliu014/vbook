import json
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


if __name__ == "__main__":
    unittest.main()
