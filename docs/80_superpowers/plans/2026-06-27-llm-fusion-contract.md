# LLM Fusion Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a provider-neutral, deterministic LLM fusion request/response contract that can be tested without calling any model service.

**Architecture:** Create `vbook_fusion.llm_contract` beside existing fusion modules. It builds `fusion/llm_request.json` from `VideoAsset` and evidence `KnowledgeSection[]`, validates LLM JSON responses, converts valid sections back into `KnowledgeSection[]`, and writes request/section artifacts.

**Tech Stack:** Python 3.11+ standard library, existing vBook dataclasses, `unittest`, JSON serialization helpers.

---

## File Structure

- Create: `vbook_fusion/llm_contract.py`
  - `build_llm_fusion_request()`
  - `parse_llm_fusion_response()`
  - `write_llm_fusion_request()`
  - `write_llm_fusion_sections()`
  - private validation helpers
- Create: `tests/test_fusion/test_llm_contract.py`
  - request builder tests
  - parser success tests
  - parser validation failure tests
  - writer tests
- Modify: `docs/00_project/status.md`
  - mention LLM-ready fusion contract after implementation.
- Modify: `docs/30_pipeline/overview.md`
  - mention that LLM fusion contract exists but execution is not enabled.
- Modify: `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`
  - update P4 next-work wording after contract implementation.

No CLI wiring in this plan. No model or service calls in this plan.

---

## Task 1: Add LLM Request Builder Tests

**Files:**
- Create: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Create failing request builder test file**

Create `tests/test_fusion/test_llm_contract.py` with:

```python
import json
import math
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import KnowledgeSection, VideoAsset
from vbook_fusion.llm_contract import (
    build_llm_fusion_request,
    parse_llm_fusion_response,
    write_llm_fusion_request,
    write_llm_fusion_sections,
)


class LlmFusionContractTest(unittest.TestCase):
    def test_build_llm_fusion_request_uses_evidence_sections(self) -> None:
        video = VideoAsset(
            id="lesson-001",
            path=Path("lessons/lesson.mp4"),
            course_title="短线课",
            lesson_title="买点条件",
            duration_seconds=120.0,
        )
        sections = [
            KnowledgeSection(
                title="短线选股",
                summary="讲解：均线多头排列。",
                source_timestamps=[0.0, 14.0],
                image_refs=["outputs/lesson/frames/selected/frame_000001.jpg"],
                key_points=["均线多头排列"],
                tags=["evidence", "visual:slide"],
            )
        ]

        request = build_llm_fusion_request(video, sections)

        self.assertEqual(request["schema_version"], "1")
        self.assertEqual(request["intent"], "llm_fusion_request")
        self.assertEqual(request["task"], "course_note_synthesis")
        self.assertEqual(request["video"]["id"], "lesson-001")
        self.assertEqual(request["video"]["course_title"], "短线课")
        self.assertEqual(request["video"]["lesson_title"], "买点条件")
        self.assertEqual(request["video"]["duration_seconds"], 120.0)
        self.assertEqual(
            request["output_contract"]["required_top_level_fields"],
            ["title", "overview", "sections"],
        )
        self.assertIn("Use only provided evidence.", request["instructions"])
        self.assertEqual(len(request["evidence_sections"]), 1)
        self.assertEqual(request["evidence_sections"][0]["title"], "短线选股")
        self.assertEqual(
            request["evidence_sections"][0]["image_refs"],
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run request builder test to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_build_llm_fusion_request_uses_evidence_sections
```

Expected: FAIL with:

```text
ModuleNotFoundError: No module named 'vbook_fusion.llm_contract'
```

---

## Task 2: Implement LLM Request Builder

**Files:**
- Create: `vbook_fusion/llm_contract.py`
- Test: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Create `vbook_fusion/llm_contract.py`**

Create the file with:

