"""Deterministic external-command vision smoke tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write manual-json-compatible smoke visual analysis."
    )
    parser.add_argument("--input", required=True, help="Frame input JSON path")
    parser.add_argument("--output", required=True, help="Analysis output JSON path")
    args = parser.parse_args(argv)

    try:
        payload = _load_input(Path(args.input))
        analyses = [
            _analysis_for_frame(frame, index)
            for index, frame in enumerate(payload["frames"])
        ]
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "backend": "vision_stub",
                    "analyses": analyses,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _load_input(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise ValueError(f"input file does not exist: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    frames = data.get("frames")
    if not isinstance(frames, list):
        raise ValueError("input JSON must contain frames list")
    for index, frame in enumerate(frames):
        _validate_frame(frame, index)
    return data


def _validate_frame(frame: Any, index: int) -> None:
    if not isinstance(frame, dict):
        raise ValueError(f"frame at index {index} must be an object")
    frame_id = frame.get("frame_id")
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise ValueError(f"frame at index {index} requires string frame_id")


def _analysis_for_frame(frame: dict[str, Any], index: int) -> dict[str, Any]:
    frame_id = str(frame["frame_id"])
    observations = {
        "source": "vision_stub",
        "video_id": frame.get("video_id", ""),
        "timestamp": frame.get("timestamp", 0.0),
        "image_path": frame.get("image_path", ""),
        "width": frame.get("width", 0),
        "height": frame.get("height", 0),
        "frame_index": index,
    }
    return {
        "frame_id": frame_id,
        "visual_type": "other",
        "ocr_text": "",
        "vision_description": f"External command smoke analysis for {frame_id}.",
        "structured_observations": observations,
        "confidence": 0.0,
    }


if __name__ == "__main__":
    raise SystemExit(main())
