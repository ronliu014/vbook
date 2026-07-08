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
    tuple[int, dict[str, Any] | str],
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
                if isinstance(body, str):
                    response = body.encode("utf-8")
                else:
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

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
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
            _header(server.requests[0]["headers"], "Authorization"),
            "Bearer cli-token",
        )
        self.assertEqual(
            _header(server_from_env.requests[0]["headers"], "Authorization"),
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

    def test_continue_on_error_writes_placeholder_analysis(self) -> None:
        def service_error(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            return (
                503,
                {
                    "error": {
                        "code": "model_busy",
                        "message": "worker timed out",
                        "retryable": True,
                    },
                    "request_id": payload["request_id"],
                },
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, image = _write_frame_input(root)
            output_path = root / "analysis.json"

            with RecordingQwenServer(service_error) as server:
                result = _run_adapter(
                    input_path,
                    output_path,
                    server.endpoint,
                    extra_args=["--continue-on-error"],
                )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertTrue(output_path.exists())
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

        self.assertEqual(len(server.requests), 1)
        self.assertEqual(len(analyses), 1)
        analysis = analyses[0]
        self.assertEqual(analysis.frame_id, "frame-000001")
        self.assertEqual(analysis.visual_type, VisualType.OTHER)
        self.assertEqual(analysis.ocr_text, "")
        self.assertIn("unavailable", analysis.vision_description)
        self.assertIsNone(analysis.confidence)
        self.assertEqual(
            analysis.structured_observations["qwen_service"]["status"],
            "error",
        )
        self.assertIn(
            "model_busy",
            analysis.structured_observations["qwen_service"]["message"],
        )

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
                    with RecordingQwenServer(success_response) as server:
                        result = _run_adapter(
                            input_path,
                            output_path,
                            server.endpoint,
                        )
                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(output_path.exists())
                    self.assertIn(expected_message, result.stderr)
                    self.assertEqual(len(server.requests), 0)

    def test_rejects_nonstandard_json_constants_in_input_before_calling_service(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "frame_000001.jpg"
            image.write_bytes(b"fake image bytes")

            cases = [
                ("nan", float("nan"), "invalid JSON constant"),
                ("infinity", float("inf"), "invalid JSON constant"),
                ("overflow", "1e999", "non-finite number"),
            ]

            for label, timestamp, expected_message in cases:
                with self.subTest(label=label):
                    input_path = root / f"{label}-frames.json"
                    output_path = root / f"{label}-analysis.json"
                    input_text = json.dumps(
                        {
                            "backend": "external-command",
                            "frames": [
                                {
                                    "frame_id": "frame-000001",
                                    "video_id": "lesson",
                                    "timestamp": timestamp,
                                    "image_path": str(image),
                                    "width": 1280,
                                    "height": 720,
                                }
                            ],
                        },
                        allow_nan=True,
                        ensure_ascii=False,
                    )
                    input_path.write_text(
                        input_text.replace('"1e999"', "1e999"),
                        encoding="utf-8",
                    )

                    with RecordingQwenServer(success_response) as server:
                        result = _run_adapter(
                            input_path,
                            output_path,
                            server.endpoint,
                        )

                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(output_path.exists())
                    self.assertIn("invalid input JSON", result.stderr)
                    self.assertIn(expected_message, result.stderr)
                    self.assertEqual(len(server.requests), 0)

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

        def response_without_confidence(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            status, body = success_response(payload, handler)
            body.pop("confidence")
            return status, body

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
                response_with({"ocr_text": {"text": "bad"}}),
                "ocr_text for frame-000001 must be a string",
            ),
            (
                response_with({"vision_description": ["bad"]}),
                "vision_description for frame-000001 must be a string",
            ),
            (
                response_with({"confidence": "high"}),
                "confidence for frame-000001 must be a number or null",
            ),
            (
                response_with({"confidence": -0.1}),
                "confidence for frame-000001 must be between 0.0 and 1.0",
            ),
            (
                response_with({"confidence": 1.1}),
                "confidence for frame-000001 must be between 0.0 and 1.0",
            ),
            (
                response_with({"confidence": float("nan")}),
                "Qwen service returned invalid JSON for frame-000001: "
                "invalid JSON constant: NaN",
            ),
            (
                response_with({"confidence": float("inf")}),
                "Qwen service returned invalid JSON for frame-000001: "
                "invalid JSON constant: Infinity",
            ),
            (
                response_without_confidence,
                "confidence for frame-000001 is required",
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

    def test_accepts_null_confidence(self) -> None:
        def null_confidence_response(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            status, body = success_response(payload, handler)
            body["confidence"] = None
            return status, body

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)
            output_path = root / "analysis.json"

            with RecordingQwenServer(null_confidence_response) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            data = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIsNone(data["analyses"][0]["confidence"])

    def test_failed_run_removes_stale_output_file(self) -> None:
        def invalid_response(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            status, body = success_response(payload, handler)
            body["ocr_text"] = {"text": "bad"}
            return status, body

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)
            output_path = root / "analysis.json"
            output_path.write_text('{"stale": true}\n', encoding="utf-8")

            with RecordingQwenServer(invalid_response) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

        self.assertEqual(result.returncode, 1)
        self.assertFalse(output_path.exists())
        self.assertIn("ocr_text for frame-000001 must be a string", result.stderr)

    def test_rejects_nonstandard_json_constants_in_service_response(self) -> None:
        def response_with_nan_observation(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any]]:
            status, body = success_response(payload, handler)
            body["structured_observations"] = {"score": float("nan")}
            return status, body

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)
            output_path = root / "analysis.json"

            with RecordingQwenServer(response_with_nan_observation) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

        self.assertEqual(result.returncode, 1)
        self.assertFalse(output_path.exists())
        self.assertEqual(len(server.requests), 1)
        self.assertIn(
            "Qwen service returned invalid JSON for frame-000001",
            result.stderr,
        )
        self.assertIn("invalid JSON constant", result.stderr)

    def test_rejects_nonfinite_numbers_parsed_from_service_response(self) -> None:
        def response_with_overflow_observation(
            payload: dict[str, Any],
            handler: BaseHTTPRequestHandler,
        ) -> tuple[int, dict[str, Any] | str]:
            return (
                200,
                (
                    "{"
                    f'"frame_id": {json.dumps(payload["frame_id"])},'
                    '"visual_type": "slide",'
                    '"ocr_text": "",'
                    '"vision_description": "ok",'
                    '"structured_observations": {"score": 1e999},'
                    '"confidence": 0.8'
                    "}"
                ),
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path, _image = _write_frame_input(root)
            output_path = root / "analysis.json"

            with RecordingQwenServer(response_with_overflow_observation) as server:
                result = _run_adapter(input_path, output_path, server.endpoint)

        self.assertEqual(result.returncode, 1)
        self.assertFalse(output_path.exists())
        self.assertEqual(len(server.requests), 1)
        self.assertIn(
            "Qwen service returned invalid JSON for frame-000001",
            result.stderr,
        )
        self.assertIn("non-finite number", result.stderr)

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
                try:
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
                                f'"{sys.executable}" "{ADAPTER}" '
                                '--input "{input}" --output "{output}" '
                                f"--endpoint {server.endpoint} --timeout-seconds 5"
                            ),
                        ]
                    )
                except SystemExit as exc:
                    code = int(exc.code)

            self.assertEqual(code, 0)
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
