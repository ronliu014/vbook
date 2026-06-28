"""Deterministic external-command LLM fusion smoke tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
REQUEST_INTENT = "llm_fusion_request"
DEFAULT_TITLE = "vBook LLM Fusion Smoke Note"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a deterministic LLM fusion smoke response."
    )
    parser.add_argument("--input", required=True, help="LLM fusion request JSON path")
    parser.add_argument("--output", required=True, help="LLM fusion response JSON path")
    args = parser.parse_args(argv)

    try:
        request = _load_input(Path(args.input))
        response = _build_response(request)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(response, ensure_ascii=False, indent=2) + "\n",
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
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version must be '1'")
    if data.get("intent") != REQUEST_INTENT:
        raise ValueError("intent must be 'llm_fusion_request'")
    sections = data.get("evidence_sections")
    if not isinstance(sections, list):
        raise ValueError("evidence_sections must be a list")
    for index, section in enumerate(sections):
        _validate_section(section, index)
    return data


def _validate_section(section: Any, index: int) -> None:
    path = f"evidence_sections[{index}]"
    if not isinstance(section, dict):
        raise ValueError(f"{path} must be an object")
    _require_string(section, "title", f"{path}.title")
    _require_string(section, "summary", f"{path}.summary")
    _require_string_list(section, "key_points", f"{path}.key_points")
    _require_number_list(section, "source_timestamps", f"{path}.source_timestamps")
    _require_string_list(section, "image_refs", f"{path}.image_refs")
    _require_string_list(section, "tags", f"{path}.tags")


def _require_string(value: dict[str, Any], key: str, path: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"{path} must be a string")
    return item


def _require_string_list(value: dict[str, Any], key: str, path: str) -> list[str]:
    item = value.get(key)
    if not isinstance(item, list):
        raise ValueError(f"{path} must be a list")
    result = []
    for index, entry in enumerate(item):
        if not isinstance(entry, str):
            raise ValueError(f"{path}[{index}] must be a string")
        result.append(entry)
    return result


def _require_number_list(value: dict[str, Any], key: str, path: str) -> list[float]:
    item = value.get(key)
    if not isinstance(item, list):
        raise ValueError(f"{path} must be a list")
    result = []
    for index, entry in enumerate(item):
        if isinstance(entry, bool) or not isinstance(entry, (int, float)):
            raise ValueError(f"{path}[{index}] must be a number")
        result.append(float(entry))
    return result


def _build_response(request: dict[str, Any]) -> dict[str, Any]:
    evidence_sections = request["evidence_sections"]
    return {
        "schema_version": SCHEMA_VERSION,
        "title": _response_title(request),
        "overview": _overview(len(evidence_sections)),
        "sections": [
            _response_section(section, index)
            for index, section in enumerate(evidence_sections, start=1)
        ],
    }


def _response_title(request: dict[str, Any]) -> str:
    video = request.get("video")
    if not isinstance(video, dict):
        return DEFAULT_TITLE
    for key in ("lesson_title", "course_title", "id"):
        value = video.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return DEFAULT_TITLE


def _overview(section_count: int) -> str:
    suffix = "section" if section_count == 1 else "sections"
    return f"Deterministic smoke synthesis from {section_count} evidence {suffix}."


def _response_section(section: dict[str, Any], index: int) -> dict[str, Any]:
    title = section["title"].strip() or f"Evidence Section {index}"
    summary = section["summary"].strip() or f"Smoke summary for {title}."
    return {
        "title": title,
        "summary": summary,
        "key_points": list(section["key_points"]),
        "source_timestamps": list(section["source_timestamps"]),
        "image_refs": list(section["image_refs"]),
        "tags": _append_final_tag(section["tags"]),
    }


def _append_final_tag(tags: list[str]) -> list[str]:
    result = []
    seen = set()
    for tag in [*tags, "final"]:
        if tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
