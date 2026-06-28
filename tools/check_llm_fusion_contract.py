"""Validate LLM fusion request and response files against vBook contracts."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vbook_fusion.llm_contract import parse_llm_fusion_response


SCHEMA_VERSION = "1"
REQUEST_INTENT = "llm_fusion_request"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate vBook LLM fusion request and response JSON files."
    )
    parser.add_argument("--request", required=True, help="LLM fusion request JSON path")
    parser.add_argument(
        "--response",
        required=True,
        help="LLM fusion response JSON path",
    )
    args = parser.parse_args(argv)

    try:
        request = _load_json(Path(args.request), "request")
        _validate_request(request)
        response = _load_json(Path(args.response), "response")
        if not isinstance(response, dict):
            raise ValueError("response JSON must be an object")
        try:
            sections = parse_llm_fusion_response(response)
        except ValueError as exc:
            raise ValueError(f"response {exc}") from exc
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: request and response match vBook LLM fusion contract")
    print(f"Parsed sections: {len(sections)}")
    return 0


def _load_json(path: Path, label: str) -> Any:
    if not path.exists():
        raise ValueError(f"{label} file does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {label} JSON: {exc}") from exc


def _validate_request(request: Any) -> None:
    if not isinstance(request, dict):
        raise ValueError("request JSON must be an object")
    if request.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("request schema_version must be '1'")
    if request.get("intent") != REQUEST_INTENT:
        raise ValueError("request intent must be 'llm_fusion_request'")
    sections = request.get("evidence_sections")
    if not isinstance(sections, list):
        raise ValueError("request evidence_sections must be a list")
    for index, section in enumerate(sections):
        _validate_evidence_section(section, index)


def _validate_evidence_section(section: Any, index: int) -> None:
    path = f"request evidence_sections[{index}]"
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
        number = float(entry)
        if not math.isfinite(number):
            raise ValueError(f"{path}[{index}] must be finite")
        result.append(number)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
