"""Experimental transcript-and-visual-first note synthesis export."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from vbook_audio.transcript import load_transcript
from vbook_common.serialization import to_jsonable
from vbook_common.types import KnowledgeSection
from vbook_export.note import write_note
from vbook_fusion.llm_contract import (
    LLM_FUSION_OUTPUT_CONTRACT,
    LLM_FUSION_SCHEMA_VERSION,
    parse_llm_fusion_response,
    write_llm_fusion_request,
    write_llm_fusion_sections,
)
from vbook_fusion.llm_external import run_llm_fusion_command


SEMANTIC_VISUAL_REQUEST_INTENT = "semantic_visual_note_request"

SEMANTIC_VISUAL_INSTRUCTIONS = [
    "Use the timestamped transcript as the primary semantic source.",
    "Use visual OCR and visual descriptions to recover board, slide, chart, and case-study information that is missing from speech alone.",
    "Prefer completed, dense, high-information teaching pages over cover, transition, or partial pages.",
    "Skip visual evidence whose qwen_service.status is error.",
    "Return concise Simplified Chinese notes grounded only in the provided transcript and visual evidence.",
    "Each section may choose zero or more image_refs; choose only images that materially improve the note.",
]


@dataclass(frozen=True)
class SemanticVisualNotePackage:
    output_dir: Path
    request_path: Path
    manifest_path: Path
    note_path: Path | None
    sections_path: Path | None
    asset_paths: list[Path]


def write_semantic_visual_note_package(
    *,
    lesson_output_dir: Path | str,
    output_dir: Path | str,
    transcript_path: Path | str | None = None,
    transcript_source_label: str = "semantic_verified",
    llm_fusion_command: str | None = None,
    llm_response_path: Path | str | None = None,
    max_visuals_per_request: int | None = None,
) -> SemanticVisualNotePackage:
    """Write an experimental note package from timestamped text and visuals."""
    lesson_dir = Path(lesson_output_dir)
    target_dir = Path(output_dir)
    request_path = target_dir / "fusion" / "semantic_visual_request.json"
    response_path = target_dir / "fusion" / "semantic_visual_response.json"
    sections_path = target_dir / "fusion" / "semantic_visual_sections.json"
    note_path = target_dir / "note.md"
    manifest_path = target_dir / "manifest.json"

    request, request_metrics = build_semantic_visual_request(
        lesson_output_dir=lesson_dir,
        transcript_path=transcript_path,
        transcript_source_label=transcript_source_label,
        max_visuals_per_request=max_visuals_per_request,
    )
    write_llm_fusion_request(request, request_path)

    note_written_path: Path | None = None
    sections_written_path: Path | None = None
    copied_assets: list[Path] = []
    status = "request_ready"

    response_source_path: Path | None = None
    if llm_fusion_command:
        response_source_path = run_llm_fusion_command(
            llm_fusion_command,
            request_path=request_path,
            response_path=response_path,
        )
    elif llm_response_path is not None:
        response_source_path = Path(llm_response_path)

    if response_source_path is not None:
        response = _read_json(response_source_path)
        sections = parse_llm_fusion_response(response)
        sections_written_path = write_llm_fusion_sections(sections, sections_path)
        note_markdown, copied_assets = render_semantic_visual_note(
            request=request,
            sections=sections,
            output_note_path=note_path,
        )
        note_written_path = write_note(note_markdown, note_path)
        status = "preview"

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "status": status,
                "workflow": "semantic_visual_note",
                "lesson_output_dir": str(lesson_dir),
                "output_dir": str(target_dir),
                "transcript_source_label": transcript_source_label,
                "request_path": str(request_path),
                "response_path": str(response_source_path) if response_source_path else None,
                "sections_path": str(sections_written_path) if sections_written_path else None,
                "note_path": str(note_written_path) if note_written_path else None,
                "asset_count": len(copied_assets),
                "assets": [str(path) for path in copied_assets],
                "request_metrics": request_metrics,
                "safety": {
                    "source_lesson_output": "read_only",
                    "source_transcript": "read_only",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return SemanticVisualNotePackage(
        output_dir=target_dir,
        request_path=request_path,
        manifest_path=manifest_path,
        note_path=note_written_path,
        sections_path=sections_written_path,
        asset_paths=copied_assets,
    )


def build_semantic_visual_request(
    *,
    lesson_output_dir: Path | str,
    transcript_path: Path | str | None = None,
    transcript_source_label: str = "semantic_verified",
    max_visuals_per_request: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the experimental request payload from transcript and visual artifacts."""
    lesson_dir = Path(lesson_output_dir)
    manifest = _read_json(lesson_dir / "manifest.json")
    vision = _read_json(_artifact_path(manifest, lesson_dir, "vision", "analysis_path"))
    transcript_segments = _load_transcript_segments(
        manifest=manifest,
        transcript_path=transcript_path,
    )
    visual_evidence, skipped_error_count = _visual_evidence(
        vision=vision,
        timeline_links=_timeline_links(manifest),
        max_visuals=max_visuals_per_request,
    )
    video = manifest.get("video_asset") if isinstance(manifest.get("video_asset"), dict) else {}
    request = {
        "schema_version": LLM_FUSION_SCHEMA_VERSION,
        "intent": SEMANTIC_VISUAL_REQUEST_INTENT,
        "task": "semantic_visual_course_note_synthesis",
        "output_contract": LLM_FUSION_OUTPUT_CONTRACT,
        "video": {
            "id": video.get("id", lesson_dir.name),
            "path": video.get("path", ""),
            "course_title": video.get("course_title", ""),
            "lesson_title": video.get("lesson_title", lesson_dir.name),
            "duration_seconds": video.get("duration_seconds"),
        },
        "transcript_source": {
            "label": transcript_source_label,
            "path": str(transcript_path) if transcript_path is not None else _manifest_transcript_path(manifest),
            "semantics": "timestamped_text",
        },
        "instructions": SEMANTIC_VISUAL_INSTRUCTIONS,
        "transcript_segments": transcript_segments,
        "visual_evidence": visual_evidence,
    }
    metrics = {
        "transcript_segment_count": len(transcript_segments),
        "visual_evidence_count": len(visual_evidence),
        "skipped_error_visual_count": skipped_error_count,
    }
    return to_jsonable(request), metrics


