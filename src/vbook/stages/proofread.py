# src/vbook/stages/proofread.py
import copy
import json
from pathlib import Path
from typing import Optional
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..backends.base import LLMBackend
from ..output.prompts import PROOFREAD_PROMPT
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProofreadStage(Stage):
    name = "proofread"

    def __init__(self, llm_backend: LLMBackend, cache_dir: Path, glossary: Optional[dict] = None):
        self.llm_backend = llm_backend
        self.cache_dir = cache_dir
        self.glossary = glossary

    def run(self, context: dict) -> StageResult:
        if self.glossary is None:
            logger.info("未配置术语词表，跳过校对阶段")
            return StageResult(status=StageStatus.SKIPPED, output={})

        transcript_path = Path(context["transcript_path"])
        transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
        segments = transcript_data["segments"]

        glossary_text = "\n".join(
            f"- {t['term']}: {t['description']}" for t in self.glossary.get("terms", [])
        )
        prompt = PROOFREAD_PROMPT.format(glossary=glossary_text)

        segment_text = "\n".join(
            f"[{i}] {seg['text']}" for i, seg in enumerate(segments)
        )

        logger.info("开始校对转录文本（%d 段，%d 个术语）", len(segments), len(self.glossary.get("terms", [])))
        raw = self.llm_backend.analyze(segment_text, prompt)

        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        result = json.loads(raw)

        # Apply corrections to segments (on a copy to avoid corrupting data on retry)
        updated_segments = copy.deepcopy(segments)
        for corrected_seg in result.get("segments", []):
            idx = corrected_seg.get("index")
            if idx is not None and 0 <= idx < len(updated_segments):
                updated_segments[idx]["text"] = corrected_seg.get("text", updated_segments[idx]["text"])

        corrections = result.get("corrections", [])

        # Log corrections first (before writing files, so format errors don't leave partial writes)
        if corrections:
            logger.info("校对完成，修正 %d 处术语", len(corrections))
            for c in corrections:
                logger.debug("  [%d] %s → %s (%s)",
                             c.get("index", "?"), c.get("original", "?"),
                             c.get("corrected", "?"), c.get("reason", "?"))
        else:
            logger.info("校对完成，无需修正")

        # All validation passed — now write files
        transcript_data["segments"] = updated_segments
        transcript_data["full_text"] = "\n".join(seg["text"] for seg in updated_segments)
        transcript_path.write_text(
            json.dumps(transcript_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        corrections_path = self.cache_dir / "corrections.json"
        corrections_path.write_text(
            json.dumps(corrections, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"transcript_path": str(transcript_path), "corrections_path": str(corrections_path)},
        )
