# Development Commands

## Python Environment

Use the Anaconda `App` environment for local vBook development.

```powershell
conda run -n App python --version
conda run -n App python -m vbook_client --version
conda run -n App vbook --version
```

Current verified environment:

- Python: `3.13.12`
- `vbook`: editable install from `E:\projects\my_app\vbook`
- `vtext`: editable install from `E:\projects\my_app\vtext`
- `ffmpeg`: `D:\ffmpeg\bin\ffmpeg.exe`

If the `vbook` console script points to an old module path, refresh the editable
install from the repository root:

```powershell
conda run -n App python -m pip install -e .
```

## Test Commands

Run the full vBook test suite:

```powershell
conda run -n App python -m unittest discover
```

Run the vault preview focused tests:

```powershell
conda run -n App python -m unittest tests.test_export.test_vault_preview tests.test_client.test_vault_preview_cli
```

## CLI Checks

Check vBook:

```powershell
conda run -n App python -m vbook_client check
conda run -n App vbook --version
```

Check vtext integration options:

```powershell
conda run -n App python -m vtext_client --help
```

The vtext CLI should expose:

```text
--bundle [legacy|vbook]
```

Check the Qwen Vision adapter tool:

```powershell
conda run -n App python tools\vision_qwen_adapter.py --help
```

## Preview Command

After a vBook lesson output exists, generate a preview-only vault enhancement
package:

```powershell
conda run -n App python -m vbook_client vault-preview `
  --vault-note "<existing-vault-note.md>" `
  --lesson-output "<vbook-lesson-output-dir>" `
  --output "outputs\vault-enhancement-preview\<series>\<lesson>"
```

This command must write only to the preview output directory. It must not modify
`F:\vault`.
