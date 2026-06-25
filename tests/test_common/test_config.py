import tempfile
import unittest
from pathlib import Path

from vbook_common.config import VBookConfig, load_config


class ConfigTest(unittest.TestCase):
    def test_defaults_are_skeleton_safe(self) -> None:
        cfg = VBookConfig()

        self.assertEqual(cfg.output_dir, Path("outputs"))
        self.assertEqual(cfg.frame_interval_seconds, 3.0)
        self.assertEqual(cfg.alignment_window_seconds, 10.0)
        self.assertEqual(cfg.ocr_backend, "none")
        self.assertEqual(cfg.vision_backend, "multimodal")
        self.assertIsNone(cfg.transcript_command)

    def test_toml_file_overrides_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "vbook.toml"
            config_file.write_text(
                "\n".join(
                    [
                        'output_dir = "custom-output"',
                        "frame_interval_seconds = 5",
                        "alignment_window_seconds = 8",
                        'ocr_backend = "paddleocr"',
                        'vision_backend = "qwen-vl"',
                        'transcript_command = "vtext {input} -f vtt -o {output}"',
                    ]
                ),
                encoding="utf-8",
            )

            cfg = load_config(config_file=config_file, env={})

        self.assertEqual(cfg.output_dir, Path("custom-output"))
        self.assertEqual(cfg.frame_interval_seconds, 5.0)
        self.assertEqual(cfg.alignment_window_seconds, 8.0)
        self.assertEqual(cfg.ocr_backend, "paddleocr")
        self.assertEqual(cfg.vision_backend, "qwen-vl")
        self.assertEqual(cfg.transcript_command, "vtext {input} -f vtt -o {output}")

    def test_env_overrides_toml_and_explicit_overrides_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "vbook.toml"
            config_file.write_text(
                'output_dir = "toml-output"\nframe_interval_seconds = 4\n',
                encoding="utf-8",
            )

            cfg = load_config(
                config_file=config_file,
                env={
                    "VBOOK_OUTPUT_DIR": "env-output",
                    "VBOOK_FRAME_INTERVAL_SECONDS": "6",
                    "VBOOK_VISION_BACKEND": "env-vision",
                },
                overrides={
                    "output_dir": "override-output",
                    "vision_backend": "override-vision",
                },
            )

        self.assertEqual(cfg.output_dir, Path("override-output"))
        self.assertEqual(cfg.frame_interval_seconds, 6.0)
        self.assertEqual(cfg.vision_backend, "override-vision")


if __name__ == "__main__":
    unittest.main()
