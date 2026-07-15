from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_FORBIDDEN_OUTPUT_ROOTS = (
    "f:/vault/20_learning/vbook",
    "f:/vault/20_learning/vtext",
)


@dataclass(frozen=True)
class PreflightIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class PreflightReport:
    root: str
    note_count: int
    manifest_count: int
    image_link_count: int
    missing_image_count: int
    issues: list[PreflightIssue]

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def ok(self) -> bool:
        return self.error_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "ok": self.ok,
            "note_count": self.note_count,
            "manifest_count": self.manifest_count,
            "image_link_count": self.image_link_count,
            "missing_image_count": self.missing_image_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [
                {
                    "severity": issue.severity,
                    "code": issue.code,
                    "path": issue.path,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preflight-check vtext-first vault-enhance preview outputs."
    )
    parser.add_argument("--root", required=True, help="Preview root or note file to scan.")
    parser.add_argument("--json-output", help="Optional JSON report path.")
    parser.add_argument("--markdown-output", help="Optional Markdown report path.")
    args = parser.parse_args(argv)

    report = run_preflight(args.root)
    if args.json_output:
        write_json_report(report, args.json_output)
    if args.markdown_output:
        write_markdown_report(report, args.markdown_output)
    if not args.json_output and not args.markdown_output:
        print(render_markdown_report(report))
    return 0 if report.ok else 1


def run_preflight(root: Path | str) -> PreflightReport:
    root_path = Path(root)
    notes = _find_markdown_notes(root_path)
    issues: list[PreflightIssue] = []
    image_link_count = 0
    missing_image_count = 0
    manifest_paths: set[Path] = set()

    for note in notes:
        markdown = note.read_text(encoding="utf-8")
        image_results = _check_markdown_images(note, markdown)
        image_link_count += image_results[0]
        missing_image_count += image_results[1]
        issues.extend(image_results[2])
        issues.extend(_check_markdown_for_error_placeholder(note, markdown))

        manifest = _manifest_for_note(note)
        if manifest is None:
            issues.append(
                PreflightIssue(
                    severity="error",
                    code="missing_manifest",
                    path=str(note),
                    message="No sibling manifest.json or <note>.manifest.json was found.",
                )
            )
            continue
        manifest_paths.add(manifest)
        issues.extend(_check_manifest(note=note, manifest_path=manifest))

    return PreflightReport(
        root=str(root_path),
        note_count=len(notes),
        manifest_count=len(manifest_paths),
        image_link_count=image_link_count,
        missing_image_count=missing_image_count,
        issues=issues,
    )


def write_json_report(report: PreflightReport, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def write_markdown_report(report: PreflightReport, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown_report(report), encoding="utf-8")
    return target


def render_markdown_report(report: PreflightReport) -> str:
    lines = [
        "# vtext-first 预检报告",
        "",
        f"- 根目录：`{report.root}`",
        f"- 状态：{'PASS' if report.ok else 'FAIL'}",
        f"- 笔记数量：{report.note_count}",
        f"- Manifest 数量：{report.manifest_count}",
        f"- 图片链接数量：{report.image_link_count}",
        f"- 缺失图片数量：{report.missing_image_count}",
        f"- 错误数量：{report.error_count}",
        f"- 警告数量：{report.warning_count}",
        "",
        "## Issues",
        "",
    ]
    if not report.issues:
        lines.append("No issues found.")
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
    for issue in report.issues:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_table_cell(issue.severity),
                    _escape_table_cell(issue.code),
                    _escape_table_cell(issue.path),
                    _escape_table_cell(issue.message),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _find_markdown_notes(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() == ".md" else []
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if not _is_generated_report(path) and "assets" not in path.parts
    )


def _is_generated_report(path: Path) -> bool:
    normalized = path.name.lower()
    return normalized in {
        "preflight.md",
        "preflight-report.md",
        "vtext-first-preflight.md",
    }


def _check_markdown_images(
    note: Path,
    markdown: str,
) -> tuple[int, int, list[PreflightIssue]]:
    issues: list[PreflightIssue] = []
    link_count = 0
    missing_count = 0
    for match in _IMAGE_LINK_RE.finditer(markdown):
        raw_target = match.group(1).strip()
        target = _strip_optional_title(raw_target)
        if _is_external_or_anchor_link(target):
            continue
        link_count += 1
        image_path = _resolve_markdown_link(note, target)
        if not image_path.is_file():
            missing_count += 1
            issues.append(
                PreflightIssue(
                    severity="error",
                    code="missing_markdown_image",
                    path=str(note),
                    message=f"Image link does not resolve: {target}",
                )
            )
    return link_count, missing_count, issues


def _check_markdown_for_error_placeholder(
    note: Path,
    markdown: str,
) -> list[PreflightIssue]:
    text = markdown.lower()
    has_qwen_error = "qwen_service" in text and (
        "status=error" in text or '"status": "error"' in text or "504" in text
    )
    if not has_qwen_error:
        return []
    return [
        PreflightIssue(
            severity="error",
            code="qwen_error_placeholder",
            path=str(note),
            message="Markdown appears to include a Qwen error/504 placeholder.",
        )
    ]


def _manifest_for_note(note: Path) -> Path | None:
    candidates = [note.with_suffix(".manifest.json"), note.parent / "manifest.json"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _check_manifest(note: Path, manifest_path: Path) -> list[PreflightIssue]:
    issues: list[PreflightIssue] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [
            PreflightIssue(
                severity="error",
                code="invalid_manifest_json",
                path=str(manifest_path),
                message=str(exc),
            )
        ]
    if not isinstance(manifest, dict):
        return [
            PreflightIssue(
                severity="error",
                code="invalid_manifest_shape",
                path=str(manifest_path),
                message="Manifest root must be a JSON object.",
            )
        ]

    if manifest.get("text_source") != "vtext":
        issues.append(
            PreflightIssue(
                severity="warning",
                code="unexpected_text_source",
                path=str(manifest_path),
                message="Expected manifest.text_source to be 'vtext'.",
            )
        )
    safety = manifest.get("safety")
    if not isinstance(safety, dict) or safety.get("source_vtext") != "read_only":
        issues.append(
            PreflightIssue(
                severity="warning",
                code="missing_source_vtext_read_only",
                path=str(manifest_path),
                message="Expected manifest.safety.source_vtext to be 'read_only'.",
            )
        )
    if "inserted_image_count" not in manifest:
        issues.append(
            PreflightIssue(
                severity="warning",
                code="missing_inserted_image_count",
                path=str(manifest_path),
                message="Expected inserted_image_count for review comparison.",
            )
        )

    issues.extend(_check_unsafe_output_paths(note, manifest_path, manifest))
    issues.extend(_check_manifest_for_error_placeholders(manifest_path, manifest))
    return issues


def _check_unsafe_output_paths(
    note: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> list[PreflightIssue]:
    issues = []
    candidate_values = [str(note)]
    for key in ("output_note", "note_path", "enhancement_md"):
        value = manifest.get(key)
        if isinstance(value, str):
            candidate_values.append(value)
    outputs = manifest.get("outputs")
    if isinstance(outputs, dict):
        for key in ("enhancement_md", "note", "output_note"):
            value = outputs.get(key)
            if isinstance(value, str):
                candidate_values.append(value)

    for value in candidate_values:
        if _is_forbidden_output_path(value):
            issues.append(
                PreflightIssue(
                    severity="error",
                    code="unsafe_vault_output",
                    path=str(manifest_path),
                    message=f"Experiment output points to vault publication root: {value}",
                )
            )
    return issues


def _check_manifest_for_error_placeholders(
    manifest_path: Path,
    manifest: dict[str, Any],
) -> list[PreflightIssue]:
    issues = []
    for key_path, value in _walk_json(manifest):
        if not isinstance(value, dict):
            continue
        if value.get("status") != "error":
            continue
        joined_path = ".".join(key_path).lower()
        if "skipped" in joined_path:
            continue
        if "qwen" in joined_path or "qwen" in json.dumps(value, ensure_ascii=False):
            issues.append(
                PreflightIssue(
                    severity="error",
                    code="qwen_error_placeholder",
                    path=str(manifest_path),
                    message=f"Manifest includes inserted Qwen error evidence at {joined_path}.",
                )
            )
    return issues


def _walk_json(value: Any, key_path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    items = [(key_path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(_walk_json(child, key_path + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_walk_json(child, key_path + (str(index),)))
    return items


def _strip_optional_title(target: str) -> str:
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    if " " not in target:
        return target
    return target.split(" ", 1)[0]


def _is_external_or_anchor_link(target: str) -> bool:
    if target.startswith("#"):
        return True
    parsed = urlparse(target)
    return bool(parsed.scheme and parsed.scheme.lower() not in {"", "file"})


def _resolve_markdown_link(note: Path, target: str) -> Path:
    decoded = unquote(target)
    parsed = urlparse(decoded)
    if parsed.scheme.lower() == "file":
        return Path(parsed.path)
    path = Path(decoded)
    if path.is_absolute():
        return path
    return note.parent / path


def _is_forbidden_output_path(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    return any(normalized.startswith(root) for root in _FORBIDDEN_OUTPUT_ROOTS)


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
