# 2026-07-18 Allwin Production Patrol

## Scope

The user expanded production scope to every video under:

- `F:/downloads/allwin/读书会`
- `F:/downloads/allwin/基础教学`
- `F:/downloads/allwin/量化模式`
- `F:/downloads/allwin/牛股实战班`
- `F:/downloads/allwin/投资训练营`

Accepted production route:

- `vtext_first_vault_enhance`

Current policy:

- vtext source vault remains read-only.
- vBook previews are generated under `F:/vbook/experiments`.
- vBook publication requires explicit user approval, backup on overwrite, and
  postcheck pass.

## Inventory

Initial video counts:

- `读书会`: 135
- `基础教学`: 254
- `量化模式`: 105
- `牛股实战班`: 19
- `投资训练营`: 450

Total videos: 963.

## Queue Audit

Full production queue audit outputs:

```text
F:/vbook/production-queues/Q20260718-allwin-all-libraries/production-library-audit.json
F:/vbook/production-queues/Q20260718-allwin-all-libraries/production-library-audit.md
```

Repository preview copy:

```text
outputs/production-queues/Q20260718-allwin-all-libraries/production-library-audit.json
outputs/production-queues/Q20260718-allwin-all-libraries/production-library-audit.md
```

Initial audit summary:

- Libraries: 5
- Lessons: 963
- Published: 4
- Waiting for both vtext source note and lesson output: 959
- Ready for preview: 0

Per-library status:

- `读书会`: 135 waiting
- `基础教学`: 254 waiting
- `量化模式`: 105 waiting
- `牛股实战班`: 19 waiting
- `投资训练营`: 4 published, 446 waiting

## Tooling

`tools/production_queue_audit.py` now supports:

- single-course audit;
- full-library audit across multiple video library roots;
- matching vtext notes under `F:/vault/20_Learning/vtext/<library>/...`;
- matching published vBook notes under `F:/vault/20_Learning/vbook/<library>/...`;
- matching ready lesson outputs that contain:
  - `manifest.json`
  - `vision/analysis.json`
  - `fusion/sections.json`

Test coverage:

```text
tests/test_tools/test_production_queue_audit.py
```

## vtext Coordination

vBook sent a full-backlog vsync request to vtext:

```text
E:/projects/my_app/vsync/mailbox/messages/2026-07-18-vbook-vtext-allwin-library-source-backlog-request.md
```

The request asks vtext to plan and produce source notes and semantic/temporal
text artifacts for the 959 waiting videos. The message is indexed in:

```text
E:/projects/my_app/vsync/mailbox/outbox/vbook/README.md
E:/projects/my_app/vsync/mailbox/inbox/vtext/README.md
```

## Patrol Automation

Created Codex heartbeat:

```text
Name: vBook production patrol
ID: vbook-production-patrol
Cadence: every 30 minutes
Destination: current Codex task
```

Each patrol should:

1. run `git status -sb`;
2. regenerate the full queue audit;
3. summarize deltas only;
4. check vsync responses from vtext or vision;
5. generate preview-only batches when items become `ready_for_preview`;
6. hold publication for explicit user approval;
7. write vsync requests when partner project support is needed.

## Plan

Durable operations plan:

```text
docs/80_superpowers/plans/2026-07-18-allwin-production-patrol.md
```

## Current State

vBook can operate as the production coordinator now, but the full library is
not ready for direct note generation yet. The current blocking condition is
upstream source availability:

- no new lessons are currently `ready_for_preview`;
- 959 videos require vtext source notes and ready 240s lesson outputs;
- publication remains limited to the 4 already accepted and postchecked notes.
