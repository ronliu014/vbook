# Qwen Vision Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/vision_qwen_adapter.py`, so vBook can call a Qwen Vision Service through the existing `external-command` backend.

**Architecture:** The adapter remains a command-line bridge, not a new core backend. It reads vBook `frames.json`, posts each frame image to `POST /analyze-frame`, writes manual-json-compatible `analysis.json`, and lets vBook core keep the final validation boundary through `load_manual_visual_analysis()`.

**Tech Stack:** Python 3.11 standard library only: `argparse`, `base64`, `json`, `os`, `sys`, `urllib.request`, `urllib.error`, `http.server`, `threading`, and `unittest`.

---

## File Structure

- Create: `tools/vision_qwen_adapter.py`
  - Responsibility: command-line Qwen service adapter for the existing `external-command` backend.
  - Public surface: CLI flags only. Internal helper functions are script-private and not package API.

- Create: `tests/test_tools/test_vision_qwen_adapter.py`
  - Responsibility: fake local HTTP server tests for adapter request mapping, response normalization, auth, local validation, service errors, and CLI build integration.
  - Uses only localhost and standard library networking.

- Modify: `docs/60_operations/smoke-tests.md`
  - Responsibility: document how to run vBook with the Qwen adapter and a real service endpoint.

- Modify: `docs/00_project/status.md`
  - Responsibility: reflect that vBook has a real-service adapter path while still not shipping built-in model intelligence.

---

### Task 1: Write Qwen Adapter Contract Tests

**Files:**
- Create: `tests/test_tools/test_vision_qwen_adapter.py`
- Read: `docs/80_superpowers/specs/2026-06-27-qwen-vision-adapter-design.md`
- Read: `tools/vision_stub.py`
- Read: `tests/test_tools/test_vision_stub.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_tools/test_vision_qwen_adapter.py` with this complete content:

