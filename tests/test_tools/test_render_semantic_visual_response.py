import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import render_semantic_visual_response as renderer


class RenderSemanticVisualResponseTest(unittest.TestCase):
    def test_renders_matching_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment = root / "experiment"
            response_dir = experiment / "responses" / "openai"
            response_dir.mkdir(parents=True)
            (experiment / "inputs").mkdir(parents=True)
            (experiment / "inputs" / "dataset.json").write_text(
                json.dumps(
                    {
                        "lessons": [
                            {
                                "lesson_id": "lesson-001",
                                "title": "Lesson One",
                                "lesson_output": "outputs/lesson-one",
                                "transcript_source_label": "verified",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (response_dir / "Lesson One.response.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "title": "Lesson One",
                        "overview": "Overview",
                        "sections": [],
                    }
                ),
                encoding="utf-8",
            )
            manifest = experiment / "renders" / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"status": "preview"}), encoding="utf-8")

            with mock.patch.object(
                renderer,
                "write_semantic_visual_note_package",
                return_value=SimpleNamespace(
                    manifest_path=manifest,
                    note_path=experiment / "renders" / "note.md",
                    asset_paths=[experiment / "renders" / "assets" / "frame.jpg"],
                ),
            ) as write_package:
                summaries = renderer.render_responses(
                    experiment_root=experiment,
                    provider="openai",
                    lesson_ids=["lesson-001"],
                    max_visuals_per_request=4,
                )

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["title"], "Lesson One")
        self.assertEqual(summaries[0]["status"], "preview")
        self.assertEqual(summaries[0]["asset_count"], 1)
        write_package.assert_called_once()
        self.assertEqual(
            write_package.call_args.kwargs["lesson_output_dir"],
            "outputs/lesson-one",
        )
        self.assertEqual(write_package.call_args.kwargs["transcript_source_label"], "verified")

    def test_returns_error_when_no_response_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            experiment = Path(tmp) / "experiment"
            (experiment / "inputs").mkdir(parents=True)
            (experiment / "inputs" / "dataset.json").write_text(
                json.dumps(
                    {
                        "lessons": [
                            {
                                "lesson_id": "lesson-001",
                                "title": "Lesson One",
                                "lesson_output": "outputs/lesson-one",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "no response JSON files found"):
                renderer.render_responses(
                    experiment_root=experiment,
                    provider="openai",
                    lesson_ids=["lesson-001"],
                    max_visuals_per_request=4,
                )


if __name__ == "__main__":
    unittest.main()
