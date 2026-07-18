from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vbook_export.vault_enhance import write_vtext_first_package


@dataclass(frozen=True)
class BatchPreviewLesson:
    lesson: str
    vtext_note: Path
    lesson_output: Path


@dataclass(frozen=True)
class BatchPreviewInput:
    dataset_id: str
    lessons: list[BatchPreviewLesson]


@dataclass(frozen=True)
class BatchPreviewPackage:
    status: str
    json_path: Path
    markdown_path: Path
    done_count: int
    failed_count: int
    skipped_count: int


def load_batch_input(path: Path | str) -> BatchPreviewInput:
    input_path = Path(path)
    data = json.loads(input_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("batch input must be a JSON object")
    if data.get("schema_version") != "1":
        raise ValueError("unsupported batch input schema_version")
    if data.get("kind") != "vtext_first_batch_input":
        raise ValueError("unsupported batch input kind")
    dataset_id = str(data.get("dataset_id") or "").strip()
    if not dataset_id:
        raise ValueError("batch input requires dataset_id")
    raw_lessons = data.get("lessons")
    if not isinstance(raw_lessons, list) or not raw_lessons:
        raise ValueError("batch input requires non-empty lessons")
    lessons = []
    for index, item in enumerate(raw_lessons):
        if not isinstance(item, dict):
            raise ValueError(f"lessons[{index}] must be an object")
        lesson = str(item.get("lesson") or "").strip()
        vtext_note = Path(str(item.get("vtext_note") or ""))
        lesson_output = Path(str(item.get("lesson_output") or ""))
        if not lesson:
            raise ValueError(f"lessons[{index}].lesson is required")
        lessons.append(
            BatchPreviewLesson(
                lesson=lesson,
                vtext_note=vtext_note,
                lesson_output=lesson_output,
            )
        )
    return BatchPreviewInput(dataset_id=dataset_id, lessons=lessons)


def run_batch_preview(
    *,
    batch_input_path: Path | str,
    output_root: Path | str,
    route: str,
    variant: str,
    max_images_per_note: int | None,
    min_image_gap_seconds: float,
) -> BatchPreviewPackage:
    if route != "vtext_first_vault_enhance":
        raise ValueError("only vtext_first_vault_enhance is supported")
    root = Path(output_root)
    _reject_vault_output_root(root)
    batch = load_batch_input(batch_input_path)
    render_root = root / "renders" / route / variant
    results = []
    for lesson in batch.lessons:
        lesson_dir = render_root / lesson.lesson
        note_path = lesson_dir / "note.md"
        manifest_path = lesson_dir / "note.manifest.json"
        try:
            if not lesson.vtext_note.is_file():
                raise FileNotFoundError(f"vtext note does not exist: {lesson.vtext_note}")
            if not lesson.lesson_output.is_dir():
                raise FileNotFoundError(
                    f"lesson output does not exist: {lesson.lesson_output}"
                )
            package = write_vtext_first_package(
                vtext_note_path=lesson.vtext_note,
                lesson_output_dir=lesson.lesson_output,
                output_note_path=note_path,
                manifest_path=manifest_path,
                max_images_per_note=max_images_per_note,
                min_image_gap_seconds=min_image_gap_seconds,
            )
            results.append(
                {
                    "lesson": lesson.lesson,
                    "status": "done",
                    "vtext_note": str(lesson.vtext_note),
                    "lesson_output": str(lesson.lesson_output),
                    "output_note": str(package.output_note_path),
                    "manifest": str(package.manifest_path),
                    "asset_count": len(package.asset_paths),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "lesson": lesson.lesson,
                    "status": "failed",
                    "vtext_note": str(lesson.vtext_note),
                    "lesson_output": str(lesson.lesson_output),
                    "failure_reason": str(exc),
                }
            )
    done_count = sum(1 for item in results if item["status"] == "done")
    failed_count = sum(1 for item in results if item["status"] == "failed")
    payload = {
        "schema_version": "1",
        "kind": "vtext_first_batch_preview",
        "status": "preview_ready" if failed_count == 0 else "preview_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": batch.dataset_id,
        "route": route,
        "variant": variant,
        "output_root": str(root),
        "render_root": str(render_root),
        "done_count": done_count,
        "failed_count": failed_count,
        "skipped_count": 0,
        "safety": {"vault_write": "disabled", "source_vtext": "read_only"},
        "lessons": results,
    }
    json_path = root / "batch-preview-manifest.json"
    markdown_path = root / "batch-preview-manifest.md"
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_batch_preview_markdown(payload), encoding="utf-8")
    return BatchPreviewPackage(
        status=str(payload["status"]),
        json_path=json_path,
        markdown_path=markdown_path,
        done_count=done_count,
        failed_count=failed_count,
        skipped_count=0,
    )


def _reject_vault_output_root(path: Path) -> None:
    normalized = str(path.resolve()).replace("/", "\\").lower()
    blocked = [
        "f:\\vault\\20_learning\\vbook",
        "f:\\vault\\20_learning\\vtext",
    ]
    if any(normalized.startswith(item) for item in blocked):
        raise ValueError("batch preview output root must not be under F:/vault/20_Learning")


def _render_batch_preview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vtext-First Batch Preview: {payload['dataset_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Route: `{payload['route']}`",
        f"- Variant: `{payload['variant']}`",
        f"- Done: {payload['done_count']}",
        f"- Failed: {payload['failed_count']}",
        f"- Vault write: `{payload['safety']['vault_write']}`",
        "",
        "## Lessons",
        "",
    ]
    for item in payload["lessons"]:
        line = f"- `{item['status']}` {item['lesson']}"
        if item["status"] == "done":
            line += f" -> `{item['output_note']}`"
        else:
            line += f" -> {item['failure_reason']}"
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run preview-only vtext-first vault enhancement for a lesson batch."
    )
    parser.add_argument("--batch-input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--route", default="vtext_first_vault_enhance")
    parser.add_argument("--variant", default="baseline")
    parser.add_argument("--max-images-per-note", type=int)
    parser.add_argument("--min-image-gap-seconds", type=float, default=0.0)
    args = parser.parse_args(argv)
    package = run_batch_preview(
        batch_input_path=args.batch_input,
        output_root=args.output_root,
        route=args.route,
        variant=args.variant,
        max_images_per_note=args.max_images_per_note,
        min_image_gap_seconds=args.min_image_gap_seconds,
    )
    print(str(package.json_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
