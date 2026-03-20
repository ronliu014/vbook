from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageResult:
    status: StageStatus
    output: dict = field(default_factory=dict)
    error: Optional[str] = None

class Stage(ABC):
    name: str

    @abstractmethod
    def run(self, context: dict) -> StageResult:
        pass

    def can_skip(self, tracker) -> bool:
        return tracker.is_complete(self.name)