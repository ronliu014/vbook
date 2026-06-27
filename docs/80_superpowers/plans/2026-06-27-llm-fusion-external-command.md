# LLM Fusion External Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing provider-neutral LLM fusion contract into the CLI through a deterministic `external-command` execution path.

**Architecture:** Keep `vbook_fusion.llm_contract` as the schema layer and add `vbook_fusion.llm_external` as the command-execution layer. The CLI will continue to generate deterministic evidence sections by default, and only when `--llm-fusion-command` is provided will it write an LLM request, run an external command, parse the response into `KnowledgeSection[]`, write LLM sections, and render `note.md` from those sections.

**Tech Stack:** Python 3.11 standard library, `argparse`, `json`, `shlex`, `subprocess`, existing vBook dataclasses, `unittest`.

---

## File Structure

- Create: `vbook_fusion/llm_external.py`
  - Owns external command execution for LLM fusion.
  - Does not parse LLM response schema.
- Create: `tests/test_fusion/test_llm_external.py`
  - Covers command placeholder validation, success path, missing response, non-zero exit, and stale response cleanup.
- Modify: `vbook_export/manifest.py`
  - Adds `llm_fusion` stage status.
  - Records LLM request / response / parsed sections artifacts.
  - Adds LLM fusion output paths.
- Modify: `tests/test_export/test_manifest.py`
  - Covers default skipped state and successful artifact recording.
- Modify: `vbook_client/cli.py`
  - Adds CLI arguments.
  - Wires LLM fusion after evidence sections and before note rendering.
  - Ensures `build-batch` preserves default behavior by passing empty LLM arguments.
- Modify: `tests/test_client/test_manifest_cli.py`
  - Covers end-to-end fake-command LLM fusion.
  - Covers missing command placeholder failure.
- Modify docs after implementation:
  - `docs/00_project/status.md`
  - `docs/30_pipeline/overview.md`
  - `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

No real LLM service, network call, SDK, or provider-specific code is added.

---

## Task 1: Add LLM External Command Tests

**Files:**
- Create: `tests/test_fusion/test_llm_external.py`

- [ ] **Step 1: Create failing tests for `run_llm_fusion_command()`**

Create `tests/test_fusion/test_llm_external.py` with:

```python
import json
import sys
import tempfile
import unittest
from pathlib import Path

from vbook_fusion.llm_external import run_llm_fusion_command


