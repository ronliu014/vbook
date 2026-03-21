import httpx
from ..base import STTBackend, TranscriptResult, TranscriptSegment


class WhisperRemoteBackend(STTBackend):
    """远程 Whisper 后端，调用 faster-whisper-server 的 OpenAI 兼容 API。"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str = "medium",
        language: str = "zh",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.language = language

    def transcribe(self, audio_path: str) -> TranscriptResult:
        url = f"{self.base_url}/v1/audio/transcriptions"

        with open(audio_path, "rb") as f:
            resp = httpx.post(
                url,
                files={"file": (audio_path, f, "audio/wav")},
                data={
                    "model": self.model,
                    "language": self.language,
                    "response_format": "verbose_json",
                },
                timeout=600.0,
            )
        resp.raise_for_status()

        data = resp.json()
        segments = [
            TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
            )
            for seg in data.get("segments", [])
        ]
        return TranscriptResult(
            segments=segments,
            language=data.get("language", self.language),
        )
