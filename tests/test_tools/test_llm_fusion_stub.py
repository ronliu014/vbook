import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.llm_fusion_stub import main


class LlmFusionStubTest(unittest.TestCase):
    def test_writes_valid_llm_fusion_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "fusion" / "llm_request.json"
            response = root / "fusion" / "llm_response.json"
            request.parent.mkdir(parents=True)
            request.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "intent": "llm_fusion_request",
                        "task": "course_note_synthesis",
                        "video": {
                            "id": "lesson-id",
                            "course_title": "Stock Course",
                            "lesson_title": "MA Support",
                        },
                        "evidence_sections": [
                            {
                                "title": "短线选股",
                                "summary": "讲解短线选股的基本观察条件。",
                                "key_points": ["均线多头排列"],
                                "source_timestamps": [14.0, 0.0],
                                "image_refs": [
                                    "outputs/lesson/frames/selected/frame_000001.jpg"
                                ],
                                "tags": ["evidence", "visual:slide"],
                            },
                            {
                                "title": "",
                                "summary": "",
                                "key_points": [],
                                "source_timestamps": [],
                                "image_refs": [],
                                "tags": ["final"],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            code = main(["--input", str(request), "--output", str(response)])
            data = json.loads(response.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["title"], "MA Support")
        self.assertEqual(
            data["overview"],
            "Deterministic smoke synthesis from 2 evidence sections.",
        )
        self.assertEqual(len(data["sections"]), 2)
        self.assertEqual(data["sections"][0]["title"], "短线选股")
        self.assertEqual(
            data["sections"][0]["summary"],
            "讲解短线选股的基本观察条件。",
        )
        self.assertEqual(data["sections"][0]["key_points"], ["均线多头排列"])
        self.assertEqual(data["sections"][0]["source_timestamps"], [14.0, 0.0])
        self.assertEqual(
            data["sections"][0]["image_refs"],
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertEqual(
            data["sections"][0]["tags"],
            ["evidence", "visual:slide", "final"],
        )
        self.assertEqual(data["sections"][1]["title"], "Evidence Section 2")
        self.assertEqual(
            data["sections"][1]["summary"],
            "Smoke summary for Evidence Section 2.",
        )
        self.assertEqual(data["sections"][1]["tags"], ["final"])

    def test_missing_input_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--input",
                        str(root / "missing.json"),
                        "--output",
                        str(root / "response.json"),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("input file does not exist", stderr.getvalue())

    def test_invalid_json_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--input",
                        str(request),
                        "--output",
                        str(root / "response.json"),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("invalid input JSON", stderr.getvalue())

    def test_invalid_top_level_shape_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("[]", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--input",
                        str(request),
                        "--output",
                        str(root / "response.json"),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("input JSON must be an object", stderr.getvalue())

    def test_invalid_request_fields_return_error(self) -> None:
        cases = [
            (
                {
                    "schema_version": "2",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [],
                },
                "schema_version must be '1'",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "wrong",
                    "evidence_sections": [],
                },
                "intent must be 'llm_fusion_request'",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": {},
                },
                "evidence_sections must be a list",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [
                        {
                            "title": 1,
                            "summary": "",
                            "key_points": [],
                            "source_timestamps": [],
                            "image_refs": [],
                            "tags": [],
                        }
                    ],
                },
                "evidence_sections[0].title must be a string",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [
                        {
                            "title": "",
                            "summary": "",
                            "key_points": [42],
                            "source_timestamps": [],
                            "image_refs": [],
                            "tags": [],
                        }
                    ],
                },
                "evidence_sections[0].key_points[0] must be a string",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [
                        {
                            "title": "",
                            "summary": "",
                            "key_points": [],
                            "source_timestamps": [True],
                            "image_refs": [],
                            "tags": [],
                        }
                    ],
                },
                "evidence_sections[0].source_timestamps[0] must be a number",
            ),
        ]
        for payload, message in cases:
            with self.subTest(message=message):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    request = root / "request.json"
                    request.write_text(
                        json.dumps(payload, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        code = main(
                            [
                                "--input",
                                str(request),
                                "--output",
                                str(root / "response.json"),
                            ]
                        )

                self.assertEqual(code, 1)
                self.assertIn(message, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
