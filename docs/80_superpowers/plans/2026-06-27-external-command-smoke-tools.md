# External Command Smoke Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加仓库内置 `tools/vision_stub.py` 和 operations smoke 文档，让 `external-command` backend 不依赖用户临时脚本即可验证输入/输出契约。

**Architecture:** `tools/vision_stub.py` 是独立标准库脚本，只读取 `frames.json` 并写出兼容 `manual-json` 的 `analysis.json`。测试通过 `subprocess.run()` 调用真实脚本，CLI 集成测试复用当前 `build --vision-backend external-command` 路径，operations 文档说明可复制命令和产物检查点。

**Tech Stack:** Python stdlib `argparse`、`json`、`pathlib`、`sys`、`subprocess`、`unittest`；现有 `load_manual_visual_analysis()` 和 `vbook_client.main()`。

---

## Files

- Create: `tools/vision_stub.py`
  - 读取 `--input` JSON。
  - 校验 `frames` list、frame object 和 `frame_id`。
  - 写出 deterministic `manual-json` compatible output。
  - 错误时 stderr 输出简短信息并返回 exit code `1`。
- Create: `tests/test_tools/__init__.py`
- Create: `tests/test_tools/test_vision_stub.py`
  - 直接通过 `subprocess.run()` 测试脚本。
  - 用 `load_manual_visual_analysis()` 验证输出可归一化。
  - 覆盖缺失 input 文件和缺失 `frames` list。
- Modify: `tests/test_client/test_manifest_cli.py`
  - 新增 CLI build 使用仓库 `tools/vision_stub.py` 的集成测试。
- Create: `docs/60_operations/smoke-tests.md`
  - 记录 placeholder、manual-json 定位和 external-command smoke 命令。
- Modify: `docs/60_operations/README.md`
  - 将 planned `smoke-tests.md` 改为已存在链接。
- Modify: `docs/00_project/status.md`
  - 记录内置 smoke 工具和最新测试数。

---

### Task 1: Vision Stub Script Tests

**Files:**
- Create: `tests/test_tools/__init__.py`
- Create: `tests/test_tools/test_vision_stub.py`

- [ ] **Step 1: Create failing tests**

Create `tests/test_tools/__init__.py` as an empty package marker.

Create `tests/test_tools/test_vision_stub.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vbook_common.types import FrameCandidate, VisualType
from vbook_vision.analysis import load_manual_visual_analysis


REPO_ROOT = Path(__file__).resolve().parents[2]
VISION_STUB = REPO_ROOT / "tools" / "vision_stub.py"


class VisionStubToolTest(unittest.TestCase):
    def test_writes_manual_json_compatible_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "frames.json"
            output_path = root / "nested" / "analysis.json"
            image = root / "frame_000001.jpg"
            image.write_bytes(b"image")
            input_path.write_text(
                json.dumps(
                    {
                        "backend": "external-command",
                        "frames": [
                            {
                                "frame_id": "frame-000001",
                                "video_id": "lesson",
                                "timestamp": 12.5,
                                "image_path": image.as_posix(),
                                "width": 1280,
                                "height": 720,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(VISION_STUB),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            data = json.loads(output_path.read_text(encoding="utf-8"))
            analyses = load_manual_visual_analysis(
                [
                    FrameCandidate(
                        id="frame-000001",
                        video_id="lesson",
                        timestamp=12.5,
                        image_path=image,
                        width=1280,
                        height=720,
                    )
                ],
                output_path,
                backend="external-command",
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(data["backend"], "vision_stub")
        self.assertEqual(len(data["analyses"]), 1)
        self.assertEqual(data["analyses"][0]["frame_id"], "frame-000001")
        self.assertEqual(data["analyses"][0]["visual_type"], "other")
        self.assertEqual(data["analyses"][0]["ocr_text"], "")
        self.assertEqual(
            data["analyses"][0]["vision_description"],
            "External command smoke analysis for frame-000001.",
        )
        self.assertEqual(
            data["analyses"][0]["structured_observations"]["source"],
            "vision_stub",
        )
        self.assertEqual(
            data["analyses"][0]["structured_observations"]["image_path"],
            image.as_posix(),
        )
        self.assertEqual(data["analyses"][0]["confidence"], 0.0)
        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].visual_type, VisualType.OTHER)
        self.assertEqual(analyses[0].backend, "external-command")

    def test_missing_input_file_exits_with_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(VISION_STUB),
                    "--input",
                    str(root / "missing.json"),
                    "--output",
                    str(root / "analysis.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("input file does not exist", result.stderr)

    def test_missing_frames_list_exits_with_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "frames.json"
            input_path.write_text(json.dumps({"items": []}), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(VISION_STUB),
                    "--input",
                    str(input_path),
                    "--output",
                    str(root / "analysis.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("input JSON must contain frames list", result.stderr)
```

