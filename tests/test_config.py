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