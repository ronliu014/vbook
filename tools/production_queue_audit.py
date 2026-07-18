import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProductionQueuePackage:
    output_dir: Path
    json_path: Path
    markdown_path: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit vBook production queue readiness for a course directory."
    )
    parser.add_argument("--course", required=True)
    parser.add_argument("--vtext-root", required=True)
    parser.add_argument("--video-root", required=True)
    parser.add_argument("--lesson-output-root", action="append", required=True)
    parser.add_argument("--published-vault-root")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    package = create_production_queue_audit(
        course=args.course,
        vtext_root=args.vtext_root,
        video_root=args.video_root,
        lesson_output_roots=args.lesson_output_root,
        published_vault_root=args.published_vault_root,
        output_dir=args.output_dir,
    )
    print(str(package.json_path))
    return 0


def create_production_queue_audit(
    *,
    course: str,
    vtext_root: Path | str,
    video_root: Path | str,
    lesson_output_roots: list[Path | str],
    published_vault_root: Path | str | None,
    output_dir: Path | str,
) -> ProductionQueuePackage:
    course = course.strip().strip("/\\")
    if not course:
        raise ValueError("course is required")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = build_production_queue_audit(
        course=course,
        vtext_root=Path(vtext_root),
        video_root=Path(video_root),
        lesson_output_roots=[Path(path) for path in lesson_output_roots],
        published_vault_root=Path(published_vault_root)
        if published_vault_root is not None
        else None,
    )
    json_path = output / "production-queue-audit.json"
    markdown_path = output / "production-queue-audit.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return ProductionQueuePackage(
        output_dir=output,
        json_path=json_path,
        markdown_path=markdown_path,
    )


def build_production_queue_audit(
    *,
    course: str,
    vtext_root: Path,
    video_root: Path,
    lesson_output_roots: list[Path],
    published_vault_root: Path | None,
) -> dict[str, Any]:
    video_course_dir = video_root / course
    vtext_course_dir = vtext_root / course
    published_course_dir = published_vault_root if published_vault_root else None
    lesson_output_index = _index_lesson_outputs(lesson_output_roots)
    lessons = []
    for video in _video_files(video_course_dir):
        lesson = video.stem
        vtext_note = vtext_course_dir / f"{lesson}.md"
        lesson_output = lesson_output_index.get(lesson)
        published_note = (
            published_course_dir / f"{lesson}.md" if published_course_dir else None
        )
        status = _status(
            has_vtext=vtext_note.is_file(),
            has_lesson_output=lesson_output is not None,
            has_published=published_note.is_file() if published_note else False,
        )
        lessons.append(
            {
                "lesson": lesson,
                "status": status,
                "video": str(video),
                "vtext_note": str(vtext_note) if vtext_note.is_file() else None,
                "lesson_output": str(lesson_output) if lesson_output else None,
                "published_note": str(published_note)
                if published_note and published_note.is_file()
                else None,
                "missing": _missing(
                    has_vtext=vtext_note.is_file(),
                    has_lesson_output=lesson_output is not None,
                ),
            }
        )
    return {
        "schema_version": "1",
        "kind": "vbook_production_queue_audit",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "course": course,
        "vtext_root": str(vtext_root),
        "video_root": str(video_root),
        "lesson_output_roots": [str(path) for path in lesson_output_roots],
        "published_vault_root": str(published_vault_root)
        if published_vault_root
        else None,
        "lesson_count": len(lessons),
        "status_counts": _count_statuses(lessons),
        "lessons": lessons,
    }


def _video_files(video_course_dir: Path) -> list[Path]:
    if not video_course_dir.is_dir():
        return []
    suffixes = {".mp4", ".mkv", ".avi", ".mov"}
    return sorted(
        (path for path in video_course_dir.iterdir() if path.suffix.lower() in suffixes),
        key=lambda path: path.name,
    )


def _index_lesson_outputs(roots: list[Path]) -> dict[str, Path]:
    candidates: dict[str, list[Path]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for manifest in root.rglob("manifest.json"):
            lesson_dir = manifest.parent
            if not _is_ready_lesson_output(lesson_dir):
                continue
            candidates.setdefault(lesson_dir.name, []).append(lesson_dir)
    return {
        lesson: _preferred_lesson_output(paths)
        for lesson, paths in candidates.items()
    }


def _is_ready_lesson_output(path: Path) -> bool:
    return (
        (path / "manifest.json").is_file()
        and (path / "vision" / "analysis.json").is_file()
        and (path / "fusion" / "sections.json").is_file()
    )


def _preferred_lesson_output(paths: list[Path]) -> Path:
    def score(path: Path) -> tuple[int, float, str]:
        normalized = str(path).replace("\\", "/").lower()
        is_240s = 1 if "/240s/" in normalized or normalized.endswith("-240s") else 0
        return (is_240s, path.stat().st_mtime, str(path))

    return sorted(paths, key=score, reverse=True)[0]


def _status(*, has_vtext: bool, has_lesson_output: bool, has_published: bool) -> str:
    if has_published:
        return "published"
    if has_vtext and has_lesson_output:
        return "ready_for_preview"
    if not has_vtext and not has_lesson_output:
        return "waiting_vtext_and_lesson_output"
    if not has_vtext:
        return "waiting_vtext"
    return "waiting_lesson_output"


def _missing(*, has_vtext: bool, has_lesson_output: bool) -> list[str]:
    missing = []
    if not has_vtext:
        missing.append("vtext_note")
    if not has_lesson_output:
        missing.append("lesson_output")
    return missing


def _count_statuses(lessons: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for lesson in lessons:
        status = str(lesson["status"])
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Production Queue Audit: {payload['course']}",
        "",
        f"- Lessons: {payload['lesson_count']}",
        f"- Vtext root: `{payload['vtext_root']}`",
        f"- Video root: `{payload['video_root']}`",
        f"- Published vault root: `{payload['published_vault_root']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in payload["status_counts"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Lessons", ""])
    for item in payload["lessons"]:
        missing = ", ".join(item["missing"]) if item["missing"] else "none"
        lines.append(f"### {item['lesson']}")
        lines.append("")
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Missing: `{missing}`")
        lines.append(f"- Video: `{item['video']}`")
        lines.append(f"- Vtext note: `{item['vtext_note']}`")
        lines.append(f"- Lesson output: `{item['lesson_output']}`")
        lines.append(f"- Published note: `{item['published_note']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
