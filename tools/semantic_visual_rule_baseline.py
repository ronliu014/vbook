"""Deterministic semantic+visual note baseline without external models."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from vbook_export.semantic_visual_note import build_semantic_visual_request


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        summaries = write_rule_baseline(
            dataset_path=Path(args.dataset),
            output_root=Path(args.output),
            max_visuals_per_lesson=args.max_visuals_per_lesson,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"semantic visual rule baseline error: {exc}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write deterministic semantic+visual rule baseline notes."
    )
    parser.add_argument("--dataset", required=True, help="Dataset registry JSON")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--max-visuals-per-lesson",
        type=int,
        default=4,
        help="Maximum non-error visual evidence records per lesson",
    )
    return parser


def write_rule_baseline(
    *,
    dataset_path: Path | str,
    output_root: Path | str,
    max_visuals_per_lesson: int,
) -> list[dict[str, Any]]:
    dataset = _read_json(Path(dataset_path))
    lessons = dataset.get("lessons")
    if not isinstance(lessons, list):
        raise ValueError("dataset.lessons must be a list")

    root = Path(output_root)
    summaries = []
    for lesson in lessons:
        if not isinstance(lesson, dict):
            continue
        title = _require_string(lesson, "title")
        lesson_output = _require_string(lesson, "lesson_output")
        request, metrics = build_semantic_visual_request(
            lesson_output_dir=lesson_output,
            transcript_source_label=str(
                lesson.get("transcript_source_label") or "vtext_semantic_verified"
            ),
            max_visuals_per_request=max_visuals_per_lesson,
        )
        evidence = [
            item for item in request.get("visual_evidence", []) if isinstance(item, dict)
        ]
        segments = {
            str(item.get("id")): item
            for item in request.get("transcript_segments", [])
            if isinstance(item, dict) and item.get("id") is not None
        }
        output_dir = root / title
        assets_dir = output_dir / "assets"
        copied_assets, missing_count = _copy_assets(evidence, assets_dir)
        sections = [
            _section_from_visual(item, index, segments)
            for index, item in enumerate(evidence, start=1)
        ]
        note_path = output_dir / "note.md"
        manifest_path = output_dir / "manifest.json"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(
            _render_note(
                title=title,
                course=str(lesson.get("course") or ""),
                sections=sections,
                copied_assets=copied_assets,
            ),
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "1",
            "route_label": "semantic_visual_rule_baseline",
            "lesson_id": lesson.get("lesson_id"),
            "title": title,
            "lesson_output": lesson_output,
            "note_path": str(note_path),
            "asset_count": len(copied_assets),
            "missing_image_count": missing_count,
            "section_count": len(sections),
            "visual_evidence_count": len(evidence),
            "skipped_error_visual_count": metrics.get("skipped_error_visual_count", 0),
            "request_metrics": metrics,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summaries.append(manifest)
    return summaries


def _section_from_visual(
    visual: dict[str, Any],
    index: int,
    segments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    linked_ids = [
        str(value)
        for value in visual.get("linked_transcript_segment_ids", [])
        if value is not None
    ]
    linked_segments = [segments[value] for value in linked_ids if value in segments]
    observations = visual.get("structured_observations")
    topic = ""
    if isinstance(observations, dict) and isinstance(observations.get("topic"), str):
        topic = observations["topic"].strip()
    if not topic:
        topic = _first_non_empty_line(str(visual.get("ocr_text") or ""))
    if not topic:
        topic = str(visual.get("frame_id") or f"视觉证据 {index}")
    return {
        "title": topic,
        "image_path": str(visual.get("image_path") or ""),
        "timestamp": visual.get("timestamp"),
        "frame_id": visual.get("frame_id"),
        "vision_description": str(visual.get("vision_description") or "").strip(),
        "ocr_text": str(visual.get("ocr_text") or "").strip(),
        "linked_segments": linked_segments,
        "observations": observations if isinstance(observations, dict) else {},
    }


def _render_note(
    *,
    title: str,
    course: str,
    sections: list[dict[str, Any]],
    copied_assets: dict[str, Path],
) -> str:
    lines = [
        f"# {title}",
        "",
        "## 课程信息",
        "",
        f"- 课程：{course}",
        "- 生成方式：本地规则 baseline（时序文本 + Qwen 视觉证据）",
        "",
        "## 知识结构",
        "",
    ]
    if not sections:
        lines.extend(["No non-error visual evidence was found.", ""])
        return "\n".join(lines)

    for index, section in enumerate(sections, start=1):
        section_title = str(section["title"])
        lines.extend([f"### {index}. {section_title}", ""])
        copied = copied_assets.get(str(section.get("image_path") or ""))
        if copied is not None:
            lines.extend(
                [
                    f"![{section_title}]({_markdown_path(Path('assets') / copied.name)})",
                    "",
                ]
            )
        lines.extend(
            [
                f"- 时间：{_format_timestamp(section.get('timestamp'))}",
                f"- Frame：{section.get('frame_id') or ''}",
                "",
            ]
        )
        if section.get("vision_description"):
            lines.extend(["**视觉说明**", "", str(section["vision_description"]), ""])
        observations = section.get("observations")
        if isinstance(observations, dict) and observations.get("key_points"):
            lines.extend(["**视觉要点**", ""])
            for point in observations["key_points"]:
                lines.append(f"- {point}")
            lines.append("")
        linked_segments = section.get("linked_segments")
        if isinstance(linked_segments, list) and linked_segments:
            lines.extend(["**对应时序文本**", ""])
            for segment in linked_segments:
                start = _format_timestamp(segment.get("start"))
                end = _format_timestamp(segment.get("end"))
                text = str(segment.get("text") or "").strip()
                if text:
                    lines.append(f"- {start} - {end}: {text}")
            lines.append("")
        if section.get("ocr_text"):
            lines.extend(["**OCR**", "", str(section["ocr_text"]), ""])
    return "\n".join(lines).rstrip() + "\n"


def _copy_assets(
    evidence: list[dict[str, Any]],
    assets_dir: Path,
) -> tuple[dict[str, Path], int]:
    copied: dict[str, Path] = {}
    missing_count = 0
    for item in evidence:
        image_path = item.get("image_path")
        if not isinstance(image_path, str) or not image_path:
            missing_count += 1
            continue
        source = Path(image_path)
        if not source.is_file():
            missing_count += 1
            continue
        target = assets_dir / source.name
        if image_path not in copied:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied[image_path] = target
    return copied, missing_count


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return clean
    return ""


def _format_timestamp(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ""
    return f"{float(value):.2f}s"


def _markdown_path(path: Path) -> str:
    return "/".join(quote(part, safe="") for part in path.parts)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"JSON file does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return data


def _require_string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"lesson.{key} must be a non-empty string")
    return item


if __name__ == "__main__":
    raise SystemExit(main())
