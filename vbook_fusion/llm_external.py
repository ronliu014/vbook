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
