"""Qwen Vision Service adapter for the external-command backend."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SUPPORTED_VISUAL_TYPES = {"slide", "kline_case", "other"}
MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
DEFAULT_PROMPT_PROFILE = "vbook_visual_analysis_v1"
ENV_TOKEN = "VBOOK_QWEN_VISION_TOKEN"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Call a Qwen Vision Service and write manual-json visual analysis."
    )
    parser.add_argument("--input", required=True, help="Frame input JSON path")
    parser.add_argument("--output", required=True, help="Analysis output JSON path")
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Qwen Vision Service POST /analyze-frame URL",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=120.0,
        help="Per-frame HTTP timeout in seconds",
    )
    parser.add_argument(
        "--prompt-profile",
        default=DEFAULT_PROMPT_PROFILE,
        help="Prompt profile sent to the Qwen Vision Service",
    )
    parser.add_argument("--token", help="Optional bearer token")
    args = parser.parse_args(argv)

    try:
        output_path = Path(args.output)
        cleanup_output(output_path)
        frames = load_frame_input(Path(args.input))
        token = args.token or os.environ.get(ENV_TOKEN)
        analyses = []
        for frame in frames:
            frame_id = str(frame["frame_id"])
            payload = build_qwen_request(frame, args.prompt_profile)
            response = post_json(
                endpoint=args.endpoint,
                payload=payload,
                token=token,
                timeout_seconds=args.timeout_seconds,
                frame_id=frame_id,
            )
            analyses.append(normalize_response(frame_id, response))
        write_output(output_path, analyses)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def load_frame_input(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists():
        raise ValueError(f"input file does not exist: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input JSON: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"failed to read input file: {input_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    frames = data.get("frames")
    if not isinstance(frames, list):
        raise ValueError("input JSON must contain frames list")

    validated = []
    for index, frame in enumerate(frames):
        validated.append(_validate_frame(frame, index))
    return validated


def build_qwen_request(
    frame: dict[str, Any],
    prompt_profile: str,
) -> dict[str, Any]:
    frame_id = str(frame["frame_id"])
    image_path_text = str(frame["image_path"])
    image_path = Path(image_path_text)
    return {
        "request_id": f"vbook-{frame_id}",
        "frame_id": frame_id,
        "video_id": _string_or_default(frame.get("video_id"), ""),
        "timestamp": _number_or_default(frame.get("timestamp"), 0.0),
        "image_base64": _read_image_base64(image_path, frame_id),
        "image_mime_type": _infer_mime_type(image_path, frame_id),
        "image_path": image_path_text,
        "prompt_profile": prompt_profile,
        "metadata": {},
    }


def post_json(
    *,
    endpoint: str,
    payload: dict[str, Any],
    token: str | None,
    timeout_seconds: float,
    frame_id: str,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = response.getcode()
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        detail = _format_service_error(raw)
        message = f"Qwen service returned HTTP {exc.code} for {frame_id}"
        if detail:
            message = f"{message}: {detail}"
        raise ValueError(message) from exc
    except urllib.error.URLError as exc:
        raise ValueError(
            f"Qwen service request failed for {frame_id}: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise ValueError(f"Qwen service request timed out for {frame_id}") from exc

    if status < 200 or status >= 300:
        raise ValueError(f"Qwen service returned HTTP {status} for {frame_id}")
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Qwen service returned invalid JSON for {frame_id}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"Qwen service response for {frame_id} must be an object")
    return data


def normalize_response(
    frame_id: str,
    response: dict[str, Any],
) -> dict[str, Any]:
    response_frame_id = response.get("frame_id")
    if response_frame_id != frame_id:
        raise ValueError(
            f"response frame_id mismatch for {frame_id}: {response_frame_id}"
        )

    visual_type = response.get("visual_type")
    if visual_type not in SUPPORTED_VISUAL_TYPES:
        raise ValueError(f"invalid visual_type for {frame_id}: {visual_type}")

    if "ocr_text" not in response:
        raise ValueError(f"ocr_text for {frame_id} is required")
    if "vision_description" not in response:
        raise ValueError(f"vision_description for {frame_id} is required")
    if not isinstance(response["ocr_text"], str):
        raise ValueError(f"ocr_text for {frame_id} must be a string")
    if not isinstance(response["vision_description"], str):
        raise ValueError(f"vision_description for {frame_id} must be a string")

    observations = response.get("structured_observations")
    if not isinstance(observations, dict):
        raise ValueError(f"structured_observations for {frame_id} must be an object")

    if "confidence" not in response:
        raise ValueError(f"confidence for {frame_id} is required")

    confidence = response.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise ValueError(f"confidence for {frame_id} must be a number or null")
        confidence = float(confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"confidence for {frame_id} must be between 0.0 and 1.0"
            )

    return {
        "frame_id": frame_id,
        "visual_type": visual_type,
        "ocr_text": response["ocr_text"],
        "vision_description": response["vision_description"],
        "structured_observations": _merge_service_debug(observations, response),
        "confidence": confidence,
    }


def cleanup_output(output_path: Path) -> None:
    for path in (output_path, _output_temp_path(output_path)):
        try:
            if path.exists():
                path.unlink()
        except OSError as exc:
            raise ValueError(
                f"failed to remove stale output file: {path}: {exc}"
            ) from exc


def write_output(output_path: Path, analyses: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _output_temp_path(output_path)
    try:
        temp_path.write_text(
            json.dumps(
                {
                    "backend": "qwen-vision-service",
                    "analyses": analyses,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temp_path.replace(output_path)
    except OSError as exc:
        raise ValueError(
            f"failed to write output file: {output_path}: {exc}"
        ) from exc


def _output_temp_path(output_path: Path) -> Path:
    return output_path.with_name(f".{output_path.name}.tmp")


def _validate_frame(frame: Any, index: int) -> dict[str, Any]:
    if not isinstance(frame, dict):
        raise ValueError(f"frame at index {index} must be an object")
    frame_id = frame.get("frame_id")
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise ValueError(f"frame at index {index} requires string frame_id")
    image_path_value = frame.get("image_path")
    if not isinstance(image_path_value, str) or not image_path_value.strip():
        raise ValueError(f"frame {frame_id} requires string image_path")
    image_path = Path(image_path_value)
    if not image_path.exists():
        raise ValueError(f"image file does not exist for {frame_id}: {image_path}")
    _infer_mime_type(image_path, frame_id)
    return dict(frame)


def _infer_mime_type(image_path: Path, frame_id: str) -> str:
    suffix = image_path.suffix.lower()
    mime_type = MIME_BY_SUFFIX.get(suffix)
    if mime_type is None:
        suffix_label = suffix if suffix else "<none>"
        raise ValueError(f"unsupported image suffix for {frame_id}: {suffix_label}")
    return mime_type


def _read_image_base64(image_path: Path, frame_id: str) -> str:
    try:
        return base64.b64encode(image_path.read_bytes()).decode("ascii")
    except OSError as exc:
        raise ValueError(f"failed to read image file for {frame_id}: {image_path}") from exc


def _string_or_default(value: Any, default: str) -> str:
    return value if isinstance(value, str) else default


def _number_or_default(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _format_service_error(raw: bytes) -> str:
    if not raw:
        return ""
    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text[:500]
    if not isinstance(data, dict):
        return text[:500]
    error = data.get("error")
    if not isinstance(error, dict):
        return text[:500]
    code = error.get("code")
    message = error.get("message")
    if code and message:
        return f"{code}: {message}"
    if code:
        return str(code)
    if message:
        return str(message)
    return text[:500]


def _merge_service_debug(
    observations: dict[str, Any],
    response: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(observations)
    debug = {
        key: response[key]
        for key in ("request_id", "model", "usage", "warnings")
        if key in response
    }
    if debug:
        debug_key = "qwen_service"
        if debug_key in merged:
            debug_key = "qwen_service_response"
        merged[debug_key] = debug
    return merged


if __name__ == "__main__":
    raise SystemExit(main())
