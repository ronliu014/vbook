from pathlib import Path
from typing import Optional
import yaml
from .schema import VbookConfig

def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(
    config_path: Optional[Path] = None,
    overrides: Optional[dict] = None,
) -> VbookConfig:
    data = {}

    # 全局配置
    global_config = Path.home() / ".vbook" / "config.yaml"
    if global_config.exists():
        data = yaml.safe_load(global_config.read_text()) or {}

    # 项目配置
    if config_path and config_path.exists():
        project_data = yaml.safe_load(config_path.read_text()) or {}
        data = _deep_merge(data, project_data)

    # CLI 参数覆盖（dot-notation: "backends.stt" -> {"backends": {"stt": ...}}）
    if overrides:
        for key, value in overrides.items():
            parts = key.split(".")
            d = data
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value

    return VbookConfig(**data)