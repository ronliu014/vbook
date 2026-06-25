"""Timeline alignment helpers."""

from __future__ import annotations

from collections.abc import Sequence

from vbook_common.types import FrameCandidate, TimelineLink, TranscriptSegment


def link_frames_to_transcript(
    frames: Sequence[FrameCandidate],
    segments: Sequence[TranscriptSegment],
    window_seconds: float,
    match_strategy: str = "timestamp_window",
) -> list[TimelineLink]:
    """Link frames to transcript segments whose timestamps overlap a frame window."""
    window = float(window_seconds)
    if window < 0:
        raise ValueError("window_seconds must be non-negative")

    sorted_segments = sorted(segments, key=lambda segment: (segment.start, segment.end))
    links: list[TimelineLink] = []
    for frame in sorted(frames, key=lambda item: item.timestamp):
        window_start = max(0.0, frame.timestamp - window)
        window_end = frame.timestamp + window
        segment_ids = [
            segment.id
            for segment in sorted_segments
            if _overlaps(segment.start, segment.end, window_start, window_end)
        ]
        links.append(
            TimelineLink(
                frame_id=frame.id,
                transcript_segment_ids=segment_ids,
                window_start=window_start,
                window_end=window_end,
                match_strategy=match_strategy,
            )
        )
    return links


def _overlaps(
    segment_start: float,
    segment_end: float,
    window_start: float,
    window_end: float,
) -> bool:
    return segment_start < window_end and segment_end > window_start
