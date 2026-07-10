"""OpenAI-compatible Responses adapter for semantic visual note experiments."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://aihub.lingrendev.com:8080"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_REASONING_EFFORT = "xhigh"
DEFAULT_API_KEY_ENVS = (
    "OPENAI_API_KEY",
    "AIHUB_API_KEY",
    "AIHUB_AUTH_TOKEN",
    "ANTHROPIC_AUTH_TOKEN",
)

SYSTEM_PROMPT = """You are vBook's note synthesis model.

Return only valid JSON matching this contract:
{
  "schema_version": "1",
  "title": "string",
  "overview": "string",
  "sections": [
    {
      "title": "string",
      "summary": "string",
      "key_points": ["string"],
      "source_timestamps": [number],
      "image_refs": ["string"],
      "tags": ["string"]
    }
  ]
}

Rules:
- Use Simplified Chinese.
- Use only the provided timestamped transcript and visual_evidence.
- Do not invent unsupported facts or investment advice.
- Prefer complete, high-information visual pages.
- image_refs must exactly match image_path values from visual_evidence.
- Keep the note concise enough for a learning vault note.
"""


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        request = _read_request(Path(args.input))
        api_key = _resolve_api_key(args.api_key_env)
        payload = build_responses_payload(
            request=request,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            store=not args.disable_response_storage,
        )
        response = post_responses(
            base_url=args.base_url,
            api_key=api_key,
            payload=payload,
            timeout_seconds=args.timeout_seconds,
        )
        model_json = parse_model_json(extract_response_text(response))
        _validate_response(model_json)
        _write_json(model_json, Path(args.output))
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"openai responses adapter error: {exc}", file=sys.stderr)
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an OpenAI-compatible Responses model for vBook semantic visual notes."
    )
    parser.add_argument("--input", required=True, help="Semantic visual request JSON")
    parser.add_argument("--output", required=True, help="Output vBook response JSON")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AIHUB_OPENAI_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL,
        help="OpenAI-compatible base URL",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("VBOOK_OPENAI_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or DEFAULT_MODEL,
        help="Model name",
    )
    parser.add_argument(
        "--reasoning-effort",
        default=os.environ.get("VBOOK_OPENAI_REASONING_EFFORT")
        or os.environ.get("OPENAI_REASONING_EFFORT")
        or DEFAULT_REASONING_EFFORT,
        help="Reasoning effort passed to the Responses API",
    )
    parser.add_argument(
        "--api-key-env",
        action="append",
        default=None,
        help="Environment variable containing the bearer token; may be repeated",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.environ.get("VBOOK_OPENAI_TIMEOUT_SECONDS", "300")),
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--disable-response-storage",
        action="store_true",
        default=os.environ.get("VBOOK_DISABLE_RESPONSE_STORAGE", "1") != "0",
        help="Pass store=false to providers that support it",
    )
    return parser


def build_responses_payload(
    *,
    request: dict[str, Any],
    model: str,
    reasoning_effort: str,
    store: bool,
) -> dict[str, Any]:
    user_payload = {
        "task": request.get("task"),
        "output_contract": request.get("output_contract"),
        "video": request.get("video"),
        "instructions": request.get("instructions"),
        "transcript_segments": request.get("transcript_segments", []),
        "visual_evidence": request.get("visual_evidence", []),
    }
    payload: dict[str, Any] = {
        "model": model,
        "store": store,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(user_payload, ensure_ascii=False),
                    }
                ],
            },
        ],
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    return payload


def post_responses(
    *,
    base_url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    endpoint = _responses_endpoint(base_url)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(
            f"Responses API returned HTTP {exc.code}: {detail[:500]}"
        ) from exc
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Responses API response must be an object")
    return data


def extract_response_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = response.get("output")
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        if chunks:
            return "\n".join(chunks)

    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]

    raise ValueError("could not extract model text from response")


def parse_model_json(text: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(text.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model output is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("model output JSON must be an object")
    return data


def _strip_json_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _validate_response(response: dict[str, Any]) -> None:
    if response.get("schema_version") != "1":
        raise ValueError("response.schema_version must be '1'")
    for key in ("title", "overview"):
        if not isinstance(response.get(key), str):
            raise ValueError(f"response.{key} must be a string")
    sections = response.get("sections")
    if not isinstance(sections, list):
        raise ValueError("response.sections must be a list")
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"response.sections[{index}] must be an object")
        for key in ("title", "summary"):
            if not isinstance(section.get(key), str):
                raise ValueError(f"response.sections[{index}].{key} must be a string")
        for key in ("key_points", "image_refs", "tags"):
            value = section.get(key)
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ValueError(
                    f"response.sections[{index}].{key} must be a string list"
                )
        timestamps = section.get("source_timestamps")
        if not isinstance(timestamps, list) or not all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in timestamps
        ):
            raise ValueError(
                f"response.sections[{index}].source_timestamps must be a number list"
            )


def _read_request(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"input file does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def _resolve_api_key(env_names: list[str] | None) -> str:
    names = env_names or list(DEFAULT_API_KEY_ENVS)
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    raise ValueError(
        "missing API key environment variable; checked: " + ", ".join(names)
    )


def _responses_endpoint(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/responses"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/responses"
    return f"{normalized}/v1/responses"


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
