from pathlib import Path
from typing import Any, Optional
import yaml

class ProcessingTracker:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.status_file = cache_dir / "status.yaml"
        self._data = self._load()

    def _load(self) -> dict:
        if self.status_file.exists():
            return yaml.safe_load(self.status_file.read_text()) or {}
        return {}

    def _save(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(yaml.dump(self._data))

    def mark_complete(self, stage_name: str, output: dict):
        self._data[stage_name] = {"status": "success", "output": output}
        self._save()

    def mark_failed(self, stage_name: str, error: str):
        self._data[stage_name] = {"status": "failed", "error": error}
        self._save()

    def is_complete(self, stage_name: str) -> bool:
        return self._data.get(stage_name, {}).get("status") == "success"

    def get_output(self, stage_name: str) -> Optional[dict]:
        entry = self._data.get(stage_name, {})
        if entry.get("status") == "success":
            return entry.get("output")
        return None