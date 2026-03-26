from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class SourceConfig(BaseModel):
    video_dirs: list[Path] = Field(default_factory=list)

class OutputConfig(BaseModel):
    root: Optional[Path] = None
    structure: str = "mirror"

class ProcessingConfig(BaseModel):
    intermediate_dir: str = ".vbook_cache"
    keep_intermediate: bool = True
    max_retries: int = 3

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
    backends: BackendsConfig = Field(default_factory=BackendsConfig)