# LLM Fusion Contract Samples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add repo-local LLM fusion contract samples, a deterministic contract checker, and external-team handoff docs so service teams can self-test responses before vBook integration.

**Architecture:** Keep the checker as a standalone reference tool under `tools/`, using only standard-library file/JSON handling plus the existing `vbook_fusion.llm_contract.parse_llm_fusion_response()` for response validation. Store static request/response examples under `docs/90_reference/samples/` and document the service-team workflow without changing the current CLI pipeline, LLM contract, note renderer, or provider boundary.

**Tech Stack:** Python 3.11 standard library, existing `vbook_fusion.llm_contract`, JSON sample files, `unittest`, Markdown documentation.

---

## File Structure

- Create: `docs/90_reference/samples/llm_fusion_request.valid.json`
  - Valid request example for external LLM fusion services.
- Create: `docs/90_reference/samples/llm_fusion_response.valid.json`
  - Valid response example accepted by vBook's current parser.
- Create: `docs/90_reference/samples/llm_fusion_response.invalid_markdown.txt`
  - Invalid model-output example showing Markdown-wrapped JSON.
- Create: `docs/90_reference/samples/llm_fusion_response.invalid_schema.json`
  - Invalid JSON response that parses as JSON but fails vBook schema validation.
- Create: `tools/check_llm_fusion_contract.py`
  - Local command for validating request/response files against vBook's LLM fusion contract.
- Create: `tests/test_tools/test_check_llm_fusion_contract.py`
  - Unit tests for valid samples and checker failures.
- Create: `docs/90_reference/llm-fusion-service-integration-request.md`
  - Short handoff checklist that can be sent to an external LLM/Qwen text synthesis service team.
- Modify: `docs/90_reference/README.md`
  - Replace the stale planned `sample-json.md` entry with the actual sample directory and new handoff doc.
- Modify: `docs/90_reference/llm-fusion-command-requirements.md`
  - Add sample files, checker command, and service-team self-test instructions.
- Modify: `docs/00_project/status.md`
  - Record the checker and sample pack, and update the verification snapshot after full test execution.

No network client, model SDK, HTTP adapter, LLM schema change, CLI argument, or `note.md` template change is included.

---

## Task 1: Add Failing Checker Tests

**Files:**
- Create: `tests/test_tools/test_check_llm_fusion_contract.py`
- Test: `tests/test_tools/test_check_llm_fusion_contract.py`

- [ ] **Step 1: Create unit tests for the contract checker**

Create `tests/test_tools/test_check_llm_fusion_contract.py` with:

