"""Knowledge-section construction and writing."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import (
    KnowledgeSection,
    TimelineLink,
    TranscriptSegment,
    VisualAnalysis,
)

MAX_TOPIC_MERGE_GAP_SECONDS = 30.0
MAX_SHARED_FRAME_MERGE_GAP_SECONDS = 30.0
MAX_SHORT_TEXT_MERGE_GAP_SECONDS = 1.0
MAX_MERGED_TRANSCRIPT_CHARS = 240


@dataclass(frozen=True)
class _EvidenceSegment:
    segment: TranscriptSegment
    evidence_items: tuple[VisualAnalysis, ...]


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

    evidence_segments = [
        _EvidenceSegment(
            segment=segment,
            evidence_items=tuple(evidence_by_segment_id.get(segment.id, [])),
        )
        for segment in sorted(segments, key=lambda item: (item.start, item.end, item.id))
    ]
    return [
        _section_from_group(group)
        for group in _merge_evidence_segments(evidence_segments)
    ]


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


def _merge_evidence_segments(
    evidence_segments: Sequence[_EvidenceSegment],
) -> list[list[_EvidenceSegment]]:
    groups: list[list[_EvidenceSegment]] = []
    for evidence_segment in evidence_segments:
        if groups and _should_merge_with_group(groups[-1], evidence_segment):
            groups[-1].append(evidence_segment)
            continue
        groups.append([evidence_segment])
    return groups


def _should_merge_with_group(
    group: Sequence[_EvidenceSegment],
    next_item: _EvidenceSegment,
) -> bool:
    gap_seconds = _gap_seconds(group[-1].segment, next_item.segment)
    if _merged_transcript_length([*group, next_item]) > MAX_MERGED_TRANSCRIPT_CHARS:
        return False

    group_heading = _group_semantic_heading(group)
    next_heading = _semantic_heading(next_item.evidence_items)
    if group_heading and next_heading and group_heading != next_heading:
        return False

    group_has_evidence = _group_has_visual_evidence(group)
    next_has_evidence = bool(next_item.evidence_items)

    if _groups_share_frame(group, next_item):
        return gap_seconds <= MAX_SHARED_FRAME_MERGE_GAP_SECONDS
    if group_heading and next_heading and group_heading == next_heading:
        return gap_seconds <= MAX_TOPIC_MERGE_GAP_SECONDS
    if group_has_evidence and next_has_evidence:
        return False
    if not group_has_evidence and not next_has_evidence:
        return gap_seconds <= MAX_SHORT_TEXT_MERGE_GAP_SECONDS
    if group_has_evidence and not next_has_evidence:
        return gap_seconds <= MAX_SHORT_TEXT_MERGE_GAP_SECONDS
    return False


def _gap_seconds(left: TranscriptSegment, right: TranscriptSegment) -> float:
    return max(0.0, right.start - left.end)


def _merged_transcript_length(group: Sequence[_EvidenceSegment]) -> int:
    return len(_combined_transcript_text(item.segment for item in group))


def _combined_transcript_text(segments: Sequence[TranscriptSegment] | Any) -> str:
    return " ".join(segment.text.strip() for segment in segments if segment.text.strip())


def _group_semantic_heading(group: Sequence[_EvidenceSegment]) -> str | None:
    for item in group:
        heading = _semantic_heading(item.evidence_items)
        if heading:
            return heading
    return None


def _semantic_heading(evidence_items: Sequence[VisualAnalysis]) -> str | None:
    for analysis in evidence_items:
        for key in ("topic", "title", "heading"):
            value = analysis.structured_observations.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _group_has_visual_evidence(group: Sequence[_EvidenceSegment]) -> bool:
    return any(item.evidence_items for item in group)


def _groups_share_frame(
    group: Sequence[_EvidenceSegment],
    next_item: _EvidenceSegment,
) -> bool:
    group_frame_ids = {
        analysis.frame_id
        for item in group
        for analysis in item.evidence_items
    }
    next_frame_ids = {analysis.frame_id for analysis in next_item.evidence_items}
    return bool(group_frame_ids.intersection(next_frame_ids))


def _section_from_group(group: Sequence[_EvidenceSegment]) -> KnowledgeSection:
    segments = [item.segment for item in group]
    evidence_items = _group_evidence_items(group)
    return KnowledgeSection(
        title=_section_title(segments[0], evidence_items),
        summary=_section_summary(segments, evidence_items),
        source_timestamps=[segments[0].start, segments[-1].end],
        image_refs=_section_image_refs(evidence_items),
        key_points=_section_key_points(segments, evidence_items),
        tags=_section_tags(evidence_items),
    )


def _group_evidence_items(
    group: Sequence[_EvidenceSegment],
) -> list[VisualAnalysis]:
    evidence_items: list[VisualAnalysis] = []
    for item in group:
        for analysis in item.evidence_items:
            if analysis not in evidence_items:
                evidence_items.append(analysis)
    return evidence_items


def _section_title(
    segment: TranscriptSegment,
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    heading = _semantic_heading(evidence_items)
    if heading:
        return heading
    transcript_title = _compact_text(segment.text, max_chars=18)
    if transcript_title:
        return transcript_title
    return f"Segment {segment.id}"


def _section_summary(
    segments: Sequence[TranscriptSegment],
    evidence_items: Sequence[VisualAnalysis],
) -> str:
    parts = []
    transcript_text = _combined_transcript_text(segments)
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
    segments: Sequence[TranscriptSegment],
    evidence_items: Sequence[VisualAnalysis],
) -> list[str]:
    points = []
    for segment in segments:
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
