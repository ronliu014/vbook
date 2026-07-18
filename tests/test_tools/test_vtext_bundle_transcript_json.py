import json
import tempfile
import unittest
from pathlib import Path

from tools.vtext_bundle_transcript_json import write_transcript_json_from_bundle
from vbook_audio.transcript import load_transcript


class VtextBundleTranscriptJsonTest(unittest.TestCase):
    def test_writes_loadable_coarse_transcript_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            bundle.mkdir()
            (bundle / "manifest.json").write_text(
                json.dumps(
                    {
                        "source_video": str(Path(tmp) / "lesson.mp4"),
                        "outputs": {"clean_txt": "transcript.clean.txt"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (bundle / "transcript.clean.txt").write_text(
                "第一段 讲解黄金分割线 第二段 讲解止损位 第三段 讲解案例",
                encoding="utf-8",
            )
            output = Path(tmp) / "transcript.json"

            package = write_transcript_json_from_bundle(
                bundle_dir=bundle,
                output=output,
                duration_seconds=90,
                max_segment_chars=12,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            segments = load_transcript(output)

        self.assertEqual(package.json_path, output)
        self.assertGreater(package.segment_count, 1)
        self.assertEqual(payload["kind"], "vbook_coarse_transcript_json")
        self.assertEqual(
            payload["source"]["strategy"],
            "coarse_uniform_from_vtext_clean_text",
        )
        self.assertEqual(segments[0].start, 0.0)
        self.assertEqual(segments[-1].end, 90.0)
        self.assertTrue(all(segment.text for segment in segments))

    def test_falls_back_to_raw_txt_when_clean_txt_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            bundle.mkdir()
            (bundle / "manifest.json").write_text(
                json.dumps(
                    {
                        "source_video": str(Path(tmp) / "lesson.mp4"),
                        "outputs": {"raw_txt": "transcript.raw.txt"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (bundle / "transcript.raw.txt").write_text("只有 raw 文本", encoding="utf-8")
            output = Path(tmp) / "transcript.json"

            write_transcript_json_from_bundle(
                bundle_dir=bundle,
                output=output,
                duration_seconds=12,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["source"]["text_source"], "raw_txt")