```python
"""Provider-neutral LLM fusion request and response contracts."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vbook_common.serialization import to_jsonable
from vbook_common.types import KnowledgeSection, VideoAsset


LLM_FUSION_REQUEST_INTENT = "llm_fusion_request"
LLM_FUSION_SECTIONS_INTENT = "llm_fusion_sections"
LLM_FUSION_SCHEMA_VERSION = "1"

LLM_FUSION_INSTRUCTIONS = [
    "Use only provided evidence.",
    "Preserve source_timestamps and image_refs.",
    "Do not invent facts not supported by evidence.",
    "Write concise Simplified Chinese notes unless evidence is clearly another language.",
]

LLM_FUSION_OUTPUT_CONTRACT = {
    "schema_version": LLM_FUSION_SCHEMA_VERSION,
    "required_top_level_fields": ["title", "overview", "sections"],
    "section_required_fields": [
        "title",
        "summary",
        "key_points",
        "source_timestamps",
        "image_refs",
        "tags",
    ],
}


def build_llm_fusion_request(
    video: VideoAsset,
    evidence_sections: Sequence[KnowledgeSection],
) -> dict[str, Any]:
    """Build a provider-neutral request payload for future LLM synthesis."""
    return to_jsonable(
        {
            "schema_version": LLM_FUSION_SCHEMA_VERSION,
            "intent": LLM_FUSION_REQUEST_INTENT,
            "task": "course_note_synthesis",
            "output_contract": LLM_FUSION_OUTPUT_CONTRACT,
            "video": {
                "id": video.id,
                "course_title": video.course_title,
                "lesson_title": video.lesson_title,
                "duration_seconds": video.duration_seconds,
            },
            "instructions": LLM_FUSION_INSTRUCTIONS,
            "evidence_sections": list(evidence_sections),
        }
    )
```

- [ ] **Step 2: Add temporary stubs for imports used by later tests**

Append these stubs to the same file:

```python
def parse_llm_fusion_response(response: dict[str, Any]) -> list[KnowledgeSection]:
    raise NotImplementedError


def write_llm_fusion_request(request: dict[str, Any], path: Path | str) -> Path:
    raise NotImplementedError


def write_llm_fusion_sections(
    sections: Sequence[KnowledgeSection],
    path: Path | str,
) -> Path:
    raise NotImplementedError
```