```python
import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from vbook_client.cli import main as vbook_main
from vbook_common.types import FrameCandidate, VisualType
from vbook_vision.analysis import load_manual_visual_analysis


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER = REPO_ROOT / "tools" / "vision_qwen_adapter.py"


Responder = Callable[
    [dict[str, Any], BaseHTTPRequestHandler],
    tuple[int, dict[str, Any]],
]


class RecordingQwenServer:
    def __init__(self, responder: Responder) -> None:
        self.responder = responder
        self.requests: list[dict[str, Any]] = []
        self.endpoint = ""
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "RecordingQwenServer":
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length)
                payload = json.loads(raw_body.decode("utf-8"))
                outer.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers.items()),
                        "body": payload,
                    }
                )
                status, body = outer.responder(payload, self)
                response = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, format: str, *args: Any) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = self._server.server_address[1]
        self.endpoint = f"http://127.0.0.1:{port}/analyze-frame"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)


def success_response(
    payload: dict[str, Any],
    handler: BaseHTTPRequestHandler,
) -> tuple[int, dict[str, Any]]:
    return (
        200,
        {
            "request_id": payload["request_id"],
            "frame_id": payload["frame_id"],
            "visual_type": "slide",
            "ocr_text": "课程标题",
            "vision_description": "一页课程幻灯片。",
            "structured_observations": {
                "topic": "短线选股",
                "visible_elements": ["标题", "项目符号"],
            },
            "confidence": 0.86,
            "model": {
                "provider": "qwen",
                "name": "qwen-vl",
            },
            "usage": {
                "latency_ms": 25,
            },
            "warnings": ["low readability"],
        },
    )


def _header(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def _write_frame_input(
    root: Path,
    *,
    suffix: str = ".jpg",
    image_exists: bool = True,
) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    image = root / f"frame_000001{suffix}"
    if image_exists:
        image.write_bytes(b"fake image bytes")
    input_path = root / "frames.json"
    input_path.write_text(
        json.dumps(
            {
                "backend": "external-command",
                "frames": [
                    {
                        "frame_id": "frame-000001",
                        "video_id": "lesson",
                        "timestamp": 12.5,
                        "image_path": str(image),
                        "width": 1280,
                        "height": 720,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return input_path, image


def _run_adapter(
    input_path: Path,
    output_path: Path,
    endpoint: str,
    *,
    extra_args: list[str] | None = None,
    env: dict[str, str | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(ADAPTER),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--endpoint",
        endpoint,
        "--timeout-seconds",
        "5",
    ]
    if extra_args:
        command.extend(extra_args)
    process_env = os.environ.copy()
    if env is not None:
        for key, value in env.items():
            if value is None:
                process_env.pop(key, None)
            else:
                process_env[key] = value
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=process_env,
    )


class VisionQwenAdapterToolTest(unittest.TestCase):
    def test_posts_frame_and_writes_manual_json_compatible_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, image = _write_frame_input(root)
            output_path = root / "nested" / "analysis.json"

            with RecordingQwenServer(success_response) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

            data = json.loads(output_path.read_text(encoding="utf-8"))
            analyses = load_manual_visual_analysis(
                [
                    FrameCandidate(
                        id="frame-000001",
                        video_id="lesson",
                        timestamp=12.5,
                        image_path=image,
                        width=1280,
                        height=720,
                    )
                ],
                output_path,
                backend="external-command",
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(server.requests), 1)
        request = server.requests[0]
        body = request["body"]
        self.assertEqual(request["path"], "/analyze-frame")
        self.assertEqual(_header(request["headers"], "Accept"), "application/json")
        self.assertIn(
            "application/json",
            _header(request["headers"], "Content-Type"),
        )
        self.assertEqual(body["request_id"], "vbook-frame-000001")
        self.assertEqual(body["frame_id"], "frame-000001")
        self.assertEqual(body["video_id"], "lesson")
        self.assertEqual(body["timestamp"], 12.5)
        self.assertEqual(body["image_mime_type"], "image/jpeg")
        self.assertEqual(
            body["image_base64"],
            base64.b64encode(b"fake image bytes").decode("ascii"),
        )
        self.assertEqual(body["prompt_profile"], "vbook_visual_analysis_v1")
        self.assertEqual(body["metadata"], {})
        self.assertEqual(data["backend"], "qwen-vision-service")
        self.assertEqual(data["analyses"][0]["frame_id"], "frame-000001")
        self.assertEqual(data["analyses"][0]["visual_type"], "slide")
        self.assertEqual(data["analyses"][0]["ocr_text"], "课程标题")
        self.assertEqual(
            data["analyses"][0]["structured_observations"]["qwen_service"]["model"][
                "provider"
            ],
            "qwen",
        )
        self.assertEqual(
            data["analyses"][0]["structured_observations"]["qwen_service"]["usage"][
                "latency_ms"
            ],
            25,
        )
        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].visual_type, VisualType.SLIDE)
        self.assertEqual(analyses[0].backend, "external-command")

    def test_uses_bearer_token_from_cli_or_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)

            with RecordingQwenServer(success_response) as server:
                cli_result = _run_adapter(
                    input_path,
                    root / "cli-token.json",
                    server.endpoint,
                    extra_args=["--token", "cli-token"],
                    env={"VBOOK_QWEN_VISION_TOKEN": "env-token"},
                )

            with RecordingQwenServer(success_response) as server_from_env:
                env_result = _run_adapter(
                    input_path,
                    root / "env-token.json",
                    server_from_env.endpoint,
                    env={"VBOOK_QWEN_VISION_TOKEN": "env-token"},
                )

        self.assertEqual(cli_result.returncode, 0)
        self.assertEqual(env_result.returncode, 0)
        self.assertEqual(
            server.requests[0]["headers"]["Authorization"],
            "Bearer cli-token",
        )
        self.assertEqual(
            server_from_env.requests[0]["headers"]["Authorization"],
            "Bearer env-token",
        )

    def test_reports_standard_service_error(self) -> None:
        def service_error(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            return (
                400,
                {
                    "error": {
                        "code": "invalid_request",
                        "message": "image_base64 is required",
                        "retryable": False,
                    },
                    "request_id": payload["request_id"],
                },
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)
            output_path = root / "analysis.json"

            with RecordingQwenServer(service_error) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

        self.assertEqual(result.returncode, 1)
        self.assertFalse(output_path.exists())
        self.assertIn(
            "Qwen service returned HTTP 400 for frame-000001",
            result.stderr,
        )
        self.assertIn("invalid_request", result.stderr)
        self.assertIn("image_base64 is required", result.stderr)

    def test_rejects_frame_id_mismatch(self) -> None:
        def mismatched_response(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            status, body = success_response(payload, handler)
            body["frame_id"] = "frame-999999"
            return status, body

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)
            output_path = root / "analysis.json"

            with RecordingQwenServer(mismatched_response) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

        self.assertEqual(result.returncode, 1)
        self.assertFalse(output_path.exists())
        self.assertIn("response frame_id mismatch for frame-000001", result.stderr)
        self.assertIn("frame-999999", result.stderr)

    def test_rejects_local_input_errors_before_calling_service(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_frames = root / "missing-frames.json"
            missing_frames.write_text(json.dumps({"items": []}), encoding="utf-8")

            unsupported_input, _unsupported_image = _write_frame_input(
                root / "unsupported",
                suffix=".gif",
            )

            missing_image_input, _missing_image = _write_frame_input(
                root / "missing-image",
                image_exists=False,
            )

            cases = [
                (
                    missing_frames,
                    root / "out-missing-frames.json",
                    "input JSON must contain frames list",
                ),
                (
                    unsupported_input,
                    root / "out-unsupported.json",
                    "unsupported image suffix for frame-000001: .gif",
                ),
                (
                    missing_image_input,
                    root / "out-missing-image.json",
                    "image file does not exist for frame-000001",
                ),
            ]

            for input_path, output_path, expected_message in cases:
                with self.subTest(expected_message=expected_message):
                    result = _run_adapter(
                        input_path,
                        output_path,
                        "http://127.0.0.1:1/analyze-frame",
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(output_path.exists())
                    self.assertIn(expected_message, result.stderr)

    def test_rejects_invalid_response_fields(self) -> None:
        def response_with(body_update: dict[str, Any]) -> Responder:
            def responder(
                payload: dict[str, Any],
                handler: BaseHTTPRequestHandler,
            ) -> tuple[int, dict[str, Any]]:
                status, body = success_response(payload, handler)
                body.update(body_update)
                return status, body

            return responder

        cases: list[tuple[Responder, str]] = [
            (
                response_with({"visual_type": "diagram"}),
                "invalid visual_type for frame-000001: diagram",
            ),
            (
                response_with({"structured_observations": []}),
                "structured_observations for frame-000001 must be an object",
            ),
            (
                response_with({"confidence": "high"}),
                "confidence for frame-000001 must be a number or null",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)

            for index, (responder, expected_message) in enumerate(cases):
                with self.subTest(expected_message=expected_message):
                    output_path = root / f"invalid-response-{index}.json"
                    with RecordingQwenServer(responder) as server:
                        result = _run_adapter(input_path, output_path, server.endpoint)
                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(output_path.exists())
                    self.assertIn(expected_message, result.stderr)

    def test_build_can_use_qwen_adapter_via_external_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_bytes(b"fake image bytes")

            with RecordingQwenServer(success_response) as server:
                code = vbook_main(
                    [
                        "build",
                        "--video",
                        str(video),
                        "--transcript",
                        str(transcript),
                        "--output",
                        str(output),
                        "--frame-candidates-dir",
                        str(candidate_dir),
                        "--alignment-window-seconds",
                        "3",
                        "--vision-backend",
                        "external-command",
                        "--vision-command",
                        (
                            f"{sys.executable} {ADAPTER} "
                            "--input {input} --output {output} "
                            f"--endpoint {server.endpoint} --timeout-seconds 5"
                        ),
                    ]
                )

            vision = json.loads(
                (output / "vision" / "analysis.json").read_text(encoding="utf-8")
            )
            external_input = json.loads(
                (output / "vision" / "external" / "frames.json").read_text(
                    encoding="utf-8"
                )
            )
            external_output = json.loads(
                (output / "vision" / "external" / "analysis.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(len(server.requests), 1)
        self.assertEqual(external_input["backend"], "external-command")
        self.assertEqual(external_output["backend"], "qwen-vision-service")
        self.assertEqual(vision["backend"], "external-command")
        self.assertEqual(vision["analysis_count"], 1)
        self.assertEqual(vision["analyses"][0]["backend"], "external-command")
        self.assertEqual(vision["analyses"][0]["ocr_text"], "课程标题")
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
        self.assertEqual(manifest["artifacts"]["vision"]["analysis_count"], 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail before implementation**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_qwen_adapter
```

