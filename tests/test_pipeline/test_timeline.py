import unittest
from pathlib import Path

from vbook_common.types import FrameCandidate, TranscriptSegment
from vbook_pipeline.timeline import link_frames_to_transcript


class TimelineAlignmentTest(unittest.TestCase):
    def test_link_frames_to_transcript_uses_timestamp_window_overlap(self) -> None:
        frames = [
            FrameCandidate("frame-000001", "lesson", 10.0, Path("frame1.jpg"), 0, 0),
            FrameCandidate("frame-000002", "lesson", 30.0, Path("frame2.jpg"), 0, 0),
        ]
        segments = [
            TranscriptSegment("seg-000001", 0.0, 5.0, "intro"),
            TranscriptSegment("seg-000002", 8.0, 12.0, "moving average"),
            TranscriptSegment("seg-000003", 24.0, 28.0, "setup"),
            TranscriptSegment("seg-000004", 40.0, 45.0, "later"),
        ]

        links = link_frames_to_transcript(frames, segments, window_seconds=5.0)

        self.assertEqual([link.frame_id for link in links], ["frame-000001", "frame-000002"])
        self.assertEqual(links[0].transcript_segment_ids, ["seg-000002"])
        self.assertEqual(links[0].window_start, 5.0)
        self.assertEqual(links[0].window_end, 15.0)
        self.assertEqual(links[1].transcript_segment_ids, ["seg-000003"])

    def test_link_frames_to_transcript_clamps_window_start_to_zero(self) -> None:
        frames = [FrameCandidate("frame-000001", "lesson", 2.0, Path("frame1.jpg"), 0, 0)]
        segments = [TranscriptSegment("seg-000001", 0.0, 1.0, "intro")]

        links = link_frames_to_transcript(frames, segments, window_seconds=5.0)

        self.assertEqual(links[0].window_start, 0.0)
        self.assertEqual(links[0].window_end, 7.0)
        self.assertEqual(links[0].transcript_segment_ids, ["seg-000001"])

    def test_link_frames_to_transcript_rejects_negative_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "window_seconds must be non-negative"):
            link_frames_to_transcript([], [], window_seconds=-1.0)


if __name__ == "__main__":
    unittest.main()
