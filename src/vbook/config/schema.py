from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class SourceConfig(BaseModel):
    video_dirs: list[Path] = Field(default_factory=list)

class OutputConfig(BaseModel):
    root: Optional[Path] = None
    structure: str = "mirror"

SCREENSHOT_PRESETS = {
    "ppt": {"sample_interval": 2.0, "threshold": 0.15, "search_window": 10.0, "dedup_window": 5.0},
    "lecture": {"sample_interval": 3.0, "threshold": 0.25, "search_window": 10.0, "dedup_window": 5.0},
    "demo": {"sample_interval": 1.0, "threshold": 0.10, "search_window": 5.0, "dedup_window": 3.0},
    "mixed": {"sample_interval": 2.0, "threshold": 0.20, "search_window": 8.0, "dedup_window": 5.0},
}

class ScreenshotConfig(BaseModel):
    preset: Optional[str] = None
    sample_interval: Optional[float] = None
    threshold: Optional[float] = None
    search_window: Optional[float] = None
    dedup_window: Optional[float] = None

    def _resolve(self, field: str, default: float) -> float:
        explicit = getattr(self, field)
        if explicit is not None:
            return explicit
        if self.preset and self.preset in SCREENSHOT_PRESETS:
            return SCREENSHOT_PRESETS[self.preset][field]
        return SCREENSHOT_PRESETS["mixed"][field]

    @property
    def resolved_sample_interval(self) -> float:
        return self._resolve("sample_interval", 2.0)

    @property
    def resolved_threshold(self) -> float:
        return self._resolve("threshold", 0.20)

    @property
    def resolved_search_window(self) -> float:
        return self._resolve("search_window", 8.0)

    @property
    def resolved_dedup_window(self) -> float:
        return self._resolve("dedup_window", 5.0)

class ProcessingConfig(BaseModel):
    intermediate_dir: str = ".vbook_cache"
    keep_intermediate: bool = True
    max_retries: int = 3
    glossary: Optional[str] = None
    screenshot: ScreenshotConfig = Field(default_factory=ScreenshotConfig)

class LoggingConfig(BaseModel):
    level: str = "INFO"

class BackendsConfig(BaseModel):
    stt: str = "whisper_local"
    llm: str = "ollama_qwen"
    whisper_local: dict = Field(default_factory=lambda: {"model": "medium", "device": "cpu"})
    whisper_remote: dict = Field(default_factory=lambda: {
        "base_url": "http://localhost:7867",
        "model": "medium",
        "language": "zh",
    })
    ollama_qwen: dict = Field(default_factory=lambda: {"base_url": "http://localhost:7866", "model": "qwen3.5:9b"})

class VbookConfig(BaseModel):
    source: SourceConfig = Field(default_factory=SourceConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    backends: BackendsConfig = Field(default_factory=BackendsConfig)