Expected: FAIL. At least the first subprocess call should fail because
`tools/vision_qwen_adapter.py` does not exist yet, with output similar to:

```text
AssertionError: 2 != 0
```

The exact stderr will come from Python trying to open the missing script.

---

### Task 2: Implement `tools/vision_qwen_adapter.py`

**Files:**
- Create: `tools/vision_qwen_adapter.py`
- Test: `tests/test_tools/test_vision_qwen_adapter.py`

- [ ] **Step 1: Add the adapter implementation**

Create `tools/vision_qwen_adapter.py` with this complete content:

```python
"""Qwen Vision Service adapter for the external-command backend."""

from __future__ import annotations

import argparse
import base64
import json
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
        write_output(Path(args.output), analyses)
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
        raise ValueError(f"Qwen service returned invalid JSON for {frame_id}: {exc}") from exc
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

    observations = response.get("structured_observations")
    if not isinstance(observations, dict):
        raise ValueError(f"structured_observations for {frame_id} must be an object")

    confidence = response.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise ValueError(f"confidence for {frame_id} must be a number or null")
        confidence = float(confidence)

    return {
        "frame_id": frame_id,
        "visual_type": visual_type,
        "ocr_text": str(response["ocr_text"]),
        "vision_description": str(response["vision_description"]),
        "structured_observations": _merge_service_debug(observations, response),
        "confidence": confidence,
    }


def write_output(output_path: Path, analyses: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
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
```

