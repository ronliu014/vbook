# 2026-07-18 Production Queue Start

## Scope

- Course: `投资训练营/韩珂龙头班：基础篇`
- Accepted route: `vtext_first_vault_enhance`
- Visual baseline: `240s`
- User decision: current notes are acceptable for production use.
- vtext source policy: read-only.
- vBook target vault:
  `F:/vault/20_Learning/vbook/投资训练营/韩珂龙头班：基础篇`

## Current Published Batch

The first production batch has been published and postchecked:

- Published lessons: 4
- Final publication postcheck: `pass`
- File checks: 8
- Hash matches: 8
- Missing Markdown images: 0
- Publication result:
  `F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/publication-plans/vtext_first_vault_enhance-production-batch-002/publication-result.json`
- Postcheck:
  `F:/vbook/experiments/E20260718-vtext-first-production-batch-preview-004/publication-plans/vtext_first_vault_enhance-production-batch-002/publication-postcheck.json`

Published lessons:

- `反抽 反弹 反转`
- `如何筛选龙头股？`
- `如何高效选股，构建自己的短线股票池`
- `龙头股的上涨逻辑是什么？`

## Queue Audit

A production queue audit was generated for the full local course video
directory:

```text
F:/vbook/production-queues/Q20260718-hanke-basic/production-queue-audit.json
F:/vbook/production-queues/Q20260718-hanke-basic/production-queue-audit.md
```

Repository preview copy:

```text
outputs/production-queues/Q20260718-hanke-basic/production-queue-audit.json
outputs/production-queues/Q20260718-hanke-basic/production-queue-audit.md
```

Audit summary:

- Total local videos: 13
- Published through vBook: 4
- Waiting for both vtext source note and 240s lesson output: 9
- Ready-for-preview new lessons: 0

Missing lessons:

- `不同战法的黄金分割线如何画`
- `主力军情 内盘 外盘`
- `如何借力游资抓龙头？`
- `如何识别龙头股是否出货？`
- `新手如何做好国债逆回购`
- `止损对短线交易的重要性`
- `短线龙头与中线龙头的区别`
- `龙头股到底该怎么低吸？`
- `龙头股战法简介`

## Tooling

Added a queue audit helper:

```text
tools/production_queue_audit.py
tests/test_tools/test_production_queue_audit.py
```

Purpose:

- enumerate course videos;
- match vtext source notes;
- match ready lesson outputs with `manifest.json`, `vision/analysis.json`, and
  `fusion/sections.json`;
- detect already published vBook notes;
- write JSON and Markdown queue reports.

Statuses:

- `published`
- `ready_for_preview`
- `waiting_vtext`
- `waiting_lesson_output`
- `waiting_vtext_and_lesson_output`

## Cross-Project Request

vBook sent a vsync request to vtext asking for the 9 missing vtext-owned source
notes and, where available, semantically validated temporal text artifacts:

```text
E:/projects/my_app/vsync/mailbox/messages/2026-07-18-vbook-vtext-hanke-basic-batch-source-gap-request.md
```

The message is indexed in:

```text
E:/projects/my_app/vsync/mailbox/outbox/vbook/README.md
E:/projects/my_app/vsync/mailbox/inbox/vtext/README.md
```

## Next Gates

1. Wait for vtext to provide one or more missing source notes, or produce them
   through the agreed vtext pipeline.
2. For each newly available lesson, generate or locate a 240s vBook
   `lesson_output`.
3. Regenerate the production queue audit.
4. Create the next `vtext_first_vault_enhance` batch input only for lessons
   that are `ready_for_preview`.
5. Generate previews under `F:/vbook/experiments`.
6. Run preflight, user review, publication dry-run, conflict report, explicit
   approval, apply with backup, and postcheck.
