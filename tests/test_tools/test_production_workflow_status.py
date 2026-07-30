import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from tools.production_workflow_status import (
    WorkflowStatusError,
    _expand_short_command,
    collect_workflow_status,
    discover_runtime_plan,
    main,
    render_text,
)


class ProductionWorkflowStatusTest(unittest.TestCase):
    def test_quick_commands_expand_to_the_existing_cli_options(self) -> None:
        cases = {
            (): [],
            ("show",): [],
            ("watch",): ["--watch-seconds", "30"],
            ("w", "60"): ["--watch-seconds", "60"],
            ("lesson", "course title"): ["--detail", "course title"],
            ("run", "R-test"): ["--detail", "R-test"],
            ("task", "001-test"): ["--detail", "001-test"],
            ("wave", "lesson_output", "131"): [
                "--stage",
                "lesson_output",
                "--wave",
                "131",
            ],
            ("json",): ["--format", "json"],
            ("j", "status.json"): [
                "--format",
                "json",
                "--output",
                "status.json",
            ],
            ("check",): ["--strict"],
            ("help",): ["--help"],
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(_expand_short_command(list(raw)), expected)

    def test_quick_commands_preserve_trailing_long_options(self) -> None:
        self.assertEqual(
            _expand_short_command(["lesson", "course title", "--limit", "2"]),
            ["--detail", "course title", "--limit", "2"],
        )
        self.assertEqual(
            _expand_short_command(["watch", "--iterations", "3"]),
            ["--watch-seconds", "30", "--iterations", "3"],
        )

    def test_invalid_quick_commands_are_rejected(self) -> None:
        for raw in (["unknown"], ["lesson"], ["run", "--limit", "1"], ["wave"]):
            with self.subTest(raw=raw):
                with self.assertRaises(WorkflowStatusError):
                    _expand_short_command(raw)

    def test_overview_combines_plan_runs_quality_controls_and_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))

            report = collect_workflow_status(
                project_root=fixture["root"],
                runtime_plan_path=fixture["runtime_plan"],
                now=datetime(2026, 7, 30, 10, 0, tzinfo=timezone.utc),
                stale_seconds=300,
            )

        self.assertEqual(report["health"]["status"], "BLOCKED")
        self.assertEqual(report["plan"]["bundle_counts"]["vtext"], 1)
        self.assertEqual(report["plan"]["pipeline"]["usable_lesson_outputs"], 0)
        self.assertEqual(report["runs"]["by_stage"]["lesson_output"]["completed"], 1)
        self.assertEqual(report["quality"]["rejected_bundle_count"], 1)
        self.assertEqual(report["quality"]["degraded_frame_count"], 1)
        self.assertEqual(report["quality"]["error_frame_count"], 0)
        self.assertTrue(report["controls"]["scheduler"]["pause_requested"])
        self.assertEqual(len(report["controls"]["run_pause_requests"]), 1)
        self.assertTrue(report["scheduler"]["stale"])
        self.assertEqual(report["scheduler"]["latest_actions"][0]["action"], "started")

    def test_run_detail_reports_artifact_stages_and_vision_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))

            report = collect_workflow_status(
                project_root=fixture["root"],
                runtime_plan_path=fixture["runtime_plan"],
                detail="R-test-lesson-output-wave-001",
            )

        detail = report["detail"]
        self.assertEqual(detail["type"], "run")
        self.assertEqual(detail["run"]["status"], "completed")
        self.assertEqual(detail["tasks"][0]["attempt_count"], 2)
        artifact = detail["tasks"][0]["artifact"]
        self.assertTrue(artifact["required_files_ok"])
        self.assertEqual(artifact["stage_status"]["fusion_sections"], "done")
        self.assertEqual(artifact["vision"]["status_counts"], {"degraded": 1})

    def test_task_and_lesson_queries_show_attempts_and_related_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))

            task_report = collect_workflow_status(
                project_root=fixture["root"],
                runtime_plan_path=fixture["runtime_plan"],
                detail="001-testtask0001",
            )
            lesson_report = collect_workflow_status(
                project_root=fixture["root"],
                runtime_plan_path=fixture["runtime_plan"],
                detail="测试课程",
            )

        self.assertEqual(task_report["detail"]["type"], "task")
        self.assertEqual(task_report["detail"]["result"]["attempt_count"], 2)
        self.assertEqual(
            task_report["detail"]["result"]["attempts"][-1]["status"],
            "succeeded",
        )
        self.assertEqual(lesson_report["detail"]["type"], "lesson")
        self.assertEqual(lesson_report["detail"]["lesson"]["state"], "lesson_output_ready")
        self.assertEqual(lesson_report["detail"]["related_tasks"][0]["stage"], "lesson_output")

    def test_stage_wave_filter_resolves_single_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))

            report = collect_workflow_status(
                project_root=fixture["root"],
                runtime_plan_path=fixture["runtime_plan"],
                stage="lesson_output",
                wave=1,
            )

        self.assertEqual(report["detail"]["type"], "run")
        self.assertEqual(report["detail"]["run"]["wave_index"], 1)

    def test_text_report_makes_snapshot_and_drill_down_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))
            report = collect_workflow_status(
                project_root=fixture["root"],
                runtime_plan_path=fixture["runtime_plan"],
            )

            rendered = render_text(report)

        self.assertIn("Status: BLOCKED", rendered)
        self.assertIn("Pipeline Progress", rendered)
        self.assertIn("usable vision + fusion notes", rendered)
        self.assertIn("Rejected degraded frames: 1", rendered)
        self.assertIn("scheduler-status.json is historical", rendered)
        self.assertIn("Use lesson <name>, run <id>, task <id>", rendered)
        self.assertIn("Use json for automation", rendered)

    def test_cli_json_output_and_strict_exit_are_automation_friendly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))
            output = fixture["root"] / "status.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--runtime-plan",
                        str(fixture["runtime_plan"]),
                        "--run-root",
                        str(fixture["run_root"]),
                        "--format",
                        "json",
                        "--output",
                        str(output),
                        "--strict",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            persisted = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(payload["kind"], "vbook_production_workflow_status")
        self.assertEqual(payload["health"]["status"], "BLOCKED")
        self.assertEqual(persisted["generated_at"], payload["generated_at"])

    def test_discovers_newest_runtime_plan_by_created_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "outputs" / "production-workflow" / "older" / "runtime-plan.json"
            newer = root / "outputs" / "production-workflow" / "newer" / "runtime-plan.json"
            _write_json(older, {"created_at": "2026-07-29T00:00:00+00:00"})
            _write_json(newer, {"created_at": "2026-07-30T00:00:00+00:00"})

            selected = discover_runtime_plan(root)

        self.assertEqual(selected, newer.resolve())


