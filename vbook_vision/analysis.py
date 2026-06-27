"""Visual analysis helpers."""

from __future__ import annotations

import json
import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import FrameCandidate, VisualAnalysis, VisualType


def analyze_frames(
    frames: Sequence[FrameCandidate],
    backend: str = "placeholder",
    visual_analysis_input: Path | str | None = None,
    vision_command: str | None = None,
    work_dir: Path | str | None = None,
) -> list[VisualAnalysis]:
    """Analyze frames using a supported visual backend."""
    if backend == "placeholder":
        return analyze_frames_placeholder(frames)
    if backend == "manual-json":
        return load_manual_visual_analysis(frames, visual_analysis_input)
    if backend == "external-command":
        return run_external_vision_command(
            frames,
            vision_command=vision_command,
            work_dir=work_dir,
        )
    raise ValueError(f"Unsupported vision backend: {backend}")


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


def load_manual_visual_analysis(
    frames: Sequence[FrameCandidate],
    visual_analysis_input: Path | str | None,
    backend: str = "manual-json",
) -> list[VisualAnalysis]:
    """Load normalized visual analysis records from a manual JSON file."""
    if visual_analysis_input is None:
        raise ValueError("manual-json backend requires visual_analysis_input")

    input_path = Path(visual_analysis_input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    records = _extract_manual_records(data)
    frame_by_id = {frame.id: frame for frame in frames}
    seen_frame_ids: set[str] = set()
    analyses: list[VisualAnalysis] = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"manual-json record at index {index} must be an object")
        frame_id = _required_string(record, "frame_id", index)
        if frame_id in seen_frame_ids:
            raise ValueError(f"Duplicate frame_id in manual-json input: {frame_id}")
        seen_frame_ids.add(frame_id)
        frame = frame_by_id.get(frame_id)
        if frame is None:
            raise ValueError(f"Unknown frame_id in manual-json input: {frame_id}")
        observations = record.get("structured_observations", {})
        if not isinstance(observations, dict):
            raise ValueError(
                f"manual-json structured_observations for {frame_id} must be an object"
            )
        analyses.append(
            VisualAnalysis(
                frame_id=frame_id,
                visual_type=_parse_visual_type(
                    record.get("visual_type", "other"), frame_id
                ),
                image_path=(
                    Path(record["image_path"]) if record.get("image_path") else frame.image_path
                ),
                ocr_text=str(record.get("ocr_text", "")),
                vision_description=str(record.get("vision_description", "")),
                structured_observations=dict(observations),
                confidence=_parse_confidence(record.get("confidence"), frame_id),
                backend=backend,
            )
        )

    return analyses


def run_external_vision_command(
    frames: Sequence[FrameCandidate],
    vision_command: str | None,
    work_dir: Path | str | None,
) -> list[VisualAnalysis]:
    """Run an external command that writes manual-json-compatible analysis."""
    if not vision_command:
        raise ValueError("external-command backend requires vision_command")
    if "{input}" not in vision_command:
        raise ValueError("vision_command must contain {input}")
    if "{output}" not in vision_command:
        raise ValueError("vision_command must contain {output}")

    external_dir = Path(work_dir) if work_dir is not None else Path("vision") / "external"
    external_dir.mkdir(parents=True, exist_ok=True)
    input_path = external_dir / "frames.json"
    output_path = external_dir / "analysis.json"
    input_payload = {
        "backend": "external-command",
        "frames": [
            {
                "frame_id": frame.id,
                "video_id": frame.video_id,
                "timestamp": frame.timestamp,
                "image_path": frame.image_path,
                "width": frame.width,
                "height": frame.height,
            }
            for frame in frames
        ],
    }
    input_path.write_text(
        json.dumps(to_jsonable(input_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    command_parts = [
        _strip_outer_quotes(
            part.replace("{input}", str(input_path)).replace("{output}", str(output_path))
        )
        for part in shlex.split(vision_command, posix=False)
    ]
    result = subprocess.run(
        command_parts,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        message = f"external vision command failed with exit code {result.returncode}"
        if detail:
            message = f"{message}: {detail[:500]}"
        raise ValueError(message)
    if not output_path.exists():
        raise ValueError("external vision command did not write output")
    return load_manual_visual_analysis(
        frames,
        output_path,
        backend="external-command",
    )


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


def _extract_manual_records(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        records = data.get("analyses")
        if isinstance(records, list):
            return records
        raise ValueError("manual-json object input must contain an analyses list")
    raise ValueError("manual-json input must be an object with analyses or a list")


def _strip_outer_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _required_string(record: dict[str, Any], key: str, index: int) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"manual-json record at index {index} requires string {key}")
    return value


def _parse_visual_type(value: Any, frame_id: str) -> VisualType:
    try:
        return VisualType(value)
    except ValueError as exc:
        raise ValueError(f"Invalid visual_type for {frame_id}: {value}") from exc


def _parse_confidence(value: Any, frame_id: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    raise ValueError(f"manual-json confidence for {frame_id} must be a number")
