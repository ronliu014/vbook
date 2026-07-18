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
from vbook_export.note import render_placeholder_note, render_sections_note, write_note
from vbook_export.semantic_visual_note import write_semantic_visual_note_package
from vbook_export.vault_enhance import write_vtext_first_package
from vbook_export.vault_preview import load_preview_sources, write_preview_package
from vbook_fusion.llm_contract import (
    build_llm_fusion_request,
    parse_llm_fusion_response,
    write_llm_fusion_request,
    write_llm_fusion_sections,
)
from vbook_fusion.llm_external import run_llm_fusion_command
from vbook_fusion.sections import build_evidence_sections, write_fusion_sections
from vbook_fusion.snapshot import (
    build_fusion_prompt_snapshot,
    write_fusion_prompt_snapshot,
)
from vbook_pipeline.batch import (
    BatchLessonResult,
    discover_batch_lessons,
    write_batch_manifest,
)
from vbook_pipeline.timeline import link_frames_to_transcript
from vbook_vision.analysis import analyze_frames, write_visual_analysis
from vbook_vision.frames import (
    discover_frame_candidates,
    extract_frame_candidates,
    select_frame_candidates,
)
from tools.vtext_first_batch_preview import run_batch_preview


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
        return _run_manifest_pipeline(args, parser, defaults={})

    if args.command == "build":
        return _run_manifest_pipeline(
            args,
            parser,
            defaults={
                "align_timeline": True,
                "analyze_vision_placeholder": True,
                "extract_frames": True,
                "select_frames": True,
                "write_fusion_prompt": True,
                "write_fusion_sections": True,
                "write_note": True,
            },
        )

    if args.command == "build-batch":
        return _run_build_batch(args, parser)

    if args.command == "vault-preview":
        return _run_vault_preview(args, parser)

    if args.command == "vault-enhance":
        return _run_vault_enhance(args, parser)

    if args.command == "semantic-visual-note":
        return _run_semantic_visual_note(args, parser)

    if args.command == "production-batch-preview":
        return _run_production_batch_preview(args, parser)

    parser.print_help()
    return 0


