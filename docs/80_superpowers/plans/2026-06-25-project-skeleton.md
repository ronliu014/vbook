# vBook Project Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the P1 Python project skeleton for vBook without implementing media processing.

**Architecture:** Use the vtext-inspired mixed skeleton confirmed in docs: CLI + local pipeline are the MVP execution path, while `vbook_server` exists only as an empty future boundary. Runtime dependencies stay minimal; common types, config, and serialization are implemented first so later pipeline stages have stable contracts.

**Tech Stack:** Python 3.11+, setuptools, argparse, dataclasses, unittest, optional dev tools pytest and ruff.

---

## File Structure

- Create `pyproject.toml` for packaging, console script, pytest configuration, and optional dev tools.
- Create `vbook_common/` for version, config, dataclasses, enums, and JSON-safe serialization.
- Create `vbook_client/` for CLI entry points using stdlib `argparse`.
- Create empty boundary packages: `vbook_server/`, `vbook_pipeline/`, `vbook_audio/`, `vbook_vision/`, `vbook_fusion/`, and `vbook_export/`.
- Create `tests/` with focused unittest coverage for common types, config precedence, and CLI behavior.
- Update `README.md` and `AGENTS.md` with the first real development commands.

### Task 1: Packaging and Package Boundaries

**Files:**
- Create: `pyproject.toml`
- Create: `vbook_common/__init__.py`
- Create: `vbook_common/version.py`
- Create: `vbook_client/__init__.py`
- Create: `vbook_client/__main__.py`
- Create: `vbook_server/__init__.py`
- Create: `vbook_pipeline/__init__.py`
- Create: `vbook_audio/__init__.py`
- Create: `vbook_vision/__init__.py`
- Create: `vbook_fusion/__init__.py`
- Create: `vbook_export/__init__.py`

- [ ] Add `pyproject.toml` with project name `vbook`, version `0.1.0`, Python `>=3.11`, setuptools package discovery for `vbook_*`, and console script `vbook = vbook_client.__main__:main`.
- [ ] Add package `__init__.py` files with concise docstrings and no heavy imports.
- [ ] Verify import discovery with `python -c "import vbook_common, vbook_client, vbook_server"`.

### Task 2: Shared Types and Serialization

**Files:**
- Create: `vbook_common/types.py`
- Create: `vbook_common/serialization.py`
- Create: `tests/__init__.py`
- Create: `tests/test_common/__init__.py`
- Create: `tests/test_common/test_types.py`

- [ ] Add enums `VisualType`, `FilterStatus`, `StageStatus`, and `TranscriptSourceType`.
- [ ] Add dataclasses `VideoAsset`, `TranscriptSegment`, `FrameCandidate`, `VisualAnalysis`, `TimelineLink`, `KnowledgeSection`, `PipelineRun`, and `Manifest`.
- [ ] Add `to_jsonable(value)` to convert dataclasses, enums, `Path`, lists, tuples, and dicts to JSON-safe objects.
- [ ] Add unittest coverage proving `VisualAnalysis` serializes `VisualType.KLINE_CASE` as `"kline_case"` and nested dataclasses are JSON-safe.
- [ ] Run `python -m unittest tests.test_common.test_types`.

### Task 3: Configuration Loader

**Files:**
- Create: `vbook_common/config.py`
- Create: `tests/test_common/test_config.py`

- [ ] Add `VBookConfig` with defaults for `output_dir`, `frame_interval_seconds`, `alignment_window_seconds`, `ocr_backend`, `vision_backend`, and `transcript_command`.
- [ ] Add `load_config(config_file=None, env=None, overrides=None)` with precedence `defaults < TOML < env < overrides`.
- [ ] Support environment variables `VBOOK_OUTPUT_DIR`, `VBOOK_FRAME_INTERVAL_SECONDS`, `VBOOK_ALIGNMENT_WINDOW_SECONDS`, `VBOOK_OCR_BACKEND`, `VBOOK_VISION_BACKEND`, and `VBOOK_TRANSCRIPT_COMMAND`.
- [ ] Add unittest coverage for TOML loading, environment override, and explicit override precedence.
- [ ] Run `python -m unittest tests.test_common.test_config`.

### Task 4: CLI Skeleton

**Files:**
- Create: `vbook_client/cli.py`
- Modify: `vbook_client/__main__.py`
- Create: `tests/test_client/__init__.py`
- Create: `tests/test_client/test_cli.py`

- [ ] Add `vbook --version` command that prints `0.1.0`.
- [ ] Add `vbook check` command that prints a concise skeleton readiness message.
- [ ] Add `vbook config --show` command that prints current config as formatted JSON.
- [ ] Add tests for `--version` and `check`.
- [ ] Run `python -m unittest tests.test_client.test_cli`.

### Task 5: Documentation and Full Verification

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] Update commands to include `python -m unittest discover`, `python -m vbook_client --version`, `python -m vbook_client check`, and editable install guidance.
- [ ] Run `python -m unittest discover`.
- [ ] Run `python -m vbook_client --version`.
- [ ] Run `python -m vbook_client check`.
- [ ] Run `git status --short --branch`.
- [ ] Commit with `git commit -m "feat: add Python project skeleton"`.

## Self-Review

- Spec coverage: P1 roadmap requirements map to packaging, mixed skeleton packages, common contracts, CLI entry, and tests.
- Scope boundary: no frame extraction, OCR, multi-modal model calls, transcript parsing, fusion, or server API is implemented in this plan.
- Type consistency: the plan uses `TranscriptSegment`, `VisualAnalysis`, `Manifest`, `note.md`, `manifest.json`, `slide`, and `kline_case` consistently with the design docs.
