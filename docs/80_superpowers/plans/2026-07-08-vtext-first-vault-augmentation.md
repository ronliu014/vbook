# vtext-first Vault Augmentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `vault-enhance` workflow that reads a vtext Markdown note, preserves its text, and writes a separate vBook Markdown note with selected screenshots and short captions.

**Architecture:** Add a focused exporter module for vtext-first augmentation instead of extending the deprecated append-style preview renderer. Reuse `load_preview_sources()` and `build_preview_scenes()` from `vbook_export.vault_preview` for artifact loading and final-value image selection, then insert compact image blocks into the vtext Markdown by matching scene text to existing headings. Add a CLI command that writes the enhanced note, copied assets, and a manifest.

**Tech Stack:** Python standard library, `pathlib`, `json`, `shutil`, `dataclasses`, `unittest`, existing vBook CLI patterns.

---

## File Structure

- Create: `vbook_export/vault_enhance.py`
  - Owns vtext-first note augmentation.
  - Exposes `write_vtext_first_package(vtext_note, lesson_output, output_note, manifest_path=None)`.
  - Keeps source vtext note read-only.
  - Copies selected images beside the output note under `assets/<lesson-stem>/`.
  - Writes relative Markdown image links and a JSON manifest.

- Create: `tests/test_export/test_vault_enhance.py`
  - Tests note preservation, insertion placement, unmatched fallback, asset copying, manifest fields, and read-only source behavior.

- Modify: `vbook_client/cli.py`
  - Add `vault-enhance`.
  - Required args: `--vtext-note`, `--lesson-output`, `--output-note`.
  - Optional arg: `--manifest-output`.

- Modify: `tests/test_client/test_vault_preview_cli.py`
  - Add a CLI test for `vault-enhance` beside the existing deprecated `vault-preview` compatibility test.

- Modify: `docs/60_operations/README.md`
  - Add the new `vault-enhance` workflow after implementation docs exist or as a short current entry point.

---

### Task 1: Exporter Red Tests

**Files:**
- Create: `tests/test_export/test_vault_enhance.py`
- Create later: `vbook_export/vault_enhance.py`

- [ ] **Step 1: Write tests for vtext preservation and relevant image insertion**

Test fixture:

```python
vtext_note.write_text(
    "# 如何高效选股\n\n"
    "## 构建股票池之前的准备\n\n"
    "- **聚焦龙头**，不要什么票都放进来。\n"
    "- 结合近期热点和频繁涨停筛选。\n\n"
    "## 复盘执行\n\n"
    "收盘后更新候选池。\n",
    encoding="utf-8",
)
```

Expected behavior:

- Existing heading/list/bold text remains unchanged.
- One image block is inserted under `## 构建股票池之前的准备`.
- The block uses `assets/lesson/frame_000002.jpg`.
- The caption starts with `> 图示补充：`.

- [ ] **Step 2: Run the test and confirm RED**

Run:

```powershell
& "D:\anaconda3\envs\App\python.exe" -m unittest tests.test_export.test_vault_enhance
```

Expected: import failure because `vbook_export.vault_enhance` does not exist yet.

### Task 2: Minimal Exporter Implementation

**Files:**
- Create: `vbook_export/vault_enhance.py`
- Test: `tests/test_export/test_vault_enhance.py`

- [ ] **Step 1: Implement package dataclasses and public API**

Add:

```python
@dataclass(frozen=True)
class VaultEnhancePackage:
    output_note_path: Path
    manifest_path: Path
    asset_paths: list[Path]
```

Add:

```python
def write_vtext_first_package(
    vtext_note_path: Path | str,
    lesson_output_dir: Path | str,
    output_note_path: Path | str,
    manifest_path: Path | str | None = None,
) -> VaultEnhancePackage:
    ...
```

- [ ] **Step 2: Reuse preview sources and scene selection**

Load artifacts with:

