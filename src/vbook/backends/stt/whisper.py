from faster_whisper import WhisperModel
from ..base import STTBackend, TranscriptResult, TranscriptSegment

class WhisperSTTBackend(STTBackend):
    def __init__(self, model: str = "medium", device: str = "cpu"):
        self.model = WhisperModel(model, device=device)

    def transcribe(self, audio_path: str) -> TranscriptResult:
        segments, info = self.model.transcribe(audio_path, language="zh")
        return TranscriptResult(
            segments=[
                TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
                for s in segments
            ],
            language=info.language,
        )