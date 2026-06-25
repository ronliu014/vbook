"""Manifest construction and writing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from vbook_common.serialization import to_jsonable
from vbook_common.types import (
    FrameCandidate,
    Manifest,
    PipelineRun,
    StageStatus,
    TimelineLink,
    TranscriptSegment,
    TranscriptSourceType,
    VisualAnalysis,
    VideoAsset,
)


def build_manifest(
    video_path: Path | str,
    transcript_path: Path | str,
    output_dir: Path | str,
    segments: Sequence[TranscriptSegment],
    config: dict[str, Any],
    course_title: str = "",
    lesson_title: str | None = None,
    transcript_source: TranscriptSourceType = TranscriptSourceType.IMPORTED,
    frames: Sequence[FrameCandidate] | None = None,
    selected_frames: Sequence[FrameCandidate] | None = None,
    rejected_frames: Sequence[FrameCandidate] | None = None,
    selection_strategy: str = "min_interval",
    timeline_links: Sequence[TimelineLink] | None = None,
    timeline_match_strategy: str = "timestamp_window",
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    visual_analysis_path: Path | str | None = None,
    note_path: Path | str | None = None,
    note_written: bool = False,
    fusion_prompt_path: Path | str | None = None,
    fusion_prompt_written: bool = False,
    fusion_sections_path: Path | str | None = None,
    fusion_sections_written: bool = False,
) -> Manifest:
    """Build the minimal manifest produced by the P2 transcript foundation."""
    video = Path(video_path)
    transcript = Path(transcript_path)
    output = Path(output_dir)
    resolved_note_path = Path(note_path) if note_path is not None else output / "note.md"
    resolved_fusion_prompt_path = (
        Path(fusion_prompt_path)
        if fusion_prompt_path is not None
        else output / "fusion" / "prompt.json"
    )
    resolved_fusion_sections_path = (
        Path(fusion_sections_path)
        if fusion_sections_path is not None
        else output / "fusion" / "sections.json"
    )
    lesson_id = output.name or video.stem
    resolved_lesson_title = lesson_title if lesson_title is not None else video.stem
    stage_status = {
        "transcript_import": StageStatus.DONE,
        "frame_extraction": StageStatus.SKIPPED if frames is None else StageStatus.DONE,
        "timeline_alignment": StageStatus.SKIPPED
        if timeline_links is None
        else StageStatus.DONE,
        "vision_analysis": StageStatus.SKIPPED
        if visual_analyses is None
        else StageStatus.DONE,
        "fusion_prompt": StageStatus.DONE
        if fusion_prompt_written
        else StageStatus.SKIPPED,
        "fusion_sections": StageStatus.DONE
        if fusion_sections_written
        else StageStatus.SKIPPED,
        "note_export": StageStatus.DONE if note_written else StageStatus.SKIPPED,
        "manifest": StageStatus.DONE,
    }
    artifacts: dict[str, Any] = {
        "transcript": {
            "path": transcript,
            "segment_count": len(segments),
            "segments": list(segments),
        }
    }
    if frames is not None:
        frame_list = list(frames)
        artifacts["frames"] = {
            "candidate_dir": _common_parent(frame_list),
            "candidate_count": len(frame_list),
            "candidates": frame_list,
        }
        if selected_frames is not None:
            selected_list = list(selected_frames)
            rejected_list = list(rejected_frames or [])
            artifacts["frames"].update(
                {
                    "selected_dir": _common_parent(selected_list),
                    "selected_count": len(selected_list),
                    "rejected_count": len(rejected_list),
                    "selected": selected_list,
                    "rejected": rejected_list,
                    "selection_strategy": selection_strategy,
                }
            )

    if timeline_links is not None:
        link_list = list(timeline_links)
        artifacts["timeline"] = {
            "link_count": len(link_list),
            "links": link_list,
            "match_strategy": timeline_match_strategy,
        }

    if visual_analyses is not None:
        analysis_list = list(visual_analyses)
        artifacts["vision"] = {
            "analysis_path": Path(visual_analysis_path)
            if visual_analysis_path is not None
            else output / "vision" / "analysis.json",
            "analysis_count": len(analysis_list),
            "analyses": analysis_list,
        }

    if note_written:
        artifacts["note"] = {
            "path": resolved_note_path,
            "format": "markdown",
        }

    if fusion_prompt_written:
        artifacts.setdefault("fusion", {}).update(
            {
                "prompt_path": resolved_fusion_prompt_path,
                "prompt_format": "json",
            }
        )

    if fusion_sections_written:
        artifacts.setdefault("fusion", {}).update(
            {
                "sections_path": resolved_fusion_sections_path,
                "sections_format": "json",
            }
        )

    pipeline_run = PipelineRun(
        run_id=f"local-{lesson_id}",
        config=dict(config),
        stage_status=stage_status,
        output_paths={
            "fusion_prompt": resolved_fusion_prompt_path,
            "fusion_sections": resolved_fusion_sections_path,
            "note": resolved_note_path,
            "manifest": output / "manifest.json",
        },
    )

    return Manifest(
        video_asset=VideoAsset(
            id=lesson_id,
            path=video,
            course_title=course_title,
            lesson_title=resolved_lesson_title,
        ),
        transcript_source=transcript_source,
        pipeline_run=pipeline_run,
        artifacts=artifacts,
        note_path=resolved_note_path,
        stage_status=stage_status,
    )


def write_manifest(manifest: Manifest, path: Path | str) -> Path:
    """Write a manifest as formatted UTF-8 JSON."""
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(to_jsonable(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _common_parent(frames: Sequence[FrameCandidate]) -> Path | None:
    if not frames:
        return None
    return frames[0].image_path.parent
