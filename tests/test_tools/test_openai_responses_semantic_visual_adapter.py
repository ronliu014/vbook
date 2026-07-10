import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import openai_responses_semantic_visual_adapter as adapter


class OpenAIResponsesSemanticVisualAdapterTest(unittest.TestCase):
    def test_build_payload_uses_responses_shape_and_disables_storage(self) -> None:
        payload = adapter.build_responses_payload(
            request={
                "task": "semantic_visual_course_note_synthesis",
                "output_contract": {"schema_version": "1"},
                "video": {"lesson_title": "如何筛选龙头股？"},
                "instructions": ["Use evidence"],
                "transcript_segments": [{"id": "s1", "text": "龙头股"}],
                "visual_evidence": [{"image_path": "frame.jpg"}],
            },
            model="gpt-5.5",
            reasoning_effort="xhigh",
            store=False,
        )

        self.assertEqual(payload["model"], "gpt-5.5")
        self.assertIs(payload["store"], False)
        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["input"][0]["role"], "system")
        self.assertEqual(payload["input"][1]["role"], "user")
        user_text = payload["input"][1]["content"][0]["text"]
        self.assertIn("transcript_segments", user_text)
        self.assertIn("visual_evidence", user_text)

    def test_extract_response_text_supports_output_text(self) -> None:
        self.assertEqual(
            adapter.extract_response_text({"output_text": '{"schema_version":"1"}'}),
            '{"schema_version":"1"}',
        )

    def test_extract_response_text_supports_nested_output_content(self) -> None:
        text = adapter.extract_response_text(
            {
                "output": [
                    {
                        "content": [
                            {"type": "output_text", "text": '{"schema_version":"1"}'}
                        ]
                    }
                ]
            }
        )

        self.assertEqual(text, '{"schema_version":"1"}')

    def test_parse_model_json_strips_markdown_fence(self) -> None:
        data = adapter.parse_model_json(
            '```json\n{"schema_version":"1","title":"t","overview":"o","sections":[]}\n```'
        )

        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["title"], "t")

    def test_main_writes_model_json_without_storing_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            output_path = root / "response.json"
            request_path.write_text(
                json.dumps(
                    {
                        "task": "semantic_visual_course_note_synthesis",
                        "video": {"lesson_title": "Lesson"},
                        "transcript_segments": [],
                        "visual_evidence": [],
                    }
                ),
                encoding="utf-8",
            )
            fake_response = {
                "schema_version": "1",
                "title": "Lesson",
                "overview": "Overview",
                "sections": [
                    {
                        "title": "Section",
                        "summary": "Summary",
                        "key_points": ["Point"],
                        "source_timestamps": [1.0],
                        "image_refs": [],
                        "tags": ["semantic_visual_note"],
                    }
                ],
            }

            with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "secret-token"}):
                with mock.patch.object(
                    adapter,
                    "post_responses",
                    return_value={"output_text": json.dumps(fake_response)},
                ) as post:
                    code = adapter.main(
                        [
                            "--input",
                            str(request_path),
                            "--output",
                            str(output_path),
                            "--base-url",
                            "http://example.test",
                        ]
                    )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            output_text = output_path.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertEqual(payload["title"], "Lesson")
        self.assertNotIn("secret-token", output_text)
        self.assertEqual(post.call_args.kwargs["api_key"], "secret-token")


if __name__ == "__main__":
    unittest.main()
