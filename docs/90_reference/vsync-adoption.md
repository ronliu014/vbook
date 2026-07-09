# vsync Adoption

Status: active
Date: 2026-07-08
Protocol: vsync/v1
Project: vbook

vBook uses vsync/v1 as the central mailbox for communication with vtext and vision inside the v-series video-note processing cluster.

Canonical protocol source:

- E:/projects/my_app/vsync/PROTOCOL.md

Best practices:

- E:/projects/my_app/vsync/docs/60_operations/participant-mailbox-best-practices.md

Mailbox:

- inbox: E:/projects/my_app/vsync/mailbox/inbox/vbook/README.md
- outbox: E:/projects/my_app/vsync/mailbox/outbox/vbook/README.md
- messages: E:/projects/my_app/vsync/mailbox/messages/

Current cluster participants:

- vbook
- vtext
- vision

Rules:

- Store canonical cross-project messages in vsync/mailbox/messages/.
- Index sent messages in vsync/mailbox/outbox/vbook/README.md.
- Check received messages in vsync/mailbox/inbox/vbook/README.md.
- Use Protocol: vsync/v1 and Mailbox-Path: in new message envelopes.
- Set In-Reply-To when responding to an existing mailbox message.
- Do not write mailbox copies into other participant repositories.
- Do not use this project docs/90_reference/ directory as the cross-project mailbox.
- Update vBook docs only when a mailbox conversation changes durable vBook-owned facts such as contracts, runbooks, operations, compatibility, defaults, latency, risk, or backlog.
- Keep videos, generated notes, extracted frames, large logs, and model artifacts out of vsync messages; link paths and summarize evidence instead.
