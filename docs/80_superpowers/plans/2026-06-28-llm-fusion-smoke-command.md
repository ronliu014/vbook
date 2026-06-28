# LLM Fusion Smoke Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic repo-local `tools/llm_fusion_stub.py` command that can run vBook's `--llm-fusion-command` path without any real LLM service.

**Architecture:** Mirror the style of `tools/vision_stub.py`: a small CLI script owns input validation, deterministic response generation, and file writing. The existing vBook CLI, LLM contract, manifest schema, and expert note renderer remain unchanged; tests verify the smoke command directly and through a real build integration path.

**Tech Stack:** Python 3.11 standard library, `argparse`, `json`, `pathlib`, existing LLM fusion JSON contract, `unittest`.

---

## File Structure

- Create: `tools/llm_fusion_stub.py`
  - Deterministic external-command smoke tool for LLM fusion.
  - Reads `--input` request JSON and writes `--output` response JSON.
  - Does not import vBook internals; stays useful as an external command reference.
- Create: `tests/test_tools/test_llm_fusion_stub.py`
  - Unit tests for valid output and validation failures.
- Modify: `tests/test_client/test_manifest_cli.py`
  - Adds an integration test using the real `tools/llm_fusion_stub.py` instead of a temporary fake script.
- Modify: `docs/00_project/status.md`
  - Records the new smoke command and keeps the distinction from real model execution.
- Modify: `docs/30_pipeline/overview.md`
  - Mentions the local LLM fusion smoke command in stage 7.
- Modify: `docs/90_reference/llm-fusion-command-requirements.md`
  - Adds the repo-local smoke command as a concrete example for external implementers.

No package dependency, network access, model SDK, LLM response schema change, CLI flag, or manifest schema change is added.

---

## Task 1: Add Failing Unit Tests

**Files:**
- Create: `tests/test_tools/test_llm_fusion_stub.py`
- Test: `tests/test_tools/test_llm_fusion_stub.py`

- [ ] **Step 1: Create unit tests for the smoke command**

Create `tests/test_tools/test_llm_fusion_stub.py` with:

