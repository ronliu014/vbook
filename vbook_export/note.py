"""Markdown note rendering and writing."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from vbook_common.types import (
    FilterStatus,
    FrameCandidate,
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


def _format_time_range(segments: Sequence[TranscriptSegment]) -> str:
    if not segments:
        return "0.00s - 0.00s"
    return f"{segments[0].start:.2f}s - {segments[-1].end:.2f}s"