def _write_fixture(root: Path) -> dict[str, Path]:
    workflow_dir = root / "outputs" / "production-workflow" / "P-test"
    run_root = root / "outputs" / "production-runs"
    run_dir = run_root / "R-test-lesson-output-wave-001"
    task_id = "001-testtask0001"
    task_dir = run_dir / "tasks" / task_id
    artifact = root / "outputs" / "production-artifacts" / "lesson-output-wave-001" / task_id
    summary_path = run_dir / "summary.json"
    runtime_path = workflow_dir / "runtime-plan.json"
    lesson_key = "资料库/测试课程/第一课"

    for relative, content in {
        "manifest.json": {
            "stage_status": {
                "timeline_alignment": "done",
                "vision_analysis": "done",
                "fusion_sections": "done",
                "manifest": "done",
            }
        },
        "vision/analysis.json": {
            "analysis_count": 1,
            "analyses": [
                {
                    "frame_id": "frame-000001",
                    "structured_observations": {
                        "degraded": True,
                        "degraded_reason": "empty_model_response_after_recovery",
                        "qwen_service": {
                            "request_id": "vbook-frame-000001",
                            "warnings": [
                                "model_json_recovery_retry",
                                "degraded_empty_model_response",
                            ],
                        },
                    },
                }
            ],
        },
        "vision/external/analysis.json": {
            "analysis_count": 1,
            "degraded_count": 1,
            "analyses": [
                {
                    "frame_id": "frame-000001",
                    "structured_observations": {
                        "degraded": True,
                        "degraded_reason": "empty_model_response_after_recovery",
                        "qwen_service": {
                            "request_id": "vbook-frame-000001",
                            "warnings": [
                                "model_json_recovery_retry",
                                "degraded_empty_model_response",
                            ],
                        },
                    },
                }
            ],
        },
        "fusion/sections.json": {"sections": [{"title": "测试"}]},
    }.items():
        _write_json(artifact / relative, content)
    _write_text(artifact / "note.md", "# 测试课程\n")

    attempts = [
        {
            "attempt": 1,
            "status": "failed",
            "classification": "process_exit",
            "exit_code": 1,
            "elapsed_seconds": 1.0,
            "stdout": str(task_dir / "attempt-01.stdout.log"),
            "stderr": str(task_dir / "attempt-01.stderr.log"),
        },
        {
            "attempt": 2,
            "status": "succeeded",
            "classification": None,
            "exit_code": 0,
            "elapsed_seconds": 2.0,
            "stdout": str(task_dir / "attempt-02.stdout.log"),
            "stderr": str(task_dir / "attempt-02.stderr.log"),
        },
    ]
    task_summary = {
        "task_id": task_id,
        "lesson_key": lesson_key,
        "status": "succeeded",
        "attempt_count": 2,
        "classification": None,
        "result": str(task_dir / "result.json"),
        "artifact_dir": str(artifact),
    }
    _write_json(
        run_dir / "run.manifest.json",
        {
            "kind": "vbook_production_workflow_run",
            "run_id": "R-test-lesson-output-wave-001",
            "stage": "lesson_output",
            "wave_index": 1,
            "status": "completed",
            "mode": "execute",
            "task_count": 1,
            "started_at": "2026-07-30T08:00:00+00:00",
            "updated_at": "2026-07-30T08:10:00+00:00",
            "finished_at": "2026-07-30T08:10:00+00:00",
        },
    )
    _write_json(
        summary_path,
        {
            "kind": "vbook_production_workflow_run_summary",
            "run_id": "R-test-lesson-output-wave-001",
            "stage": "lesson_output",
            "wave_index": 1,
            "status": "completed",
            "task_count": 1,
            "counts": {"succeeded": 1},
            "resume_skipped_count": 0,
            "tasks": [task_summary],
            "finished_at": "2026-07-30T08:10:00+00:00",
        },
    )
    _write_json(
        task_dir / "task.json",
        {
            "kind": "vbook_production_workflow_task",
            "task_id": task_id,
            "stage": "lesson_output",
            "lesson_key": lesson_key,
            "lesson": "第一课",
            "artifact_dir": str(artifact),
            "status": "planned",
        },
    )
    _write_json(
        task_dir / "result.json",
        {
            "kind": "vbook_production_workflow_task_result",
            "task_id": task_id,
            "stage": "lesson_output",
            "lesson_key": lesson_key,
            "status": "succeeded",
            "attempt_count": 2,
            "classification": None,
            "message": "Task attempt completed successfully.",
            "artifact_dir": str(artifact),
            "attempts": attempts,
        },
    )
    _write_text(
        run_dir / "events.jsonl",
        json.dumps(
            {
                "timestamp": "2026-07-30T08:10:00+00:00",
                "event_type": "run_completed",
            }
        )
        + "\n",
    )
    _write_text(run_dir / "control" / "pause.request", "quality gate\n")
    _write_text(workflow_dir / "scheduler-control" / "pause.request", "global gate\n")
    _write_text(
        run_dir / "control" / "pause.request.repair-authorized",
        "audit\n",
    )
    _write_json(
        workflow_dir / "scheduler-status.json",
        {
            "kind": "vbook_production_scheduler_status",
            "status": "completed",
            "updated_at": "2026-07-29T00:00:00+00:00",
            "execute": True,
            "actions": [
                {
                    "action": "started",
                    "stage": "lesson_output",
                    "wave_index": 1,
                    "run_id": "R-test-lesson-output-wave-001",
                }
            ],
        },
    )
    _write_json(
        runtime_path,
        {
            "schema_version": "1",
            "kind": "vbook_production_workflow_plan",
            "created_at": "2026-07-30T09:00:00+00:00",
            "reconciled": True,
            "source_plan": str(workflow_dir / "workflow-plan.json"),
            "run_root": str(run_root),
            "lesson_count": 1,
            "bundle_counts": {"vtext": 1, "frame_extract": 1, "lesson_output": 0},
            "state_counts": {"lesson_output_ready": 1},
            "task_counts": {"lesson_output_ready": 1},
            "capacity": {"vision_lesson_inflight": 1},
            "workstreams": {
                "lesson_output": {
                    "ready_count": 1,
                    "wave_size": 1,
                    "wave_count": 1,
                    "waves": [[lesson_key]],
                }
            },
            "rejected_bundle_count": 1,
            "rejected_bundles": [
                {
                    "summary": str(summary_path),
                    "reason": "vision analysis contains an explicit degraded model result",
                }
            ],
            "lessons": [
                {
                    "lesson_key": lesson_key,
                    "library": "资料库",
                    "course": "测试课程",
                    "lesson": "第一课",
                    "state": "lesson_output_ready",
                    "video": str(root / "input.mp4"),
                    "tasks": [
                        {
                            "stage": "lesson_output",
                            "owner": "vbook",
                            "status": "ready",
                            "depends_on": ["vtext", "frame_extract"],
                        }
                    ],
                }
            ],
        },
    )
    return {
        "root": root,
        "runtime_plan": runtime_path,
        "run_root": run_root,
        "artifact": artifact,
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
