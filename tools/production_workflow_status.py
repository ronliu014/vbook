"""Inspect vBook production workflow state without changing production data."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vbook_vision.qwen_contract import (
    QWEN_RESULT_DEGRADED,
    QWEN_RESULT_ERROR,
    qwen_result_status,
)


SCHEMA_VERSION = "1"
REPORT_KIND = "vbook_production_workflow_status"
STAGE_ORDER = ("frame_extract", "vtext", "lesson_output", "delivery_shape")
TERMINAL_RUN_STATES = {"completed", "dry_run", "failed", "paused", "stopped"}
ACTIVE_MANIFEST_STATES = {"running"}
SRT_TIMESTAMP_RE = re.compile(
    r"\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}"
)


class WorkflowStatusError(ValueError):
    """Raised when the requested workflow status cannot be loaded."""


def main(argv: list[str] | None = None) -> int:
    _configure_console_encoding()
    parser = argparse.ArgumentParser(
        prog=r".\vstatus",
        description=(
            "Show a read-only vBook production workflow overview or drill into a "
            "run, task, lesson, stage, or wave."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Quick commands:\n"
            "  .\\vstatus                         overview\n"
            "  .\\vstatus watch [seconds]         refresh every 30s by default\n"
            "  .\\vstatus lesson <name>           inspect one lesson pipeline\n"
            "  .\\vstatus run <run-id>            inspect one run\n"
            "  .\\vstatus task <task-id>          inspect task matches\n"
            "  .\\vstatus wave <stage> <number>   inspect one stage wave\n"
            "  .\\vstatus json [output-file]      emit JSON\n"
            "  .\\vstatus check                   strict gate check\n"
            "\nShort aliases: w, l, r, t, j. Long --options remain supported."
        ),
    )
    parser.add_argument(
        "--runtime-plan",
        help=(
            "runtime-plan.json to inspect. By default the newest plan under "
            "outputs/production-workflow is selected."
        ),
    )
    parser.add_argument(
        "--run-root",
        help="Override the run root recorded by the runtime plan.",
    )
    parser.add_argument(
        "--detail",
        help="Run ID, task ID, exact lesson key, or lesson-name substring to inspect.",
    )
    parser.add_argument("--stage", choices=STAGE_ORDER)
    parser.add_argument("--wave", type=int, help="1-based wave index; requires --stage.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Console and --output representation.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Maximum rows shown in detailed text sections.",
    )
    parser.add_argument(
        "--stale-seconds",
        type=float,
        default=300.0,
        help="Age after which scheduler status or an active run heartbeat is stale.",
    )
    parser.add_argument(
        "--watch-seconds",
        type=float,
        default=0.0,
        help="Refresh continuously at this interval; zero prints one snapshot.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Stop watch mode after N snapshots; zero means until interrupted.",
    )
    parser.add_argument(
        "--output",
        help="Optional snapshot file. It is atomically replaced on every refresh.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 when the workflow is blocked, paused, or stale.",
    )
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    try:
        expanded_argv = _expand_short_command(raw_argv)
    except WorkflowStatusError as exc:
        parser.error(str(exc))
    args = parser.parse_args(expanded_argv)

    if args.wave is not None and args.stage is None:
        parser.error("--wave requires --stage")
    if args.wave is not None and args.wave < 1:
        parser.error("--wave must be at least 1")
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.stale_seconds <= 0:
        parser.error("--stale-seconds must be greater than zero")
    if args.watch_seconds < 0:
        parser.error("--watch-seconds cannot be negative")
    if args.iterations < 0:
        parser.error("--iterations cannot be negative")
    if args.iterations > 1 and args.watch_seconds <= 0:
        parser.error("--iterations greater than 1 requires --watch-seconds")

    project_root = PROJECT_ROOT
    snapshot_count = 0
    last_level = "READY"
    try:
        while True:
            report = collect_workflow_status(
                project_root=project_root,
                runtime_plan_path=args.runtime_plan,
                run_root=args.run_root,
                stale_seconds=args.stale_seconds,
                detail=args.detail,
                stage=args.stage,
                wave=args.wave,
                limit=args.limit,
            )
            rendered = (
                json.dumps(report, ensure_ascii=False, indent=2) + "\n"
                if args.format == "json"
                else render_text(report, limit=args.limit)
            )
            if args.watch_seconds > 0 and snapshot_count > 0 and sys.stdout.isatty():
                print("\033[2J\033[H", end="")
            print(rendered, end="")
            if args.output:
                _atomic_write_text(_resolve_path(args.output, project_root), rendered)

            snapshot_count += 1
            last_level = str(report["health"]["status"])
            if args.watch_seconds <= 0:
                break
            if args.iterations and snapshot_count >= args.iterations:
                break
            time.sleep(args.watch_seconds)
    except KeyboardInterrupt:
        return 130
    except (OSError, json.JSONDecodeError, WorkflowStatusError) as exc:
        print(f"production workflow status error: {exc}", file=sys.stderr)
        return 1

    if args.strict and last_level in {"BLOCKED", "PAUSED", "STALE"}:
        return 2
    return 0


def collect_workflow_status(
    *,
    project_root: Path | str,
    runtime_plan_path: Path | str | None = None,
    run_root: Path | str | None = None,
    stale_seconds: float = 300.0,
    detail: str | None = None,
    stage: str | None = None,
    wave: int | None = None,
    limit: int = 12,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    generated_at = now or datetime.now(timezone.utc)
    runtime_path = (
        _resolve_path(runtime_plan_path, root)
        if runtime_plan_path
        else discover_runtime_plan(root)
    )
    runtime = _read_json_object(runtime_path, "runtime plan")
    if runtime.get("kind") != "vbook_production_workflow_plan":
        raise WorkflowStatusError(
            f"runtime plan kind is not vbook_production_workflow_plan: {runtime_path}"
        )

    configured_run_root = run_root or runtime.get("run_root") or "outputs/production-runs"
    runs_path = _resolve_path(configured_run_root, root)
    scan_issues: list[dict[str, Any]] = []
    runs = _scan_runs(
        runs_path,
        now=generated_at,
        stale_seconds=stale_seconds,
        issues=scan_issues,
    )
    workflow_dir = runtime_path.parent
    controls = _collect_controls(workflow_dir, runs)
    scheduler = _collect_scheduler_status(
        workflow_dir,
        now=generated_at,
        stale_seconds=stale_seconds,
        issues=scan_issues,
    )
    quality = _collect_quality(runtime, root, scan_issues)
    run_summary = _summarize_runs(runs)
    health = _build_health(
        runtime=runtime,
        runs=runs,
        controls=controls,
        scheduler=scheduler,
        issues=scan_issues,
    )
    selected_detail = _resolve_detail(
        query=detail,
        stage=stage,
        wave=wave,
        runtime=runtime,
        runs=runs,
        project_root=root,
        limit=limit,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": REPORT_KIND,
        "generated_at": generated_at.isoformat(),
        "health": health,
        "workflow": {
            "name": workflow_dir.name,
            "runtime_plan": str(runtime_path),
            "runtime_created_at": runtime.get("created_at"),
            "runtime_age_seconds": _age_seconds(runtime.get("created_at"), generated_at),
            "reconciled": bool(runtime.get("reconciled")),
            "source_plan": runtime.get("source_plan") or str(runtime_path),
            "run_root": str(runs_path),
            "lesson_count": int(runtime.get("lesson_count") or 0),
        },
        "plan": {
            "bundle_counts": _integer_mapping(runtime.get("bundle_counts")),
            "state_counts": _integer_mapping(runtime.get("state_counts")),
            "task_counts": _integer_mapping(runtime.get("task_counts")),
            "workstreams": _workstream_summary(runtime.get("workstreams")),
            "capacity": runtime.get("capacity") if isinstance(runtime.get("capacity"), dict) else {},
            "pipeline": _pipeline_summary(runtime),
        },
        "scheduler": scheduler,
        "controls": controls,
        "runs": {
            "total": len(runs),
            "by_stage": run_summary,
            "active": [_public_run(run) for run in runs if run["recorded_active"]],
            "terminal_failures": [
                _public_run(run) for run in runs if run["terminal_failure"]
            ],
            "recovered_failures": [
                _public_run(run)
                for run in runs
                if run["historical_terminal_failure"] and run["recovered_by"]
            ],
        },
        "quality": quality,
        "issues": scan_issues,
        "detail": selected_detail,
    }


def _expand_short_command(argv: list[str]) -> list[str]:
    if not argv or argv[0].startswith("-"):
        return argv
    command = argv[0].casefold()
    remainder = argv[1:]
    if command in {"show", "status", "s"}:
        return remainder
    if command in {"watch", "w"}:
        seconds = "30"
        if remainder and not remainder[0].startswith("-"):
            seconds = remainder[0]
            remainder = remainder[1:]
        return ["--watch-seconds", seconds, *remainder]
    if command in {"lesson", "l", "run", "r", "task", "t", "detail", "d"}:
        if not remainder or remainder[0].startswith("-"):
            raise WorkflowStatusError(f"{command} requires a name or ID")
        return ["--detail", remainder[0], *remainder[1:]]
    if command == "wave":
        if len(remainder) < 2 or any(item.startswith("-") for item in remainder[:2]):
            raise WorkflowStatusError("wave requires <stage> <number>")
        return ["--stage", remainder[0], "--wave", remainder[1], *remainder[2:]]
    if command in {"json", "j"}:
        expanded = ["--format", "json"]
        if remainder and not remainder[0].startswith("-"):
            expanded.extend(["--output", remainder[0]])
            remainder = remainder[1:]
        return [*expanded, *remainder]
    if command in {"check", "c"}:
        return ["--strict", *remainder]
    if command in {"help", "h", "?"}:
        return ["--help", *remainder]
    raise WorkflowStatusError(
        f"unknown quick command {argv[0]!r}; use help or a long --option"
    )


def discover_runtime_plan(project_root: Path | str) -> Path:
    root = Path(project_root).resolve()
    workflow_root = root / "outputs" / "production-workflow"
    candidates = list(workflow_root.glob("*/runtime-plan.json"))
    if not candidates:
        raise WorkflowStatusError(
            f"no runtime-plan.json found under {workflow_root}"
        )

    def candidate_key(path: Path) -> tuple[float, float, str]:
        created = 0.0
        try:
            payload = _read_json_object(path, "runtime plan")
            timestamp = _parse_datetime(payload.get("created_at"))
            if timestamp:
                created = timestamp.timestamp()
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        return created, path.stat().st_mtime, str(path)

    return max(candidates, key=candidate_key).resolve()


def render_text(report: dict[str, Any], *, limit: int = 12) -> str:
    health = report["health"]
    workflow = report["workflow"]
    plan = report["plan"]
    lines = [
        "vBook Production Workflow Status",
        "=" * 32,
        f"Status: {health['status']}",
        f"Generated: {report['generated_at']}",
        f"Workflow: {workflow['name']}",
        f"Runtime plan: {workflow['runtime_plan']}",
        f"Run root: {workflow['run_root']}",
        f"Snapshot: reconciled={str(workflow['reconciled']).lower()}, "
        f"age={_format_age(workflow.get('runtime_age_seconds'))}",
        "",
    ]
    if health["reasons"]:
        lines.extend(["Current Gates", "-------------"])
        for reason in health["reasons"][:limit]:
            lines.append(
                f"[{str(reason['severity']).upper()}] {reason['message']}"
            )
            if reason.get("path"):
                lines.append(f"  {reason['path']}")
        lines.append("")

    bundles = plan["bundle_counts"]
    lines.extend(
        [
            "Plan Snapshot",
            "-------------",
            f"Lessons: {workflow['lesson_count']}",
            "Bundles: " + _join_counts(bundles),
            "States: " + _join_counts(plan["state_counts"]),
            "Tasks: " + _join_counts(plan["task_counts"]),
            "",
            "Pipeline Progress",
            "-----------------",
        ]
    )
    pipeline_rows = [
        ["vtext timestamped bundles", plan["pipeline"]["vtext_bundles"]],
        ["frame extraction bundles", plan["pipeline"]["frame_bundles"]],
        ["usable vision + fusion notes", plan["pipeline"]["usable_lesson_outputs"]],
        ["delivery ready", plan["pipeline"]["delivery_ready"]],
        ["delivery accepted", plan["pipeline"]["delivery_accepted"]],
        ["published", plan["pipeline"]["published"]],
    ]
    lines.extend(_render_table(["Milestone", "Count"], pipeline_rows))
    lines.extend(
        [
            "",
            "Workstreams",
            "-----------",
        ]
    )
    workstream_rows = []
    for name in STAGE_ORDER:
        stream = plan["workstreams"].get(name)
        if not stream:
            continue
        workstream_rows.append(
            [
                name,
                stream["ready_count"],
                stream["wave_count"],
                stream["wave_size"],
            ]
        )
    lines.extend(_render_table(["Stage", "Items*", "Waves", "Wave size"], workstream_rows))
    lines.append("* Items is the stable wave universe; remaining work is shown in Tasks.")
    lines.extend(["", "Run History", "-----------"])
    run_rows = []
    for name in STAGE_ORDER:
        item = report["runs"]["by_stage"].get(name)
        if not item:
            continue
        run_rows.append(
            [
                name,
                item["run_count"],
                item["completed"],
                item["recovered"],
                item["failed"],
                item["paused"],
                item["recorded_active"],
                item.get("latest_run_id") or "-",
            ]
        )
    lines.extend(
        _render_table(
            [
                "Stage",
                "Runs",
                "Done",
                "Recovered",
                "Failed",
                "Paused",
                "Active*",
                "Latest",
            ],
            run_rows,
        )
    )
    lines.append("* Active is recorded workflow state, not an OS process check.")

    quality = report["quality"]
    lines.extend(
        [
            "",
            "Quality Gates",
            "-------------",
            f"Rejected bundles: {quality['rejected_bundle_count']}",
            f"Rejected degraded frames: {quality['degraded_frame_count']}",
            f"Rejected error frames: {quality['error_frame_count']}",
        ]
    )
    for bundle in quality["rejected_bundles"][:limit]:
        frame_ids = ", ".join(frame["frame_id"] for frame in bundle["frames"])
        suffix = f"; frames={frame_ids}" if frame_ids else ""
        lines.append(
            f"- wave {bundle.get('wave_index') or '?'} {bundle.get('run_id') or '?'}: "
            f"{bundle['reason']}{suffix}"
        )

    controls = report["controls"]
    lines.extend(
        [
            "",
            "Controls",
            "--------",
            f"Scheduler pause: {_yes_no(controls['scheduler']['pause_requested'])}",
            f"Scheduler stop: {_yes_no(controls['scheduler']['stop_requested'])}",
            f"Run pauses: {len(controls['run_pause_requests'])}",
            f"Run stops: {len(controls['run_stop_requests'])}",
            f"Audit markers: {len(controls['audit_markers'])}",
        ]
    )
    for item in controls["run_pause_requests"][:limit]:
        lines.append(f"- pause {item['run_id']}: {item['path']}")

    scheduler = report["scheduler"]
    lines.extend(["", "Scheduler Record", "----------------"])
    if scheduler["exists"]:
        lines.extend(
            [
                f"Recorded status: {scheduler.get('status') or '-'}",
                f"Updated: {scheduler.get('updated_at') or '-'} "
                f"(age {_format_age(scheduler.get('age_seconds'))})",
                f"Fresh: {_yes_no(not scheduler['stale'])}",
                f"Execute mode: {_yes_no(bool(scheduler.get('execute')))}",
            ]
        )
        if scheduler.get("latest_actions"):
            for action in scheduler["latest_actions"][:limit]:
                lines.append(
                    f"- {action.get('action')} {action.get('stage')} "
                    f"wave={action.get('wave_index')} run={action.get('run_id')}"
                )
    else:
        lines.append("No scheduler-status.json exists.")

    if report.get("detail"):
        lines.extend(["", *_render_detail(report["detail"], limit=limit)])
    else:
        lines.extend(
            [
                "",
                "Drill Down",
                "----------",
                "Use lesson <name>, run <id>, task <id>, or wave <stage> <N>.",
                "Use json for automation, watch [seconds] for refresh, or help for all options.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _scan_runs(
    run_root: Path,
    *,
    now: datetime,
    stale_seconds: float,
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not run_root.is_dir():
        issues.append(
            _issue("warning", "missing_run_root", f"Run root does not exist: {run_root}", run_root)
        )
        return []
    records = []
    for manifest_path in sorted(run_root.glob("*/run.manifest.json")):
        try:
            manifest = _read_json_object(manifest_path, "run manifest")
            summary_path = manifest_path.parent / "summary.json"
            summary = (
                _read_json_object(summary_path, "run summary")
                if summary_path.is_file()
                else {}
            )
            last_event = _read_last_json_line(manifest_path.parent / "events.jsonl")
            summary_status = _optional_text(summary.get("status"))
            manifest_status = _optional_text(manifest.get("status")) or "unknown"
            status = summary_status or manifest_status
            tasks = summary.get("tasks") if isinstance(summary.get("tasks"), list) else []
            counts = _integer_mapping(summary.get("counts"))
            task_count = int(summary.get("task_count") or manifest.get("task_count") or len(tasks))
            succeeded = int(counts.get("succeeded") or _task_status_count(tasks, "succeeded"))
            failed = int(counts.get("failed") or _task_status_count(tasks, "failed"))
            recorded_active = (
                manifest_status in ACTIVE_MANIFEST_STATES
                and summary_status not in TERMINAL_RUN_STATES
            )
            last_timestamp = last_event.get("timestamp") or manifest.get("updated_at")
            age = _age_seconds(last_timestamp, now)
            stale = bool(recorded_active and age is not None and age > stale_seconds)
            successful = (
                summary_status == "completed"
                and task_count > 0
                and succeeded == task_count
                and failed == 0
            )
            terminal_failure = bool(
                summary_status in TERMINAL_RUN_STATES
                and summary_status != "dry_run"
                and not successful
            )
            recovery_for = _optional_text(
                summary.get("recovery_for") or manifest.get("recovery_for")
            )
            records.append(
                {
                    "run_id": str(manifest.get("run_id") or manifest_path.parent.name),
                    "stage": str(manifest.get("stage") or summary.get("stage") or "unknown"),
                    "wave_index": int(manifest.get("wave_index") or summary.get("wave_index") or 0),
                    "status": status,
                    "manifest_status": manifest_status,
                    "summary_status": summary_status,
                    "mode": manifest.get("mode"),
                    "task_count": task_count,
                    "counts": counts,
                    "succeeded_count": succeeded,
                    "failed_count": failed,
                    "resume_skipped_count": int(summary.get("resume_skipped_count") or 0),
                    "started_at": manifest.get("started_at") or summary.get("started_at"),
                    "updated_at": manifest.get("updated_at") or summary.get("finished_at"),
                    "finished_at": summary.get("finished_at") or manifest.get("finished_at"),
                    "last_event": last_event,
                    "last_event_age_seconds": age,
                    "recorded_active": recorded_active,
                    "stale": stale,
                    "successful": successful,
                    "terminal_failure": terminal_failure,
                    "historical_terminal_failure": terminal_failure,
                    "recovery": bool(
                        summary.get("recovery")
                        or manifest.get("recovery")
                        or recovery_for
                    ),
                    "recovery_for": recovery_for,
                    "recovered_by": [],
                    "run_dir": str(manifest_path.parent.resolve()),
                    "manifest": str(manifest_path.resolve()),
                    "summary": str(summary_path.resolve()) if summary_path.is_file() else None,
                    "tasks": tasks,
                }
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(
                _issue(
                    "warning",
                    "invalid_run_record",
                    f"Cannot inspect run record: {exc}",
                    manifest_path,
                )
            )
    records_by_id = {record["run_id"]: record for record in records}
    for recovery in records:
        target = records_by_id.get(recovery["recovery_for"])
        if (
            not recovery["successful"]
            or target is None
            or target["stage"] != recovery["stage"]
            or not target["historical_terminal_failure"]
        ):
            continue
        target["terminal_failure"] = False
        target["recovered_by"].append(recovery["run_id"])
    records.sort(key=lambda item: (_stage_rank(item["stage"]), item["wave_index"], item["run_id"]))
    return records


def _collect_controls(workflow_dir: Path, runs: list[dict[str, Any]]) -> dict[str, Any]:
    scheduler_dir = workflow_dir / "scheduler-control"
    scheduler_pause = scheduler_dir / "pause.request"
    scheduler_stop = scheduler_dir / "stop.request"
    run_pauses = []
    run_stops = []
    audit_markers = [str(path.resolve()) for path in sorted(scheduler_dir.glob("*.request.*"))]
    for run in runs:
        control_dir = Path(run["run_dir"]) / "control"
        pause = control_dir / "pause.request"
        stop = control_dir / "stop.request"
        if pause.exists():
            run_pauses.append({"run_id": run["run_id"], "path": str(pause.resolve())})
        if stop.exists():
            run_stops.append({"run_id": run["run_id"], "path": str(stop.resolve())})
        audit_markers.extend(
            str(path.resolve()) for path in sorted(control_dir.glob("*.request.*"))
        )
    return {
        "scheduler": {
            "directory": str(scheduler_dir.resolve()),
            "pause_requested": scheduler_pause.exists(),
            "pause_path": str(scheduler_pause.resolve()),
            "stop_requested": scheduler_stop.exists(),
            "stop_path": str(scheduler_stop.resolve()),
        },
        "run_pause_requests": run_pauses,
        "run_stop_requests": run_stops,
        "audit_markers": sorted(set(audit_markers)),
    }


def _collect_scheduler_status(
    workflow_dir: Path,
    *,
    now: datetime,
    stale_seconds: float,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    status_path = workflow_dir / "scheduler-status.json"
    events_path = workflow_dir / "scheduler-events.jsonl"
    if not status_path.is_file():
        return {
            "exists": False,
            "path": str(status_path.resolve()),
            "events": str(events_path.resolve()),
            "stale": False,
            "latest_actions": [],
            "last_event": _read_last_json_line(events_path),
        }
    try:
        payload = _read_json_object(status_path, "scheduler status")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(
            _issue("warning", "invalid_scheduler_status", str(exc), status_path)
        )
        return {
            "exists": True,
            "path": str(status_path.resolve()),
            "events": str(events_path.resolve()),
            "stale": True,
            "latest_actions": [],
            "last_event": _read_last_json_line(events_path),
            "error": str(exc),
        }
    age = _age_seconds(payload.get("updated_at"), now)
    return {
        "exists": True,
        "path": str(status_path.resolve()),
        "events": str(events_path.resolve()),
        "status": payload.get("status"),
        "updated_at": payload.get("updated_at"),
        "age_seconds": age,
        "stale": bool(age is not None and age > stale_seconds),
        "pid": payload.get("pid"),
        "execute": payload.get("execute"),
        "stages": payload.get("stages") if isinstance(payload.get("stages"), list) else [],
        "next_tick_at": payload.get("next_tick_at"),
        "recorded_bundle_counts": _integer_mapping(payload.get("bundle_counts")),
        "recorded_rejected_bundle_count": int(payload.get("rejected_bundle_count") or 0),
        "latest_actions": payload.get("actions") if isinstance(payload.get("actions"), list) else [],
        "last_event": _read_last_json_line(events_path),
    }


def _collect_quality(
    runtime: dict[str, Any],
    project_root: Path,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    rejected = runtime.get("rejected_bundles")
    rejected_items = rejected if isinstance(rejected, list) else []
    bundles = []
    degraded_count = 0
    error_count = 0
    for raw in rejected_items:
        if not isinstance(raw, dict):
            continue
        reason = str(raw.get("reason") or "reconciliation rejected bundle")
        summary_value = raw.get("summary")
        summary_path = _resolve_path(summary_value, project_root) if summary_value else None
        bundle = {
            "reason": reason,
            "summary": str(summary_path) if summary_path else None,
            "run_id": None,
            "wave_index": None,
            "lesson_keys": [],
            "frames": [],
        }
        if summary_path and summary_path.is_file():
            try:
                summary = _read_json_object(summary_path, "rejected run summary")
                bundle["run_id"] = summary.get("run_id")
                bundle["wave_index"] = summary.get("wave_index")
                tasks = summary.get("tasks") if isinstance(summary.get("tasks"), list) else []
                for task in tasks:
                    if not isinstance(task, dict):
                        continue
                    lesson_key = _optional_text(task.get("lesson_key"))
                    if lesson_key:
                        bundle["lesson_keys"].append(lesson_key)
                    artifact_value = task.get("artifact_dir")
                    if not artifact_value:
                        continue
                    artifact = _resolve_path(artifact_value, project_root)
                    vision = _inspect_vision_artifact(artifact)
                    for frame in vision["problem_frames"]:
                        record = dict(frame)
                        record["task_id"] = task.get("task_id")
                        record["artifact_dir"] = str(artifact)
                        record["analysis_path"] = vision.get("analysis_path")
                        bundle["frames"].append(record)
                        if frame["status"] == QWEN_RESULT_DEGRADED:
                            degraded_count += 1
                        if frame["status"] == QWEN_RESULT_ERROR:
                            error_count += 1
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                issues.append(
                    _issue(
                        "warning",
                        "invalid_rejected_bundle_evidence",
                        str(exc),
                        summary_path,
                    )
                )
        bundles.append(bundle)
    return {
        "rejected_bundle_count": int(runtime.get("rejected_bundle_count") or len(bundles)),
        "degraded_frame_count": degraded_count,
        "error_frame_count": error_count,
        "rejected_bundles": bundles,
    }


def _inspect_vision_artifact(artifact_dir: Path) -> dict[str, Any]:
    candidates = (
        artifact_dir / "vision" / "external" / "analysis.json",
        artifact_dir / "vision" / "analysis.json",
    )
    analysis_path = next((path for path in candidates if path.is_file()), None)
    if analysis_path is None:
        return {
            "exists": False,
            "analysis_path": str(candidates[-1]),
            "analysis_count": 0,
            "status_counts": {},
            "problem_frames": [],
        }
    payload = _read_json_object(analysis_path, "vision analysis")
    analyses = payload.get("analyses") if isinstance(payload.get("analyses"), list) else []
    status_counts: Counter[str] = Counter()
    problem_frames = []
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        status = qwen_result_status(analysis)
        status_counts[status] += 1
        if status not in {QWEN_RESULT_DEGRADED, QWEN_RESULT_ERROR}:
            continue
        observations = analysis.get("structured_observations")
        observations = observations if isinstance(observations, dict) else {}
        services = [
            service
            for key in ("qwen_service", "qwen_service_response")
            if isinstance((service := observations.get(key)), dict)
        ]
        warnings = _string_values(analysis.get("warnings"))
        for service in services:
            warnings.extend(_string_values(service.get("warnings")))
        request_id = next(
            (
                str(service["request_id"])
                for service in services
                if service.get("request_id")
            ),
            None,
        )
        error = next(
            (service.get("error") for service in services if service.get("error")),
            observations.get("service_error"),
        )
        problem_frames.append(
            {
                "frame_id": str(analysis.get("frame_id") or "unknown"),
                "status": status,
                "request_id": request_id,
                "warnings": sorted(set(warnings)),
                "degraded_reason": observations.get("degraded_reason"),
                "error": error,
            }
        )
    return {
        "exists": True,
        "analysis_path": str(analysis_path.resolve()),
        "analysis_count": len(analyses),
        "status_counts": dict(sorted(status_counts.items())),
        "declared_analysis_count": payload.get("analysis_count"),
        "declared_degraded_count": payload.get("degraded_count"),
        "declared_recovery_count": payload.get("recovery_count"),
        "problem_frames": problem_frames,
    }


def _summarize_runs(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for stage in STAGE_ORDER:
        selected = [run for run in runs if run["stage"] == stage]
        if not selected:
            continue
        statuses = Counter(str(run["status"]) for run in selected)
        latest = max(
            selected,
            key=lambda item: (
                _parse_datetime(item.get("updated_at")) or datetime.min.replace(tzinfo=timezone.utc),
                item["wave_index"],
            ),
        )
        result[stage] = {
            "run_count": len(selected),
            "completed": statuses.get("completed", 0),
            "failed": sum(1 for run in selected if run["terminal_failure"]),
            "recovered": sum(
                1
                for run in selected
                if run["historical_terminal_failure"] and run["recovered_by"]
            ),
            "paused": statuses.get("paused", 0),
            "stopped": statuses.get("stopped", 0),
            "dry_run": statuses.get("dry_run", 0),
            "recorded_active": sum(1 for run in selected if run["recorded_active"]),
            "status_counts": dict(sorted(statuses.items())),
            "latest_run_id": latest["run_id"],
            "latest_wave_index": latest["wave_index"],
            "latest_status": latest["status"],
            "latest_updated_at": latest.get("updated_at"),
        }
    return result


def _public_run(run: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in run.items() if key != "tasks"}


def _build_health(
    *,
    runtime: dict[str, Any],
    runs: list[dict[str, Any]],
    controls: dict[str, Any],
    scheduler: dict[str, Any],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    reasons: list[dict[str, Any]] = []
    rejected_count = int(runtime.get("rejected_bundle_count") or 0)
    if rejected_count:
        reasons.append(
            _issue(
                "error",
                "rejected_bundles",
                f"Reconciliation rejected {rejected_count} bundle(s).",
                runtime.get("source_plan"),
            )
        )
    failures = [run for run in runs if run["terminal_failure"]]
    if failures:
        reasons.append(
            _issue(
                "error",
                "terminal_run_failures",
                f"{len(failures)} terminal run(s) are not successful.",
                failures[-1]["run_dir"],
            )
        )
    stale_runs = [run for run in runs if run["stale"]]
    if stale_runs:
        reasons.append(
            _issue(
                "error",
                "stale_active_runs",
                f"{len(stale_runs)} recorded active run(s) have stale heartbeats.",
                stale_runs[-1]["run_dir"],
            )
        )
    scheduler_control = controls["scheduler"]
    if scheduler_control["stop_requested"]:
        reasons.append(
            _issue(
                "error",
                "scheduler_stop_requested",
                "The global scheduler stop request is active.",
                scheduler_control["stop_path"],
            )
        )
    if controls["run_stop_requests"]:
        reasons.append(
            _issue(
                "error",
                "run_stop_requested",
                f"{len(controls['run_stop_requests'])} run stop request(s) are active.",
                controls["run_stop_requests"][-1]["path"],
            )
        )
    if scheduler_control["pause_requested"]:
        reasons.append(
            _issue(
                "warning",
                "scheduler_paused",
                "The global scheduler pause request is active.",
                scheduler_control["pause_path"],
            )
        )
    if controls["run_pause_requests"]:
        reasons.append(
            _issue(
                "warning",
                "runs_paused",
                f"{len(controls['run_pause_requests'])} run pause request(s) are active.",
                controls["run_pause_requests"][-1]["path"],
            )
        )
    if scheduler.get("exists") and scheduler.get("stale"):
        reasons.append(
            _issue(
                "info",
                "stale_scheduler_record",
                "scheduler-status.json is historical and must not be treated as a live process.",
                scheduler.get("path"),
            )
        )
    reasons.extend(issues)

    if any(reason["severity"] == "error" for reason in reasons):
        status = "BLOCKED"
    elif any(reason["code"] in {"scheduler_paused", "runs_paused"} for reason in reasons):
        status = "PAUSED"
    elif any(run["stale"] for run in runs) or scheduler.get("stale"):
        status = "STALE"
    elif any(run["recorded_active"] for run in runs):
        status = "RUNNING"
    else:
        status = "READY"
    return {"status": status, "reason_count": len(reasons), "reasons": reasons}


def _resolve_detail(
    *,
    query: str | None,
    stage: str | None,
    wave: int | None,
    runtime: dict[str, Any],
    runs: list[dict[str, Any]],
    project_root: Path,
    limit: int,
) -> dict[str, Any] | None:
    if stage:
        selected = [run for run in runs if run["stage"] == stage]
        if wave is not None:
            selected = [run for run in selected if run["wave_index"] == wave]
        if query is None:
            return _run_selection_detail(stage, wave, selected, runtime, project_root, limit)

    if not query:
        return None
    normalized = query.strip().casefold()
    exact_run = next((run for run in runs if run["run_id"].casefold() == normalized), None)
    if exact_run:
        return _run_detail(exact_run, project_root, limit)

    task_matches = []
    for run in runs:
        for task in run["tasks"]:
            if not isinstance(task, dict):
                continue
            task_id = str(task.get("task_id") or "")
            if task_id.casefold() == normalized:
                task_matches.append((run, task))
    if len(task_matches) == 1:
        return _task_detail(task_matches[0][0], task_matches[0][1], project_root)
    if len(task_matches) > 1:
        return {
            "type": "task_matches",
            "query": query,
            "matches": [
                {
                    "run_id": run["run_id"],
                    "stage": run["stage"],
                    "wave_index": run["wave_index"],
                    "task_id": task.get("task_id"),
                    "lesson_key": task.get("lesson_key"),
                    "status": task.get("status"),
                }
                for run, task in task_matches[:limit]
            ],
        }

    lessons = runtime.get("lessons") if isinstance(runtime.get("lessons"), list) else []
    lesson_matches = [
        lesson
        for lesson in lessons
        if isinstance(lesson, dict)
        and (
            str(lesson.get("lesson_key") or "").casefold() == normalized
            or normalized in str(lesson.get("lesson") or "").casefold()
            or normalized in str(lesson.get("lesson_key") or "").casefold()
        )
    ]
    if len(lesson_matches) == 1:
        return _lesson_detail(lesson_matches[0], runs, project_root, limit)
    if lesson_matches:
        return {
            "type": "lesson_matches",
            "query": query,
            "matches": [
                {
                    "lesson_key": lesson.get("lesson_key"),
                    "state": lesson.get("state"),
                    "lesson": lesson.get("lesson"),
                }
                for lesson in lesson_matches[:limit]
            ],
            "truncated": len(lesson_matches) > limit,
        }
    return {"type": "not_found", "query": query}


def _run_selection_detail(
    stage: str,
    wave: int | None,
    runs: list[dict[str, Any]],
    runtime: dict[str, Any],
    project_root: Path,
    limit: int,
) -> dict[str, Any]:
    stream = runtime.get("workstreams", {}).get(stage, {})
    detail: dict[str, Any] = {
        "type": "run_selection",
        "stage": stage,
        "wave_index": wave,
        "workstream": stream if isinstance(stream, dict) else {},
        "runs": [
            {key: value for key, value in run.items() if key != "tasks"}
            for run in runs[-limit:]
        ],
        "truncated": len(runs) > limit,
    }
    if wave is not None and len(runs) == 1:
        return _run_detail(runs[0], project_root, limit)
    return detail


def _run_detail(run: dict[str, Any], project_root: Path, limit: int) -> dict[str, Any]:
    tasks = []
    for task in run["tasks"][:limit]:
        if not isinstance(task, dict):
            continue
        task_summary = dict(task)
        artifact_value = task.get("artifact_dir")
        if artifact_value:
            artifact = _resolve_path(artifact_value, project_root)
            task_summary["artifact"] = _inspect_artifact(run["stage"], artifact)
        tasks.append(task_summary)
    return {
        "type": "run",
        "run": {key: value for key, value in run.items() if key != "tasks"},
        "tasks": tasks,
        "truncated": len(run["tasks"]) > limit,
    }


def _task_detail(
    run: dict[str, Any], task_summary: dict[str, Any], project_root: Path
) -> dict[str, Any]:
    task_id = str(task_summary.get("task_id") or "")
    task_dir = Path(run["run_dir"]) / "tasks" / task_id
    task_path = task_dir / "task.json"
    result_path = task_dir / "result.json"
    task = _read_json_object(task_path, "task definition") if task_path.is_file() else {}
    result = _read_json_object(result_path, "task result") if result_path.is_file() else {}
    artifact_value = result.get("artifact_dir") or task_summary.get("artifact_dir")
    artifact = _resolve_path(artifact_value, project_root) if artifact_value else None
    return {
        "type": "task",
        "run": {key: value for key, value in run.items() if key != "tasks"},
        "task": task,
        "result": result,
        "artifact": _inspect_artifact(run["stage"], artifact) if artifact else None,
        "paths": {
            "task": str(task_path.resolve()),
            "result": str(result_path.resolve()),
        },
    }


def _lesson_detail(
    lesson: dict[str, Any],
    runs: list[dict[str, Any]],
    project_root: Path,
    limit: int,
) -> dict[str, Any]:
    lesson_key = str(lesson.get("lesson_key") or "")
    related = []
    for run in runs:
        for task in run["tasks"]:
            if not isinstance(task, dict) or task.get("lesson_key") != lesson_key:
                continue
            item = {
                "run_id": run["run_id"],
                "stage": run["stage"],
                "wave_index": run["wave_index"],
                "run_status": run["status"],
                "task_id": task.get("task_id"),
                "task_status": task.get("status"),
                "attempt_count": task.get("attempt_count"),
                "classification": task.get("classification"),
                "artifact_dir": task.get("artifact_dir"),
            }
            if task.get("artifact_dir"):
                item["artifact"] = _inspect_artifact(
                    run["stage"], _resolve_path(task["artifact_dir"], project_root)
                )
            related.append(item)
    return {
        "type": "lesson",
        "lesson": lesson,
        "related_tasks": related[-limit:],
        "truncated": len(related) > limit,
    }


def _inspect_artifact(stage: str, artifact: Path) -> dict[str, Any]:
    base = {"path": str(artifact.resolve()), "exists": artifact.is_dir()}
    if not artifact.is_dir():
        return base
    if stage == "lesson_output":
        required = ("manifest.json", "note.md", "vision/analysis.json", "fusion/sections.json")
        files = _file_statuses(artifact, required)
        manifest_path = artifact / "manifest.json"
        manifest = _read_json_object(manifest_path, "lesson manifest") if manifest_path.is_file() else {}
        fusion_path = artifact / "fusion" / "sections.json"
        fusion_count = None
        if fusion_path.is_file():
            fusion = _read_json_object(fusion_path, "fusion sections")
            sections = fusion.get("sections") if isinstance(fusion, dict) else None
            fusion_count = len(sections) if isinstance(sections, list) else None
        return {
            **base,
            "required_files": files,
            "required_files_ok": all(item["exists"] and item["bytes"] > 0 for item in files),
            "stage_status": manifest.get("stage_status") if isinstance(manifest.get("stage_status"), dict) else {},
            "vision": _inspect_vision_artifact(artifact),
            "fusion_section_count": fusion_count,
        }
    if stage == "vtext":
        required = (
            "manifest.json",
            "transcript.raw.srt",
            "transcript.raw.txt",
            "transcript.clean.txt",
            "summary.md",
        )
        files = _file_statuses(artifact, required)
        manifest_path = artifact / "manifest.json"
        manifest = _read_json_object(manifest_path, "vtext manifest") if manifest_path.is_file() else {}
        srt_path = artifact / "transcript.raw.srt"
        timestamp_count = 0
        if srt_path.is_file():
            text = srt_path.read_text(encoding="utf-8-sig", errors="replace")
            timestamp_count = len(SRT_TIMESTAMP_RE.findall(text))
        return {
            **base,
            "required_files": files,
            "required_files_ok": all(item["exists"] and item["bytes"] > 0 for item in files),
            "manifest_status": manifest.get("status"),
            "manifest_error_count": len(manifest.get("errors") or [])
            if isinstance(manifest.get("errors"), list)
            else int(bool(manifest.get("errors"))),
            "srt_timestamp_count": timestamp_count,
        }
    if stage == "frame_extract":
        candidates = sorted((artifact / "frames" / "candidates").glob("frame_*.jpg"))
        return {
            **base,
            "candidate_count": len(candidates),
            "empty_candidate_count": sum(1 for path in candidates if path.stat().st_size == 0),
            "candidate_bytes": sum(path.stat().st_size for path in candidates),
        }
    return base


def _render_detail(detail: dict[str, Any], *, limit: int) -> list[str]:
    kind = detail["type"]
    lines = ["Detail", "------"]
    if kind == "not_found":
        return [*lines, f"No run, task, or lesson matched: {detail['query']}"]
    if kind in {"lesson_matches", "task_matches"}:
        lines.append(f"Multiple {kind.replace('_', ' ')} for: {detail['query']}")
        for item in detail["matches"][:limit]:
            lines.append("- " + ", ".join(f"{key}={value}" for key, value in item.items()))
        return lines
    if kind == "run_selection":
        lines.append(
            f"Stage={detail['stage']} wave={detail.get('wave_index') or '*'}"
        )
        for run in detail["runs"][:limit]:
            lines.append(
                f"- {run['run_id']}: status={run['status']}, wave={run['wave_index']}, "
                f"tasks={run['task_count']}, updated={run.get('updated_at')}"
            )
        return lines
    if kind == "run":
        run = detail["run"]
        lines.extend(
            [
                f"Run: {run['run_id']}",
                f"Stage/wave: {run['stage']} / {run['wave_index']}",
                f"Status: {run['status']} (manifest={run['manifest_status']}, "
                f"summary={run.get('summary_status')})",
                f"Tasks: {run['task_count']}; counts={_join_counts(run['counts'])}",
                f"Resume skipped: {run['resume_skipped_count']}",
                f"Last event: {run['last_event'].get('event_type') or '-'} at "
                f"{run['last_event'].get('timestamp') or '-'}",
                f"Run directory: {run['run_dir']}",
            ]
        )
        for task in detail["tasks"][:limit]:
            artifact = task.get("artifact") or {}
            extra = ""
            if artifact.get("vision"):
                extra = f", vision={_join_counts(artifact['vision']['status_counts'])}"
            lines.append(
                f"- {task.get('task_id')} {task.get('status')} attempts="
                f"{task.get('attempt_count')} {task.get('lesson_key')}{extra}"
            )
        return lines
    if kind == "task":
        result = detail["result"]
        task = detail["task"]
        lines.extend(
            [
                f"Task: {task.get('task_id') or result.get('task_id')}",
                f"Run: {detail['run']['run_id']}",
                f"Lesson: {task.get('lesson_key') or result.get('lesson_key')}",
                f"Status: {result.get('status') or task.get('status')}",
                f"Attempts: {result.get('attempt_count', 0)}",
                f"Classification: {result.get('classification') or '-'}",
                f"Message: {result.get('message') or '-'}",
            ]
        )
        for attempt in (result.get("attempts") or [])[-limit:]:
            lines.append(
                f"- attempt {attempt.get('attempt')}: {attempt.get('status')}, "
                f"class={attempt.get('classification') or '-'}, exit={attempt.get('exit_code')}, "
                f"elapsed={attempt.get('elapsed_seconds')}s"
            )
            lines.append(f"  stdout={attempt.get('stdout')}")
            lines.append(f"  stderr={attempt.get('stderr')}")
        artifact = detail.get("artifact") or {}
        if artifact.get("vision"):
            lines.append(
                "Vision: " + _join_counts(artifact["vision"]["status_counts"])
            )
            for frame in artifact["vision"]["problem_frames"][:limit]:
                lines.append(
                    f"- {frame['frame_id']} {frame['status']} request={frame.get('request_id')} "
                    f"warnings={','.join(frame['warnings']) or '-'}"
                )
        lines.append(f"Artifact: {artifact.get('path') or '-'}")
        return lines
    if kind == "lesson":
        lesson = detail["lesson"]
        lines.extend(
            [
                f"Lesson: {lesson.get('lesson_key')}",
                f"State: {lesson.get('state')}",
                f"Video: {lesson.get('video')}",
                "Planned tasks: "
                + ", ".join(
                    f"{task.get('stage')}={task.get('status')}"
                    for task in lesson.get("tasks", [])
                    if isinstance(task, dict)
                ),
            ]
        )
        for task in detail["related_tasks"][:limit]:
            artifact = task.get("artifact") or {}
            extra = ""
            if artifact.get("vision"):
                extra = f", vision={_join_counts(artifact['vision']['status_counts'])}"
            lines.append(
                f"- {task['stage']} wave={task['wave_index']} run={task['run_id']} "
                f"task={task['task_id']} status={task['task_status']} "
                f"attempts={task.get('attempt_count')}{extra}"
            )
        return lines
    return [*lines, json.dumps(detail, ensure_ascii=False, indent=2)]


def _workstream_summary(value: Any) -> dict[str, dict[str, int]]:
    if not isinstance(value, dict):
        return {}
    result = {}
    for stage, stream in value.items():
        if not isinstance(stream, dict):
            continue
        result[str(stage)] = {
            "ready_count": int(stream.get("ready_count") or 0),
            "wave_size": int(stream.get("wave_size") or 0),
            "wave_count": int(stream.get("wave_count") or 0),
        }
    return result


def _pipeline_summary(runtime: dict[str, Any]) -> dict[str, int]:
    bundles = _integer_mapping(runtime.get("bundle_counts"))
    states = _integer_mapping(runtime.get("state_counts"))
    return {
        "vtext_bundles": int(bundles.get("vtext") or 0),
        "frame_bundles": int(bundles.get("frame_extract") or 0),
        "usable_lesson_outputs": int(bundles.get("lesson_output") or 0),
        "delivery_ready": int(states.get("delivery_ready") or 0),
        "delivery_accepted": int(states.get("delivery_accepted") or 0),
        "published": int(states.get("published") or 0),
    }


def _file_statuses(root: Path, names: tuple[str, ...]) -> list[dict[str, Any]]:
    result = []
    for name in names:
        path = root / name
        result.append(
            {
                "name": name,
                "path": str(path.resolve()),
                "exists": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else 0,
            }
        )
    return result


def _read_last_json_line(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        return {}
    with path.open("rb") as handle:
        handle.seek(0, 2)
        position = handle.tell()
        buffer = b""
        while position > 0 and b"\n" not in buffer.rstrip(b"\r\n"):
            size = min(4096, position)
            position -= size
            handle.seek(position)
            buffer = handle.read(size) + buffer
        for raw in reversed(buffer.splitlines()):
            if not raw.strip():
                continue
            payload = json.loads(raw.decode("utf-8-sig"))
            return payload if isinstance(payload, dict) else {}
    return {}


def _render_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    rendered_rows = [[str(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rendered_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    result = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
        "  ".join("-" * width for width in widths),
    ]
    result.extend(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rendered_rows
    )
    return result


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise WorkflowStatusError(f"{label} does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise WorkflowStatusError(f"{label} must be a JSON object: {path}")
    return payload


def _resolve_path(value: Path | str, project_root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_seconds(value: Any, now: datetime) -> float | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    current = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return max(0.0, (current.astimezone(timezone.utc) - parsed).total_seconds())


def _format_age(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "unknown"
    seconds = max(0, int(value))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h"
    return f"{hours // 24}d"


def _integer_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): int(item)
        for key, item in value.items()
        if isinstance(item, int) and not isinstance(item, bool)
    }


def _join_counts(value: dict[str, Any]) -> str:
    if not value:
        return "(none)"
    return ", ".join(f"{key}={item}" for key, item in value.items())


def _task_status_count(tasks: list[Any], status: str) -> int:
    return sum(
        1
        for task in tasks
        if isinstance(task, dict) and str(task.get("status") or "") == status
    )


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _stage_rank(stage: str) -> int:
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return len(STAGE_ORDER)


def _issue(
    severity: str, code: str, message: str, path: Path | str | None = None
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": str(path) if path else None,
    }


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
