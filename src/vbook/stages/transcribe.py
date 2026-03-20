import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import STTBackend

class TranscribeStage(Stage):
    name = "transcribe"

    def __init__(self, stt_backend: STTBackend, cache_dir: Path):
        self.stt_backend = stt_backend
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        audio_path = context.get("audio_path")
        if not audio_path:
            raise ValueError("audio_path not found in context")

        result = self.stt_backend.transcribe(audio_path)

        transcript_path = self.cache_dir / "transcript.json"
        transcript_data = {
            "language": result.language,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in result.segments
            ],
            "full_text": result.full_text,
        }
        transcript_path.write_text(
            json.dumps(transcript_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"transcript_path": str(transcript_path), "language": result.language},
        )