```python
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.llm_fusion_stub import main


class LlmFusionStubTest(unittest.TestCase):
    def test_writes_valid_llm_fusion_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "fusion" / "llm_request.json"
            response = root / "fusion" / "llm_response.json"
            request.parent.mkdir(parents=True)
            request.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "intent": "llm_fusion_request",
                        "task": "course_note_synthesis",
                        "video": {
                            "id": "lesson-id",
                            "course_title": "Stock Course",
                            "lesson_title": "MA Support",
                        },
                        "evidence_sections": [
                            {
                                "title": "短线选股",
                                "summary": "讲解短线选股的基本观察条件。",
                                "key_points": ["均线多头排列"],
                                "source_timestamps": [14.0, 0.0],
                                "image_refs": [
                                    "outputs/lesson/frames/selected/frame_000001.jpg"
                                ],
                                "tags": ["evidence", "visual:slide"],
                            },
                            {
                                "title": "",
                                "summary": "",
                                "key_points": [],
                                "source_timestamps": [],
                                "image_refs": [],
                                "tags": ["final"],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            code = main(["--input", str(request), "--output", str(response)])
            data = json.loads(response.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["title"], "MA Support")
        self.assertEqual(
            data["overview"],
            "Deterministic smoke synthesis from 2 evidence sections.",
        )
        self.assertEqual(len(data["sections"]), 2)
        self.assertEqual(data["sections"][0]["title"], "短线选股")
        self.assertEqual(
            data["sections"][0]["summary"],
            "讲解短线选股的基本观察条件。",
        )
        self.assertEqual(data["sections"][0]["key_points"], ["均线多头排列"])
        self.assertEqual(data["sections"][0]["source_timestamps"], [14.0, 0.0])
        self.assertEqual(
            data["sections"][0]["image_refs"],
            ["outputs/lesson/frames/selected/frame_000001.jpg"],
        )
        self.assertEqual(
            data["sections"][0]["tags"],
            ["evidence", "visual:slide", "final"],
        )
        self.assertEqual(data["sections"][1]["title"], "Evidence Section 2")
        self.assertEqual(
            data["sections"][1]["summary"],
            "Smoke summary for Evidence Section 2.",
        )
        self.assertEqual(data["sections"][1]["tags"], ["final"])

    def test_missing_input_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--input",
                        str(root / "missing.json"),
                        "--output",
                        str(root / "response.json"),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("input file does not exist", stderr.getvalue())

    def test_invalid_json_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--input",
                        str(request),
                        "--output",
                        str(root / "response.json"),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("invalid input JSON", stderr.getvalue())

    def test_invalid_top_level_shape_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("[]", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--input",
                        str(request),
                        "--output",
                        str(root / "response.json"),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("input JSON must be an object", stderr.getvalue())

    def test_invalid_request_fields_return_error(self) -> None:
        cases = [
            (
                {"schema_version": "2", "intent": "llm_fusion_request", "evidence_sections": []},
                "schema_version must be '1'",
            ),
            (
                {"schema_version": "1", "intent": "wrong", "evidence_sections": []},
                "intent must be 'llm_fusion_request'",
            ),
            (
                {"schema_version": "1", "intent": "llm_fusion_request", "evidence_sections": {}},
                "evidence_sections must be a list",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [
                        {
                            "title": 1,
                            "summary": "",
                            "key_points": [],
                            "source_timestamps": [],
                            "image_refs": [],
                            "tags": [],
                        }
                    ],
                },
                "evidence_sections[0].title must be a string",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [
                        {
                            "title": "",
                            "summary": "",
                            "key_points": [42],
                            "source_timestamps": [],
                            "image_refs": [],
                            "tags": [],
                        }
                    ],
                },
                "evidence_sections[0].key_points[0] must be a string",
            ),
            (
                {
                    "schema_version": "1",
                    "intent": "llm_fusion_request",
                    "evidence_sections": [
                        {
                            "title": "",
                            "summary": "",
                            "key_points": [],
                            "source_timestamps": [True],
                            "image_refs": [],
                            "tags": [],
                        }
                    ],
                },
                "evidence_sections[0].source_timestamps[0] must be a number",
            ),
        ]
        for payload, message in cases:
            with self.subTest(message=message):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    request = root / "request.json"
                    request.write_text(
                        json.dumps(payload, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        code = main(
                            [
                                "--input",
                                str(request),
                                "--output",
                                str(root / "response.json"),
                            ]
                        )

                self.assertEqual(code, 1)
                self.assertIn(message, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run focused tests to verify RED**

Run:

```powershell
python -m unittest tests.test_tools.test_llm_fusion_stub
```

Expected: FAIL with:

```text
ModuleNotFoundError: No module named 'tools.llm_fusion_stub'
```

---

## Task 2: Implement `tools/llm_fusion_stub.py`

**Files:**
- Create: `tools/llm_fusion_stub.py`
- Test: `tests/test_tools/test_llm_fusion_stub.py`

- [ ] **Step 1: Create the smoke command**

Create `tools/llm_fusion_stub.py` with:

```python
"""Deterministic external-command LLM fusion smoke tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
REQUEST_INTENT = "llm_fusion_request"
DEFAULT_TITLE = "vBook LLM Fusion Smoke Note"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a deterministic LLM fusion smoke response."
    )
    parser.add_argument("--input", required=True, help="LLM fusion request JSON path")
    parser.add_argument("--output", required=True, help="LLM fusion response JSON path")
    args = parser.parse_args(argv)

    try:
        request = _load_input(Path(args.input))
        response = _build_response(request)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(response, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _load_input(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise ValueError(f"input file does not exist: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version must be '1'")
    if data.get("intent") != REQUEST_INTENT:
        raise ValueError("intent must be 'llm_fusion_request'")
    sections = data.get("evidence_sections")
    if not isinstance(sections, list):
        raise ValueError("evidence_sections must be a list")
    for index, section in enumerate(sections):
        _validate_section(section, index)
    return data


def _validate_section(section: Any, index: int) -> None:
    path = f"evidence_sections[{index}]"
    if not isinstance(section, dict):
        raise ValueError(f"{path} must be an object")
    _require_string(section, "title", f"{path}.title")
    _require_string(section, "summary", f"{path}.summary")
    _require_string_list(section, "key_points", f"{path}.key_points")
    _require_number_list(section, "source_timestamps", f"{path}.source_timestamps")
    _require_string_list(section, "image_refs", f"{path}.image_refs")
    _require_string_list(section, "tags", f"{path}.tags")


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
        result.append(float(entry))
    return result


def _build_response(request: dict[str, Any]) -> dict[str, Any]:
    evidence_sections = request["evidence_sections"]
    return {
        "schema_version": SCHEMA_VERSION,
        "title": _response_title(request),
        "overview": _overview(len(evidence_sections)),
        "sections": [
            _response_section(section, index)
            for index, section in enumerate(evidence_sections, start=1)
        ],
    }


def _response_title(request: dict[str, Any]) -> str:
    video = request.get("video")
    if not isinstance(video, dict):
        return DEFAULT_TITLE
    for key in ("lesson_title", "course_title", "id"):
        value = video.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return DEFAULT_TITLE


def _overview(section_count: int) -> str:
    suffix = "section" if section_count == 1 else "sections"
    return f"Deterministic smoke synthesis from {section_count} evidence {suffix}."


def _response_section(section: dict[str, Any], index: int) -> dict[str, Any]:
    title = section["title"].strip() or f"Evidence Section {index}"
    summary = section["summary"].strip() or f"Smoke summary for {title}."
    return {
        "title": title,
        "summary": summary,
        "key_points": list(section["key_points"]),
        "source_timestamps": list(section["source_timestamps"]),
        "image_refs": list(section["image_refs"]),
        "tags": _append_final_tag(section["tags"]),
    }


def _append_final_tag(tags: list[str]) -> list[str]:
    result = []
    seen = set()
    for tag in [*tags, "final"]:
        if tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run focused tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_tools.test_llm_fusion_stub
```

Expected:

```text
Ran 5 tests
OK
```

- [ ] **Step 3: Commit smoke command**

Run:

```powershell
git add tools/llm_fusion_stub.py tests/test_tools/test_llm_fusion_stub.py
git commit -m "Add LLM fusion smoke command"
```

---

## Task 3: Add CLI Smoke Integration Test

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Add integration test using the real smoke command**

Append this test inside `ManifestCliTest`:

```python
    def test_build_command_can_run_repo_llm_fusion_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            stub = Path("tools") / "llm_fusion_stub.py"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

            code = main(
                [
                    "build",
                    "--video",
                    str(video),
                    "--transcript",
                    str(transcript),
                    "--output",
                    str(output),
                    "--frame-candidates-dir",
                    str(candidate_dir),
                    "--alignment-window-seconds",
                    "3",
                    "--course-title",
                    "Stock Course",
                    "--lesson-title",
                    "MA Support",
                    "--llm-fusion-command",
                    f'"{sys.executable}" "{stub}" --input {{input}} --output {{output}}',
                ]
            )

            request = json.loads(
                (output / "fusion" / "llm_request.json").read_text(encoding="utf-8")
            )
            response = json.loads(
                (output / "fusion" / "llm_response.json").read_text(encoding="utf-8")
            )
            llm_sections = json.loads(
                (output / "fusion" / "llm_sections.json").read_text(encoding="utf-8")
            )
            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(request["intent"], "llm_fusion_request")
        self.assertEqual(response["title"], "MA Support")
        self.assertEqual(
            response["overview"],
            "Deterministic smoke synthesis from 1 evidence section.",
        )
        self.assertEqual(llm_sections["intent"], "llm_fusion_sections")
        self.assertEqual(llm_sections["section_count"], 1)
        self.assertIn("final", llm_sections["sections"][0]["tags"])
        self.assertIn("## 课程信息", note)
        self.assertIn("## 知识结构", note)
        self.assertIn(llm_sections["sections"][0]["title"], note)
        self.assertIn(llm_sections["sections"][0]["summary"], note)
        self.assertEqual(manifest["stage_status"]["llm_fusion"], "done")
```

- [ ] **Step 2: Run focused CLI test to verify GREEN**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_run_repo_llm_fusion_stub
```

Expected: PASS.

- [ ] **Step 3: Run related CLI suite**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli
```

Expected: PASS.

- [ ] **Step 4: Commit CLI smoke test**

Run:

```powershell
git add tests/test_client/test_manifest_cli.py
git commit -m "Use LLM fusion smoke command in CLI test"
```

---

## Task 4: Update Documentation

**Files:**
- Modify: `docs/00_project/status.md`
- Modify: `docs/30_pipeline/overview.md`
- Modify: `docs/90_reference/llm-fusion-command-requirements.md`

- [ ] **Step 1: Update project status**

In `docs/00_project/status.md`, under "What Works Now", add after the LLM fusion external-command bullet:

```text
- Built-in `tools/llm_fusion_stub.py` for deterministic LLM fusion smoke checks
  without model runtimes, network services, or API credentials.
```

In "What Is Still Placeholder or Partial", replace:

```text
- LLM fusion execution is available only through an explicit external command;
  vBook still does not ship an embedded model provider or model SDK integration.
```

with:

```text
- LLM fusion execution is available through an explicit external command and a
  deterministic smoke stub; vBook still does not ship an embedded model provider
  or model SDK integration.
```

- [ ] **Step 2: Update pipeline overview**

In `docs/30_pipeline/overview.md`, after the paragraph describing `--llm-fusion-command`, add:

```text
仓库内置 `tools/llm_fusion_stub.py` 可作为本地 smoke command，读取
`fusion/llm_request.json` 并写出合法 `fusion/llm_response.json`，用于在没有真实模型服务时
验证 request、response、parsed LLM sections 和专家笔记导出的闭环。
```

- [ ] **Step 3: Update LLM command requirements**

In `docs/90_reference/llm-fusion-command-requirements.md`, after section `10.1 默认路径`, add:

```markdown
### 10.2 Repo 内置 smoke command

vBook 仓库提供一个确定性 smoke command，可用于验证集成链路：

```powershell
python -m vbook_client build `
  --video data\lesson.mp4 `
  --transcript data\lesson.srt `
  --output outputs\lesson `
  --llm-fusion-command "python tools\llm_fusion_stub.py --input {input} --output {output}"
```

该工具不调用真实模型，只把 `fusion/llm_request.json` 中的 evidence sections 转换为合法
`fusion/llm_response.json`。它适合 smoke、CI 和排查 vBook pipeline 问题，不代表最终
LLM 输出质量。
```

Rename the current heading:

```markdown
### 10.2 自定义路径
```

to:

```markdown
### 10.3 自定义路径
```

- [ ] **Step 4: Run documentation checks**

Run:

```powershell
git diff --check
$placeholderPattern = ('T' + 'BD') + '|待' + '定|占位' + '未完成'
rg -n $placeholderPattern docs/00_project/status.md docs/30_pipeline/overview.md docs/90_reference/llm-fusion-command-requirements.md
```

Expected:

- `git diff --check` exits 0 with no output.
- `rg` exits 1 with no matches.

- [ ] **Step 5: Commit documentation updates**

Run:

```powershell
git add docs/00_project/status.md docs/30_pipeline/overview.md docs/90_reference/llm-fusion-command-requirements.md
git commit -m "Document LLM fusion smoke command"
```

---

## Task 5: Full Verification and Push

**Files:**
- All changed files from Tasks 1-4.

- [ ] **Step 1: Run focused verification**

Run:

```powershell
python -m unittest tests.test_tools.test_llm_fusion_stub
python -m unittest tests.test_client.test_manifest_cli
```

Expected: each command exits 0 with `OK`.

- [ ] **Step 2: Run full suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits 0 with `OK`.

- [ ] **Step 3: Update verification snapshot**

In `docs/00_project/status.md`, update the verification snapshot label to:

```text
Latest full suite run after LLM fusion smoke command integration:
```

Update the test count to the exact number reported by `python -m unittest discover`.

- [ ] **Step 4: Commit verification snapshot if changed**

Run:

```powershell
git add docs/00_project/status.md
git commit -m "Update LLM fusion smoke verification snapshot"
```

If the test count and label already match, skip this commit and record that no snapshot change was needed.

- [ ] **Step 5: Run diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 6: Push to main**

Run:

```powershell
git push origin main
```

Expected: push updates `main -> main` without force. If the command returns non-zero but prints a successful update, verify with Step 7 before treating it as failed.

- [ ] **Step 7: Verify remote alignment**

Run:

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline -1
```

Expected:

- `git status --short --branch` prints `## main...origin/main`.
- `git rev-parse HEAD` and `git rev-parse origin/main` print the same commit hash.
- `git log --oneline -1` shows the last commit from this implementation stage.

---

## Self-Review

Spec coverage:

- `tools/llm_fusion_stub.py` CLI, input validation, output response, and error handling are covered by Tasks 1-2.
- The real `--llm-fusion-command` smoke path is covered by Task 3.
- Status, pipeline, and external implementer docs are covered by Task 4.
- Full verification, snapshot update, push, and remote alignment are covered by Task 5.
- No network access, model provider, dependency, manifest schema change, LLM contract change, or CLI flag change is included.

Placeholder scan:

- Every code-changing step includes concrete code.
- Every test step includes exact command and expected result.
- No step delegates unspecified behavior to the implementer.

Type consistency:

- The smoke command keeps `main(argv: list[str] | None = None) -> int`, matching `tools/vision_stub.py` style.
- Request validation mirrors the current `llm_contract` response requirements.
- CLI integration uses the existing `--llm-fusion-command` placeholder mechanism.