- [ ] **Step 2: Run red tests**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_stub
```

Expected: fail because `tools/vision_stub.py` does not exist yet.

---

### Task 2: Vision Stub Script Implementation

**Files:**
- Create: `tools/vision_stub.py`
- Test: `tests/test_tools/test_vision_stub.py`

- [ ] **Step 1: Implement script**

Create `tools/vision_stub.py`:

```python
"""Deterministic external-command vision smoke tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write manual-json-compatible smoke visual analysis."
    )
    parser.add_argument("--input", required=True, help="Frame input JSON path")
    parser.add_argument("--output", required=True, help="Analysis output JSON path")
    args = parser.parse_args(argv)

    try:
        payload = _load_input(Path(args.input))
        analyses = [_analysis_for_frame(frame, index) for index, frame in enumerate(payload["frames"])]
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "backend": "vision_stub",
                    "analyses": analyses,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
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
    frames = data.get("frames")
    if not isinstance(frames, list):
        raise ValueError("input JSON must contain frames list")
    for index, frame in enumerate(frames):
        _validate_frame(frame, index)
    return data


def _validate_frame(frame: Any, index: int) -> None:
    if not isinstance(frame, dict):
        raise ValueError(f"frame at index {index} must be an object")
    frame_id = frame.get("frame_id")
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise ValueError(f"frame at index {index} requires string frame_id")


def _analysis_for_frame(frame: dict[str, Any], index: int) -> dict[str, Any]:
    frame_id = str(frame["frame_id"])
    observations = {
        "source": "vision_stub",
        "video_id": frame.get("video_id", ""),
        "timestamp": frame.get("timestamp", 0.0),
        "image_path": frame.get("image_path", ""),
        "width": frame.get("width", 0),
        "height": frame.get("height", 0),
        "frame_index": index,
    }
    return {
        "frame_id": frame_id,
        "visual_type": "other",
        "ocr_text": "",
        "vision_description": f"External command smoke analysis for {frame_id}.",
        "structured_observations": observations,
        "confidence": 0.0,
    }


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run focused script tests**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_stub
```

Expected: all script tests pass.

- [ ] **Step 3: Commit script and tests**

Run:

```powershell
git add tools/vision_stub.py tests/test_tools/__init__.py tests/test_tools/test_vision_stub.py
git commit -m "Add external vision smoke tool"
```

---

### Task 3: CLI Integration With Repository Stub

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Add failing CLI test using repo tool**

Add this test before `test_build_command_external_command_requires_vision_command`:

```python
    def test_build_command_can_use_repository_vision_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            repo_root = Path(__file__).resolve().parents[2]
            script = repo_root / "tools" / "vision_stub.py"
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
                    "--vision-backend",
                    "external-command",
                    "--vision-command",
                    f"{sys.executable} {script} --input {{input}} --output {{output}}",
                ]
            )

            vision = json.loads(
                (output / "vision" / "analysis.json").read_text(encoding="utf-8")
            )
            external_output = json.loads(
                (output / "vision" / "external" / "analysis.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(external_output["backend"], "vision_stub")
        self.assertEqual(vision["backend"], "external-command")
        self.assertEqual(vision["analyses"][0]["backend"], "external-command")
        self.assertEqual(
            vision["analyses"][0]["vision_description"],
            "External command smoke analysis for frame-000001.",
        )
        self.assertEqual(
            manifest["artifacts"]["vision"]["analyses"][0]["structured_observations"][
                "source"
            ],
            "vision_stub",
        )
        self.assertEqual(manifest["stage_status"]["vision_analysis"], "done")
```

- [ ] **Step 2: Run test**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_use_repository_vision_stub
```

Expected: pass once Task 2 is implemented.

- [ ] **Step 3: Run all client tests**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli
```

Expected: all client tests pass.

- [ ] **Step 4: Commit CLI test**

Run:

```powershell
git add tests/test_client/test_manifest_cli.py
git commit -m "Test CLI with repository vision stub"
```

---

### Task 4: Operations Documentation and Status

**Files:**
- Create: `docs/60_operations/smoke-tests.md`
- Modify: `docs/60_operations/README.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Create smoke tests documentation**

Create `docs/60_operations/smoke-tests.md`:

```markdown
# Smoke Tests

This page lists small local checks for verifying that vBook pipeline boundaries
are wired correctly. Smoke tests are not quality benchmarks; they confirm that
commands run, expected artifacts are written, and contracts are readable.

## Placeholder Build Smoke

Use the default `build` path when you only need to verify the local MVP pipeline:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson
```

Expected artifacts:

- `outputs\lesson\manifest.json`
- `outputs\lesson\vision\analysis.json`
- `outputs\lesson\fusion\prompt.json`
- `outputs\lesson\fusion\sections.json`
- `outputs\lesson\note.md`

## Manual JSON Vision Smoke

Use `manual-json` when visual analysis has already been prepared by a person or
external process:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-manual `
  --vision-backend manual-json `
  --visual-analysis-input path\to\manual-vision.json
```

The manual JSON must contain an `analyses` list or be a list itself. Each record
must reference a `frame_id` selected or discovered in the current build.

## External Command Vision Smoke

Use `tools\vision_stub.py` to verify the `external-command` contract without
installing OCR, model runtimes, or API credentials:

```powershell
python -m vbook_client build `
  --video path\to\lesson.mp4 `
  --transcript path\to\lesson.srt `
  --output outputs\lesson-external `
  --vision-backend external-command `
  --vision-command "python tools\vision_stub.py --input {input} --output {output}"
```

Expected external-command artifacts:

- `outputs\lesson-external\vision\external\frames.json`
- `outputs\lesson-external\vision\external\analysis.json`
- `outputs\lesson-external\vision\analysis.json`
- `outputs\lesson-external\manifest.json`

`tools\vision_stub.py` does not perform OCR or multimodal visual understanding.
It writes deterministic smoke analysis so the command contract, paths, JSON
validation, manifest stage status, and downstream fusion inputs can be checked.

## Direct Vision Stub Check

You can also run the tool directly against an existing frame input JSON:

```powershell
python tools\vision_stub.py `
  --input outputs\lesson-external\vision\external\frames.json `
  --output outputs\lesson-external\vision\external\analysis.json
```

The output is compatible with the `manual-json` visual analysis contract.
```

- [ ] **Step 2: Update operations README**

In `docs/60_operations/README.md`, replace the planned document bullet:

```markdown
- `smoke-tests.md`
```

with:

```markdown
- [smoke-tests.md](./smoke-tests.md)
```

- [ ] **Step 3: Update project status**

In `docs/00_project/status.md`:

- Add a "What Works Now" bullet for `tools/vision_stub.py`.
- Update verification snapshot test count after final full suite run.

- [ ] **Step 4: Run docs sanity checks**

Run:

```powershell
rg -n "tools\\vision_stub.py|tools/vision_stub.py|smoke-tests.md" docs/60_operations docs/80_superpowers/specs docs/00_project/status.md
git diff --check
```

Expected: references are present and whitespace check is clean.

- [ ] **Step 5: Commit docs**

Run:

```powershell
git add docs/60_operations/smoke-tests.md docs/60_operations/README.md docs/00_project/status.md
git commit -m "Document external vision smoke workflow"
```

---

### Task 5: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_tools.test_vision_stub
python -m unittest tests.test_client.test_manifest_cli
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run full suite and diff check**

Run:

```powershell
python -m unittest discover
git diff --check
```

Expected: full suite passes and whitespace check is clean.

- [ ] **Step 3: Update status test count if needed**

If `python -m unittest discover` reports a count different from `docs/00_project/status.md`, update the status document and commit:

```powershell
git add docs/00_project/status.md
git commit -m "Update verification snapshot"
```

- [ ] **Step 4: Report branch state**

Run:

```powershell
git status --short --branch
git log --oneline --decorate -6
```

Expected: clean `external-command-smoke-tools` branch with spec, script/test, CLI test, and docs commits.

---

## Self-Review

- Spec coverage: plan covers `tools/vision_stub.py`, direct script tests, CLI build smoke, operations smoke docs, status update, and final verification.
- Scope check: no real OCR, no model provider, no batch vision passthrough, no generated media.
- Placeholder scan: no unresolved placeholder steps; each code-changing task includes concrete code or exact file edit.
- Type consistency: names match the spec: `vision_stub`, `external-command`, `frames.json`, `analysis.json`, `smoke-tests.md`.
