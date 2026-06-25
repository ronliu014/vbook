# vBook Sync Protocol

`sync/` is the Git-backed protocol directory for collaboration between Codex agents on different machines. Git is the transport layer: each side pulls before reading, writes handoff files under `sync/`, commits, and pushes.

## Roles

- `wcodex` - Windows-side Codex.
- `lcodex` - Linux-side Codex.

Use these names consistently in messages, filenames, and handoffs.

## Directory Layout

- `inbox/` - messages addressed to this checkout or agent.
- `outbox/` - messages produced by this checkout or agent.
- `shared/` - persistent shared state, decisions, and handoff notes.

## Message Naming

Use timestamped Markdown files:

```text
YYYYMMDD_HHMMSS_from-to_topic.md
```

Examples:

```text
20260625_210000_wcodex-lcodex_bootstrap.md
20260625_213000_lcodex-wcodex_build_notes.md
```

## Message Format

Each message should include:

- `From:` sender role.
- `To:` receiver role.
- `Subject:` short task or decision.
- `Status:` `request`, `in_progress`, `done`, or `blocked`.
- `Context:` relevant files, commands, and constraints.
- `Next:` expected action.

## Operating Rules

1. Pull before reading or writing sync files.
2. Write concise Markdown messages; avoid generated binaries in `sync/`.
3. Commit sync changes with clear messages, for example `Sync wcodex handoff`.
4. Push after committing so the other side can pull.
5. Keep durable project decisions in `sync/shared/`, not only transient inbox or outbox files.
