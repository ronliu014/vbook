"""Placeholder knowledge-section construction and writing."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from vbook_common.serialization import to_jsonable
from vbook_common.types import (
    KnowledgeSection,
    TimelineLink,
    TranscriptSegment,
    VisualAnalysis,
)


def build_placeholder_sections(
    segments: Sequence[TranscriptSegment],
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    timeline_links: Sequence[TimelineLink] | None = None,
) -> list[KnowledgeSection]:
    """Build traceable placeholder knowledge sections from transcript segments."""
    image_by_frame_id = {
        analysis.frame_id: analysis.image_path.as_posix()
        for analysis in visual_analyses or []
    }
    image_refs_by_segment_id = _build_image_refs_by_segment_id(
        image_by_frame_id=image_by_frame_id,
        timeline_links=timeline_links or [],
    )

    sections: list[KnowledgeSection] = []
    for segment in sorted(segments, key=lambda item: (item.start, item.end, item.id)):
        sections.append(
            KnowledgeSection(
                title=f"Segment {segment.id}",
                summary=segment.text,
                source_timestamps=[segment.start, segment.end],
                image_refs=image_refs_by_segment_id.get(segment.id, []),
                key_points=[],
                tags=["placeholder"],
            )
        )
    return sections


def write_fusion_sections(
    sections: Sequence[KnowledgeSection],
    path: Path | str,
) -> Path:
    """Write placeholder fusion sections as formatted UTF-8 JSON."""
    sections_path = Path(path)
    sections_path.parent.mkdir(parents=True, exist_ok=True)
    sections_path.write_text(
        json.dumps(
            to_jsonable(
                {
                    "schema_version": "1",
                    "intent": "fusion_sections_placeholder",
                    "section_count": len(sections),
                    "sections": list(sections),
                }
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return sections_path


def _build_image_refs_by_segment_id(
    image_by_frame_id: dict[str, str],
    timeline_links: Sequence[TimelineLink],
) -> dict[str, list[str]]:
    image_refs_by_segment_id: dict[str, list[str]] = {}
    for link in sorted(timeline_links, key=lambda item: item.frame_id):
        image_ref = image_by_frame_id.get(link.frame_id)
        if not image_ref:
            continue
        for segment_id in link.transcript_segment_ids:
            image_refs = image_refs_by_segment_id.setdefault(segment_id, [])
            if image_ref not in image_refs:
                image_refs.append(image_ref)
    return image_refs_by_segment_id
