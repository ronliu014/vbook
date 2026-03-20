import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import LLMBackend
from ..output.prompts import ANALYZE_PROMPT

class AnalyzeStage(Stage):
    name = "analyze"

    def __init__(self, llm_backend: LLMBackend, cache_dir: Path):
        self.llm_backend = llm_backend
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        transcript_path = context.get("transcript_path")
        transcript_data = json.loads(Path(transcript_path).read_text(encoding="utf-8"))

        raw = self.llm_backend.analyze(transcript_data["full_text"], ANALYZE_PROMPT)

        # 提取JSON（防止LLM返回markdown代码块）
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        analysis = json.loads(raw)
        analysis_path = self.cache_dir / "analysis.json"
        analysis_path.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"analysis_path": str(analysis_path)},
        )