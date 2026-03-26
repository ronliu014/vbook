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

def test_config_screenshot_defaults():
    from vbook.config.schema import VbookConfig
    cfg = VbookConfig()
    assert cfg.processing.screenshot.sample_interval == 5.0
    assert cfg.processing.screenshot.threshold == 0.3
    assert cfg.processing.screenshot.search_window == 10.0
    assert cfg.processing.screenshot.dedup_window == 5.0