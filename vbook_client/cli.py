"""Command-line interface for vBook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from vbook_audio.transcript import load_transcript
from vbook_common.config import load_config
from vbook_common.serialization import to_jsonable
from vbook_common.types import VideoAsset
from vbook_common.version import __version__
from vbook_export.manifest import build_manifest, write_manifest
from vbook_export.note import render_placeholder_note, write_note
from vbook_fusion.snapshot import (
    build_fusion_prompt_snapshot,
    write_fusion_prompt_snapshot,
)
from vbook_pipeline.timeline import link_frames_to_transcript
from vbook_vision.analysis import analyze_frames_placeholder, write_visual_analysis
from vbook_vision.frames import discover_frame_candidates, select_frame_candidates


def main(argv: Sequence[str] | None = None) -> int:
    """Run the vBook CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "check":
        print("vBook skeleton ready")
        return 0

    if args.command == "config":
        if args.show:
            print(json.dumps(to_jsonable(load_config()), ensure_ascii=False, indent=2))
            return 0
        parser.error("config requires --show")

    if args.command == "manifest":
        config = load_config(config_file=args.config)
        segments = load_transcript(args.transcript)
        frames = None
        selected_frames = None
        rejected_frames = None
        timeline_links = None
        visual_analyses = None
        visual_analysis_path = None
        note_path = Path(args.note_path) if args.note_path else Path(args.output) / "note.md"
        note_written = False
        fusion_prompt_path = (
            Path(args.fusion_prompt_path)
            if args.fusion_prompt_path
            else Path(args.output) / "fusion" / "prompt.json"
        )
        fusion_prompt_written = False
        video_asset = _build_video_asset(
            video_path=args.video,
            output_dir=args.output,
            course_title=args.course_title,
            lesson_title=args.lesson_title,
        )
        if args.frame_candidates_dir:
            frames = discover_frame_candidates(
                candidate_dir=args.frame_candidates_dir,
                video_id=Path(args.output).name or Path(args.video).stem,
                interval_seconds=args.frame_interval_seconds,
            )
        if args.select_frames:
            if frames is None:
                parser.error("manifest --select-frames requires --frame-candidates-dir")
            selected_dir = (
                Path(args.selected_frames_dir)
                if args.selected_frames_dir
                else Path(args.output) / "frames" / "selected"
            )
            selected_frames, rejected_frames = select_frame_candidates(
                list(frames),
                selected_dir=selected_dir,
                min_interval_seconds=args.min_selected_frame_interval_seconds,
            )
        if args.align_timeline:
            link_frames = selected_frames if selected_frames is not None else frames
            if link_frames is None:
                parser.error("manifest --align-timeline requires frame metadata")
            timeline_links = link_frames_to_transcript(
                link_frames,
                segments,
                window_seconds=(
                    args.alignment_window_seconds
                    if args.alignment_window_seconds is not None
                    else config.alignment_window_seconds
                ),
            )
        if args.analyze_vision_placeholder:
            analysis_frames = selected_frames if selected_frames is not None else frames
            if analysis_frames is None:
                parser.error("manifest --analyze-vision-placeholder requires frame metadata")
            visual_analyses = analyze_frames_placeholder(analysis_frames)
            visual_analysis_path = (
                Path(args.visual_analysis_path)
                if args.visual_analysis_path
                else Path(args.output) / "vision" / "analysis.json"
            )
            write_visual_analysis(visual_analyses, visual_analysis_path)
        if args.write_note:
            note_frames = (
                list(selected_frames) + list(rejected_frames or [])
                if selected_frames is not None
                else frames
            )
            note_markdown = render_placeholder_note(
                video=video_asset,
                segments=segments,
                frames=note_frames,
                visual_analyses=visual_analyses,
                timeline_links=timeline_links,
            )
            write_note(note_markdown, note_path)
            note_written = True
        if args.write_fusion_prompt:
            fusion_snapshot = build_fusion_prompt_snapshot(
                video=video_asset,
                segments=segments,
                visual_analyses=visual_analyses,
                timeline_links=timeline_links,
            )
            write_fusion_prompt_snapshot(fusion_snapshot, fusion_prompt_path)
            fusion_prompt_written = True
        manifest = build_manifest(
            video_path=args.video,
            transcript_path=args.transcript,
            output_dir=args.output,
            segments=segments,
            config=to_jsonable(config),
            course_title=args.course_title,
            lesson_title=args.lesson_title,
            frames=frames,
            selected_frames=selected_frames,
            rejected_frames=rejected_frames,
            timeline_links=timeline_links,
            visual_analyses=visual_analyses,
            visual_analysis_path=visual_analysis_path,
            note_path=note_path,
            note_written=note_written,
            fusion_prompt_path=fusion_prompt_path,
            fusion_prompt_written=fusion_prompt_written,
        )
        manifest_path = write_manifest(manifest, Path(args.output) / "manifest.json")
        print(manifest_path)
        return 0

    parser.print_help()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vbook")
    parser.add_argument("--version", action="store_true", help="Print vBook version and exit")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Check skeleton readiness")

    config_parser = subparsers.add_parser("config", help="Inspect configuration")
    config_parser.add_argument("--show", action="store_true", help="Print resolved configuration")

    manifest_parser = subparsers.add_parser("manifest", help="Import transcript and write manifest")
    manifest_parser.add_argument("--video", required=True, help="Source lesson video path")
    manifest_parser.add_argument("--transcript", required=True, help="Timestamped transcript JSON path")
    manifest_parser.add_argument("--output", required=True, help="Output directory for manifest.json")
    manifest_parser.add_argument("--config", help="Optional vBook TOML config path")
    manifest_parser.add_argument("--course-title", default="", help="Course title stored in manifest")
    manifest_parser.add_argument("--lesson-title", help="Lesson title stored in manifest")
    manifest_parser.add_argument(
        "--frame-candidates-dir",
        help="Existing frame candidate directory to include in manifest",
    )
    manifest_parser.add_argument(
        "--frame-interval-seconds",
        type=float,
        default=3.0,
        help="Seconds between candidate frames when inferring timestamps",
    )
    manifest_parser.add_argument(
        "--select-frames",
        action="store_true",
        help="Select candidate frames into frames/selected before writing manifest",
    )
    manifest_parser.add_argument(
        "--selected-frames-dir",
        help="Directory for selected frame copies; defaults to <output>/frames/selected",
    )
    manifest_parser.add_argument(
        "--min-selected-frame-interval-seconds",
        type=float,
        default=10.0,
        help="Minimum seconds between selected frames",
    )
    manifest_parser.add_argument(
        "--align-timeline",
        action="store_true",
        help="Link frames to transcript segments by timestamp window",
    )
    manifest_parser.add_argument(
        "--alignment-window-seconds",
        type=float,
        help="Seconds before and after each frame timestamp used for transcript matching",
    )
    manifest_parser.add_argument(
        "--analyze-vision-placeholder",
        action="store_true",
        help="Write placeholder visual analysis records for frames",
    )
    manifest_parser.add_argument(
        "--visual-analysis-path",
        help="Path for visual analysis JSON; defaults to <output>/vision/analysis.json",
    )
    manifest_parser.add_argument(
        "--write-note",
        action="store_true",
        help="Write placeholder note.md alongside manifest.json",
    )
    manifest_parser.add_argument(
        "--note-path",
        help="Path for Markdown note; defaults to <output>/note.md",
    )
    manifest_parser.add_argument(
        "--write-fusion-prompt",
        action="store_true",
        help="Write fusion prompt snapshot JSON for later knowledge fusion",
    )
    manifest_parser.add_argument(
        "--fusion-prompt-path",
        help="Path for fusion prompt JSON; defaults to <output>/fusion/prompt.json",
    )

    return parser


def _build_video_asset(
    video_path: Path | str,
    output_dir: Path | str,
    course_title: str,
    lesson_title: str | None,
) -> VideoAsset:
    video = Path(video_path)
    output = Path(output_dir)
    return VideoAsset(
        id=output.name or video.stem,
        path=video,
        course_title=course_title,
        lesson_title=lesson_title if lesson_title is not None else video.stem,
    )