- [ ] **Step 2: Run adapter tests to verify they pass**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_qwen_adapter
```

Expected: PASS.

```text
Ran 7 tests
OK
```

- [ ] **Step 3: Run related existing tool and CLI tests**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_stub tests.test_client.test_manifest_cli
```

Expected: PASS.

- [ ] **Step 4: Commit tests and adapter**

Run:

```powershell
git add tools/vision_qwen_adapter.py tests/test_tools/test_vision_qwen_adapter.py
git commit -m "Add Qwen vision adapter"
```

Expected: commit succeeds with the new tool and test file.

---

### Task 3: Document Qwen Adapter Smoke Workflow

**Files:**
- Modify: `docs/60_operations/smoke-tests.md`
- Modify: `docs/00_project/status.md`
- Test: `python -m unittest discover`

- [ ] **Step 1: Update smoke test documentation**

In `docs/60_operations/smoke-tests.md`, insert this section after
`External Command Vision Smoke` and before `Direct Vision Stub Check`:

````markdown
## Qwen Vision Adapter Smoke

Use `tools\vision_qwen_adapter.py` when a Qwen Vision Service compatible with
`docs/90_reference/qwen-vision-service-requirements.md` is running:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-qwen `
  --vision-backend external-command `
  --vision-command "python tools\vision_qwen_adapter.py --input {input} --output {output} --endpoint http://127.0.0.1:8000/analyze-frame --timeout-seconds 120"
