"""Batch input discovery and manifest helpers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from vbook_common.serialization import to_jsonable


SUPPORTED_MEDIA_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
}
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "outputs",
    "sync",
    "text",
}
TRANSCRIPT_CANDIDATE_SUFFIXES = (
    "_raw.srt",
    ".srt",
    "_raw.vtt",
    ".vtt",
    "_raw.txt",
    ".txt",
)


@dataclass(frozen=True)
class BatchLessonPlan:
    lesson_id: str
    media_path: Path
    relative_media_path: Path
    output_dir: Path
    transcript_path: Path | None
    vtext_compatible: bool
    skip_reason: str | None = None


@dataclass(frozen=True)
class BatchLessonResult:
    lesson_id: str
    media_path: Path
    transcript_path: Path | None
    output_dir: Path
    status: str
    vtext_compatible: bool
    manifest_path: Path | None = None
    failure_reason: str | None = None


def discover_batch_lessons(
    input_dir: Path | str,
    output_dir: Path | str,
) -> list[BatchLessonPlan]:
    """Discover vtext-compatible media inputs and matching transcript files."""
    root = Path(input_dir)
    output_root = Path(output_dir)
    plans: list[BatchLessonPlan] = []
    for media_path in _iter_media_files(root):
        relative_media = media_path.relative_to(root)
        transcript_path = _find_transcript(root, relative_media)
        output_lesson_dir = output_root / relative_media.with_suffix("")
        lesson_id = relative_media.with_suffix("").as_posix()
        plans.append(
            BatchLessonPlan(
                lesson_id=lesson_id,
                media_path=media_path,
                relative_media_path=relative_media,
                output_dir=output_lesson_dir,
                transcript_path=transcript_path,
                vtext_compatible=transcript_path is not None,
                skip_reason=None if transcript_path is not None else "missing_transcript",
            )
        )
    return plans


def write_batch_manifest(
    results: Sequence[BatchLessonResult],
    path: Path | str,
) -> Path:
    """Write the batch run manifest."""
    result_list = list(results)
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "lesson_count": len(result_list),
        "done_count": sum(1 for result in result_list if result.status == "done"),
        "failed_count": sum(1 for result in result_list if result.status == "failed"),
        "skipped_count": sum(1 for result in result_list if result.status == "skipped"),
        "lessons": result_list,
    }
    manifest_path.write_text(
        json.dumps(to_jsonable(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _iter_media_files(root: Path) -> list[Path]:
    media_files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _has_ignored_parent(path.relative_to(root)):
            continue
        if path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS:
            media_files.append(path)
    return sorted(media_files, key=lambda item: item.relative_to(root).as_posix())


def _has_ignored_parent(relative_path: Path) -> bool:
    return any(part in IGNORED_DIRECTORY_NAMES for part in relative_path.parts[:-1])


def _find_transcript(root: Path, relative_media: Path) -> Path | None:
    transcript_dir = root / "text" / relative_media.parent
    stem = relative_media.stem
    for suffix in TRANSCRIPT_CANDIDATE_SUFFIXES:
        candidate = transcript_dir / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    return None
