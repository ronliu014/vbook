# vBook Cross-Project Coordination Notice

Status: proposed by vBook  
Date: 2026-07-07  
From: vBook  
To: vtext, vision  
Related:

- [qwen-vision-service-integration-request.md](./qwen-vision-service-integration-request.md)
- [integration-response.md](./integration-response.md)
- [../40_development/sync-protocol.md](../40_development/sync-protocol.md)
- [../00_project/task-board.md](../00_project/task-board.md)

## Purpose

vBook is becoming the orchestrator for video-course knowledge production. It
coordinates text extraction, visual understanding, evidence fusion, note
export, and future vault write-back.

The adjacent projects should remain independently evolvable:

- `vtext` provides transcript, text correction, and text-summary capability.
- `vision` provides image understanding through Qwen Vision Service or similar
  visual backends.
- `vbook` owns the end-to-end course-note workflow, final knowledge structure,
  evidence fusion, preview output, and future vault integration.

This notice proposes a shared documentation and request/response protocol so
the three projects can coordinate through stable files and contracts rather
than informal chat history or source-level coupling.

## Coordination Principle

The projects should integrate through stable boundaries:

- CLI commands, HTTP APIs, and JSON/Markdown artifact contracts are acceptable.
- Shared source-code imports, vendoring, or project-internal assumptions are not
  acceptable as the long-term integration boundary.
- Each project documents the contract it exposes and the operational steps
  required to run it.
- vBook may call vtext and vision, but vBook should not own their
  implementation details.
- Requests and replies should be preserved in `docs/90_reference/` or a
  project-equivalent integration directory.

## Proposed Docs Layout

vBook already uses numbered documentation layers. vtext and vision do not need
to copy every document, but they should adopt the same high-level categories
for integration-relevant material.

```text
docs/
|-- 00_project/
|   |-- status.md
|   +-- task-board.md
|-- 20_architecture/
|   +-- module-boundaries.md
|-- 40_development/
|   +-- sync-protocol.md
|-- 60_operations/
|   +-- <service-or-cli-runbook>.md
|-- 70_progress/
|   +-- YYYY-MM-DD-<topic>.md
+-- 90_reference/
    |-- vbook-integration-request.md
    |-- vbook-integration-response.md
    +-- samples/
```

Minimum useful adoption for vtext:

```text
docs/
|-- 00_project/
|   |-- status.md
|   +-- task-board.md
|-- 60_operations/
|   +-- vbook-text-integration.md
+-- 90_reference/
    |-- vbook-text-integration-request.md
    |-- vbook-text-integration-response.md
    +-- samples/
```

Minimum useful adoption for vision:

```text
docs/
|-- 00_project/
|   |-- status.md
|   +-- task-board.md
|-- 60_operations/
|   +-- qwen-vision-service.md
+-- 90_reference/
    |-- vbook-vision-integration-request.md
    |-- vbook-vision-integration-response.md
    +-- samples/
```

If a project already has flat `docs/` files, it can move gradually. The first
priority is not cosmetic reorganization; it is to make integration requests,
responses, samples, and runbooks easy to find.

## Request And Response Pattern

For every cross-project integration topic:

1. vBook writes an integration request.
2. The target project replies with an integration response.
3. Both sides keep a copy or reference to the paired documents.
4. Any later contract change gets a dated progress log and, when needed, a new
   request/response pair.

Suggested names:

```text
docs/90_reference/vbook-text-integration-request.md
docs/90_reference/vbook-text-integration-response.md
docs/90_reference/vbook-vision-integration-request.md
docs/90_reference/vbook-vision-integration-response.md
```

Each request should include:

- requester and target project;
- goal and non-goals;
- expected CLI/API entry points;
- expected input and output artifacts;
- required schema fields;
- smoke-test command or fixture expectation;
- failure behavior and retry behavior;
- what vBook needs before it can consume the project reliably.

Each response should include:

- supported command/API shape;
- exact version or commit assumptions;
- output contract and sample artifacts;
- error model;
- performance and resource notes;
- known limitations;
- smoke-test status and command output summary;
- questions or contract changes requested from vBook.

## vtext Request

vBook asks vtext to expose a stable text-processing contract that can be called
per lesson and later in batch mode.

The preferred per-video output bundle is:

```text
<lesson-output>/
|-- transcript.raw.srt
|-- transcript.raw.txt
|-- transcript.clean.txt
|-- summary.md
+-- manifest.json
```

`manifest.json` should include:

```json
{
  "schema_version": "1",
  "source_video": "path/to/video.mp4",
  "course": "投资训练营",
  "series": "韩珂龙头班：基础篇",
  "lesson_title": "如何高效选股，构建自己的短线股票池",
  "language": "zh",
  "status": "done",
  "outputs": {
    "raw_srt": "transcript.raw.srt",
    "raw_txt": "transcript.raw.txt",
    "clean_txt": "transcript.clean.txt",
    "summary_md": "summary.md"
  },
  "errors": []
}
```

For current vtext compatibility, vBook already recognizes the existing
vtext-style layout:

```text
<input-root>/
|-- <lesson>.mp4
+-- text/
    +-- <lesson>_raw.srt
```

The future contract should make `clean_txt`, `summary_md`, and `manifest.json`
first-class artifacts so vBook can merge text evidence with visual evidence
without reverse-engineering filenames.

## vision Request

vision has already replied to the Qwen Vision Service integration request, and
vBook has successfully smoke-tested:

- `GET /health`
- `POST /analyze-frame`
- model: `qwen3-vl:8b`
- endpoint: `http://192.168.0.33:8866`
- no auth token required in the current local environment

The next request for vision is to keep the integration contract discoverable in
the same docs pattern:

```text
docs/90_reference/vbook-vision-integration-response.md
docs/60_operations/qwen-vision-service.md
docs/70_progress/YYYY-MM-DD-<smoke-or-change>.md
```

The response should continue to document:

- health endpoint;
- analysis endpoint;
- request schema;
- response schema;
- OCR/text extraction fields;
- model metadata;
- latency/resource expectations;
- failure codes and retry guidance.

## sync Directory Scope

`sync/` is a lightweight agent coordination mailbox, not a data channel.

Allowed:

- handoffs;
- review requests;
- short state summaries;
- links to docs;
- decisions and ownership notes.

Not allowed:

- videos;
- extracted frames;
- transcripts;
- model responses with large payloads;
- generated vault attachments;
- batch output directories.

Large artifacts should stay in ignored runtime paths such as `outputs/`,
`runs/`, or an external vault/assets directory, with paths recorded in
manifests.

## Initial vBook Plan After This Notice

After this notice is accepted as the shared coordination baseline, vBook should
continue with the following work:

1. Define the vtext integration request in vBook terms.
2. Build a preview-only vault enhancement flow for the existing
   `F:\vault\20_Learning\投资训练营` notes.
3. Use vtext notes as the text backbone and vBook/Qwen Vision frames as visual
   evidence.
4. Produce `outputs/vault-enhancement-preview/.../enhancement.md`,
   selected images, and a manifest before any vault write-back.
5. Only after preview review, design a controlled write-back path into
   `F:\vault`, respecting the vault's own Git state, templates, assets folder,
   index files, and logs.

## Acceptance Checklist

This coordination baseline is ready when:

- vBook has this notice under `docs/90_reference/`.
- vtext has a corresponding request/response location documented.
- vision keeps the service response and runbook in a predictable docs location.
- Each project can answer "what does vBook call, what files are produced, and
  how do we smoke-test it?" without searching chat history.
- vBook can proceed with preview output generation without depending on private
  implementation details of vtext or vision.
