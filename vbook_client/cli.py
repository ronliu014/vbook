"""Command-line interface for vBook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from vbook_audio.transcript import load_transcript
from vbook_common.config import load_config
from vbook_common.serialization import to_jsonable
from vbook_common.version import __version__
from vbook_export.manifest import build_manifest, write_manifest
from vbook_pipeline.timeline import link_frames_to_transcript
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

    return parser
