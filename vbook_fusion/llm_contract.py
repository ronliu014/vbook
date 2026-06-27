"""Provider-neutral LLM fusion request and response contracts."""

from __future__ import annotations

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
    raise NotImplementedError


def write_llm_fusion_request(request: dict[str, Any], path: Path | str) -> Path:
    raise NotImplementedError


def write_llm_fusion_sections(
    sections: Sequence[KnowledgeSection],
    path: Path | str,
) -> Path:
    raise NotImplementedError
