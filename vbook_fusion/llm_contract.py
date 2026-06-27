"""Provider-neutral LLM fusion request and response contracts."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import KnowledgeSection, VideoAsset


LLM_FUSION_REQUEST_INTENT = "llm_fusion_request"
LLM_FUSION_SECTIONS_INTENT = "llm_fusion_sections"
LLM_FUSION_SCHEMA_VERSION = "1"

LLM_FUSION_INSTRUCTIONS = [
    "Use only provided evidence.",
    "Preserve source_timestamps and image_refs.",
    "Do not invent facts not supported by evidence.",
    "Write concise Simplified Chinese notes unless evidence is clearly another language.",
]

LLM_FUSION_OUTPUT_CONTRACT = {
    "schema_version": LLM_FUSION_SCHEMA_VERSION,
    "required_top_level_fields": ["title", "overview", "sections"],
    "section_required_fields": [
        "title",
        "summary",
        "key_points",
        "source_timestamps",
        "image_refs",
        "tags",
    ],
}


def build_llm_fusion_request(
    video: VideoAsset,
    evidence_sections: Sequence[KnowledgeSection],
) -> dict[str, Any]:
    """Build a provider-neutral request payload for future LLM synthesis."""
    return to_jsonable(
        {
            "schema_version": LLM_FUSION_SCHEMA_VERSION,
            "intent": LLM_FUSION_REQUEST_INTENT,
            "task": "course_note_synthesis",
            "output_contract": LLM_FUSION_OUTPUT_CONTRACT,
            "video": {
                "id": video.id,
                "course_title": video.course_title,
                "lesson_title": video.lesson_title,
                "duration_seconds": video.duration_seconds,
            },
            "instructions": LLM_FUSION_INSTRUCTIONS,
            "evidence_sections": list(evidence_sections),
        }
    )


def parse_llm_fusion_response(response: dict[str, Any]) -> list[KnowledgeSection]:
    """Validate an LLM JSON response and convert it to knowledge sections."""
    if not isinstance(response, dict):
        raise ValueError("response must be an object")
    _require_string(response, "schema_version", "schema_version")
    if response["schema_version"] != LLM_FUSION_SCHEMA_VERSION:
        raise ValueError("schema_version must be '1'")
    _require_string(response, "title", "title")
    _require_string(response, "overview", "overview")
    sections = response.get("sections")
    if not isinstance(sections, list):
        raise ValueError("sections must be a list")

    return [
        _knowledge_section_from_response(section, index)
        for index, section in enumerate(sections)
    ]


def _knowledge_section_from_response(value: Any, index: int) -> KnowledgeSection:
    path = f"sections[{index}]"
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    title = _require_string(value, "title", f"{path}.title")
    summary = _require_string(value, "summary", f"{path}.summary")
    return KnowledgeSection(
        title=title,
        summary=summary,
        key_points=_require_string_list(value, "key_points", f"{path}.key_points"),
        source_timestamps=_require_number_list(
            value,
            "source_timestamps",
            f"{path}.source_timestamps",
        ),
        image_refs=_unique(
            _require_string_list(value, "image_refs", f"{path}.image_refs")
        ),
        tags=_unique(["llm", *_require_string_list(value, "tags", f"{path}.tags")]),
    )


def _require_string(value: dict[str, Any], key: str, path: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"{path} must be a string")
    return item


def _require_string_list(value: dict[str, Any], key: str, path: str) -> list[str]:
    item = value.get(key)
    if not isinstance(item, list):
        raise ValueError(f"{path} must be a list")
    result = []
    for index, entry in enumerate(item):
        if not isinstance(entry, str):
            raise ValueError(f"{path}[{index}] must be a string")
        result.append(entry)
    return result


def _require_number_list(value: dict[str, Any], key: str, path: str) -> list[float]:
    item = value.get(key)
    if not isinstance(item, list):
        raise ValueError(f"{path} must be a list")
    result = []
    for index, entry in enumerate(item):
        if isinstance(entry, bool) or not isinstance(entry, (int, float)):
            raise ValueError(f"{path}[{index}] must be a number")
        number = float(entry)
        if not math.isfinite(number):
            raise ValueError(f"{path}[{index}] must be finite")
        result.append(number)
    return result


def _unique(values: Sequence[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def write_llm_fusion_request(request: dict[str, Any], path: Path | str) -> Path:
    """Write an LLM fusion request payload as formatted UTF-8 JSON."""
    return _write_json(request, path)


def write_llm_fusion_sections(
    sections: Sequence[KnowledgeSection],
    path: Path | str,
) -> Path:
    """Write parsed LLM fusion sections as formatted UTF-8 JSON."""
    return _write_json(
        {
            "schema_version": LLM_FUSION_SCHEMA_VERSION,
            "intent": LLM_FUSION_SECTIONS_INTENT,
            "section_count": len(sections),
            "sections": list(sections),
        },
        path,
    )


def _write_json(payload: dict[str, Any], path: Path | str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
