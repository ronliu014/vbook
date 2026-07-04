"""Markdown note rendering and writing."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from vbook_common.types import (
    FilterStatus,
    FrameCandidate,
    KnowledgeSection,
    TimelineLink,
    TranscriptSegment,
    VideoAsset,
    VisualAnalysis,
)


def render_placeholder_note(
    video: VideoAsset,
    segments: Sequence[TranscriptSegment],
    frames: Sequence[FrameCandidate] | None = None,
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    timeline_links: Sequence[TimelineLink] | None = None,
) -> str:
    """Render a deterministic placeholder note from currently available artifacts."""
    segment_list = sorted(segments, key=lambda item: (item.start, item.end, item.id))
    frame_list = sorted(frames or [], key=lambda item: (item.timestamp, item.id))
    analysis_list = sorted(visual_analyses or [], key=lambda item: item.frame_id)
    link_list = sorted(timeline_links or [], key=lambda item: item.frame_id)

    selected_count = sum(
        1 for frame in frame_list if frame.filter_status == FilterStatus.SELECTED
    )
    candidate_count = len(frame_list)
    title = video.lesson_title or video.id
    course_title = video.course_title or ""
    time_range = _format_time_range(segment_list)

    lines = [
        f"# {title}",
        "",
        "## Course",
        "",
        f"- Course: {course_title}",
        f"- Lesson: {title}",
        f"- Video: {video.path}",
        "",
        "## Transcript Summary",
        "",
        f"- Segments: {len(segment_list)}",
        f"- Time Range: {time_range}",
        "",
        "## Visual Assets",
        "",
        f"- Candidate Frames: {candidate_count}",
        f"- Selected Frames: {selected_count}",
        f"- Visual Analyses: {len(analysis_list)}",
        "",
        "## Timeline Links",
        "",
    ]

    if link_list:
        for link in link_list:
            segment_ids = ", ".join(link.transcript_segment_ids) or "(none)"
            lines.append(f"- {link.frame_id}: {segment_ids}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Transcript", ""])
    if segment_list:
        for segment in segment_list:
            lines.append(
                f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}"
            )
    else:
        lines.append("(empty)")

    return "\n".join(lines) + "\n"


def write_note(markdown: str, path: Path | str) -> Path:
    """Write Markdown note text as UTF-8."""
    note_path = Path(path)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(markdown, encoding="utf-8")
    return note_path


def render_sections_note(
    video: VideoAsset,
    sections: Sequence[KnowledgeSection],
) -> str:
    """Render a readable expert course note from fused knowledge sections."""
    section_list = sorted(sections, key=_section_sort_key)
    title = video.lesson_title or video.id
    course_title = video.course_title or ""
    time_range = _format_course_time_range(section_list)

    lines = [
        f"# {title}",
        "",
        "## 课程信息",
        "",
        f"- 课程：{course_title}",
        f"- 课节：{title}",
        f"- 视频：{video.path}",
        f"- 知识段落：{len(section_list)}",
        f"- 时间范围：{time_range}",
        "",
        "## 课程总览",
        "",
    ]

    if not section_list:
        lines.append("当前没有可导出的知识段落。")
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            f"本节共整理 {len(section_list)} 个知识段落，覆盖 {time_range}。",
            "",
            "## 学习目标",
            "",
        ]
    )
    _append_learning_objectives(lines, section_list)
    lines.extend(["", "## 核心结论", ""])
    lines.extend(f"- {section.title}" for section in section_list)
    lines.extend(["", "## 知识结构", ""])

    for index, section in enumerate(section_list, start=1):
        _append_expert_section(lines, index, section)

    _append_review_index(lines, section_list)
    _append_review_questions(lines, section_list)
    _append_tag_index(lines, section_list)

    return "\n".join(lines).rstrip() + "\n"


def _format_time_range(segments: Sequence[TranscriptSegment]) -> str:
    if not segments:
        return "0.00s - 0.00s"
    return f"{segments[0].start:.2f}s - {segments[-1].end:.2f}s"


def _format_section_source(section: KnowledgeSection) -> str:
    return _format_timestamps(section.source_timestamps)


def _format_course_time_range(sections: Sequence[KnowledgeSection]) -> str:
    timestamps = [
        timestamp
        for section in sections
        for timestamp in section.source_timestamps
    ]
    return _format_timestamps(timestamps)


def _format_timestamps(timestamps: Sequence[float]) -> str:
    if not timestamps:
        return "未知"
    sorted_timestamps = sorted(timestamps)
    if len(sorted_timestamps) == 1:
        return f"{sorted_timestamps[0]:.2f}s"
    return f"{sorted_timestamps[0]:.2f}s - {sorted_timestamps[-1]:.2f}s"


def _append_expert_section(
    lines: list[str],
    index: int,
    section: KnowledgeSection,
) -> None:
    lines.extend(
        [
            f"### {index}. {section.title}",
            "",
            "**讲解摘要**",
            "",
            section.summary or "暂无摘要。",
            "",
        ]
    )

    if section.key_points:
        lines.extend(["**关键要点**", ""])
        lines.extend(f"- {point}" for point in section.key_points)
        lines.append("")

    lines.extend(
        [
            "**证据与回看**",
            "",
            f"- 时间：{_format_section_source(section)}",
        ]
    )
    lines.extend(f"- 图片：{image_ref}" for image_ref in section.image_refs)
    lines.append("")

    if section.tags:
        lines.extend(
            [
                "**元数据**",
                "",
                f"- 标签：{_format_tags(section.tags)}",
                "",
            ]
        )


def _append_learning_objectives(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    for section in sections:
        if section.key_points:
            lines.extend(f"- 掌握：{point}" for point in section.key_points)
        else:
            lines.append(f"- 理解：{section.title}")


def _append_review_index(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    lines.extend(["", "## 回看索引", ""])
    for section in sections:
        image_suffix = (
            f"；图片：{_format_image_refs(section.image_refs)}"
            if section.image_refs
            else ""
        )
        lines.append(
            f"- {section.title}：{_format_section_source(section)}{image_suffix}"
        )


def _append_review_questions(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    lines.extend(["", "## 复习问题", ""])
    for section in sections:
        if section.source_timestamps:
            lines.append(
                f"- {section.title} 的核心观点是什么？"
                f"请回看 {_format_section_source(section)}。"
            )
        else:
            lines.append(
                f"- {section.title} 的核心观点是什么？请结合本节笔记回看。"
            )
        if section.image_refs:
            lines.append(f"- 哪些图片证据支持 {section.title} 这一段的判断？")


def _append_tag_index(
    lines: list[str],
    sections: Sequence[KnowledgeSection],
) -> None:
    tags = sorted({tag for section in sections for tag in section.tags})
    if not tags:
        return

    lines.extend(["", "## 标签索引", ""])
    lines.extend(f"- `{tag}`" for tag in tags)


def _format_image_refs(image_refs: Sequence[str]) -> str:
    return ", ".join(image_refs)


def _format_tags(tags: Sequence[str]) -> str:
    return ", ".join(tags)


def _section_sort_key(section: KnowledgeSection) -> tuple[float, str]:
    first_timestamp = (
        section.source_timestamps[0] if section.source_timestamps else float("inf")
    )
    return first_timestamp, section.title
