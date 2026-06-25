# Shared Handoff

## Current Roles

- `wcodex`: Windows-side Codex working from this checkout.
- `lcodex`: Linux-side Codex working from a synced checkout.

## Current State

- Repository initialized for vBook.
- `sync/` protocol uses Git as the file transport layer.
- vBook may learn from `vtext`, but remains independent and must not depend on vtext code.

## Next Coordination Tasks

- Confirm the Linux checkout path and environment assumptions.
- Decide the first implementation milestone after repository setup.
