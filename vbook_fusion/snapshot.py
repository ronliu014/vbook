"""Fusion prompt snapshot construction and writing."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import (
    TimelineLink,
    TranscriptSegment,
    VideoAsset,
    VisualAnalysis,
)


def build_fusion_prompt_snapshot(
    video: VideoAsset,
    segments: Sequence[TranscriptSegment],
    visual_analyses: Sequence[VisualAnalysis] | None = None,
    timeline_links: Sequence[TimelineLink] | None = None,
) -> dict[str, Any]:
    """Build the auditable input payload for a future knowledge-fusion step."""
    segment_list = sorted(segments, key=lambda item: (item.start, item.end, item.id))
    analysis_list = sorted(visual_analyses or [], key=lambda item: item.frame_id)
    link_list = sorted(timeline_links or [], key=lambda item: item.frame_id)

    return to_jsonable(
        {
            "schema_version": "1",
            "intent": "fusion_prompt_snapshot",
            "video": video,
            "inputs": {
                "transcript_segment_count": len(segment_list),
                "visual_analysis_count": len(analysis_list),
                "timeline_link_count": len(link_list),
            },
            "transcript_segments": segment_list,
            "visual_analyses": analysis_list,
            "timeline_links": link_list,
        }
    )


def write_fusion_prompt_snapshot(snapshot: dict[str, Any], path: Path | str) -> Path:
    """Write a fusion prompt snapshot as formatted UTF-8 JSON."""
    prompt_path = Path(path)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(
        json.dumps(to_jsonable(snapshot), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return prompt_path