class LlmExternalCommandTest(unittest.TestCase):
    def test_run_llm_fusion_command_requires_input_and_output_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "response.json"
            request.write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                r"llm-fusion-command requires \{input\} and \{output\} placeholders",
            ):
                run_llm_fusion_command(
                    "python fake.py --input {input}",
                    request,
                    response,
                )

            with self.assertRaisesRegex(
                ValueError,
                r"llm-fusion-command requires \{input\} and \{output\} placeholders",
            ):
                run_llm_fusion_command(
                    "python fake.py --output {output}",
                    request,
                    response,
                )

    def test_run_llm_fusion_command_writes_response_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "nested" / "response.json"
            script = root / "fake_llm.py"
            request.write_text(
                json.dumps({"schema_version": "1", "evidence_sections": []}),
                encoding="utf-8",
            )
            script.write_text(
                (
                    "import argparse, json\n"
                    "from pathlib import Path\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "args = parser.parse_args()\n"
                    "request = json.loads(Path(args.input).read_text(encoding='utf-8'))\n"
                    "Path(args.output).write_text(json.dumps({\n"
                    "    'schema_version': request['schema_version'],\n"
                    "    'title': 'LLM note',\n"
                    "    'overview': 'Generated note.',\n"
                    "    'sections': [],\n"
                    "}), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )

            written = run_llm_fusion_command(
                f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                request,
                response,
            )
            data = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written, response)
        self.assertEqual(data["schema_version"], "1")
        self.assertEqual(data["title"], "LLM note")

    def test_run_llm_fusion_command_rejects_missing_response_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "response.json"
            script = root / "fake_llm.py"
            request.write_text("{}", encoding="utf-8")
            script.write_text(
                (
                    "import argparse\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "parser.parse_args()\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                r"llm fusion command did not create response file:",
            ):
                run_llm_fusion_command(
                    f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                    request,
                    response,
                )

    def test_run_llm_fusion_command_removes_stale_response_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.json"
            response = root / "response.json"
            script = root / "fake_llm.py"
            request.write_text("{}", encoding="utf-8")
            response.write_text('{"stale": true}', encoding="utf-8")
            script.write_text(
                (
                    "import argparse, sys\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "parser.parse_args()\n"
                    "print('model failed', file=sys.stderr)\n"
                    "sys.exit(7)\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                r"llm fusion command failed with exit code 7",
            ):
                run_llm_fusion_command(
                    f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
                    request,
                    response,
                )

            self.assertFalse(response.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests to verify RED**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_external
```

Expected: FAIL with:

```text
ModuleNotFoundError: No module named 'vbook_fusion.llm_external'
```

---

## Task 2: Implement `vbook_fusion.llm_external`

**Files:**
- Create: `vbook_fusion/llm_external.py`
- Test: `tests/test_fusion/test_llm_external.py`

- [ ] **Step 1: Create `vbook_fusion/llm_external.py`**

Create `vbook_fusion/llm_external.py` with:

```python
"""External-command execution for LLM fusion."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


def run_llm_fusion_command(
    command_template: str,
    request_path: Path | str,
    response_path: Path | str,
) -> Path:
    """Run an external command that writes an LLM fusion response JSON file."""
    if "{input}" not in command_template or "{output}" not in command_template:
        raise ValueError(
            "llm-fusion-command requires {input} and {output} placeholders"
        )

    resolved_request_path = Path(request_path)
    resolved_response_path = Path(response_path)
    resolved_response_path.parent.mkdir(parents=True, exist_ok=True)
    if resolved_response_path.exists():
        resolved_response_path.unlink()

    command_parts = [
        _strip_outer_quotes(
            part.replace("{input}", str(resolved_request_path)).replace(
                "{output}",
                str(resolved_response_path),
            )
        )
        for part in shlex.split(command_template, posix=False)
    ]
    result = subprocess.run(
        command_parts,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        message = f"llm fusion command failed with exit code {result.returncode}"
        if detail:
            message = f"{message}: {detail[:500]}"
        raise ValueError(message)
    if not resolved_response_path.exists():
        raise ValueError(
            f"llm fusion command did not create response file: {resolved_response_path}"
        )
    return resolved_response_path


def _strip_outer_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
```

- [ ] **Step 2: Run focused tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_external
```

Expected:

```text
Ran 4 tests
OK
```

- [ ] **Step 3: Commit external command helper**

Run:

```powershell
git add vbook_fusion/llm_external.py tests/test_fusion/test_llm_external.py
git commit -m "Add LLM fusion external command runner"
```

---

## Task 3: Add Manifest Tests for LLM Fusion Artifacts

**Files:**
- Modify: `tests/test_export/test_manifest.py`

- [ ] **Step 1: Add default skipped-state test**

Append this test inside `ManifestExportTest`:

```python
    def test_build_manifest_skips_llm_fusion_by_default(self) -> None:
        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
        )

        self.assertEqual(manifest.stage_status["llm_fusion"], StageStatus.SKIPPED)
        self.assertEqual(
            manifest.pipeline_run.stage_status["llm_fusion"],
            StageStatus.SKIPPED,
        )
        self.assertEqual(
            manifest.pipeline_run.output_paths["llm_fusion_request"],
            Path("outputs/lesson/fusion/llm_request.json"),
        )
        self.assertEqual(
            manifest.pipeline_run.output_paths["llm_fusion_response"],
            Path("outputs/lesson/fusion/llm_response.json"),
        )
        self.assertEqual(
            manifest.pipeline_run.output_paths["llm_fusion_sections"],
            Path("outputs/lesson/fusion/llm_sections.json"),
        )
```

- [ ] **Step 2: Add successful artifact recording test**

Append this test inside `ManifestExportTest`:

```python
    def test_build_manifest_can_record_llm_fusion_artifacts(self) -> None:
        manifest = build_manifest(
            video_path=Path("course/lesson.mp4"),
            transcript_path=Path("course/transcript.json"),
            output_dir=Path("outputs/lesson"),
            segments=[],
            config={},
            llm_fusion_request_path=Path("outputs/lesson/fusion/llm_request.json"),
            llm_fusion_response_path=Path("outputs/lesson/fusion/llm_response.json"),
            llm_fusion_sections_path=Path("outputs/lesson/fusion/llm_sections.json"),
            llm_fusion_written=True,
        )

        self.assertEqual(manifest.stage_status["llm_fusion"], StageStatus.DONE)
        self.assertEqual(
            manifest.pipeline_run.stage_status["llm_fusion"],
            StageStatus.DONE,
        )
        self.assertEqual(
            manifest.artifacts["fusion"]["llm_request_path"],
            Path("outputs/lesson/fusion/llm_request.json"),
        )
        self.assertEqual(
            manifest.artifacts["fusion"]["llm_request_format"],
            "json",
        )
        self.assertEqual(
            manifest.artifacts["fusion"]["llm_response_path"],
            Path("outputs/lesson/fusion/llm_response.json"),
        )
        self.assertEqual(
            manifest.artifacts["fusion"]["llm_response_format"],
            "json",
        )
        self.assertEqual(
            manifest.artifacts["fusion"]["llm_sections_path"],
            Path("outputs/lesson/fusion/llm_sections.json"),
        )
        self.assertEqual(
            manifest.artifacts["fusion"]["llm_sections_format"],
            "json",
        )
```

- [ ] **Step 3: Run the new manifest tests to verify RED**

Run:

```powershell
python -m unittest tests.test_export.test_manifest.ManifestExportTest.test_build_manifest_skips_llm_fusion_by_default tests.test_export.test_manifest.ManifestExportTest.test_build_manifest_can_record_llm_fusion_artifacts
```

Expected: FAIL. The first test fails with missing `llm_fusion`; the second fails with:

```text
TypeError: build_manifest() got an unexpected keyword argument 'llm_fusion_request_path'
```

---

## Task 4: Implement Manifest LLM Fusion Fields

**Files:**
- Modify: `vbook_export/manifest.py`
- Test: `tests/test_export/test_manifest.py`

- [ ] **Step 1: Extend `build_manifest()` signature**

In `vbook_export/manifest.py`, add these parameters after `fusion_sections_written`:

```python
    llm_fusion_request_path: Path | str | None = None,
    llm_fusion_response_path: Path | str | None = None,
    llm_fusion_sections_path: Path | str | None = None,
    llm_fusion_written: bool = False,
```

- [ ] **Step 2: Resolve default LLM fusion paths**

After `resolved_fusion_sections_path`, add:

```python
    resolved_llm_fusion_request_path = (
        Path(llm_fusion_request_path)
        if llm_fusion_request_path is not None
        else output / "fusion" / "llm_request.json"
    )
    resolved_llm_fusion_response_path = (
        Path(llm_fusion_response_path)
        if llm_fusion_response_path is not None
        else output / "fusion" / "llm_response.json"
    )
    resolved_llm_fusion_sections_path = (
        Path(llm_fusion_sections_path)
        if llm_fusion_sections_path is not None
        else output / "fusion" / "llm_sections.json"
    )
```

- [ ] **Step 3: Add `llm_fusion` stage status**

In the `stage_status` dict, insert after `fusion_sections`:

```python
        "llm_fusion": StageStatus.DONE
        if llm_fusion_written
        else StageStatus.SKIPPED,
```

- [ ] **Step 4: Add LLM fusion artifacts**

After the existing `if fusion_sections_written:` block, add:

```python
    if llm_fusion_written:
        artifacts.setdefault("fusion", {}).update(
            {
                "llm_request_path": resolved_llm_fusion_request_path,
                "llm_request_format": "json",
                "llm_response_path": resolved_llm_fusion_response_path,
                "llm_response_format": "json",
                "llm_sections_path": resolved_llm_fusion_sections_path,
                "llm_sections_format": "json",
            }
        )
```

- [ ] **Step 5: Add output paths**

In `PipelineRun(output_paths={...})`, add:

```python
            "llm_fusion_request": resolved_llm_fusion_request_path,
            "llm_fusion_response": resolved_llm_fusion_response_path,
            "llm_fusion_sections": resolved_llm_fusion_sections_path,
```

- [ ] **Step 6: Run manifest tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_export.test_manifest
```

Expected: all manifest export tests pass.

- [ ] **Step 7: Commit manifest support**

Run:

```powershell
git add vbook_export/manifest.py tests/test_export/test_manifest.py
git commit -m "Record LLM fusion artifacts in manifest"
```

---

## Task 5: Add CLI Integration Tests for LLM Fusion Command

**Files:**
- Modify: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Add successful fake-command integration test**

Append this test inside `ManifestCliTest`:

```python
    def test_build_command_can_run_llm_fusion_external_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            script = root / "fake_llm_fusion.py"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")
            script.write_text(
                (
                    "import argparse, json\n"
                    "from pathlib import Path\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--input', required=True)\n"
                    "parser.add_argument('--output', required=True)\n"
                    "args = parser.parse_args()\n"
                    "request = json.loads(Path(args.input).read_text(encoding='utf-8'))\n"
                    "evidence = request['evidence_sections'][0]\n"
                    "Path(args.output).write_text(json.dumps({\n"
                    "    'schema_version': '1',\n"
                    "    'title': 'LLM course note',\n"
                    "    'overview': 'LLM overview.',\n"
                    "    'sections': [{\n"
                    "        'title': 'LLM refined intro',\n"
                    "        'summary': 'LLM summary from evidence.',\n"
                    "        'key_points': ['LLM point'],\n"
                    "        'source_timestamps': evidence['source_timestamps'],\n"
                    "        'image_refs': evidence['image_refs'],\n"
                    "        'tags': ['evidence', 'final'],\n"
                    "    }],\n"
                    "}, ensure_ascii=False), encoding='utf-8')\n"
                ),
                encoding="utf-8",
            )

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
                    "--llm-fusion-command",
                    f'"{sys.executable}" "{script}" --input {{input}} --output {{output}}',
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
            evidence_sections = json.loads(
                (output / "fusion" / "sections.json").read_text(encoding="utf-8")
            )
            note = (output / "note.md").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(request["intent"], "llm_fusion_request")
        self.assertEqual(len(request["evidence_sections"]), 1)
        self.assertEqual(response["title"], "LLM course note")
        self.assertEqual(evidence_sections["intent"], "fusion_sections_evidence")
        self.assertEqual(llm_sections["intent"], "llm_fusion_sections")
        self.assertEqual(llm_sections["section_count"], 1)
        self.assertEqual(llm_sections["sections"][0]["title"], "LLM refined intro")
        self.assertEqual(
            llm_sections["sections"][0]["tags"],
            ["llm", "evidence", "final"],
        )
        self.assertIn("### LLM refined intro", note)
        self.assertIn("LLM summary from evidence.", note)
        self.assertEqual(manifest["stage_status"]["llm_fusion"], "done")
        self.assertEqual(
            manifest["artifacts"]["fusion"]["llm_request_path"],
            (output / "fusion" / "llm_request.json").as_posix(),
        )
        self.assertEqual(
            manifest["artifacts"]["fusion"]["llm_response_path"],
            (output / "fusion" / "llm_response.json").as_posix(),
        )
        self.assertEqual(
            manifest["artifacts"]["fusion"]["llm_sections_path"],
            (output / "fusion" / "llm_sections.json").as_posix(),
        )
```

- [ ] **Step 2: Add missing-placeholder CLI failure test**

Append this test inside `ManifestCliTest`:

```python
    def test_build_command_llm_fusion_command_requires_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "lesson.mp4"
            transcript = root / "transcript.json"
            output = root / "outputs" / "lesson"
            candidate_dir = output / "frames" / "candidates"
            video.write_text("placeholder", encoding="utf-8")
            transcript.write_text(
                json.dumps({"segments": [{"start": 0, "end": 3, "text": "intro"}]}),
                encoding="utf-8",
            )
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "frame_000001.jpg").write_text("a", encoding="utf-8")

            with self.assertRaises(SystemExit) as exc:
                main(
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
                        "--llm-fusion-command",
                        "python fake_llm.py --input {input}",
                    ]
                )

        self.assertEqual(exc.exception.code, 2)
```

- [ ] **Step 3: Run the new CLI tests to verify RED**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_run_llm_fusion_external_command tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_llm_fusion_command_requires_placeholders
```

Expected: FAIL with argparse rejecting `--llm-fusion-command` as an unrecognized argument.

---

## Task 6: Implement CLI LLM Fusion Wiring

**Files:**
- Modify: `vbook_client/cli.py`
- Test: `tests/test_client/test_manifest_cli.py`

- [ ] **Step 1: Add imports**

In `vbook_client/cli.py`, add:

```python
from vbook_fusion.llm_contract import (
    build_llm_fusion_request,
    parse_llm_fusion_response,
    write_llm_fusion_request,
    write_llm_fusion_sections,
)
from vbook_fusion.llm_external import run_llm_fusion_command
```

- [ ] **Step 2: Add CLI arguments**

In `_add_pipeline_arguments()`, after `--fusion-sections-path`, add:

```python
    command_parser.add_argument(
        "--llm-fusion-command",
        help="External command template for LLM fusion; must contain {input} and {output}",
    )
    command_parser.add_argument(
        "--llm-fusion-request-path",
        help="Path for LLM fusion request JSON; defaults to <output>/fusion/llm_request.json",
    )
    command_parser.add_argument(
        "--llm-fusion-response-path",
        help="Path for LLM fusion response JSON; defaults to <output>/fusion/llm_response.json",
    )
    command_parser.add_argument(
        "--llm-fusion-sections-path",
        help="Path for parsed LLM fusion sections JSON; defaults to <output>/fusion/llm_sections.json",
    )
```

- [ ] **Step 3: Add default path and state variables**

In `_run_manifest_pipeline()`, after `fusion_sections_written = False`, add:

```python
    llm_fusion_request_path = (
        Path(args.llm_fusion_request_path)
        if args.llm_fusion_request_path
        else Path(args.output) / "fusion" / "llm_request.json"
    )
    llm_fusion_response_path = (
        Path(args.llm_fusion_response_path)
        if args.llm_fusion_response_path
        else Path(args.output) / "fusion" / "llm_response.json"
    )
    llm_fusion_sections_path = (
        Path(args.llm_fusion_sections_path)
        if args.llm_fusion_sections_path
        else Path(args.output) / "fusion" / "llm_sections.json"
    )
    llm_fusion_written = False
    note_sections = None
```

- [ ] **Step 4: Set note source after evidence sections**

After `fusion_sections_written = True`, add:

```python
        note_sections = fusion_sections
```

- [ ] **Step 5: Add LLM fusion block before note rendering**

Before `if _flag(args, "write_note", defaults):`, add:

```python
    if args.llm_fusion_command:
        if fusion_sections is None:
            parser.error(f"{args.command} --llm-fusion-command requires fusion sections")
        try:
            llm_request = build_llm_fusion_request(video_asset, fusion_sections)
            write_llm_fusion_request(llm_request, llm_fusion_request_path)
            response_path = run_llm_fusion_command(
                args.llm_fusion_command,
                request_path=llm_fusion_request_path,
                response_path=llm_fusion_response_path,
            )
            llm_response = json.loads(response_path.read_text(encoding="utf-8"))
            llm_sections = parse_llm_fusion_response(llm_response)
            write_llm_fusion_sections(llm_sections, llm_fusion_sections_path)
        except (ValueError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        llm_fusion_written = True
        note_sections = llm_sections
```

- [ ] **Step 6: Render note from selected section source**

Replace this expression inside the note rendering block:

```python
            render_sections_note(video=video_asset, sections=fusion_sections)
            if fusion_sections is not None
```

with:

```python
            render_sections_note(video=video_asset, sections=note_sections)
            if note_sections is not None
```

- [ ] **Step 7: Pass LLM fields into `build_manifest()`**

In the `build_manifest()` call, add:

```python
        llm_fusion_request_path=llm_fusion_request_path,
        llm_fusion_response_path=llm_fusion_response_path,
        llm_fusion_sections_path=llm_fusion_sections_path,
        llm_fusion_written=llm_fusion_written,
```

- [ ] **Step 8: Preserve `build-batch` default behavior**

In the `argparse.Namespace(...)` created inside `_run_build_batch()`, add:

```python
            llm_fusion_command=None,
            llm_fusion_request_path=None,
            llm_fusion_response_path=None,
            llm_fusion_sections_path=None,
```

- [ ] **Step 9: Run focused CLI tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_can_run_llm_fusion_external_command tests.test_client.test_manifest_cli.ManifestCliTest.test_build_command_llm_fusion_command_requires_placeholders
```

Expected: PASS.

- [ ] **Step 10: Run related suites**

Run:

```powershell
python -m unittest tests.test_client.test_manifest_cli tests.test_export.test_manifest tests.test_fusion.test_llm_external tests.test_fusion.test_llm_contract
```

Expected: PASS.

- [ ] **Step 11: Commit CLI integration**

Run:

```powershell
git add vbook_client/cli.py tests/test_client/test_manifest_cli.py
git commit -m "Wire LLM fusion external command into CLI"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `docs/00_project/status.md`
- Modify: `docs/30_pipeline/overview.md`
- Modify: `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`

- [ ] **Step 1: Update project status**

In `docs/00_project/status.md`, under "What Works Now", add:

```text
- LLM fusion through explicit `--llm-fusion-command`, producing request,
  response, parsed LLM sections, manifest records, and `note.md` from LLM
  sections without binding vBook core to a model provider.
```

In "What Is Still Placeholder or Partial", replace:

```text
- LLM fusion execution is not wired into the CLI and no model provider is called.
```

with:

```text
- LLM fusion execution is available only through an explicit external command;
  vBook still does not ship an embedded model provider or model SDK integration.
```

Keep the verification count unchanged until Task 8 runs the full suite.

- [ ] **Step 2: Update pipeline overview**

In `docs/30_pipeline/overview.md`, extend stage 7 with:

```text
显式提供 `--llm-fusion-command` 时，vBook 会把 evidence sections 写成
`fusion/llm_request.json`，调用外部命令生成 `fusion/llm_response.json`，再校验并写出
`fusion/llm_sections.json`。此时 `note.md` 使用 LLM sections 渲染；未提供该参数时默认
仍使用 deterministic evidence draft。
```

- [ ] **Step 3: Update stage summary P4**

In `docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md`, update P4 to:

```text
### P4: 推进 fusion / note 质量

如果 Qwen 服务部署还需要时间，可以继续推进：

- 外部 LLM command 的真实模型实现和 smoke 样例。
- `note.md` 的最终专家笔记结构。
- 用 `manual-json`、fake Qwen output、真实 Qwen smoke output 或
  `--llm-fusion-command` 输出继续验证融合逻辑。
```

- [ ] **Step 4: Commit documentation updates after final test count is known**

Do not commit yet. Task 8 will run the full suite and update the verification count before committing docs.

---

## Task 8: Full Verification and Status Snapshot

**Files:**
- Modify: `docs/00_project/status.md`
- Commit docs from Task 7.

- [ ] **Step 1: Run focused verification**

Run:

```powershell
python -m unittest tests.test_fusion.test_llm_external
python -m unittest tests.test_client.test_manifest_cli
python -m unittest tests.test_export.test_manifest
python -m unittest tests.test_fusion.test_llm_contract
```

Expected: each command exits 0 with `OK`.

- [ ] **Step 2: Run full suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits 0 with `OK`.

- [ ] **Step 3: Update verification snapshot**

In `docs/00_project/status.md`, update:

```text
Latest full suite run after LLM fusion contract readiness:
```

to:

```text
Latest full suite run after LLM fusion external-command integration:
```

Update the test count to the exact number from Step 2:

```text
Ran <N> tests
OK
```

- [ ] **Step 4: Run `git diff --check`**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit docs**

Run:

```powershell
git add docs/00_project/status.md docs/30_pipeline/overview.md docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md
git commit -m "Document LLM fusion external command"
```

---

## Final Verification

- [ ] **Step 1: Run full test suite**

Run:

```powershell
python -m unittest discover
```

Expected: exits 0 with `OK`.

- [ ] **Step 2: Check git status**

Run:

```powershell
git status --short --branch
```

Expected: clean branch.

- [ ] **Step 3: Review changed files**

Run:

```powershell
git diff --stat origin/main..HEAD
```

Expected changes are limited to:

```text
docs/80_superpowers/specs/2026-06-27-llm-fusion-external-command-design.md
docs/80_superpowers/plans/2026-06-27-llm-fusion-external-command.md
vbook_fusion/llm_external.py
tests/test_fusion/test_llm_external.py
vbook_export/manifest.py
tests/test_export/test_manifest.py
vbook_client/cli.py
tests/test_client/test_manifest_cli.py
docs/00_project/status.md
docs/30_pipeline/overview.md
docs/70_progress/2026-06-27-qwen-adapter-stage-summary.md
```

- [ ] **Step 4: Merge and push**

If executed in a feature branch or worktree, merge back to `main`, rerun:

```powershell
python -m unittest discover
```

Then push:

```powershell
git push origin main
```

Expected: push succeeds without force.

---

## Self-Review

Spec coverage:

- `external-command` execution helper is covered by Tasks 1-2.
- Manifest stage status and artifacts are covered by Tasks 3-4.
- CLI request / command / response / sections / note flow is covered by Tasks 5-6.
- Documentation and verification snapshot are covered by Tasks 7-8.
- No provider SDK, network call, batch-specific LLM configuration, or model service is included.

Placeholder scan:

- No implementation step contains an unspecified code block.
- No task depends on a function that is not defined in an earlier task.
- Every production-code task has a failing test before implementation.

Type consistency:

- `run_llm_fusion_command(command_template, request_path, response_path) -> Path`
  is used consistently in tests and CLI.
- Manifest parameters use `llm_fusion_request_path`, `llm_fusion_response_path`,
  `llm_fusion_sections_path`, and `llm_fusion_written`.
- CLI paths use `--llm-fusion-request-path`, `--llm-fusion-response-path`, and
  `--llm-fusion-sections-path`.
