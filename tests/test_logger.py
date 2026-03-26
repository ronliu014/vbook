# tests/test_logger.py
import logging
from pathlib import Path
from vbook.utils.logger import get_logger, setup_logging

def test_get_logger_returns_logger():
    logger = get_logger("vbook.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "vbook.test"

def test_setup_logging_creates_log_file(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    setup_logging(output_dir=output_dir, verbose=False)

    log_file = output_dir / "vbook.log"
    logger = get_logger("vbook.test_file")
    logger.info("test message")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "test message" in content

def test_setup_logging_verbose_sets_debug_level(tmp_path):
    output_dir = tmp_path / "output2"
    output_dir.mkdir()
    setup_logging(output_dir=output_dir, verbose=True)

    root_logger = logging.getLogger("vbook")
    assert root_logger.level == logging.DEBUG

def test_setup_logging_creates_project_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output3"
    output_dir.mkdir()
    setup_logging(output_dir=output_dir, verbose=False)

    project_log = tmp_path / "logs" / "vbook.log"
    assert project_log.exists()
