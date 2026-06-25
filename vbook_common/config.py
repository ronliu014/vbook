"""Configuration loading for vBook."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping


@dataclass
class VBookConfig:
    """Runtime configuration shared by skeleton commands."""

    output_dir: Path = Path("outputs")
    frame_interval_seconds: float = 3.0
    alignment_window_seconds: float = 10.0
    ocr_backend: str = "none"
    vision_backend: str = "multimodal"
    transcript_command: str | None = None


_ENV_TO_FIELD = {
    "VBOOK_OUTPUT_DIR": "output_dir",
    "VBOOK_FRAME_INTERVAL_SECONDS": "frame_interval_seconds",
    "VBOOK_ALIGNMENT_WINDOW_SECONDS": "alignment_window_seconds",
    "VBOOK_OCR_BACKEND": "ocr_backend",
    "VBOOK_VISION_BACKEND": "vision_backend",
    "VBOOK_TRANSCRIPT_COMMAND": "transcript_command",
}


def load_config(
    config_file: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> VBookConfig:
    """Load config with precedence defaults < TOML < env < overrides."""
    data = _config_to_dict(VBookConfig())

    if config_file is not None:
        data.update(_read_toml(Path(config_file)))

    source_env = os.environ if env is None else env
    data.update(_read_env(source_env))

    if overrides:
        data.update({key: value for key, value in overrides.items() if value is not None})

    return VBookConfig(**_coerce_values(data))


def _config_to_dict(config: VBookConfig) -> dict[str, Any]:
    return {field.name: getattr(config, field.name) for field in fields(config)}


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        parsed = tomllib.load(handle)
    allowed = {field.name for field in fields(VBookConfig)}
    return {key: value for key, value in parsed.items() if key in allowed}


def _read_env(env: Mapping[str, str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for env_name, field_name in _ENV_TO_FIELD.items():
        if env_name in env:
            values[field_name] = env[env_name]
    return values


def _coerce_values(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "output_dir": Path(data["output_dir"]),
        "frame_interval_seconds": float(data["frame_interval_seconds"]),
        "alignment_window_seconds": float(data["alignment_window_seconds"]),
        "ocr_backend": str(data["ocr_backend"]),
        "vision_backend": str(data["vision_backend"]),
        "transcript_command": (
            None if data.get("transcript_command") in (None, "") else str(data["transcript_command"])
        ),
    }