def _run_vault_preview(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        sources = load_preview_sources(args.vault_note, args.lesson_output)
        package = write_preview_package(sources, args.output)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(package.manifest_path)
    return 0


def _run_vault_enhance(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        package = write_vtext_first_package(
            vtext_note_path=args.vtext_note,
            lesson_output_dir=args.lesson_output,
            output_note_path=args.output_note,
            manifest_path=args.manifest_output,
            max_images_per_note=args.max_images_per_note,
            min_image_gap_seconds=args.min_image_gap_seconds,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(package.manifest_path)
    return 0


def _run_semantic_visual_note(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        package = write_semantic_visual_note_package(
            lesson_output_dir=args.lesson_output,
            output_dir=args.output,
            transcript_path=args.transcript,
            transcript_source_label=args.transcript_source_label,
            llm_fusion_command=args.llm_fusion_command,
            llm_response_path=args.llm_response,
            max_visuals_per_request=args.max_visuals_per_request,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(package.manifest_path)
    return 0


def _run_production_batch_preview(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        package = run_batch_preview(
            batch_input_path=args.batch_input,
            output_root=args.output_root,
            route=args.route,
            variant=args.variant,
            max_images_per_note=args.max_images_per_note,
            min_image_gap_seconds=args.min_image_gap_seconds,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(package.json_path)
    return 0 if package.status == "preview_ready" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vbook")
    parser.add_argument("--version", action="store_true", help="Print vBook version and exit")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Check skeleton readiness")

    config_parser = subparsers.add_parser("config", help="Inspect configuration")
    config_parser.add_argument("--show", action="store_true", help="Print resolved configuration")

    manifest_parser = subparsers.add_parser("manifest", help="Import transcript and write manifest")
    _add_pipeline_arguments(manifest_parser, include_write_flags=True)

    build_parser = subparsers.add_parser("build", help="Run the default MVP pipeline")
    _add_pipeline_arguments(build_parser, include_write_flags=False)

    batch_parser = subparsers.add_parser(
        "build-batch",
        help="Run the MVP pipeline for a directory of lessons",
    )
    batch_parser.add_argument(
        "--input",
        required=True,
        help="Input directory with media and text/",
    )
    batch_parser.add_argument(
        "--output",
        required=True,
        help="Output directory for batch results",
    )
    batch_parser.add_argument(
        "--frame-interval-seconds",
        type=float,
        default=30.0,
        help="Seconds between candidate frames for each lesson",
    )
    batch_parser.add_argument(
        "--alignment-window-seconds",
        type=float,
        help="Seconds before and after each frame timestamp used for transcript matching",
    )

    preview_parser = subparsers.add_parser(
        "vault-preview",
        help="Write a preview-only vault enhancement package",
    )
    preview_parser.add_argument("--vault-note", required=True, help="Existing vault note path")
    preview_parser.add_argument(
        "--lesson-output",
        required=True,
        help="Existing vBook lesson output directory",
    )
    preview_parser.add_argument(
        "--output",
        required=True,
        help="Preview output directory",
    )

    enhance_parser = subparsers.add_parser(
        "vault-enhance",
        help="Write a vtext-first vBook enhanced vault note",
    )
    enhance_parser.add_argument("--vtext-note", required=True, help="vtext note path")
    enhance_parser.add_argument(
        "--lesson-output",
        required=True,
        help="Existing vBook lesson output directory",
    )
    enhance_parser.add_argument(
        "--output-note",
        required=True,
        help="vBook enhanced output note path",
    )
    enhance_parser.add_argument(
        "--manifest-output",
        help="Manifest output path; defaults to <output-note>.manifest.json",
    )
    enhance_parser.add_argument(
        "--max-images-per-note",
        type=int,
        help="Maximum images inserted into the enhanced note",
    )
    enhance_parser.add_argument(
        "--min-image-gap-seconds",
        type=float,
        default=0.0,
        help="Minimum seconds between inserted images; nearby scenes keep the later completed page",
    )

    semantic_visual_parser = subparsers.add_parser(
        "semantic-visual-note",
        help="Experimental transcript-and-visual-first note synthesis package",
    )
    semantic_visual_parser.add_argument(
        "--lesson-output",
        required=True,
        help="Existing vBook lesson output directory with manifest and vision artifacts",
    )
    semantic_visual_parser.add_argument(
        "--output",
        required=True,
        help="Output directory for the experimental request or preview note",
    )
    semantic_visual_parser.add_argument(
        "--transcript",
        help="Optional corrected timestamped transcript; defaults to manifest transcript segments",
    )
    semantic_visual_parser.add_argument(
        "--transcript-source-label",
        default="semantic_verified",
        help="Label for the transcript source recorded in the request",
    )
    semantic_visual_parser.add_argument(
        "--llm-fusion-command",
        help="External command template for model synthesis; must contain {input} and {output}",
    )
    semantic_visual_parser.add_argument(
        "--llm-response",
        help="Existing model response JSON to render as a preview note",
    )
    semantic_visual_parser.add_argument(
        "--max-visuals-per-request",
        type=int,
        help="Maximum non-error visual evidence records included in the model request",
    )

    production_batch_parser = subparsers.add_parser(
        "production-batch-preview",
        description="Run preview-only vtext-first production batch",
        help="Run preview-only vtext-first production batch",
    )
    production_batch_parser.add_argument("--batch-input", required=True)
    production_batch_parser.add_argument("--output-root", required=True)
    production_batch_parser.add_argument("--route", default="vtext_first_vault_enhance")
    production_batch_parser.add_argument("--variant", default="baseline")
    production_batch_parser.add_argument("--max-images-per-note", type=int)
    production_batch_parser.add_argument(
        "--min-image-gap-seconds",
        type=float,
        default=0.0,
    )

    return parser


def _add_pipeline_arguments(
    command_parser: argparse.ArgumentParser,
    include_write_flags: bool,
) -> None:
    command_parser.add_argument("--video", required=True, help="Source lesson video path")
    command_parser.add_argument(
        "--transcript",
        required=True,
        help="Timestamped transcript JSON path",
    )
    command_parser.add_argument(
        "--output",
        required=True,
        help="Output directory for manifest.json",
    )
    command_parser.add_argument("--config", help="Optional vBook TOML config path")
    command_parser.add_argument(
        "--course-title",
        default="",
        help="Course title stored in manifest",
    )
    command_parser.add_argument("--lesson-title", help="Lesson title stored in manifest")
    command_parser.add_argument(
        "--frame-candidates-dir",
        help="Existing frame candidate directory to include in manifest",
    )
    command_parser.add_argument(
        "--frame-interval-seconds",
        type=float,
        default=3.0,
        help="Seconds between candidate frames when inferring timestamps",
    )
    command_parser.add_argument(
        "--select-frames",
        action="store_true",
        help="Select candidate frames into frames/selected before writing manifest",
    )
    command_parser.add_argument(
        "--selected-frames-dir",
        help="Directory for selected frame copies; defaults to <output>/frames/selected",
    )
    command_parser.add_argument(
        "--min-selected-frame-interval-seconds",
        type=float,
        default=10.0,
        help="Minimum seconds between selected frames",
    )
    if include_write_flags:
        command_parser.add_argument(
            "--align-timeline",
            action="store_true",
            help="Link frames to transcript segments by timestamp window",
        )
    command_parser.add_argument(
        "--alignment-window-seconds",
        type=float,
        help="Seconds before and after each frame timestamp used for transcript matching",
    )
    if include_write_flags:
        command_parser.add_argument(
            "--analyze-vision-placeholder",
            action="store_true",
            help="Write placeholder visual analysis records for frames",
        )
    command_parser.add_argument(
        "--vision-backend",
        choices=("placeholder", "manual-json", "external-command"),
        help="Visual analysis backend; build defaults to placeholder",
    )
    command_parser.add_argument(
        "--visual-analysis-input",
        help="Input JSON for backends such as manual-json",
    )
    command_parser.add_argument(
        "--vision-command",
        help="External command template for the external-command vision backend",
    )
    command_parser.add_argument(
        "--visual-analysis-path",
        help="Path for visual analysis JSON; defaults to <output>/vision/analysis.json",
    )
    if include_write_flags:
        command_parser.add_argument(
            "--write-note",
            action="store_true",
            help="Write placeholder note.md alongside manifest.json",
        )
    command_parser.add_argument(
        "--note-path",
        help="Path for Markdown note; defaults to <output>/note.md",
    )
    if include_write_flags:
        command_parser.add_argument(
            "--write-fusion-prompt",
            action="store_true",
            help="Write fusion prompt snapshot JSON for later knowledge fusion",
        )
    command_parser.add_argument(
        "--fusion-prompt-path",
        help="Path for fusion prompt JSON; defaults to <output>/fusion/prompt.json",
    )
    if include_write_flags:
        command_parser.add_argument(
            "--write-fusion-sections",
            action="store_true",
            help="Write placeholder fusion sections JSON",
        )
    command_parser.add_argument(
        "--fusion-sections-path",
        help="Path for fusion sections JSON; defaults to <output>/fusion/sections.json",
    )
    command_parser.add_argument(
        "--llm-fusion-command",
        help="External command template for LLM fusion; must contain {input} and {output}",
    )
    command_parser.add_argument(
        "--llm-fusion-request-path",
        help="Path for LLM fusion request JSON; defaults to <output>/fusion/llm_request.json",
    )
    command_parser.add_argument(
        "--llm-fusion-response-path",
        help="Path for LLM fusion response JSON; defaults to <output>/fusion/llm_response.json",
    )
    command_parser.add_argument(
        "--llm-fusion-sections-path",
        help="Path for parsed LLM fusion sections JSON; defaults to <output>/fusion/llm_sections.json",
    )


def _run_manifest_pipeline(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    defaults: dict[str, bool],
) -> int:
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
    fusion_sections_path = (
        Path(args.fusion_sections_path)
        if args.fusion_sections_path
        else Path(args.output) / "fusion" / "sections.json"
    )
    fusion_sections_written = False
    fusion_sections = None
    llm_fusion_request_path = (
        Path(args.llm_fusion_request_path)
        if args.llm_fusion_request_path
        else Path(args.output) / "fusion" / "llm_request.json"
    )
    llm_fusion_response_path = (
        Path(args.llm_fusion_response_path)
        if args.llm_fusion_response_path
        else Path(args.output) / "fusion" / "llm_response.json"
    )
    llm_fusion_sections_path = (
        Path(args.llm_fusion_sections_path)
        if args.llm_fusion_sections_path
        else Path(args.output) / "fusion" / "llm_sections.json"
    )
    llm_fusion_written = False
    note_sections = None
    video_asset = _build_video_asset(
        video_path=args.video,
        output_dir=args.output,
        course_title=args.course_title,
        lesson_title=args.lesson_title,
    )
    video_id = Path(args.output).name or Path(args.video).stem
    if args.frame_candidates_dir:
        frames = discover_frame_candidates(
            candidate_dir=args.frame_candidates_dir,
            video_id=video_id,
            interval_seconds=args.frame_interval_seconds,
        )
    elif _flag(args, "extract_frames", defaults):
        frames = extract_frame_candidates(
            video_path=args.video,
            candidate_dir=Path(args.output) / "frames" / "candidates",
            video_id=video_id,
            interval_seconds=args.frame_interval_seconds,
        )
    if _flag(args, "select_frames", defaults):
        if frames is None:
            parser.error(f"{args.command} --select-frames requires --frame-candidates-dir")
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
    if _flag(args, "align_timeline", defaults):
        link_frames = selected_frames if selected_frames is not None else frames
        if link_frames is None:
            parser.error(f"{args.command} requires frame metadata for timeline alignment")
        timeline_links = link_frames_to_transcript(
            link_frames,
            segments,
            window_seconds=(
                args.alignment_window_seconds
                if args.alignment_window_seconds is not None
                else config.alignment_window_seconds
            ),
        )
    should_analyze_vision = _should_analyze_vision(args, defaults)
    if should_analyze_vision:
        analysis_frames = selected_frames if selected_frames is not None else frames
        if analysis_frames is None:
            parser.error(f"{args.command} requires frame metadata for vision analysis")
        vision_backend = _vision_backend(args, defaults)
        try:
            visual_analyses = analyze_frames(
                analysis_frames,
                backend=vision_backend,
                visual_analysis_input=args.visual_analysis_input,
                vision_command=args.vision_command,
                work_dir=Path(args.output) / "vision" / "external",
            )
        except ValueError as exc:
            parser.error(str(exc))
        visual_analysis_path = (
            Path(args.visual_analysis_path)
            if args.visual_analysis_path
            else Path(args.output) / "vision" / "analysis.json"
        )
        write_visual_analysis(visual_analyses, visual_analysis_path, backend=vision_backend)
    if _flag(args, "write_fusion_sections", defaults):
        fusion_sections = build_evidence_sections(
            segments=segments,
            visual_analyses=visual_analyses,
            timeline_links=timeline_links,
        )
        write_fusion_sections(fusion_sections, fusion_sections_path)
        fusion_sections_written = True
        note_sections = fusion_sections
    if args.llm_fusion_command:
        if fusion_sections is None:
            parser.error(f"{args.command} --llm-fusion-command requires fusion sections")
        try:
            llm_request = build_llm_fusion_request(video_asset, fusion_sections)
            write_llm_fusion_request(llm_request, llm_fusion_request_path)
            response_path = run_llm_fusion_command(
                args.llm_fusion_command,
                request_path=llm_fusion_request_path,
                response_path=llm_fusion_response_path,
            )
            llm_response = json.loads(response_path.read_text(encoding="utf-8"))
            llm_sections = parse_llm_fusion_response(llm_response)
            write_llm_fusion_sections(llm_sections, llm_fusion_sections_path)
        except (ValueError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        llm_fusion_written = True
        note_sections = llm_sections
    if _flag(args, "write_note", defaults):
        note_frames = (
            list(selected_frames) + list(rejected_frames or [])
            if selected_frames is not None
            else frames
        )
        note_markdown = (
            render_sections_note(video=video_asset, sections=note_sections)
            if note_sections is not None
            else render_placeholder_note(
                video=video_asset,
                segments=segments,
                frames=note_frames,
                visual_analyses=visual_analyses,
                timeline_links=timeline_links,
            )
        )
        write_note(note_markdown, note_path)
        note_written = True
    if _flag(args, "write_fusion_prompt", defaults):
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
        selection_strategy=(
            "basic_interval_duplicate" if selected_frames is not None else "min_interval"
        ),
        timeline_links=timeline_links,
        visual_analyses=visual_analyses,
        visual_analysis_path=visual_analysis_path,
        note_path=note_path,
        note_written=note_written,
        fusion_prompt_path=fusion_prompt_path,
        fusion_prompt_written=fusion_prompt_written,
        fusion_sections_path=fusion_sections_path,
        fusion_sections_written=fusion_sections_written,
        llm_fusion_request_path=llm_fusion_request_path,
        llm_fusion_response_path=llm_fusion_response_path,
        llm_fusion_sections_path=llm_fusion_sections_path,
        llm_fusion_written=llm_fusion_written,
    )
    manifest_path = write_manifest(manifest, Path(args.output) / "manifest.json")
    print(manifest_path)
    return 0


def _run_build_batch(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    plans = discover_batch_lessons(input_dir=args.input, output_dir=args.output)
    results: list[BatchLessonResult] = []
    for plan in plans:
        if plan.skip_reason is not None or plan.transcript_path is None:
            results.append(
                BatchLessonResult(
                    lesson_id=plan.lesson_id,
                    media_path=plan.media_path,
                    transcript_path=plan.transcript_path,
                    output_dir=plan.output_dir,
                    status="skipped",
                    vtext_compatible=plan.vtext_compatible,
                    failure_reason=plan.skip_reason,
                )
            )
            continue
        build_args = argparse.Namespace(
            command="build",
            video=str(plan.media_path),
            transcript=str(plan.transcript_path),
            output=str(plan.output_dir),
            config=None,
            course_title="",
            lesson_title=plan.media_path.stem,
            frame_candidates_dir=None,
            frame_interval_seconds=args.frame_interval_seconds,
            select_frames=False,
            selected_frames_dir=None,
            min_selected_frame_interval_seconds=10.0,
            alignment_window_seconds=args.alignment_window_seconds,
            analyze_vision_placeholder=False,
            vision_backend=None,
            visual_analysis_input=None,
            vision_command=None,
            visual_analysis_path=None,
            write_note=False,
            note_path=None,
            write_fusion_prompt=False,
            fusion_prompt_path=None,
            write_fusion_sections=False,
            fusion_sections_path=None,
            llm_fusion_command=None,
            llm_fusion_request_path=None,
            llm_fusion_response_path=None,
            llm_fusion_sections_path=None,
        )
        try:
            _run_manifest_pipeline(
                build_args,
                parser,
                defaults={
                    "align_timeline": True,
                    "analyze_vision_placeholder": True,
                    "extract_frames": True,
                    "select_frames": True,
                    "write_fusion_prompt": True,
                    "write_fusion_sections": True,
                    "write_note": True,
                },
            )
        except Exception as exc:
            message = str(exc)
            failure_reason = (
                "unsupported_transcript_format"
                if "unsupported transcript format" in message
                else f"build_failed: {message}"
            )
            results.append(
                BatchLessonResult(
                    lesson_id=plan.lesson_id,
                    media_path=plan.media_path,
                    transcript_path=plan.transcript_path,
                    output_dir=plan.output_dir,
                    status="failed",
                    vtext_compatible=plan.vtext_compatible,
                    failure_reason=failure_reason,
                )
            )
            continue
        results.append(
            BatchLessonResult(
                lesson_id=plan.lesson_id,
                media_path=plan.media_path,
                transcript_path=plan.transcript_path,
                output_dir=plan.output_dir,
                status="done",
                vtext_compatible=plan.vtext_compatible,
                manifest_path=plan.output_dir / "manifest.json",
            )
        )
    batch_manifest_path = write_batch_manifest(
        results,
        Path(args.output) / "batch_manifest.json",
    )
    print(batch_manifest_path)
    return 0


def _flag(
    args: argparse.Namespace,
    name: str,
    defaults: dict[str, bool],
) -> bool:
    return bool(getattr(args, name, False) or defaults.get(name, False))


def _should_analyze_vision(
    args: argparse.Namespace,
    defaults: dict[str, bool],
) -> bool:
    return bool(
        getattr(args, "analyze_vision_placeholder", False)
        or getattr(args, "vision_backend", None)
        or defaults.get("analyze_vision_placeholder", False)
    )


def _vision_backend(
    args: argparse.Namespace,
    defaults: dict[str, bool],
) -> str:
    if getattr(args, "vision_backend", None):
        return args.vision_backend
    if (
        getattr(args, "analyze_vision_placeholder", False)
        or defaults.get("analyze_vision_placeholder", False)
    ):
        return "placeholder"
    return "placeholder"


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