def render_semantic_visual_note(
    *,
    request: dict[str, Any],
    sections: list[KnowledgeSection],
    output_note_path: Path | str,
) -> tuple[str, list[Path]]:
    """Render model sections as Markdown and copy referenced visual assets."""
    output_path = Path(output_note_path)
    assets_dir = output_path.parent / "assets" / output_path.stem
    image_by_ref = {
        str(item.get("image_path")): str(item.get("image_path"))
        for item in request.get("visual_evidence", [])
        if isinstance(item, dict) and item.get("image_path")
    }
    copied_assets = _copy_section_assets(sections, image_by_ref, assets_dir)
    link_by_ref = {
        original: _markdown_path(Path("assets") / output_path.stem / Path(original).name)
        for original in image_by_ref
    }

    video = request.get("video") if isinstance(request.get("video"), dict) else {}
    title = str(video.get("lesson_title") or video.get("id") or output_path.stem)
    lines = [
        f"# {title}",
        "",
        "## 课程信息",
        "",
        f"- 课程：{video.get('course_title') or ''}",
        f"- 课节：{title}",
        f"- 生成方式：时序文本 + 视觉证据实验",
        "",
        "## 知识结构",
        "",
    ]

    for index, section in enumerate(sections, start=1):
        lines.extend([f"### {index}. {section.title}", ""])
        for image_ref in section.image_refs:
            link = link_by_ref.get(image_ref)
            if not link:
                continue
            lines.extend([f"![{section.title}]({link})", ""])
        if section.summary:
            lines.extend([section.summary, ""])
        if section.key_points:
            lines.extend(["**关键要点**", ""])
            lines.extend(f"- {point}" for point in section.key_points)
            lines.append("")
        if section.source_timestamps:
            lines.extend(["**证据与回看**", ""])
            lines.append(f"- 时间：{_format_timestamps(section.source_timestamps)}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n", copied_assets


def _load_transcript_segments(
    *,
    manifest: dict[str, Any],
    transcript_path: Path | str | None,
) -> list[dict[str, Any]]:
    if transcript_path is not None:
        return to_jsonable(load_transcript(transcript_path))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return []
    transcript = artifacts.get("transcript")
    if not isinstance(transcript, dict):
        return []
    segments = transcript.get("segments")
    if not isinstance(segments, list):
        return []
    return [segment for segment in segments if isinstance(segment, dict)]


def _visual_evidence(
    *,
    vision: dict[str, Any],
    timeline_links: list[dict[str, Any]],
    max_visuals: int | None,
) -> tuple[list[dict[str, Any]], int]:
    evidence = []
    skipped_error_count = 0
    link_by_frame_id = {
        str(link.get("frame_id")): link
        for link in timeline_links
        if isinstance(link, dict) and link.get("frame_id")
    }
    analyses = vision.get("analyses")
    if not isinstance(analyses, list):
        return [], 0
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        if _analysis_has_qwen_error(analysis):
            skipped_error_count += 1
            continue
        frame_id = str(analysis.get("frame_id") or "")
        link = link_by_frame_id.get(frame_id, {})
        evidence.append(
            {
                "frame_id": frame_id,
                "timestamp": _analysis_timestamp(analysis),
                "visual_type": analysis.get("visual_type"),
                "image_path": analysis.get("image_path"),
                "ocr_text": analysis.get("ocr_text") or "",
                "vision_description": analysis.get("vision_description") or "",
                "structured_observations": _compact_observations(
                    analysis.get("structured_observations")
                ),
                "confidence": analysis.get("confidence"),
                "linked_transcript_segment_ids": link.get("transcript_segment_ids", []),
                "window_start": link.get("window_start"),
                "window_end": link.get("window_end"),
            }
        )
    evidence = sorted(evidence, key=lambda item: (item["timestamp"], item["frame_id"]))
    if max_visuals is not None:
        evidence = evidence[:max(0, max_visuals)]
    return evidence, skipped_error_count


def _compact_observations(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: value[key]
        for key in ("topic", "key_points", "visible_elements", "quality")
        if key in value
    }


def _timeline_links(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return []
    timeline = artifacts.get("timeline")
    if not isinstance(timeline, dict):
        return []
    links = timeline.get("links")
    return [link for link in links if isinstance(link, dict)] if isinstance(links, list) else []


def _artifact_path(
    manifest: dict[str, Any],
    lesson_dir: Path,
    artifact_name: str,
    path_key: str,
) -> Path:
    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, dict):
        artifact = artifacts.get(artifact_name)
        if isinstance(artifact, dict) and isinstance(artifact.get(path_key), str):
            return Path(artifact[path_key])
    return lesson_dir / artifact_name / "analysis.json"


def _manifest_transcript_path(manifest: dict[str, Any]) -> str:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return ""
    transcript = artifacts.get("transcript")
    if not isinstance(transcript, dict):
        return ""
    return str(transcript.get("path") or "")


def _analysis_has_qwen_error(analysis: dict[str, Any]) -> bool:
    observations = analysis.get("structured_observations")
    if not isinstance(observations, dict):
        return False
    service = observations.get("qwen_service")
    return isinstance(service, dict) and service.get("status") == "error"


def _analysis_timestamp(analysis: dict[str, Any]) -> float:
    timestamp = analysis.get("timestamp")
    if isinstance(timestamp, bool):
        return 0.0
    if isinstance(timestamp, (int, float)):
        return float(timestamp)
    frame_id = str(analysis.get("frame_id") or "")
    digits = "".join(char for char in frame_id if char.isdigit())
    return float(int(digits)) if digits else 0.0


def _copy_section_assets(
    sections: list[KnowledgeSection],
    image_by_ref: dict[str, str],
    assets_dir: Path,
) -> list[Path]:
    copied: list[Path] = []
    seen: set[Path] = set()
    for section in sections:
        for image_ref in section.image_refs:
            source = Path(image_by_ref.get(image_ref, image_ref))
            if not source.is_file():
                continue
            target = assets_dir / source.name
            if target in seen:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
            seen.add(target)
    return copied


def _format_timestamps(timestamps: list[float]) -> str:
    if not timestamps:
        return "未知"
    ordered = sorted(timestamps)
    if len(ordered) == 1:
        return f"{ordered[0]:.2f}s"
    return f"{ordered[0]:.2f}s - {ordered[-1]:.2f}s"


def _markdown_path(path: Path) -> str:
    return "/".join(quote(part, safe="") for part in path.parts)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required artifact does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"artifact must be a JSON object: {path}")
    return data
