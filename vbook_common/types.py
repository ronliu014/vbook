"""Shared vBook data contracts."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class VisualType(str, Enum):
    """Supported visual categories."""

    SLIDE = "slide"
    KLINE_CASE = "kline_case"
    OTHER = "other"


class FilterStatus(str, Enum):
    """Frame filtering state."""

    CANDIDATE = "candidate"
    SELECTED = "selected"
    REJECTED = "rejected"


class StageStatus(str, Enum):
    """Pipeline stage state."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


class TranscriptSourceType(str, Enum):
    """How transcript data entered vBook."""

    IMPORTED = "imported"
    EXTERNAL_COMMAND = "external_command"
    GENERATED = "generated"


@dataclass
class VideoAsset:
    """Source lesson video."""

    id: str
    path: Path
    course_title: str
    lesson_title: str
    duration_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptSegment:
    """Timestamped transcript segment."""

    id: str
    start: float
    end: float
    text: str
    language: str | None = None
    confidence: float | None = None
    source: TranscriptSourceType = TranscriptSourceType.IMPORTED


@dataclass
class FrameCandidate:
    """Frame extracted from source video."""

    id: str
    video_id: str
    timestamp: float
    image_path: Path
    width: int
    height: int
    filter_status: FilterStatus = FilterStatus.CANDIDATE
    filter_reason: str | None = None


@dataclass
class VisualAnalysis:
    """Normalized OCR and visual-understanding result."""

    frame_id: str
    visual_type: VisualType
    image_path: Path
    ocr_text: str = ""
    vision_description: str = ""
    structured_observations: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    backend: str | None = None


@dataclass
class TimelineLink:
    """Link between a visual record and transcript context."""

    frame_id: str
    transcript_segment_ids: list[str]
    window_start: float
    window_end: float
    match_strategy: str = "timestamp_window"


@dataclass
class KnowledgeSection:
    """One fused section in the final note."""

    title: str
    summary: str
    source_timestamps: list[float] = field(default_factory=list)
    image_refs: list[str] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class PipelineRun:
    """Reproducible pipeline execution record."""

    run_id: str
    config: dict[str, Any]
    stage_status: dict[str, StageStatus] = field(default_factory=dict)
    input_hashes: dict[str, str] = field(default_factory=dict)
    output_paths: dict[str, Path] = field(default_factory=dict)
    started_at: str | None = None


@dataclass
class Manifest:
    """Machine-readable output index."""

    video_asset: VideoAsset
    transcript_source: TranscriptSourceType
    pipeline_run: PipelineRun
    artifacts: dict[str, Any]
    note_path: Path
    stage_status: dict[str, StageStatus] = field(default_factory=dict)
    schema_version: str = "1"
