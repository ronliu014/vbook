from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_FORBIDDEN_OUTPUT_ROOTS = (
    "f:/vault/20_learning/vbook",
    "f:/vault/20_learning/vtext",
)


@dataclass(frozen=True)
class GateIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class MaturityGateReport:
    experiment_root: str
    route: str
    round_id: str
    status: str
    lesson_count: int
    selected_route: str
    preflight_status: str
    min_user_preference: int | None
    issues: list[GateIssue]

    @property
    def ok(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "kind": "experiment_maturity_gate",
            "experiment_root": self.experiment_root,
            "route": self.route,
            "round_id": self.round_id,
            "status": self.status,
            "ok": self.ok,
            "lesson_count": self.lesson_count,
            "selected_route": self.selected_route,
            "preflight_status": self.preflight_status,
            "min_user_preference": self.min_user_preference,
            "issues": [
                {
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate whether an experiment route passes the maturity gate."
    )
    parser.add_argument("--experiment-root", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    args = parser.parse_args(argv)

    report = evaluate_maturity_gate(
        experiment_root=args.experiment_root,
        route=args.route,
        round_id=args.round_id,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
    )
    if not args.json_output and not args.markdown_output:
        print(render_markdown_report(report))
    return 0 if report.ok else 1


def evaluate_maturity_gate(
    *,
    experiment_root: Path | str,
    route: str,
    round_id: str,
    json_output: Path | str | None = None,
    markdown_output: Path | str | None = None,
) -> MaturityGateReport:
    root = Path(experiment_root)
    issues: list[GateIssue] = []
    lesson_count = _route_lesson_count(root, route)
    if lesson_count < 3:
        issues.append(
            GateIssue(
                severity="blocked",
                code="insufficient_rendered_lessons",
                message=f"Expected at least 3 rendered lessons, found {lesson_count}.",
            )
        )

    manifest = _read_json_object(root / "reviews" / round_id / "review-manifest.json")
    selected_route = ""
    preflight_status = "missing"
    if manifest is None:
        issues.append(
            GateIssue(
                severity="blocked",
                code="missing_review_manifest",
                message=f"Missing review manifest for round {round_id}.",
            )
        )
    else:
        selected_route = str(manifest.get("selected_route") or "")
        if manifest.get("review_status") != "winner_selected":
            issues.append(
                GateIssue(
                    severity="blocked",
                    code="review_not_finalized",
                    message="Review round is not finalized with winner_selected.",
                )
            )
        if selected_route != route:
            issues.append(
                GateIssue(
                    severity="fail",
                    code="selected_route_mismatch",
                    message=f"Selected route is {selected_route or '<empty>'}, expected {route}.",
                )
            )
        preflight_status = _preflight_status_for_route(manifest, route)
        if preflight_status != "pass":
            issues.append(
                GateIssue(
                    severity="blocked",
                    code="preflight_not_passed",
                    message=f"Expected preflight pass, got {preflight_status}.",
                )
            )
        issues.extend(_candidate_path_issues(manifest, root, route))

    rows = _review_rows_for_route(root / "reviews" / round_id / "review-sheet.csv", route)
    min_preference = _min_int(row.get("user_preference") for row in rows)
    if not rows:
        issues.append(
            GateIssue(
                severity="blocked",
                code="missing_review_sheet_route",
                message=f"No review sheet rows found for route {route}.",
            )
        )
    elif min_preference is None or min_preference < 3:
        issues.append(
            GateIssue(
                severity="fail",
                code="user_preference_below_threshold",
                message=f"Expected route user_preference >= 3, got {min_preference}.",
            )
        )

    status = _status_from_issues(issues)
    report = MaturityGateReport(
        experiment_root=str(root),
        route=route,
        round_id=round_id,
        status=status,
        lesson_count=lesson_count,
        selected_route=selected_route,
        preflight_status=preflight_status,
        min_user_preference=min_preference,
        issues=issues,
    )
    if json_output is not None:
        write_json_report(report, _report_output_path(root, json_output))
    if markdown_output is not None:
        write_markdown_report(report, _report_output_path(root, markdown_output))
    return report


def write_json_report(report: MaturityGateReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def write_markdown_report(report: MaturityGateReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(report), encoding="utf-8")
    return path


def render_markdown_report(report: MaturityGateReport) -> str:
    lines = [
        f"# Maturity Gate: {report.route}",
        "",
        f"- Experiment: `{report.experiment_root}`",
        f"- Review round: `{report.round_id}`",
        f"- Status: `{report.status}`",
        f"- Rendered lessons: {report.lesson_count}",
        f"- Selected route: `{report.selected_route}`",
        f"- Preflight: `{report.preflight_status}`",
        f"- Minimum user preference: {report.min_user_preference if report.min_user_preference is not None else ''}",
        "",
        "## Issues",
        "",
    ]
    if not report.issues:
        lines.append("No issues found.")
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["| Severity | Code | Message |", "| --- | --- | --- |"])
    for issue in report.issues:
        lines.append(
            f"| {_escape(issue.severity)} | {_escape(issue.code)} | {_escape(issue.message)} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _route_lesson_count(root: Path, route: str) -> int:
    route_dir = root / "renders" / route
    if not route_dir.is_dir():
        return 0
    lesson_dirs = {
        lesson_dir
        for variant_dir in route_dir.iterdir()
        if variant_dir.is_dir()
        for lesson_dir in variant_dir.iterdir()
        if lesson_dir.is_dir() and _has_markdown_preview(lesson_dir)
    }
    return len(lesson_dirs)


def _has_markdown_preview(path: Path) -> bool:
    return any(child.is_file() and child.suffix.lower() == ".md" for child in path.iterdir())


def _preflight_status_for_route(manifest: dict[str, Any], route: str) -> str:
    statuses = manifest.get("preflight_status_by_route")
    if isinstance(statuses, dict) and isinstance(statuses.get(route), str):
        return str(statuses[route])
    candidate_statuses = {
        str(item.get("preflight_status"))
        for item in manifest.get("candidates", [])
        if isinstance(item, dict) and item.get("route") == route and item.get("preflight_status")
    }
    if not candidate_statuses:
        return "missing"
    if candidate_statuses == {"pass"}:
        return "pass"
    return ",".join(sorted(candidate_statuses))


def _candidate_path_issues(
    manifest: dict[str, Any],
    experiment_root: Path,
    route: str,
) -> list[GateIssue]:
    issues = []
    for item in manifest.get("candidates", []):
        if not isinstance(item, dict) or item.get("route") != route:
            continue
        preview_path = str(item.get("preview_path") or "")
        normalized = preview_path.replace("\\", "/").lower()
        if any(normalized.startswith(root) for root in _FORBIDDEN_OUTPUT_ROOTS):
            issues.append(
                GateIssue(
                    severity="fail",
                    code="unsafe_vault_preview_path",
                    message=f"Preview path points to vault root: {preview_path}",
                )
            )
        try:
            Path(preview_path).resolve().relative_to(experiment_root.resolve())
        except (OSError, ValueError):
            issues.append(
                GateIssue(
                    severity="fail",
                    code="preview_path_outside_experiment",
                    message=f"Preview path is outside experiment root: {preview_path}",
                )
            )
    return issues


def _review_rows_for_route(path: Path, route: str) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("route") == route]


def _min_int(values: Any) -> int | None:
    parsed = []
    for value in values:
        try:
            parsed.append(int(str(value).strip()))
        except ValueError:
            continue
    return min(parsed) if parsed else None


def _status_from_issues(issues: list[GateIssue]) -> str:
    severities = {issue.severity for issue in issues}
    if "blocked" in severities:
        return "blocked"
    if "fail" in severities:
        return "fail"
    return "pass"


def _report_output_path(experiment_root: Path, path: Path | str) -> Path:
    output = Path(path).resolve()
    comparisons = (experiment_root / "comparisons").resolve()
    try:
        output.relative_to(comparisons)
    except ValueError:
        raise ValueError(f"maturity gate reports must be under comparisons: {path}")
    return output


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
