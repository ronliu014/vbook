import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.check_llm_fusion_contract import main


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES = REPO_ROOT / "docs" / "90_reference" / "samples"
CHECKER = REPO_ROOT / "tools" / "check_llm_fusion_contract.py"
VALID_REQUEST = SAMPLES / "llm_fusion_request.valid.json"
VALID_RESPONSE = SAMPLES / "llm_fusion_response.valid.json"
INVALID_MARKDOWN_RESPONSE = SAMPLES / "llm_fusion_response.invalid_markdown.txt"
INVALID_SCHEMA_RESPONSE = SAMPLES / "llm_fusion_response.invalid_schema.json"


class CheckLlmFusionContractTest(unittest.TestCase):
    def test_valid_samples_pass(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "--request",
                    str(VALID_REQUEST),
                    "--response",
                    str(VALID_RESPONSE),
                ]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn(
            "OK: request and response match vBook LLM fusion contract",
            stdout.getvalue(),
        )
        self.assertIn("Parsed sections: 2", stdout.getvalue())

    def test_script_path_execution_can_import_vbook_package(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                "--request",
                str(VALID_REQUEST),
                "--response",
                str(VALID_RESPONSE),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn(
            "OK: request and response match vBook LLM fusion contract",
            result.stdout,
        )
        self.assertIn("Parsed sections: 2", result.stdout)

    def test_missing_request_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(root / "missing-request.json"),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: request file does not exist", stderr.getvalue())

    def test_invalid_request_json_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(request),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: invalid request JSON", stderr.getvalue())

    def test_invalid_request_shape_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("[]", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(request),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: request JSON must be an object", stderr.getvalue())

    def test_invalid_request_timestamp_bool_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "intent": "llm_fusion_request",
                        "evidence_sections": [
                            {
                                "title": "section",
                                "summary": "summary",
                                "key_points": [],
                                "source_timestamps": [True],
                                "image_refs": [],
                                "tags": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(request),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn(
            "ERROR: request evidence_sections[0].source_timestamps[0] must be a number",
            stderr.getvalue(),
        )

    def test_invalid_markdown_response_returns_error(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "--request",
                    str(VALID_REQUEST),
                    "--response",
                    str(INVALID_MARKDOWN_RESPONSE),
                ]
            )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: invalid response JSON", stderr.getvalue())

    def test_invalid_schema_response_returns_error(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "--request",
                    str(VALID_REQUEST),
                    "--response",
                    str(INVALID_SCHEMA_RESPONSE),
                ]
            )

        self.assertEqual(code, 1)
        self.assertIn(
            "ERROR: response sections[0].source_timestamps[0] must be a number",
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