- [ ] **Step 3: Run request builder test to verify GREEN**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_build_llm_fusion_request_uses_evidence_sections
```

Expected: PASS.

- [ ] **Step 4: Commit request builder**

```powershell
git add vbook_fusion/llm_contract.py tests/test_fusion/test_llm_contract.py
git commit -m "Add LLM fusion request contract"
```

---

## Task 3: Add Parser Success Test

**Files:**
- Modify: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Add parser success test**

Add this test inside `LlmFusionContractTest`:

```python
    def test_parse_llm_fusion_response_returns_knowledge_sections(self) -> None:
        sections = parse_llm_fusion_response(
            {
                "schema_version": "1",
                "title": "短线课",
                "overview": "本节课讲短线选股。",
                "sections": [
                    {
                        "title": "短线选股条件",
                        "summary": "说明均线和成交量条件。",
                        "key_points": ["均线多头排列", "成交量放大"],
                        "source_timestamps": [0.0, 14.0],
                        "image_refs": [
                            "outputs/lesson/frames/selected/frame_000001.jpg",
                            "outputs/lesson/frames/selected/frame_000001.jpg",
                        ],
                        "tags": ["evidence", "visual:slide", "evidence"],
                    }
                ],
            }
        )

        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertEqual(section.title, "短线选股条件")
        self.assertEqual(section.summary, "说明均线和成交量条件。")
        self.assertEqual(section.key_points, ["均线多头排列", "成交量放大"])
        self.assertEqual(section.source_timestamps, [0.0, 14.0])
        self.assertEqual(
            section.image_refs,
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertEqual(section.tags, ["llm", "evidence", "visual:slide"])
```

- [ ] **Step 2: Run parser success test to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_parse_llm_fusion_response_returns_knowledge_sections
```

Expected: FAIL with:

```text
NotImplementedError
```

---

## Task 4: Implement Parser Success Path

**Files:**
- Modify: `vbook_fusion/llm_contract.py`
- Test: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Replace `parse_llm_fusion_response()` stub**

Replace the stub with:

```python
def parse_llm_fusion_response(response: dict[str, Any]) -> list[KnowledgeSection]:
    """Validate an LLM JSON response and convert it to knowledge sections."""
    if not isinstance(response, dict):
        raise ValueError("response must be an object")
    _require_string(response, "schema_version", "schema_version")
    if response["schema_version"] != LLM_FUSION_SCHEMA_VERSION:
        raise ValueError("schema_version must be '1'")
    _require_string(response, "title", "title")
    _require_string(response, "overview", "overview")
    sections = response.get("sections")
    if not isinstance(sections, list):
        raise ValueError("sections must be a list")

    return [
        _knowledge_section_from_response(section, index)
        for index, section in enumerate(sections)
    ]
```

- [ ] **Step 2: Add parser helper functions**

Add these helpers below `parse_llm_fusion_response()`:

```python
def _knowledge_section_from_response(value: Any, index: int) -> KnowledgeSection:
    path = f"sections[{index}]"
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    title = _require_string(value, "title", f"{path}.title")
    summary = _require_string(value, "summary", f"{path}.summary")
    return KnowledgeSection(
        title=title,
        summary=summary,
        key_points=_require_string_list(value, "key_points", f"{path}.key_points"),
        source_timestamps=_require_number_list(
            value,
            "source_timestamps",
            f"{path}.source_timestamps",
        ),
        image_refs=_unique(
            _require_string_list(value, "image_refs", f"{path}.image_refs")
        ),
        tags=_unique(["llm", *_require_string_list(value, "tags", f"{path}.tags")]),
    )


def _require_string(value: dict[str, Any], key: str, path: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"{path} must be a string")
    return item


def _require_string_list(value: dict[str, Any], key: str, path: str) -> list[str]:
    item = value.get(key)
    if not isinstance(item, list):
        raise ValueError(f"{path} must be a list")
    result = []
    for index, entry in enumerate(item):
        if not isinstance(entry, str):
            raise ValueError(f"{path}[{index}] must be a string")
        result.append(entry)
    return result


def _require_number_list(value: dict[str, Any], key: str, path: str) -> list[float]:
    item = value.get(key)
    if not isinstance(item, list):
        raise ValueError(f"{path} must be a list")
    result = []
    for index, entry in enumerate(item):
        if isinstance(entry, bool) or not isinstance(entry, (int, float)):
            raise ValueError(f"{path}[{index}] must be a number")
        number = float(entry)
        if not math.isfinite(number):
            raise ValueError(f"{path}[{index}] must be finite")
        result.append(number)
    return result


def _unique(values: Sequence[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
```

- [ ] **Step 3: Run parser success test to verify GREEN**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_parse_llm_fusion_response_returns_knowledge_sections
```

Expected: PASS.

- [ ] **Step 4: Run all LLM contract tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract
```

Expected: PASS.

- [ ] **Step 5: Commit parser success path**

```powershell
git add vbook_fusion/llm_contract.py tests/test_fusion/test_llm_contract.py
git commit -m "Parse LLM fusion section responses"
```

---

## Task 5: Add Parser Validation Tests

**Files:**
- Modify: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Add validation failure tests**

Add this helper and tests inside `LlmFusionContractTest`:

```python
    def assertParseRaises(self, response: object, message: str) -> None:
        with self.assertRaisesRegex(ValueError, message):
            parse_llm_fusion_response(response)  # type: ignore[arg-type]

    def test_parse_llm_fusion_response_rejects_invalid_top_level_shape(self) -> None:
        self.assertParseRaises([], "response must be an object")
        self.assertParseRaises(
            {
                "schema_version": "2",
                "title": "title",
                "overview": "overview",
                "sections": [],
            },
            "schema_version must be '1'",
        )
        self.assertParseRaises(
            {"schema_version": "1", "title": "title", "overview": "overview"},
            "sections must be a list",
        )

    def test_parse_llm_fusion_response_rejects_invalid_section_fields(self) -> None:
        base = {
            "schema_version": "1",
            "title": "title",
            "overview": "overview",
            "sections": [
                {
                    "title": "section",
                    "summary": "summary",
                    "key_points": [],
                    "source_timestamps": [],
                    "image_refs": [],
                    "tags": [],
                }
            ],
        }

        invalid_title = json.loads(json.dumps(base))
        invalid_title["sections"][0]["title"] = 42
        self.assertParseRaises(invalid_title, r"sections\[0\]\.title must be a string")

        invalid_key_point = json.loads(json.dumps(base))
        invalid_key_point["sections"][0]["key_points"] = ["ok", 42]
        self.assertParseRaises(
            invalid_key_point,
            r"sections\[0\]\.key_points\[1\] must be a string",
        )

        invalid_timestamp = json.loads(json.dumps(base))
        invalid_timestamp["sections"][0]["source_timestamps"] = [0.0, math.inf]
        self.assertParseRaises(
            invalid_timestamp,
            r"sections\[0\]\.source_timestamps\[1\] must be finite",
        )
```

- [ ] **Step 2: Run validation tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_parse_llm_fusion_response_rejects_invalid_top_level_shape tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_parse_llm_fusion_response_rejects_invalid_section_fields
```

Expected: PASS.

- [ ] **Step 3: Commit validation tests**

```powershell
git add tests/test_fusion/test_llm_contract.py
git commit -m "Cover LLM fusion response validation"
```

---

## Task 6: Add Writer Tests

**Files:**
- Modify: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Add writer tests**

Add these tests inside `LlmFusionContractTest`:

```python
    def test_write_llm_fusion_request_creates_json_file(self) -> None:
        request = {
            "schema_version": "1",
            "intent": "llm_fusion_request",
            "task": "course_note_synthesis",
            "output_contract": {},
            "video": {},
            "instructions": [],
            "evidence_sections": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs" / "lesson" / "fusion" / "llm_request.json"

            written = write_llm_fusion_request(request, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written.name, "llm_request.json")
        self.assertEqual(data["intent"], "llm_fusion_request")
        self.assertEqual(data["schema_version"], "1")

    def test_write_llm_fusion_sections_creates_json_file(self) -> None:
        sections = [
            KnowledgeSection(
                title="短线选股条件",
                summary="说明均线和成交量条件。",
                key_points=["均线多头排列"],
                source_timestamps=[0.0, 14.0],
                image_refs=["outputs/lesson/frames/selected/frame_000001.jpg"],
                tags=["llm", "evidence"],
            )
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs" / "lesson" / "fusion" / "llm_sections.json"

            written = write_llm_fusion_sections(sections, path)
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written.name, "llm_sections.json")
        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["intent"], "llm_fusion_sections")
        self.assertEqual(data["section_count"], 1)
        self.assertEqual(data["sections"][0]["title"], "短线选股条件")
```

- [ ] **Step 2: Run writer tests to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_write_llm_fusion_request_creates_json_file tests.test_fusion.test_llm_contract.LlmFusionContractTest.test_write_llm_fusion_sections_creates_json_file
```

Expected: FAIL with `NotImplementedError`.

---

## Task 7: Implement Writers

**Files:**
- Modify: `vbook_fusion/llm_contract.py`
- Test: `tests/test_fusion/test_llm_contract.py`

- [ ] **Step 1: Replace writer stubs**

Replace `write_llm_fusion_request()` and `write_llm_fusion_sections()` with:

```python
def write_llm_fusion_request(request: dict[str, Any], path: Path | str) -> Path:
    """Write an LLM fusion request payload as formatted UTF-8 JSON."""
    return _write_json(request, path)


def write_llm_fusion_sections(
    sections: Sequence[KnowledgeSection],
    path: Path | str,
) -> Path:
    """Write parsed LLM fusion sections as formatted UTF-8 JSON."""
    return _write_json(
        {
            "schema_version": LLM_FUSION_SCHEMA_VERSION,
            "intent": LLM_FUSION_SECTIONS_INTENT,
            "section_count": len(sections),
            "sections": list(sections),
        },
        path,
    )


def _write_json(payload: dict[str, Any], path: Path | str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
```

- [ ] **Step 2: Run all LLM contract tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract
```

Expected:

```text
Ran 7 tests
OK
```

- [ ] **Step 3: Commit writers**

```powershell
git add vbook_fusion/llm_contract.py tests/test_fusion/test_llm_contract.py
git commit -m "Write LLM fusion contract artifacts"
```

---

## Task 8: Update Documentation and Run Full Verification

**Files:**
- Modify: `docs/00_project/status.md`
- Modify: `docs/30_pipeline/overview.md`
- Modify: `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

- [ ] **Step 1: Update status**

In `docs/00_project/status.md`, add a bullet under "What Works Now":

```text
- LLM-ready fusion request/response contract and deterministic response parser,
  without model execution.
```

In "What Is Still Placeholder or Partial", add:

```text
- LLM fusion execution is not wired into the CLI and no model provider is called.
```

Update verification count after running full suite.

- [ ] **Step 2: Update pipeline overview**

In `docs/30_pipeline/overview.md`, append to 阶段 7:

```text
同时，vBook 已准备 LLM-ready request/response contract 和 deterministic parser，
用于后续接入模型综合；当前默认输出仍使用 evidence draft，不执行模型调用。
```

- [ ] **Step 3: Update stage summary**

In `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`, update P4:

```text
- LLM fusion 执行入口和外部模型 command。
- `note.md` 的最终专家笔记结构。
- 用 `manual-json`、fake Qwen output 或真实 Qwen smoke output 继续验证融合逻辑。
```

- [ ] **Step 4: Run focused and full tests**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_contract
python -m unittest discover
```

Expected:

```text
OK
```

- [ ] **Step 5: Update status test count**

If `python -m unittest discover` reports a count different from the current status document, update:

```text
Ran <N> tests
OK
```

- [ ] **Step 6: Commit docs**

```powershell
git add docs/00_project/status.md docs/30_pipeline/overview.md docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md
git commit -m "Document LLM fusion contract readiness"
```

---

## Final Verification

- [ ] **Step 1: Run full test suite**

```powershell
python -m unittest discover
```

Expected:

```text
OK
```

- [ ] **Step 2: Check git status**

```powershell
git status --short --branch
```

Expected: clean branch.

- [ ] **Step 3: Review changed files**

```powershell
git diff --stat origin/main..HEAD
```

Expected: changes limited to:

- `vbook_fusion/llm_contract.py`
- `tests/test_fusion/test_llm_contract.py`
- status/progress/pipeline docs
- this plan and the design doc if not already merged

- [ ] **Step 4: Merge to main and push**

After tests pass on the implementation branch and again on `main`:

```powershell
git push origin main
```

Expected: push succeeds without force.

---

## Self-Review

Spec coverage:

- Qwen service reply is documented by the prior design commit and smoke docs.
- LLM request builder is covered by Tasks 1-2.
- LLM response parser is covered by Tasks 3-5.
- Writer functions are covered by Tasks 6-7.
- Docs and verification snapshot are covered by Task 8.
- No model execution or CLI wiring is included.

Placeholder scan:

- No incomplete implementation steps are present.
- Every code-changing task includes exact code.
- Every verification step includes exact commands and expected results.

Type consistency:

- Uses existing `VideoAsset` and `KnowledgeSection`.
- Public helper signatures match imports used in tests.
- Writer outputs use schema version `"1"` and explicit intents.
