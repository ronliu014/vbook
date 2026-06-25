"""Transcript import helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vbook_common.types import TranscriptSegment, TranscriptSourceType


def load_transcript(
    path: Path | str,
    source: TranscriptSourceType = TranscriptSourceType.IMPORTED,
) -> list[TranscriptSegment]:
    """Load a timestamped transcript JSON file."""
    transcript_path = Path(path)
    with transcript_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    raw_segments = _extract_segments(data)
    return [
        _segment_from_mapping(index=index, value=value, source=source)
        for index, value in enumerate(raw_segments, start=1)
    ]


def _extract_segments(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("segments"), list):
        return data["segments"]
    raise ValueError("transcript JSON must be a segment list or an object with segments")


def _segment_from_mapping(
    index: int,
    value: Any,
    source: TranscriptSourceType,
) -> TranscriptSegment:
    if not isinstance(value, dict):
        raise ValueError(f"segment {index} must be an object")

    start = _read_number(value, "start", index)
    end = _read_number(value, "end", index)
    if end < start:
        raise ValueError(f"segment {index} has end before start")

    text = str(value.get("text", "")).strip()
    if not text:
        raise ValueError(f"segment {index} has empty text")

    return TranscriptSegment(
        id=f"seg-{index:06d}",
        start=start,
        end=end,
        text=text,
        language=_read_optional_string(value, "language"),
        confidence=_read_optional_number(value, "confidence", index),
        source=source,
    )


def _read_number(value: dict[str, Any], key: str, index: int) -> float:
    raw = value.get(key)
    if not isinstance(raw, (int, float)):
        raise ValueError(f"segment {index} field {key} must be numeric")
    return float(raw)


def _read_optional_number(value: dict[str, Any], key: str, index: int) -> float | None:
    raw = value.get(key)
    if raw is None:
        return None
    if not isinstance(raw, (int, float)):
        raise ValueError(f"segment {index} field {key} must be numeric")
    return float(raw)


def _read_optional_string(value: dict[str, Any], key: str) -> str | None:
    raw = value.get(key)
    if raw is None:
        return None
    return str(raw)
