"""Render manually supplied semantic visual model responses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from vbook_export.semantic_visual_note import write_semantic_visual_note_package


DEFAULT_EXPERIMENT_ROOT = Path(
    "F:/vbook/experiments/E20260710-semantic-visual-note"
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        summaries = render_responses(
            experiment_root=Path(args.experiment_root),
            provider=args.provider,
            lesson_ids=args.lesson_id or [],
            max_visuals_per_request=args.max_visuals_per_request,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render semantic visual response error: {exc}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render local semantic_visual_note responses into Markdown previews."
    )
    parser.add_argument(
        "--experiment-root",
        default=str(DEFAULT_EXPERIMENT_ROOT),
        help="Experiment root containing inputs/, responses/, and renders/",
    )
    parser.add_argument(
        "--provider",
        default="openai",
        help="Provider directory under responses/ and renders/",
    )
    parser.add_argument(
        "--lesson-id",
        action="append",
        help="Lesson id from inputs/dataset.json; repeat or omit to render all available responses",
    )
    parser.add_argument(
        "--max-visuals-per-request",
        type=int,
        default=4,
        help="Maximum visual evidence records used when rebuilding render context",
    )
    return parser


def render_responses(
    *,
    experiment_root: Path,
    provider: str,
    lesson_ids: list[str],
    max_visuals_per_request: int,
) -> list[dict[str, Any]]:
    dataset = _read_json(experiment_root / "inputs" / "dataset.json")
    lessons = dataset.get("lessons")
    if not isinstance(lessons, list):
        raise ValueError("dataset.lessons must be a list")

    selected = [
        lesson
        for lesson in lessons
        if isinstance(lesson, dict)
        and (not lesson_ids or str(lesson.get("lesson_id")) in lesson_ids)
    ]
    if not selected:
        raise ValueError("no matching lessons found")

    summaries = []
    for lesson in selected:
        title = _require_string(lesson, "title")
        response_path = (
            experiment_root / "responses" / provider / f"{title}.response.json"
        )
        if not response_path.exists():
            continue
        output_dir = experiment_root / "renders" / "semantic_visual_note" / provider / title
        package = write_semantic_visual_note_package(
            lesson_output_dir=_require_string(lesson, "lesson_output"),
            output_dir=output_dir,
            transcript_source_label=str(
                lesson.get("transcript_source_label") or "vtext_semantic_verified"
            ),
            llm_response_path=response_path,
            max_visuals_per_request=max_visuals_per_request,
        )
        manifest = _read_json(package.manifest_path)
        summaries.append(
            {
                "lesson_id": lesson.get("lesson_id"),
                "title": title,
                "provider": provider,
                "status": manifest.get("status"),
                "response_path": str(response_path),
                "note_path": str(package.note_path) if package.note_path else None,
                "manifest_path": str(package.manifest_path),
                "asset_count": len(package.asset_paths),
            }
        )
    if not summaries:
        raise ValueError(
            f"no response JSON files found under {experiment_root / 'responses' / provider}"
        )
    return summaries


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"JSON file not found: {path}")
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
