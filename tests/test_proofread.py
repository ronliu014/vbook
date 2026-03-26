# tests/test_proofread.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from vbook.stages.proofread import ProofreadStage
from vbook.backends.llm.litellm_backend import LiteLLMBackend
from vbook.pipeline.stage import StageStatus

def test_proofread_corrects_terminology(tmp_path):
    transcript = {
        "language": "zh",
        "segments": [
            {"start": 0, "end": 5, "text": "这个底背力很明显"},
            {"start": 5, "end": 10, "text": "PE比已经很低了"},
        ],
        "full_text": "这个底背力很明显\nPE比已经很低了",
    }
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")

    glossary = {
        "domain": "投资",
        "terms": [
            {"term": "底背离", "description": "价格创新低但指标未创新低"},
            {"term": "PE比", "description": "市盈率"},
        ],
    }

    llm_response = json.dumps({
        "segments": [{"index": 0, "text": "这个底背离很明显"}],
        "corrections": [{"index": 0, "original": "底背力", "corrected": "底背离", "reason": "术语误识别"}],
    })

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=llm_response))]
        )
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b")
        stage = ProofreadStage(llm_backend=backend, cache_dir=tmp_path, glossary=glossary)
        result = stage.run(context={"transcript_path": str(transcript_path)})

    assert result.status == StageStatus.SUCCESS

    updated = json.loads(transcript_path.read_text(encoding="utf-8"))
    assert updated["segments"][0]["text"] == "这个底背离很明显"
    assert updated["segments"][1]["text"] == "PE比已经很低了"  # unchanged
    assert "底背离" in updated["full_text"]

    corrections = json.loads((tmp_path / "corrections.json").read_text(encoding="utf-8"))
    assert len(corrections) == 1
    assert corrections[0]["original"] == "底背力"

def test_proofread_skips_without_glossary(tmp_path):
    stage = ProofreadStage(llm_backend=MagicMock(), cache_dir=tmp_path, glossary=None)
    result = stage.run(context={})
    assert result.status == StageStatus.SKIPPED

def test_proofread_no_corrections_needed(tmp_path):
    transcript = {
        "language": "zh",
        "segments": [{"start": 0, "end": 5, "text": "PE比很高"}],
        "full_text": "PE比很高",
    }
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")

    glossary = {"domain": "投资", "terms": [{"term": "PE比", "description": "市盈率"}]}

    llm_response = json.dumps({"segments": [], "corrections": []})

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=llm_response))]
        )
        backend = LiteLLMBackend(model="ollama/qwen3.5:9b")
        stage = ProofreadStage(llm_backend=backend, cache_dir=tmp_path, glossary=glossary)
        result = stage.run(context={"transcript_path": str(transcript_path)})

    assert result.status == StageStatus.SUCCESS
    corrections = json.loads((tmp_path / "corrections.json").read_text(encoding="utf-8"))
    assert corrections == []
