"""Placeholder knowledge-section construction and writing."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import (
    KnowledgeSection,
    TimelineLink,
    TranscriptSegment,
    VisualAnalysis,
)


def build_evidence_sections(
    segments: Sequence[TranscriptSegment],
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    timeline_links: Sequence[TimelineLink] | None = None,
) -> list[KnowledgeSection]:
    """Build deterministic evidence sections from transcript and visual context."""
    evidence_by_segment_id = _build_visual_evidence_by_segment_id(
        visual_analyses=visual_analyses or [],
        timeline_links=timeline_links or [],
    )

    sections: list[KnowledgeSection] = []
    for segment in sorted(segments, key=lambda item: (item.start, item.end, item.id)):
        evidence_items = evidence_by_segment_id.get(segment.id, [])
        sections.append(
            KnowledgeSection(
                title=_section_title(segment, evidence_items),
                summary=_section_summary(segment, evidence_items),
                source_timestamps=[segment.start, segment.end],
                image_refs=_section_image_refs(evidence_items),
                key_points=_section_key_points(segment, evidence_items),
                tags=_section_tags(evidence_items),
            )
        )
    return sections


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
                    "intent": _fusion_sections_intent(sections),
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


def _fusion_sections_intent(sections: Sequence[KnowledgeSection]) -> str:
    if any("evidence" in section.tags for section in sections):
        return "fusion_sections_evidence"
    return "fusion_sections_placeholder"


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


def _build_visual_evidence_by_segment_id(
    visual_analyses: Sequence[VisualAnalysis],
    timeline_links: Sequence[TimelineLink],
) -> dict[str, list[VisualAnalysis]]:
    analysis_by_frame_id = {analysis.frame_id: analysis for analysis in visual_analyses}
    evidence_by_segment_id: dict[str, list[VisualAnalysis]] = {}
    for link in sorted(timeline_links, key=lambda item: item.frame_id):
        analysis = analysis_by_frame_id.get(link.frame_id)
        if analysis is None:
            continue
        for segment_id in link.transcript_segment_ids:
            items = evidence_by_segment_id.setdefault(segment_id, [])
            if analysis not in items:
                items.append(analysis)
    return evidence_by_segment_id


def _section_title(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    for analysis in evidence_items:
        for key in ("topic", "title", "heading"):
            value = analysis.structured_observations.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    transcript_title = _compact_text(segment.text, max_chars=18)
    if transcript_title:
        return transcript_title
    return f"Segment {segment.id}"


def _section_summary(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    parts = []
    transcript_text = segment.text.strip()
    if transcript_text:
        parts.append(f"讲解：{transcript_text}")
    for analysis in evidence_items:
        if analysis.vision_description.strip():
            parts.append(f"视觉：{analysis.vision_description.strip()}")
        if analysis.ocr_text.strip():
            parts.append(f"画面文字：{_first_line(analysis.ocr_text.strip())}")
    return " ".join(_unique(parts))


def _section_image_refs(evidence_items: Sequence[VisualAnalysis]) -> list[str]:
    refs = [analysis.image_path.as_posix() for analysis in evidence_items]
    return _unique(refs)


def _section_key_points(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> list[str]:
    points = []
    if segment.text.strip():
        points.append(f"讲解：{segment.text.strip()}")
    for analysis in evidence_items:
        if analysis.ocr_text.strip():
            points.append(f"画面文字：{analysis.ocr_text.strip()}")
        if analysis.vision_description.strip():
            points.append(f"视觉描述：{analysis.vision_description.strip()}")
        observations = analysis.structured_observations
        topic = observations.get("topic")
        if isinstance(topic, str) and topic.strip():
            points.append(f"主题：{topic.strip()}")
        key_points = observations.get("key_points")
        if isinstance(key_points, list):
            points.extend(item.strip() for item in key_points if isinstance(item, str))
        visible_elements = observations.get("visible_elements")
        if isinstance(visible_elements, list):
            elements = [
                item.strip()
                for item in visible_elements
                if isinstance(item, str) and item.strip()
            ]
            if elements:
                points.append(f"可见元素：{'、'.join(elements)}")
    return _unique(point for point in points if point.strip())


def _section_tags(evidence_items: Sequence[VisualAnalysis]) -> list[str]:
    tags = ["evidence"]
    for analysis in evidence_items:
        tags.append(f"visual:{analysis.visual_type.value}")
        if analysis.ocr_text.strip():
            tags.append("has_ocr")
        tags.append("has_image")
        language = analysis.structured_observations.get("language")
        if isinstance(language, str) and language.strip():
            tags.append(f"lang:{language.strip()}")
    return _unique(tags)


def _compact_text(text: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars]


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _unique(values: Sequence[str] | Any) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
