from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BatchPreviewLesson:
    lesson: str
    vtext_note: Path
    lesson_output: Path


@dataclass(frozen=True)
class BatchPreviewInput:
    dataset_id: str
    lessons: list[BatchPreviewLesson]


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
