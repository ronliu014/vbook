import pytest
from pathlib import Path
from vbook.config.loader import load_config

def test_load_default_config():
    config = load_config()
    assert config.processing.intermediate_dir == ".vbook_cache"
    assert config.output.structure == "mirror"

def test_config_from_yaml(tmp_path):
    config_file = tmp_path / "vbook.yaml"
    config_file.write_text("""
output:
  root: /tmp/output
  structure: mirror
backends:
  stt: whisper_local
  llm: ollama_qwen
""")
    config = load_config(config_path=config_file)
    assert config.output.root == Path("/tmp/output")
    assert config.backends.stt == "whisper_local"

def test_cli_args_override_config(tmp_path):
    config_file = tmp_path / "vbook.yaml"
    config_file.write_text("backends:\n  stt: whisper_local\n")
    config = load_config(config_path=config_file, overrides={"backends.stt": "cloud_api"})
    assert config.backends.stt == "cloud_api"

def test_config_glossary_field():
    from vbook.config.schema import VbookConfig
    cfg = VbookConfig()
    assert cfg.processing.glossary is None

def test_config_glossary_from_yaml(tmp_path):
    from vbook.config.loader import load_config
    config_file = tmp_path / "vbook.yaml"
    config_file.write_text("processing:\n  glossary: glossary/investment.yaml\n")
    cfg = load_config(config_path=config_file)
    assert cfg.processing.glossary == "glossary/investment.yaml"

def test_config_screenshot_defaults_no_preset():
    from vbook.config.schema import VbookConfig
    cfg = VbookConfig()
    # No preset → uses "mixed" defaults
    assert cfg.processing.screenshot.resolved_sample_interval == 2.0
    assert cfg.processing.screenshot.resolved_threshold == 0.20
    assert cfg.processing.screenshot.resolved_search_window == 8.0
    assert cfg.processing.screenshot.resolved_dedup_window == 5.0

def test_config_screenshot_preset_ppt():
    from vbook.config.schema import ScreenshotConfig
    cfg = ScreenshotConfig(preset="ppt")
    assert cfg.resolved_sample_interval == 2.0
    assert cfg.resolved_threshold == 0.15

def test_config_screenshot_preset_demo():
    from vbook.config.schema import ScreenshotConfig
    cfg = ScreenshotConfig(preset="demo")
    assert cfg.resolved_sample_interval == 1.0
    assert cfg.resolved_threshold == 0.10
    assert cfg.resolved_search_window == 5.0
    assert cfg.resolved_dedup_window == 3.0

def test_config_screenshot_preset_with_override():
    from vbook.config.schema import ScreenshotConfig
    cfg = ScreenshotConfig(preset="ppt", threshold=0.05)
    # Explicit override takes priority over preset
    assert cfg.resolved_threshold == 0.05
    # Other values from preset
    assert cfg.resolved_sample_interval == 2.0