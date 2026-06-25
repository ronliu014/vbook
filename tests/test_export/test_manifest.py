import json
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import (
    FilterStatus,
    FrameCandidate,
    StageStatus,
    TimelineLink,
    TranscriptSegment,
    VisualAnalysis,
    VisualType,
)
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

    def test_build_manifest_can_record_frame_candidates(self) -> None:
        frames = [
            FrameCandidate(
                id="frame-000001",
                video_id="lesson",
                timestamp=0.0,
                image_path=Path("outputs/lesson/frames/candidates/frame_000001.jpg"),
                width=0,
                height=0,
            )
        ]

        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            frames=frames,
        )

        self.assertEqual(manifest.artifacts["frames"]["candidate_count"], 1)
        self.assertEqual(manifest.artifacts["frames"]["candidates"], frames)
        self.assertEqual(manifest.pipeline_run.stage_status["frame_extraction"], StageStatus.DONE)

    def test_build_manifest_can_record_selected_and_rejected_frames(self) -> None:
        selected = [
            FrameCandidate(
                id="frame-000001",
                video_id="lesson",
                timestamp=0.0,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                width=0,
                height=0,
                filter_status=FilterStatus.SELECTED,
            )
        ]
        rejected = [
            FrameCandidate(
                id="frame-000002",
                video_id="lesson",
                timestamp=2.0,
                image_path=Path("outputs/lesson/frames/candidates/frame_000002.jpg"),
                width=0,
                height=0,
                filter_status=FilterStatus.REJECTED,
                filter_reason="within_min_interval",
            )
        ]

        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            frames=selected + rejected,
            selected_frames=selected,
            rejected_frames=rejected,
        )

        self.assertEqual(manifest.artifacts["frames"]["selected_count"], 1)
        self.assertEqual(manifest.artifacts["frames"]["rejected_count"], 1)
        self.assertEqual(manifest.artifacts["frames"]["selected"], selected)
        self.assertEqual(manifest.artifacts["frames"]["rejected"], rejected)
        self.assertEqual(manifest.artifacts["frames"]["selection_strategy"], "min_interval")

    def test_build_manifest_can_record_timeline_links(self) -> None:
        links = [
            TimelineLink(
                frame_id="frame-000001",
                transcript_segment_ids=["seg-000001"],
                window_start=0.0,
                window_end=10.0,
            )
        ]

        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            timeline_links=links,
        )

        self.assertEqual(manifest.artifacts["timeline"]["link_count"], 1)
        self.assertEqual(manifest.artifacts["timeline"]["links"], links)
        self.assertEqual(manifest.artifacts["timeline"]["match_strategy"], "timestamp_window")
        self.assertEqual(manifest.pipeline_run.stage_status["timeline_alignment"], StageStatus.DONE)

    def test_build_manifest_can_record_visual_analysis(self) -> None:
        analyses = [
            VisualAnalysis(
                frame_id="frame-000001",
                visual_type=VisualType.OTHER,
                image_path=Path("outputs/lesson/frames/selected/frame_000001.jpg"),
                backend="placeholder",
            )
        ]

        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            visual_analyses=analyses,
            visual_analysis_path=Path("outputs/lesson/vision/analysis.json"),
        )

        self.assertEqual(manifest.artifacts["vision"]["analysis_count"], 1)
        self.assertEqual(
            manifest.artifacts["vision"]["analysis_path"],
            Path("outputs/lesson/vision/analysis.json"),
        )
        self.assertEqual(manifest.artifacts["vision"]["analyses"], analyses)
        self.assertEqual(manifest.pipeline_run.stage_status["vision_analysis"], StageStatus.DONE)

    def test_build_manifest_can_record_written_note_artifact(self) -> None:
        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            note_path=Path("outputs/lesson/note.md"),
            note_written=True,
        )

        self.assertEqual(manifest.artifacts["note"]["path"], Path("outputs/lesson/note.md"))
        self.assertEqual(manifest.artifacts["note"]["format"], "markdown")
        self.assertEqual(manifest.stage_status["note_export"], StageStatus.DONE)
        self.assertEqual(manifest.pipeline_run.stage_status["note_export"], StageStatus.DONE)

    def test_build_manifest_can_record_fusion_prompt_artifact(self) -> None:
        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            fusion_prompt_path=Path("outputs/lesson/fusion/prompt.json"),
            fusion_prompt_written=True,
        )

        self.assertEqual(
            manifest.artifacts["fusion"]["prompt_path"],
            Path("outputs/lesson/fusion/prompt.json"),
        )
        self.assertEqual(manifest.artifacts["fusion"]["prompt_format"], "json")
        self.assertEqual(manifest.stage_status["fusion_prompt"], StageStatus.DONE)
        self.assertEqual(manifest.pipeline_run.stage_status["fusion_prompt"], StageStatus.DONE)

    def test_build_manifest_can_record_fusion_sections_artifact(self) -> None:
        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            fusion_sections_path=Path("outputs/lesson/fusion/sections.json"),
            fusion_sections_written=True,
        )

        self.assertEqual(
            manifest.artifacts["fusion"]["sections_path"],
            Path("outputs/lesson/fusion/sections.json"),
        )
        self.assertEqual(manifest.artifacts["fusion"]["sections_format"], "json")
        self.assertEqual(manifest.stage_status["fusion_sections"], StageStatus.DONE)
        self.assertEqual(manifest.pipeline_run.stage_status["fusion_sections"], StageStatus.DONE)


if __name__ == "__main__":
    unittest.main()