```python
sources = load_preview_sources(vtext_note_path, lesson_output_dir)
scenes = build_preview_scenes(sources, _analyses_by_image_path(sources.vision))
```

Use only scenes with a `primary_image_ref`.

- [ ] **Step 3: Insert image blocks into matching vtext sections**

Split Markdown into heading sections. Match scene text against heading/body text using normalized token overlap. Insert after the heading and its immediate blank line. If no confident match exists, append:

```markdown
## 图示补充待确认
```

- [ ] **Step 4: Copy selected assets and write manifest**

Copy selected primary images to:

```text
<output-note-parent>/assets/<output-note-stem>/<image-name>
```

Manifest fields:

```json
{
  "schema_version": "1",
  "status": "preview",
  "text_source": "vtext",
  "source_note": "...",
  "output_note": "...",
  "assets_dir": "...",
  "inserted_image_count": 1,
  "unmatched_image_count": 0,
  "safety": {"source_vtext": "read_only"}
}
```

- [ ] **Step 5: Run exporter tests and confirm GREEN**

Run:

```powershell
& "D:\anaconda3\envs\App\python.exe" -m unittest tests.test_export.test_vault_enhance
```

Expected: all tests pass.

### Task 3: CLI Red/Green

**Files:**
- Modify: `tests/test_client/test_vault_preview_cli.py`
- Modify: `vbook_client/cli.py`

- [ ] **Step 1: Add failing CLI test**

Call:

```python
code = main([
    "vault-enhance",
    "--vtext-note", str(vtext_note),
    "--lesson-output", str(lesson_output),
    "--output-note", str(output_note),
])
```

Expected:

- `code == 0`
- output note exists
- manifest beside output note exists as `<output-note>.manifest.json`
- copied asset exists under `assets/<lesson>/`.

- [ ] **Step 2: Run CLI test and confirm RED**

Run:

```powershell
& "D:\anaconda3\envs\App\python.exe" -m unittest tests.test_client.test_vault_preview_cli
```

Expected: argparse failure or missing command.

- [ ] **Step 3: Add CLI parser and runner**

Import:

```python
from vbook_export.vault_enhance import write_vtext_first_package
```

Add command handling:

```python
if args.command == "vault-enhance":
    return _run_vault_enhance(args, parser)
```

Add parser args:

```python
enhance_parser.add_argument("--vtext-note", required=True, ...)
enhance_parser.add_argument("--lesson-output", required=True, ...)
enhance_parser.add_argument("--output-note", required=True, ...)
enhance_parser.add_argument("--manifest-output", ...)
```

- [ ] **Step 4: Run CLI test and confirm GREEN**

Run:

```powershell
& "D:\anaconda3\envs\App\python.exe" -m unittest tests.test_client.test_vault_preview_cli
```

Expected: all tests pass.

### Task 4: Documentation and Verification

**Files:**
- Modify: `docs/60_operations/README.md`
- Optional create: `docs/60_operations/vault-enhance.md`

- [ ] **Step 1: Document the new current entry point**

Add a short current entry pointing to `vault-enhance`, with lowercase `vtext` and `vbook` directory conventions.

- [ ] **Step 2: Run focused and full verification**

Run:

```powershell
& "D:\anaconda3\envs\App\python.exe" -m unittest tests.test_export.test_vault_enhance
& "D:\anaconda3\envs\App\python.exe" -m unittest tests.test_client.test_vault_preview_cli
& "D:\anaconda3\envs\App\python.exe" -m unittest discover
git diff --check
```

Expected:

- All unittest commands report `OK`.
- `git diff --check` exits 0.

## Self-Review

- Spec coverage: the plan preserves vtext text, writes separate vBook output, copies assets with relative links, keeps source read-only, records manifest metadata, and exposes the proposed CLI.
- Placeholder scan: no `TBD` or future-only implementation steps remain.
- Type consistency: public API uses `Path | str` inputs and returns `VaultEnhancePackage`, matching CLI and tests.
