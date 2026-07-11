"""Build local Qwen visual-evidence inspection packs."""

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
        summaries = write_visual_evidence_pack(
            dataset_path=Path(args.dataset),
            output_root=Path(args.output),
            max_visuals_per_lesson=args.max_visuals_per_lesson,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"qwen visual evidence pack error: {exc}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write Markdown inspection packs for Qwen visual evidence."
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


def write_visual_evidence_pack(
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
        output_dir = root / title
        assets_dir = output_dir / "assets"
        evidence = [
            item for item in request.get("visual_evidence", []) if isinstance(item, dict)
        ]
        copied_assets, missing_count = _copy_assets(evidence, assets_dir)
        note_path = output_dir / "visual-evidence.md"
        manifest_path = output_dir / "manifest.json"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(
            _render_markdown(
                title=title,
                course=str(lesson.get("course") or ""),
                evidence=evidence,
                copied_assets=copied_assets,
            ),
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "1",
            "route_label": "qwen_visual_evidence_240s",
            "lesson_id": lesson.get("lesson_id"),
            "title": title,
            "lesson_output": lesson_output,
            "note_path": str(note_path),
            "asset_count": len(copied_assets),
            "missing_image_count": missing_count,
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


def _render_markdown(
    *,
    title: str,
    course: str,
    evidence: list[dict[str, Any]],
    copied_assets: dict[str, Path],
) -> str:
    lines = [
        f"# {title}",
        "",
        "## 课程信息",
        "",
        f"- 课程：{course}",
        f"- 视觉证据数量：{len(evidence)}",
        "",
        "## Qwen 视觉证据",
        "",
    ]
    if not evidence:
        lines.extend(["No non-error visual evidence was found.", ""])
        return "\n".join(lines)

    for index, item in enumerate(evidence, start=1):
        frame_id = str(item.get("frame_id") or f"visual-{index}")
        timestamp = item.get("timestamp")
        image_path = str(item.get("image_path") or "")
        copied = copied_assets.get(image_path)
        lines.extend(
            [
                f"### {index}. {frame_id}",
                "",
                f"- 时间：{_format_timestamp(timestamp)}",
                f"- 类型：{item.get('visual_type') or ''}",
                f"- 置信度：{item.get('confidence') if item.get('confidence') is not None else ''}",
                f"- Transcript window：{item.get('window_start') or ''} - {item.get('window_end') or ''}",
                f"- Linked segments：{', '.join(str(value) for value in item.get('linked_transcript_segment_ids', []))}",
                "",
            ]
        )
        if copied is not None:
            lines.extend([f"![{frame_id}]({_markdown_path(Path('assets') / copied.name)})", ""])
        else:
            lines.extend([f"- Missing image: `{image_path}`", ""])
        observations = item.get("structured_observations")
        if isinstance(observations, dict) and observations:
            lines.extend(["**Structured observations**", ""])
            for key, value in observations.items():
                lines.append(f"- {key}: {_format_value(value)}")
            lines.append("")
        if item.get("ocr_text"):
            lines.extend(["**OCR**", "", str(item["ocr_text"]).strip(), ""])
        if item.get("vision_description"):
            lines.extend(
                [
                    "**Vision description**",
                    "",
                    str(item["vision_description"]).strip(),
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _format_timestamp(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ""
    return f"{float(value):.2f}s"


def _format_value(value: Any) -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


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
