# Production Workflow Status Tool

Use `vstatus` as the single read-only operator entry point for the vBook
production workflow. It joins the current runtime plan, runner evidence, vtext
progress, vision quality, fusion artifacts, scheduler record, and pause/stop
controls into one report.

## Quick Start

Run commands from the repository root. The only command that needs to be
remembered is:

```powershell
.\vstatus
```

It automatically finds the newest runtime plan and prints the current overview.
Use a noun after `vstatus` when more detail is needed:

| Command | Result |
| --- | --- |
| `.\vstatus` | Show the complete current overview |
| `.\vstatus watch` | Refresh every 30 seconds until `Ctrl+C` |
| `.\vstatus watch 60` | Refresh every 60 seconds |
| `.\vstatus lesson "魏先生：笑傲股市"` | Inspect one lesson across all stages |
| `.\vstatus run R20260720-lesson-output-wave-131` | Inspect one run and its task evidence |
| `.\vstatus task 001-57c4921f0815` | Inspect matching task attempts |
| `.\vstatus wave lesson_output 131` | Inspect one stage wave |
| `.\vstatus json` | Print a machine-readable snapshot |
| `.\vstatus json outputs/production-workflow/current-status.json` | Atomically write a JSON snapshot |
| `.\vstatus check` | Return a failing exit code for blocked, paused, or stale state |
| `.\vstatus help` | Show quick commands and all long options |

The short aliases `w`, `l`, `r`, `t`, and `j` map to `watch`, `lesson`, `run`,
`task`, and `json`. For example, `.\vstatus l "魏先生：笑傲股市"` and
`.\vstatus w 60` are equivalent to their full-word forms. Prefer the full words
in shared runbooks and scripts because their intent remains obvious.

`vstatus.cmd` delegates to `tools/production_workflow_status.cmd`, which uses
`D:\anaconda3\envs\App\python.exe` when available and falls back to `python`.
Both the quick commands and the long options call the same Python
implementation, so their reports and exit codes cannot diverge.

The tool is read-only unless `--output` is supplied. It never starts vtext,
frame extraction, vision, fusion, reconciliation, delivery shaping, scheduler
ticks, publication, or vault writes. It never moves a pause or stop marker.

## What the Default Report Shows

The default invocation automatically selects the newest
`outputs/production-workflow/*/runtime-plan.json` by its `created_at` value and
shows:

- overall state: `READY`, `RUNNING`, `PAUSED`, `STALE`, or `BLOCKED`;
- reconciliation bundle counts and lesson/task state counts;
- pipeline progress for timestamped vtext, frame extraction, usable
  vision+fusion notes, delivery-ready notes, accepted notes, and publication;
- stable workstream wave sizes and remaining tasks;
- run history grouped by stage, including unsuccessful terminal runs;
- rejected bundle count and exact degraded/error frame IDs;
- scheduler-level and run-level pause/stop requests plus audit markers;
- scheduler status age, so an old `completed` record is not mistaken for a live
  scheduler;
- evidence paths needed for follow-up diagnosis.

The runtime plan is the scheduling snapshot, run summaries/results are the
execution facts, and vision analysis is the quality fact. The tool keeps those
layers separate. A runner task with `status=succeeded` can still be reported as
quality-blocked when reconciliation rejects degraded visual evidence.

## Drill Down

Inspect one run:

```powershell
.\vstatus run R20260720-lesson-output-wave-131
```

Inspect a stage and wave:

```powershell
.\vstatus wave lesson_output 131
```

Inspect a course by exact lesson key or a unique title substring:

```powershell
.\vstatus lesson '魏先生：笑傲股市'
```

The lesson view links all matching frame-extract, vtext, and lesson-output run
tasks. For lesson-output artifacts it reports manifest stage status, required
file status, fusion section count, and vision result counts such as
`ok=6, recovered=3`.

Inspect a task ID:

```powershell
.\vstatus task 001-57c4921f0815
```

Task IDs are derived from lesson keys and may appear in more than one stage. If
a task ID is ambiguous, the tool lists its run/stage matches; use the run ID or
`--stage --wave` to select the intended execution.

## Periodic Display

Refresh every 30 seconds until `Ctrl+C`:

```powershell
.\vstatus watch
```

Run a bounded watch for five snapshots:

```powershell
.\vstatus watch 30 --iterations 5
```

Write or atomically replace a text snapshot on each refresh:

```powershell
.\vstatus watch 60 --output outputs/production-workflow/current-status.txt
```

Only the explicitly named `--output` file is written. Production plans, runs,
artifacts, events, controls, and scheduler files remain unchanged.

## JSON and Automation

Produce a machine-readable snapshot:

```powershell
.\vstatus json
```

Persist JSON and return nonzero while a hard gate, pause, or stale state is
present:

```powershell
.\vstatus `
  --format json `
  --output outputs/production-workflow/current-status.json `
  --strict
```

Exit codes:

| Code | Meaning |
| ---: | --- |
| `0` | Report generated; or strict mode found no blocked/paused/stale state |
| `1` | Configuration, discovery, file I/O, or JSON parsing error |
| `2` | `--strict` found `BLOCKED`, `PAUSED`, or `STALE` |
| `130` | Watch mode was interrupted with `Ctrl+C` |

Use `--limit N` to control detailed text rows and `--stale-seconds N` to change
the default five-minute freshness threshold.

## Full Option Interface

Quick commands translate directly into the long option interface. Use long
options when composing automation, combining filters, or selecting an alternate
workflow. The explicit Python invocation is:

```powershell
D:/anaconda3/envs/App/python.exe tools/production_workflow_status.py --help
```

Override automatic discovery when inspecting an older or alternate plan:

```powershell
.\vstatus `
  --runtime-plan outputs/production-workflow/P20260720-allwin-contract-v1-001/runtime-plan.json `
  --run-root outputs/production-runs
```

`--run-root` is normally unnecessary because a reconciled runtime plan records
its authoritative run root.

## Status Interpretation

`BLOCKED` means at least one hard condition exists, such as rejected bundles,
unsuccessful terminal runs, stale recorded-active runs, or active stop
requests. `PAUSED` means no harder error was found but at least one exact
`pause.request` is active. `STALE` means the available scheduler or active-run
record is older than the freshness threshold. `RUNNING` means a run manifest
records active work. `READY` means none of those conditions was found.

The tool intentionally labels active runs as recorded workflow state. It does
not claim that a PID is alive and does not require privileged operating-system
process inspection. For an operational resume gate, combine this report with
the process check required by the production handoff.

## Evidence Sources

The report reads these files when present:

```text
runtime-plan.json
scheduler-status.json
scheduler-events.jsonl
scheduler-control/{pause.request,stop.request}
production-runs/*/run.manifest.json
production-runs/*/summary.json
production-runs/*/events.jsonl
production-runs/*/control/{pause.request,stop.request}
production-runs/*/tasks/*/{task.json,result.json}
production-artifacts/*/manifest.json
production-artifacts/*/vision/{analysis.json,external/analysis.json}
production-artifacts/*/fusion/sections.json
```

Malformed optional records are surfaced as report issues instead of silently
turning into successful state. A missing or invalid runtime plan is fatal
because there is no authoritative workflow snapshot to summarize.
