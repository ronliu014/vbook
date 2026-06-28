import json
import sys
import tempfile
import unittest
from pathlib import Path

from vbook_fusion.llm_external import run_llm_fusion_command


class LlmExternalCommandTest(unittest.TestCase):
    def test_run_llm_fusion_command_requires_input_and_output_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "response.json"
            request.write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                r"llm-fusion-command requires \{input\} and \{output\} placeholders",
            ):
                run_llm_fusion_command(
                    "python fake.py --input {input}",
                    request,
                    response,
                )

            with self.assertRaisesRegex(
                ValueError,
                r"llm-fusion-command requires \{input\} and \{output\} placeholders",
            ):
                run_llm_fusion_command(
                    "python fake.py --output {output}",
                    request,
                    response,
                )

    def test_run_llm_fusion_command_writes_response_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "nested" / "response.json"
            script = root / "fake_llm.py"
            request.write_text(
                json.dumps({"schema_version": "1", "evidence_sections": []}),
                encoding="utf-8",
            )
            script.write_text(
                (
                    "import argparse, json\n"
                    "from pathlib import Path\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "args = parser.parse_args()\n"
                    "request = json.loads(Path(args.input).read_text(encoding='utf-8'))\n"
                    "Path(args.output).write_text(json.dumps({\n"
                    "    'schema_version': request['schema_version'],\n"
                    "    'title': 'LLM note',\n"
                    "    'overview': 'Generated note.',\n"
                    "    'sections': [],\n"
                    "}), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )

            written = run_llm_fusion_command(
                f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                request,
                response,
            )
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written, response)
        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["title"], "LLM note")

    def test_run_llm_fusion_command_rejects_missing_response_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "response.json"
            script = root / "fake_llm.py"
            request.write_text("{}", encoding="utf-8")
            script.write_text(
                (
                    "import argparse\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "parser.parse_args()\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                r"llm fusion command did not create response file:",
            ):
                run_llm_fusion_command(
                    f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                    request,
                    response,
                )

    def test_run_llm_fusion_command_removes_stale_response_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "response.json"
            script = root / "fake_llm.py"
            request.write_text("{}", encoding="utf-8")
            response.write_text('{"stale": true}', encoding="utf-8")
            script.write_text(
                (
                    "import argparse, sys\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "parser.parse_args()\n"
                    "print('model failed', file=sys.stderr)\n"
                    "sys.exit(7)\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                r"llm fusion command failed with exit code 7",
            ):
                run_llm_fusion_command(
                    f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                    request,
                    response,
                )

            self.assertFalse(response.exists())


if __name__ == "__main__":
    unittest.main()
