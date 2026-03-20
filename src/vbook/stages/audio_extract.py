from pathlib import Path
import ffmpeg
from ..pipeline.stage import Stage, StageResult, StageStatus

class AudioExtractStage(Stage):
    name = "audio_extract"

    def __init__(self, video_path: Path, cache_dir: Path):
        self.video_path = video_path
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.cache_dir / "audio.wav"

        (
            ffmpeg
            .input(str(self.video_path))
            .audio
            .output(str(audio_path), acodec="pcm_s16le", ar=16000, ac=1)
            .overwrite_output()
            .run(quiet=True)
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"audio_path": str(audio_path)},
        )