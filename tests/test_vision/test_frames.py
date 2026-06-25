import tempfile
import unittest
from pathlib import Path

from vbook_common.types import FilterStatus, FrameCandidate
from vbook_vision.frames import (
    build_ffmpeg_frame_command,
    discover_frame_candidates,
    extract_frame_candidates,
    select_frame_candidates,
)


class FrameCandidateTest(unittest.TestCase):
    def test_build_ffmpeg_frame_command_uses_interval_and_pattern(self) -> None:
        command = build_ffmpeg_frame_command(
            video_path=Path("videos/lesson.mp4"),
            candidate_dir=Path("outputs/lesson/frames/candidates"),
            interval_seconds=3.0,
        )

        self.assertEqual(command[:3], ["ffmpeg", "-y", "-i"])
        self.assertIn("videos/lesson.mp4", command)
        self.assertIn("fps=1/3", command)
        self.assertEqual(command[-1], "outputs/lesson/frames/candidates/frame_%06d.jpg")

    def test_extract_frame_candidates_runs_runner_and_discovers_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate_dir = Path(tmp) / "frames" / "candidates"
            captured: list[list[str]] = []

            def runner(command: list[str]) -> None:
                captured.append(command)
                candidate_dir.mkdir(parents=True, exist_ok=True)
                (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
                (candidate_dir / "frame_000002.jpg").write_text("b", encoding="utf-8")

            frames = extract_frame_candidates(
                video_path=Path("videos/lesson.mp4"),
                candidate_dir=candidate_dir,
                video_id="lesson",
                interval_seconds=2.5,
                runner=runner,
            )

        self.assertEqual(len(captured), 1)
        self.assertEqual([frame.id for frame in frames], ["frame-000001", "frame-000002"])
        self.assertEqual([frame.timestamp for frame in frames], [0.0, 2.5])
        self.assertEqual(frames[0].filter_status, FilterStatus.CANDIDATE)

    def test_discover_frame_candidates_ignores_non_jpg_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate_dir = Path(tmp) / "candidates"
            candidate_dir.mkdir()
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            (candidate_dir / "notes.txt").write_text("ignore", encoding="utf-8")

            frames = discover_frame_candidates(
                candidate_dir=candidate_dir,
                video_id="lesson",
                interval_seconds=4.0,
            )

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].image_path.name, "frame_000001.jpg")
        self.assertEqual(frames[0].width, 0)
        self.assertEqual(frames[0].height, 0)

    def test_select_frame_candidates_copies_selected_frames_and_rejects_nearby_frames(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selected_dir = root / "selected"
            source_a = root / "frame_000001.jpg"
            source_b = root / "frame_000002.jpg"
            source_c = root / "frame_000003.jpg"
            source_a.write_text("a", encoding="utf-8")
            source_b.write_text("b", encoding="utf-8")
            source_c.write_text("c", encoding="utf-8")
            candidates = [
                FrameCandidate("frame-000001", "lesson", 0.0, source_a, 0, 0),
                FrameCandidate("frame-000002", "lesson", 2.0, source_b, 0, 0),
                FrameCandidate("frame-000003", "lesson", 6.0, source_c, 0, 0),
            ]

            selected, rejected = select_frame_candidates(
                candidates,
                selected_dir=selected_dir,
                min_interval_seconds=5.0,
            )
            selected_file_exists = (selected_dir / "frame_000001.jpg").exists()

        self.assertEqual([frame.id for frame in selected], ["frame-000001", "frame-000003"])
        self.assertEqual([frame.id for frame in rejected], ["frame-000002"])
        self.assertEqual(selected[0].filter_status, FilterStatus.SELECTED)
        self.assertEqual(rejected[0].filter_status, FilterStatus.REJECTED)
        self.assertEqual(rejected[0].filter_reason, "within_min_interval")
        self.assertTrue(selected_file_exists)

    def test_select_frame_candidates_rejects_exact_duplicate_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selected_dir = root / "selected"
            source_a = root / "frame_000001.jpg"
            source_b = root / "frame_000002.jpg"
            source_a.write_bytes(b"same image bytes")
            source_b.write_bytes(b"same image bytes")
            candidates = [
                FrameCandidate("frame-000001", "lesson", 0.0, source_a, 0, 0),
                FrameCandidate("frame-000002", "lesson", 10.0, source_b, 0, 0),
            ]

            selected, rejected = select_frame_candidates(
                candidates,
                selected_dir=selected_dir,
                min_interval_seconds=1.0,
            )

        self.assertEqual([frame.id for frame in selected], ["frame-000001"])
        self.assertEqual([frame.id for frame in rejected], ["frame-000002"])
        self.assertEqual(rejected[0].filter_status, FilterStatus.REJECTED)
        self.assertEqual(rejected[0].filter_reason, "duplicate_content")


if __name__ == "__main__":
    unittest.main()
