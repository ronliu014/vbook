# 2026-07-07 Cross-Project Coordination

## Context

vBook is moving from a local MVP pipeline into a coordinated workflow with
adjacent projects:

- `vtext` as the transcript, correction, and text-summary backend.
- `vision` as the Qwen Vision Service backend.
- `F:\vault` as the final knowledge-base target after preview review.

The Qwen Vision Service path has already passed a real adapter smoke against
`http://192.168.0.33:8866`, and the user confirmed that vBook should remain the
orchestrator while vtext behaves as the text-processing module.

## Work Done

- Added [../90_reference/cross-project-coordination-notice.md](../90_reference/cross-project-coordination-notice.md).
- Added [../90_reference/vbook-text-integration-request.md](../90_reference/vbook-text-integration-request.md).
- Added [../80_superpowers/plans/2026-07-07-vault-enhancement-preview.md](../80_superpowers/plans/2026-07-07-vault-enhancement-preview.md).
- Proposed a shared docs/request-response protocol for vBook, vtext, and
  vision.
- Defined minimum docs structure for vtext and vision integration material.
- Defined the requested vtext CLI/artifact/manifest response contract.
- Clarified that integration should happen through CLI/API/manifest contracts,
  not source-code imports or vendored code.
- Confirmed the next vBook path should be preview-first vault enhancement, not
  direct vault overwrite.
- Planned the first preview implementation as a thin export layer over existing
  vBook lesson artifacts, with no write-back to `F:\vault`.

## Next

1. Execute the vault enhancement preview implementation plan.
2. Share the coordination notice and vtext request with the vtext project and
   collect a response.
3. Run a preview-only vault enhancement workflow using:
   - existing vtext Markdown notes under `F:\vault\20_Learning\投资训练营`;
   - matching source videos under `F:\downloads\allwin\投资训练营`;
   - vBook-selected visual evidence from Qwen Vision Service;
   - output under `outputs/vault-enhancement-preview/`.
4. Review preview output before designing any controlled write-back into the
   vault.
