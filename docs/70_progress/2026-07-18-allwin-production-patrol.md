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

## 2026-07-18 Patrol Update: Han Ke Basic Source Reply

vtext replied to the 2026-07-18 Allwin backlog requests and provided 9 missing
source-note bundles for:

```text
F:/vault/20_Learning/vtext/投资训练营/韩珂龙头班：基础篇
E:/projects/my_app/vtext/var/hanke-basic-vbook-bundles/<lesson>/
```

Newly available vtext lessons:

- `不同战法的黄金分割线如何画`
- `主力军情 内盘 外盘`
- `如何借力游资抓龙头？`
- `如何识别龙头股是否出货？`
- `新手如何做好国债逆回购`
- `止损对短线交易的重要性`
- `短线龙头与中线龙头的区别`
- `龙头股到底该怎么低吸？`
- `龙头股战法简介`

Important caveat from vtext:

- `新手如何做好国债逆回购` used a fallback summary after two server-side LLM
  refine timeouts. Treat it as semantically usable but lower-confidence until
  review.

Refreshed full-library audit:

- Lessons: 963
- Published: 4
- Ready for preview: 1
- Waiting for 240s lesson output: 8
- Waiting for both vtext and lesson output: 950

Per-library status:

- `读书会`: 135 waiting for both vtext and lesson output
- `基础教学`: 254 waiting for both vtext and lesson output
- `量化模式`: 105 waiting for both vtext and lesson output
- `牛股实战班`: 19 waiting for both vtext and lesson output
- `投资训练营`: 4 published, 1 ready for preview, 8 waiting for lesson output,
  437 waiting for both vtext and lesson output

## 2026-07-18 Tooling Update: Coarse vtext Transcript JSON

vtext bundles currently provide `transcript.clean.txt`, `transcript.raw.txt`,
and `summary.md`, but vBook `build` accepts timestamped `.json` or `.srt`
transcripts. Added a preview-oriented bridge:

```text
tools/vtext_bundle_transcript_json.py
tests/test_tools/test_vtext_bundle_transcript_json.py
```

The tool converts a vtext bundle manifest into `transcript.coarse.json` by:

- preferring `outputs.clean_txt`, falling back to `outputs.raw_txt`;
- reading source video duration through `ffprobe`, unless an explicit duration
  override is provided;
- splitting text into coarse weighted segments;
- writing JSON compatible with `vbook_audio.load_transcript`.

This is only a coarse timing bridge for visual lesson-output generation. True
SRT or semantically aligned temporal text from vtext should remain the preferred
production input once available.

Generated coarse transcripts for the 9 Han Ke basic lessons under:

```text
outputs/vtext-bundle-transcripts/hanke-basic-20260718/<lesson>/transcript.coarse.json
```

Verification:

```text
D:/anaconda3/envs/App/python.exe -m unittest tests.test_tools.test_vtext_bundle_transcript_json tests.test_audio.test_transcript
```

Result: 7 tests passed.

## 2026-07-18 Preview Update: First New Han Ke Lesson

Generated one 240s lesson-output smoke for:

```text
F:/downloads/allwin/投资训练营/韩珂龙头班：基础篇/不同战法的黄金分割线如何画.mp4
```

Lesson output:

```text
outputs/hanke-basic-new-qwen-240s/韩珂龙头班：基础篇/不同战法的黄金分割线如何画
```

Stage status in `manifest.json` shows core stages complete:

- transcript import: done
- frame extraction: done
- timeline alignment: done
- vision analysis: done
- fusion prompt: done
- fusion sections: done
- note export: done

Qwen visual analysis:

- 4 selected frames at the 240s baseline.
- `frame-000001` returned HTTP 504 timeout and was recorded as a structured
  Qwen error placeholder.
- `frame-000002`, `frame-000003`, and `frame-000004` succeeded as
  `kline_case`, confidence `0.95`.

Preview batch input:

```text
F:/vbook/inputs/hanke-basic-new-visual-smoke-001/batch-input.json
```

Preview output:

```text
F:/vbook/experiments/E20260718-hanke-basic-new-visual-smoke-001
```

Preflight:

- ok: true
- notes: 1
- manifests: 1
- image links: 1
- missing images: 0
- errors: 0
- warnings: 0

Manual preview check:

- Markdown remains vtext-first and keeps the vtext note as the main body.
- The Qwen 504 placeholder image was not inserted.
- The selected image is `frame_000004.jpg`, a completed annotated K-line /
  golden-ratio support page.
- Initial preview placed the image too early under the tool-introduction
  section. vBook fixed the anchor scoring so stock-code and Chinese stock-name
  entity matches in section headings can beat generic tool/theme terms.
- After the fix, the image is inserted under
  `案例二：云南锗业（三连板一字板）`, which is the correct semantic section.

Regression coverage:

```text
tests/test_export/test_vault_enhance.py
```

Added cases for anchoring visuals by stock code and Chinese stock-name entity.

Verification:

```text
D:/anaconda3/envs/App/python.exe -m unittest tests.test_export.test_vault_enhance tests.test_tools.test_vtext_bundle_transcript_json tests.test_audio.test_transcript
```

Result: 21 tests passed.

Current production posture:

- The accepted production route remains `vtext_first_vault_enhance`.
- This route is improving toward batch use, but broad production should still
  proceed as preview-first until the remaining Han Ke lesson outputs are
  generated and sampled.
- No new content was published to `F:/vault/20_Learning/vbook` in this patrol.