```

If the service requires token auth, either pass `--token` inside the command
template or set:

```powershell
$env:VBOOK_QWEN_VISION_TOKEN = "your-token"
```

Expected adapter artifacts:

- `outputs\lesson-qwen\vision\external\frames.json`
- `outputs\lesson-qwen\vision\external\analysis.json`
- `outputs\lesson-qwen\vision\analysis.json`
- `outputs\lesson-qwen\manifest.json`

The adapter sends one request per selected frame to `POST /analyze-frame` and
writes manual-json-compatible analysis. vBook still records the normalized final
visual output as `backend = external-command`.
````

- [ ] **Step 2: Update project status**

In `docs/00_project/status.md`, update the `What Works Now` list by adding this
bullet after the existing `tools/vision_stub.py` bullet:

```markdown
- Qwen Vision Service adapter through `tools/vision_qwen_adapter.py`, using
  `external-command` to call a compatible `POST /analyze-frame` HTTP service
  without adding model dependencies to vBook core.
```

In the `What Is Still Placeholder or Partial` section, replace the existing
visual intelligence bullet with:

```markdown
- Visual intelligence is partial: `manual-json` can ingest external analysis,
  `external-command` can call a user-supplied analyzer, and
  `tools/vision_qwen_adapter.py` can call a compatible Qwen Vision Service, but
  vBook still does not ship an embedded OCR or multimodal model provider.
```

- [ ] **Step 3: Run the full suite**

Run:

```powershell
python -m unittest discover
```

Expected: PASS. The suite count will be higher than the previous 81 tests
because `tests/test_tools/test_vision_qwen_adapter.py` adds 7 tests.

- [ ] **Step 4: Commit documentation**

Run:

```powershell
git add docs/60_operations/smoke-tests.md docs/00_project/status.md
git commit -m "Document Qwen adapter smoke workflow"
```

Expected: commit succeeds with only documentation changes.

---

### Task 4: Final Verification and Handoff

**Files:**
- Read: `git status --short --branch`
- Read: `git log --oneline -5`
- Test: complete suite

- [ ] **Step 1: Run final verification**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_qwen_adapter
python -m unittest tests.test_tools.test_vision_stub tests.test_client.test_manifest_cli
python -m unittest discover
```

Expected:

```text
OK
```

for each command.

- [ ] **Step 2: Inspect git state**

Run:

```powershell
git status --short --branch
git log --oneline -5
```

Expected:

- Working tree clean.
- Recent commits include:
  - `Add Qwen vision adapter`
  - `Document Qwen adapter smoke workflow`
  - `Document Qwen vision adapter design`

- [ ] **Step 3: Report completion**

Report these items to the user:

```text
Implemented tools/vision_qwen_adapter.py.
Added fake HTTP server coverage for request mapping, response normalization, auth, service errors, local validation, and build integration.
Updated smoke-test and status docs.
Verification: python -m unittest discover passed.
```

If any verification command fails, report the exact failing command and first
actionable failure message instead of claiming completion.

---

## Self-Review Checklist

- Spec coverage:
  - CLI args from the spec are covered in Task 2.
  - Input validation from the spec is covered by Task 1 tests and Task 2 implementation.
  - Qwen request mapping is covered by `test_posts_frame_and_writes_manual_json_compatible_analysis`.
  - Token handling is covered by `test_uses_bearer_token_from_cli_or_environment`.
  - Service error parsing is covered by `test_reports_standard_service_error`.
  - Response validation is covered by mismatch and invalid field tests.
  - Build integration is covered by `test_build_can_use_qwen_adapter_via_external_command`.
  - Documentation updates are covered by Task 3.

- Type consistency:
  - Test helper `RecordingQwenServer.endpoint` is passed to `--endpoint`.
  - Adapter output field names match `manual-json`: `frame_id`, `visual_type`,
    `ocr_text`, `vision_description`, `structured_observations`, `confidence`.
  - Debug fields are stored under `structured_observations.qwen_service`.

- Scope control:
  - No new `qwen-service` backend is added.
  - No runtime dependency is added to `pyproject.toml`.
  - No Qwen model runtime, SDK, batch endpoint, retry, or concurrency is included.