```python
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.check_llm_fusion_contract import main


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES = REPO_ROOT / "docs" / "90_reference" / "samples"
VALID_REQUEST = SAMPLES / "llm_fusion_request.valid.json"
VALID_RESPONSE = SAMPLES / "llm_fusion_response.valid.json"
INVALID_MARKDOWN_RESPONSE = SAMPLES / "llm_fusion_response.invalid_markdown.txt"
INVALID_SCHEMA_RESPONSE = SAMPLES / "llm_fusion_response.invalid_schema.json"


class CheckLlmFusionContractTest(unittest.TestCase):
    def test_valid_samples_pass(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "--request",
                    str(VALID_REQUEST),
                    "--response",
                    str(VALID_RESPONSE),
                ]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn(
            "OK: request and response match vBook LLM fusion contract",
            stdout.getvalue(),
        )
        self.assertIn("Parsed sections: 2", stdout.getvalue())

    def test_missing_request_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(root / "missing-request.json"),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: request file does not exist", stderr.getvalue())

    def test_invalid_request_json_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(request),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: invalid request JSON", stderr.getvalue())

    def test_invalid_request_shape_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text("[]", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(request),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: request JSON must be an object", stderr.getvalue())

    def test_invalid_request_timestamp_bool_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "intent": "llm_fusion_request",
                        "evidence_sections": [
                            {
                                "title": "section",
                                "summary": "summary",
                                "key_points": [],
                                "source_timestamps": [True],
                                "image_refs": [],
                                "tags": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "--request",
                        str(request),
                        "--response",
                        str(VALID_RESPONSE),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn(
            "ERROR: request evidence_sections[0].source_timestamps[0] must be a number",
            stderr.getvalue(),
        )

    def test_invalid_markdown_response_returns_error(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "--request",
                    str(VALID_REQUEST),
                    "--response",
                    str(INVALID_MARKDOWN_RESPONSE),
                ]
            )

        self.assertEqual(code, 1)
        self.assertIn("ERROR: invalid response JSON", stderr.getvalue())

    def test_invalid_schema_response_returns_error(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(
                [
                    "--request",
                    str(VALID_REQUEST),
                    "--response",
                    str(INVALID_SCHEMA_RESPONSE),
                ]
            )

        self.assertEqual(code, 1)
        self.assertIn(
            "ERROR: response sections[0].source_timestamps[0] must be a number",
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run focused tests to verify RED**

Run:

```powershell
python -m unittest tests.test_tools.test_check_llm_fusion_contract
```

Expected: FAIL with:

```text
ModuleNotFoundError: No module named 'tools.check_llm_fusion_contract'
```

---

## Task 2: Add LLM Fusion Sample Files

**Files:**
- Create: `docs/90_reference/samples/llm_fusion_request.valid.json`
- Create: `docs/90_reference/samples/llm_fusion_response.valid.json`
- Create: `docs/90_reference/samples/llm_fusion_response.invalid_markdown.txt`
- Create: `docs/90_reference/samples/llm_fusion_response.invalid_schema.json`
- Test: `tests/test_tools/test_check_llm_fusion_contract.py`

- [ ] **Step 1: Create valid request sample**

Create `docs/90_reference/samples/llm_fusion_request.valid.json` with:

```json
{
  "schema_version": "1",
  "intent": "llm_fusion_request",
  "task": "course_note_synthesis",
  "output_contract": {
    "schema_version": "1",
    "required_top_level_fields": [
      "title",
      "overview",
      "sections"
    ],
    "section_required_fields": [
      "title",
      "summary",
      "key_points",
      "source_timestamps",
      "image_refs",
      "tags"
    ]
  },
  "video": {
    "id": "stock-course-lesson-001",
    "course_title": "短线交易入门",
    "lesson_title": "均线支撑与短线买点",
    "duration_seconds": 312.5
  },
  "instructions": [
    "Use only provided evidence.",
    "Preserve source_timestamps and image_refs.",
    "Do not invent facts not supported by evidence.",
    "Write concise Simplified Chinese notes unless evidence is clearly another language."
  ],
  "evidence_sections": [
    {
      "title": "均线支撑的观察条件",
      "summary": "画面展示短线买点的三个观察条件：均线多头排列、回踩不破、成交量温和放大。",
      "key_points": [
        "20日均线向上时，课程将其作为趋势仍在延续的观察条件。",
        "回踩均线但没有明显跌破，是课程中提到的短线买点观察点。",
        "成交量温和放大被用作资金参与度的辅助证据。"
      ],
      "source_timestamps": [
        12.0,
        18.5,
        24.0
      ],
      "image_refs": [
        "outputs/lesson/frames/selected/frame_000001.jpg"
      ],
      "tags": [
        "evidence",
        "visual:slide",
        "has_ocr"
      ]
    },
    {
      "title": "避免追高",
      "summary": "讲师提醒不要在价格已经远离均线时追入，应等待回踩确认。",
      "key_points": [
        "价格远离均线时，课程将其描述为短线风险升高。",
        "等待回踩确认可以降低买点过高的风险。"
      ],
      "source_timestamps": [
        46.0,
        53.0
      ],
      "image_refs": [],
      "tags": [
        "evidence",
        "transcript"
      ]
    }
  ]
}
```

- [ ] **Step 2: Create valid response sample**

Create `docs/90_reference/samples/llm_fusion_response.valid.json` with:

```json
{
  "schema_version": "1",
  "title": "均线支撑与短线买点",
  "overview": "本节课围绕均线支撑展开，说明短线买点需要同时观察趋势、回踩位置和成交量，不应在价格远离均线时追高。",
  "sections": [
    {
      "title": "识别均线支撑",
      "summary": "课程中把向上的 20 日均线作为趋势延续的观察条件，并结合回踩不破与成交量温和放大来判断短线买点是否更可靠。",
      "key_points": [
        "均线方向用于判断趋势背景，课程重点观察 20 日均线是否保持向上。",
        "回踩均线但没有明显跌破，被用作短线买点的确认条件。",
        "成交量温和放大可以辅助判断资金参与度。"
      ],
      "source_timestamps": [
        12.0,
        18.5,
        24.0
      ],
      "image_refs": [
        "outputs/lesson/frames/selected/frame_000001.jpg"
      ],
      "tags": [
        "final",
        "visual:slide",
        "has_ocr"
      ]
    },
    {
      "title": "控制追高风险",
      "summary": "讲师强调价格远离均线时短线风险升高，应等待回踩确认，而不是在上涨后段直接追入。",
      "key_points": [
        "价格远离均线时，课程将其视为风险升高的状态。",
        "等待回踩确认能降低买点过高带来的不确定性。"
      ],
      "source_timestamps": [
        46.0,
        53.0
      ],
      "image_refs": [],
      "tags": [
        "final",
        "transcript"
      ]
    }
  ]
}
```

- [ ] **Step 3: Create invalid Markdown response sample**

Create `docs/90_reference/samples/llm_fusion_response.invalid_markdown.txt` with:

````text
Here is the final course note JSON:

```json
{
  "schema_version": "1",
  "title": "均线支撑与短线买点",
  "overview": "This is wrapped in Markdown and must be rejected.",
  "sections": []
}
```
````

- [ ] **Step 4: Create invalid schema response sample**

Create `docs/90_reference/samples/llm_fusion_response.invalid_schema.json` with:

```json
{
  "schema_version": "1",
  "title": "均线支撑与短线买点",
  "overview": "This JSON parses, but the timestamp type is invalid.",
  "sections": [
    {
      "title": "Invalid timestamp",
      "summary": "The first timestamp is a boolean and must be rejected.",
      "key_points": [
        "This response is intentionally invalid."
      ],
      "source_timestamps": [
        true
      ],
      "image_refs": [],
      "tags": [
        "final"
      ]
    }
  ]
}
```

- [ ] **Step 5: Validate JSON sample syntax**

Run:

```powershell
python -m json.tool docs/90_reference/samples/llm_fusion_request.valid.json
python -m json.tool docs/90_reference/samples/llm_fusion_response.valid.json
python -m json.tool docs/90_reference/samples/llm_fusion_response.invalid_schema.json
```

Expected: each command exits 0 and prints formatted JSON.

- [ ] **Step 6: Run focused tests again**

Run:

```powershell
python -m unittest tests.test_tools.test_check_llm_fusion_contract
```

Expected: still FAIL with:

```text
ModuleNotFoundError: No module named 'tools.check_llm_fusion_contract'
```

Do not commit yet. The test, samples, and checker should be committed together after GREEN.

---

## Task 3: Implement Contract Checker

**Files:**
- Create: `tools/check_llm_fusion_contract.py`
- Test: `tests/test_tools/test_check_llm_fusion_contract.py`
- Read: `vbook_fusion/llm_contract.py`

- [ ] **Step 1: Create checker implementation**

Create `tools/check_llm_fusion_contract.py` with:

```python
"""Validate LLM fusion request and response files against vBook contracts."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from vbook_fusion.llm_contract import parse_llm_fusion_response


SCHEMA_VERSION = "1"
REQUEST_INTENT = "llm_fusion_request"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate vBook LLM fusion request and response JSON files."
    )
    parser.add_argument("--request", required=True, help="LLM fusion request JSON path")
    parser.add_argument(
        "--response",
        required=True,
        help="LLM fusion response JSON path",
    )
    args = parser.parse_args(argv)

    try:
        request = _load_json(Path(args.request), "request")
        _validate_request(request)
        response = _load_json(Path(args.response), "response")
        if not isinstance(response, dict):
            raise ValueError("response JSON must be an object")
        try:
            sections = parse_llm_fusion_response(response)
        except ValueError as exc:
            raise ValueError(f"response {exc}") from exc
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: request and response match vBook LLM fusion contract")
    print(f"Parsed sections: {len(sections)}")
    return 0


def _load_json(path: Path, label: str) -> Any:
    if not path.exists():
        raise ValueError(f"{label} file does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {label} JSON: {exc}") from exc


def _validate_request(request: Any) -> None:
    if not isinstance(request, dict):
        raise ValueError("request JSON must be an object")
    if request.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("request schema_version must be '1'")
    if request.get("intent") != REQUEST_INTENT:
        raise ValueError("request intent must be 'llm_fusion_request'")
    sections = request.get("evidence_sections")
    if not isinstance(sections, list):
        raise ValueError("request evidence_sections must be a list")
    for index, section in enumerate(sections):
        _validate_evidence_section(section, index)


def _validate_evidence_section(section: Any, index: int) -> None:
    path = f"request evidence_sections[{index}]"
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
        number = float(entry)
        if not math.isfinite(number):
            raise ValueError(f"{path}[{index}] must be finite")
        result.append(number)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run focused checker tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_tools.test_check_llm_fusion_contract
```

Expected:

```text
Ran 7 tests
OK
```

- [ ] **Step 3: Run direct checker command on valid samples**

Run:

```powershell
python tools\check_llm_fusion_contract.py --request docs\90_reference\samples\llm_fusion_request.valid.json --response docs\90_reference\samples\llm_fusion_response.valid.json
```

Expected stdout:

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: 2
```

Expected exit code: 0.

- [ ] **Step 4: Run direct checker command on invalid schema sample**

Run:

```powershell
python tools\check_llm_fusion_contract.py --request docs\90_reference\samples\llm_fusion_request.valid.json --response docs\90_reference\samples\llm_fusion_response.invalid_schema.json
```

Expected stderr contains:

```text
ERROR: response sections[0].source_timestamps[0] must be a number
```

Expected exit code: 1.

- [ ] **Step 5: Run diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit checker, tests, and samples**

Run:

```powershell
git add tools/check_llm_fusion_contract.py tests/test_tools/test_check_llm_fusion_contract.py docs/90_reference/samples
git commit -m "Add LLM fusion contract checker"
```

---

## Task 4: Add External-Team Handoff Document

**Files:**
- Create: `docs/90_reference/llm-fusion-service-integration-request.md`
- Modify: `docs/90_reference/README.md`

- [ ] **Step 1: Create the handoff document**

Create `docs/90_reference/llm-fusion-service-integration-request.md` with:

````markdown
# LLM Fusion Service 对接需求与回复清单

本文用于发给 LLM/Qwen 文本综合服务项目组，确认服务交付方式、命令契约和联调条件。

## vBook 当前状态

vBook 已经支持通过 `--llm-fusion-command` 调用外部 LLM fusion command：

```text
fusion/sections.json
  -> fusion/llm_request.json
  -> external LLM command
  -> fusion/llm_response.json
  -> fusion/llm_sections.json
  -> note.md
```

vBook core 不依赖模型 SDK，也不直接绑定某个 provider。外部服务组只需要提供一个可执行
command，读取 `--input` 指向的 request JSON，并写出 `--output` 指向的 response JSON。

## vBook 提供的样例

可用 request 样例：

```text
docs/90_reference/samples/llm_fusion_request.valid.json
```

可用 response 样例：

```text
docs/90_reference/samples/llm_fusion_response.valid.json
```

无效输出样例：

```text
docs/90_reference/samples/llm_fusion_response.invalid_markdown.txt
docs/90_reference/samples/llm_fusion_response.invalid_schema.json
```

## 服务组自测命令

服务组生成 response 后，请用 vBook checker 自测：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response path\to\service-generated-response.json
```

通过时输出：

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: <N>
```

失败时输出：

```text
ERROR: <reason>
```

## 请服务组回复的信息

请回复以下内容，便于 vBook 侧联调：

| Item | Reply |
| --- | --- |
| Service owner | |
| Contact | |
| Command path | |
| Command example | |
| Requires endpoint | yes/no |
| Endpoint URL | |
| Requires token | yes/no |
| Token passing method | env var / CLI arg / none |
| Model provider | |
| Model name | |
| Recommended timeout seconds | |
| Max evidence sections per lesson | |
| Output language | Simplified Chinese / configurable |
| Strict JSON confirmed | yes/no |
| Markdown fence never written to response | yes/no |
| Invalid input returns non-zero exit code | yes/no |
| stderr includes readable failure reason | yes/no |
| Valid sample response passes checker | yes/no |

## 第一版验收口径

第一版联调通过需要满足：

- command 能读取 vBook 生成的 `fusion/llm_request.json`。
- command 能写出合法 `fusion/llm_response.json`。
- response 能通过 `tools/check_llm_fusion_contract.py`。
- vBook 使用 `--llm-fusion-command` 后能生成：
  - `fusion/llm_request.json`
  - `fusion/llm_response.json`
  - `fusion/llm_sections.json`
  - `note.md`
  - `manifest.json`
- `manifest.json` 中 `stage_status.llm_fusion` 为 `"done"`。

## 非目标

第一版不要求服务组提供：

- vBook Python package 依赖。
- vBook manifest 解析。
- `note.md` 生成。
- 视频、音频或图片读取。
- Web UI。
- Streaming response。
- 多 provider 路由系统。

如果服务内部使用 HTTP、队列或 SDK，请封装在 command 内。vBook 第一接口仍然是同步
command。
````

- [ ] **Step 2: Update reference README**

In `docs/90_reference/README.md`, replace the whole file with:

```markdown
# 90 Reference

Reference documents preserve source material, external constraints, sample
artifacts, and related project context that are useful but not part of the main
reading path.

## Current Source Material

- [original-requirements.md](./original-requirements.md)
- [llm-fusion-command-requirements.md](./llm-fusion-command-requirements.md)
- [llm-fusion-service-integration-request.md](./llm-fusion-service-integration-request.md)
- [integration-response.md](./integration-response.md)
- [qwen-vision-service-requirements.md](./qwen-vision-service-requirements.md)
- [qwen-vision-service-integration-request.md](./qwen-vision-service-integration-request.md)
- [../40_development/sync-protocol.md](../40_development/sync-protocol.md)

## Sample Artifacts

- [samples/llm_fusion_request.valid.json](./samples/llm_fusion_request.valid.json)
- [samples/llm_fusion_response.valid.json](./samples/llm_fusion_response.valid.json)
- [samples/llm_fusion_response.invalid_markdown.txt](./samples/llm_fusion_response.invalid_markdown.txt)
- [samples/llm_fusion_response.invalid_schema.json](./samples/llm_fusion_response.invalid_schema.json)

The LLM fusion samples are contract fixtures for integration and checker tests.
They are not quality benchmarks for final model-generated notes.

## Planned Documents

- `vtext-boundary.md`
- `external-tools.md`
```

- [ ] **Step 3: Run documentation syntax checks**

Run:

```powershell
git diff --check
$placeholderPattern = ('T' + 'BD') + '|待' + '定|占位' + '未完成'
rg -n $placeholderPattern docs/90_reference/README.md docs/90_reference/llm-fusion-service-integration-request.md
```

Expected:

- `git diff --check` exits 0 with no output.
- `rg` exits 1 with no matches.

- [ ] **Step 4: Commit handoff doc and README**

Run:

```powershell
git add docs/90_reference/README.md docs/90_reference/llm-fusion-service-integration-request.md
git commit -m "Document LLM fusion service handoff"
```

---

## Task 5: Update LLM Fusion Requirements and Project Status

**Files:**
- Modify: `docs/90_reference/llm-fusion-command-requirements.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Update command requirements with samples and checker**

In `docs/90_reference/llm-fusion-command-requirements.md`, after section `10.3 自定义路径`, add:

````markdown
### 10.4 Contract samples

vBook 提供可复用的 request/response 样例：

```text
docs/90_reference/samples/llm_fusion_request.valid.json
docs/90_reference/samples/llm_fusion_response.valid.json
docs/90_reference/samples/llm_fusion_response.invalid_markdown.txt
docs/90_reference/samples/llm_fusion_response.invalid_schema.json
```

有效样例用于外部 command 自测和 vBook 侧验收；无效样例用于确认工具会拒绝 Markdown 包裹、
非法 schema 或不兼容 timestamp 类型。样例只代表 contract 形态，不代表最终模型输出质量。

### 10.5 Contract checker

外部实现方可以用仓库内置 checker 验证 response：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response docs\90_reference\samples\llm_fusion_response.valid.json
```

成功输出：

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: 2
```

如果 response 不是合法 JSON、顶层不是 object、字段缺失、timestamp 类型非法，checker 会返回
非 0 exit code，并在 stderr 输出 `ERROR: <reason>`。
````

- [ ] **Step 2: Update acceptance tests section**

In section `11.1 Valid Request`, after the command example, add:

````markdown
也可以直接使用 vBook 样例 request：

```powershell
python your_llm_fusion.py `
  --input docs\90_reference\samples\llm_fusion_request.valid.json `
  --output runs\llm_fusion_response.json
```

然后用 checker 验证：

```powershell
python tools\check_llm_fusion_contract.py `
  --request docs\90_reference\samples\llm_fusion_request.valid.json `
  --response runs\llm_fusion_response.json
```
````

- [ ] **Step 3: Update delivery checklist**

In section `13. 交付 Checklist`, replace:

```text
- 一份可用的 sample `llm_request.json`。
- 一份由工具生成的 sample `llm_response.json`。
```

with:

```text
- 使用 `docs/90_reference/samples/llm_fusion_request.valid.json` 生成的一份
  sample `llm_response.json`。
- `tools/check_llm_fusion_contract.py` 对该 sample response 的通过结果。
```

- [ ] **Step 4: Update project status**

In `docs/00_project/status.md`, under "What Works Now", add after the `tools/llm_fusion_stub.py` bullet:

```text
- LLM fusion contract samples and `tools/check_llm_fusion_contract.py` for
  external service self-tests before real model integration.
```

In "What Is Still Placeholder or Partial", add after the LLM fusion execution bullet:

```text
- LLM fusion contract samples validate file shape and parser compatibility;
  they do not evaluate final model note quality.
```

Do not update the verification snapshot in this task. The snapshot must be updated after Task 6 runs the full suite and knows the actual test count.

- [ ] **Step 5: Run documentation checks**

Run:

```powershell
git diff --check
$placeholderPattern = ('T' + 'BD') + '|待' + '定|占位' + '未完成'
rg -n $placeholderPattern docs/90_reference/llm-fusion-command-requirements.md docs/00_project/status.md
```

Expected:

- `git diff --check` exits 0 with no output.
- `rg` exits 1 with no matches.

- [ ] **Step 6: Commit requirements and status docs**

Run:

```powershell
git add docs/90_reference/llm-fusion-command-requirements.md docs/00_project/status.md
git commit -m "Document LLM fusion contract samples"
```

---

## Task 6: Full Verification and Push

**Files:**
- All changed files from Tasks 1-5.
- Modify: `docs/00_project/status.md` if the verification snapshot needs the new test count.

- [ ] **Step 1: Run focused checker tests**

Run:

```powershell
python -m unittest tests.test_tools.test_check_llm_fusion_contract
```

Expected:

```text
Ran 7 tests
OK
```

- [ ] **Step 2: Run direct checker happy path**

Run:

```powershell
python tools\check_llm_fusion_contract.py --request docs\90_reference\samples\llm_fusion_request.valid.json --response docs\90_reference\samples\llm_fusion_response.valid.json
```

Expected:

```text
OK: request and response match vBook LLM fusion contract
Parsed sections: 2
```

- [ ] **Step 3: Run full suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits 0 with `OK`.

- [ ] **Step 4: Update verification snapshot**

In `docs/00_project/status.md`, update the verification snapshot label to:

```text
Latest full suite run after LLM fusion contract samples integration:
```

Update the test count to the exact number reported by `python -m unittest discover`.

- [ ] **Step 5: Commit verification snapshot if changed**

Run:

```powershell
git add docs/00_project/status.md
git commit -m "Update LLM fusion contract sample verification snapshot"
```

If the test count and label already match, skip this commit and record that no snapshot change was needed.

- [ ] **Step 6: Run final diff check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 7: Push to main**

Run:

```powershell
git push origin main
```

Expected: push updates `main -> main` without force. If the command returns non-zero but prints a successful update, verify with Step 8 before treating it as failed.

- [ ] **Step 8: Verify remote alignment**

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

- Sample request/response assets are covered by Task 2.
- Invalid Markdown and invalid schema examples are covered by Task 2 and Task 3 tests.
- The local checker command, request validation, response parser reuse, stdout/stderr behavior, and exit codes are covered by Tasks 1 and 3.
- External service handoff documentation is covered by Task 4.
- Reference README, command requirements, status docs, verification snapshot, full suite, push, and remote alignment are covered by Tasks 4-6.
- No network access, model SDK, HTTP adapter, CLI behavior change, LLM schema change, or note template change is included.

Placeholder scan:

- Every code-changing step includes concrete code.
- Every JSON artifact step includes exact file content.
- Every documentation step includes exact insertion or replacement text.
- Every verification step includes exact command and expected result.

Type consistency:

- Checker entry point uses `main(argv: list[str] | None = None) -> int`, matching the repo's tool style.
- Request validation field names match `build_llm_fusion_request()` output.
- Response validation delegates to `parse_llm_fusion_response()` instead of duplicating parser logic.
- Tests import `tools.check_llm_fusion_contract.main`, matching the planned tool path.
