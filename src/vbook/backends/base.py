from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

@dataclass
class TranscriptResult:
    segments: list[TranscriptSegment] = field(default_factory=list)
    language: str = "zh"

    @property
    def full_text(self) -> str:
        return "\n".join(seg.text for seg in self.segments)

class STTBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, hotwords: list[str] | None = None) -> TranscriptResult:
        pass

class LLMBackend(ABC):
    @abstractmethod
    def analyze(self, text: str, prompt: str) -> str:
        pass

    def analyze_image(self, image_path: str, prompt: str) -> str:
        raise NotImplementedError("This backend does not support image analysis")