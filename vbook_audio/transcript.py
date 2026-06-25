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
    """Load a timestamped transcript file."""
    transcript_path = Path(path)
    suffix = transcript_path.suffix.lower()
    if suffix == ".json":
        return _load_json_transcript(transcript_path, source)
    if suffix == ".srt":
        return _load_srt_transcript(transcript_path, source)
    raise ValueError(f"unsupported transcript format: {suffix or '<none>'}")


def _load_json_transcript(
    path: Path,
    source: TranscriptSourceType,
) -> list[TranscriptSegment]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    raw_segments = _extract_segments(data)
    return [
        _segment_from_mapping(index=index, value=value, source=source)
        for index, value in enumerate(raw_segments, start=1)
    ]


def _load_srt_transcript(
    path: Path,
    source: TranscriptSourceType,
) -> list[TranscriptSegment]:
    content = path.read_text(encoding="utf-8-sig")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    raw_cues = [cue.strip() for cue in normalized.split("\n\n") if cue.strip()]
    segments: list[TranscriptSegment] = []
    for cue_index, cue in enumerate(raw_cues, start=1):
        lines = [line.strip() for line in cue.split("\n") if line.strip()]
        if lines and lines[0].isdigit():
            lines = lines[1:]
        if not lines:
            continue
        timing_line = lines[0]
        if "-->" not in timing_line:
            raise ValueError(f"SRT cue {cue_index} missing timing line")
        start_raw, end_raw = [part.strip() for part in timing_line.split("-->", maxsplit=1)]
        start = _parse_srt_timestamp(start_raw)
        end = _parse_srt_timestamp(end_raw.split()[0])
        if end < start:
            raise ValueError(f"SRT cue {cue_index} has end before start")
        text = "\n".join(lines[1:]).strip()
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                id=f"seg-{len(segments) + 1:06d}",
                start=start,
                end=end,
                text=text,
                source=source,
            )
        )
    return segments


def _parse_srt_timestamp(value: str) -> float:
    timestamp = value.replace(",", ".")
    pieces = timestamp.split(":")
    if len(pieces) != 3:
        raise ValueError(f"invalid SRT timestamp: {value}")
    hours_raw, minutes_raw, seconds_raw = pieces
    try:
        hours = int(hours_raw)
        minutes = int(minutes_raw)
        seconds = float(seconds_raw)
    except ValueError as exc:
        raise ValueError(f"invalid SRT timestamp: {value}") from exc
    if hours < 0 or minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
        raise ValueError(f"invalid SRT timestamp: {value}")
    return hours * 3600 + minutes * 60 + seconds


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
