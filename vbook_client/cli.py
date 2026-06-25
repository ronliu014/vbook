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
        manifest = build_manifest(
            video_path=args.video,
            transcript_path=args.transcript,
            output_dir=args.output,
            segments=segments,
            config=to_jsonable(config),
            course_title=args.course_title,
            lesson_title=args.lesson_title,
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

    return parser
