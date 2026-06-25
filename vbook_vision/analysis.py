"""Visual analysis helpers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from vbook_common.serialization import to_jsonable
from vbook_common.types import FrameCandidate, VisualAnalysis, VisualType


def analyze_frames_placeholder(
    frames: Sequence[FrameCandidate],
    backend: str = "placeholder",
) -> list[VisualAnalysis]:
    """Create placeholder visual analysis records for frames."""
    return [
        VisualAnalysis(
            frame_id=frame.id,
            visual_type=VisualType.OTHER,
            image_path=frame.image_path,
            vision_description="Visual analysis pending backend implementation.",
            structured_observations={
                "source": "placeholder",
                "timestamp": frame.timestamp,
            },
            confidence=None,
            backend=backend,
        )
        for frame in frames
    ]


def write_visual_analysis(
    analyses: Sequence[VisualAnalysis],
    path: Path | str,
    backend: str = "placeholder",
) -> Path:
    """Write visual analyses as formatted UTF-8 JSON."""
    analysis_path = Path(path)
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text(
        json.dumps(
            to_jsonable(
                {
                    "backend": backend,
                    "analysis_count": len(analyses),
                    "analyses": list(analyses),
                }
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return analysis_path
