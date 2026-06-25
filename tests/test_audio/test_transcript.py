import json
import tempfile
import unittest
from pathlib import Path

from vbook_audio.transcript import load_transcript
from vbook_common.types import TranscriptSourceType


class TranscriptImportTest(unittest.TestCase):
    def test_loads_object_wrapped_segments_with_stable_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.json"
            path.write_text(
                json.dumps(
                    {
                        "segments": [
                            {"start": 0, "end": 4.2, "text": "课程开场", "language": "zh"},
                            {
                                "start": 4.2,
                                "end": 9.0,
                                "text": "讲解均线支撑",
                                "confidence": 0.92,
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            segments = load_transcript(path)

        self.assertEqual([segment.id for segment in segments], ["seg-000001", "seg-000002"])
        self.assertEqual(segments[0].start, 0.0)
        self.assertEqual(segments[0].end, 4.2)
        self.assertEqual(segments[0].text, "课程开场")
        self.assertEqual(segments[0].language, "zh")
        self.assertEqual(segments[0].source, TranscriptSourceType.IMPORTED)
        self.assertEqual(segments[1].confidence, 0.92)

    def test_loads_top_level_segment_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.json"
            path.write_text(
                json.dumps([{"start": 10, "end": 12.5, "text": "top level list"}]),
                encoding="utf-8",
            )

            segments = load_transcript(path)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].id, "seg-000001")
        self.assertEqual(segments[0].text, "top level list")

    def test_rejects_invalid_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.json"
            path.write_text(
                json.dumps({"segments": [{"start": 5, "end": 4, "text": "bad"}]}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "end before start"):
                load_transcript(path)


if __name__ == "__main__":
    unittest.main()
