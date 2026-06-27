# Document Reclassification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move existing vBook documents into the approved numbered `docs/` layers and update live navigation links.

**Architecture:** Perform the migration in three batches: durable project/product/architecture/pipeline docs first, progress logs second, and agent planning artifacts last. Use `git mv` for moves so history remains traceable. Update current navigation files and layer READMEs, but do not rewrite historical implementation plans solely to change links embedded as historical context.

**Tech Stack:** Markdown documentation, Git file moves, PowerShell verification commands, existing Python unittest suite for no-runtime-regression verification.

---

## File Structure

### Move durable root docs

- Move `docs/business-plan.md` to `docs/10_product/business-plan.md`.
- Move `docs/design.md` to `docs/20_architecture/design.md`.
- Move `docs/architecture.md` to `docs/20_architecture/architecture.md`.
- Move `docs/data-model.md` to `docs/20_architecture/data-model.md`.
- Move `docs/modules.md` to `docs/20_architecture/module-boundaries.md`.
- Move `docs/output-behavior.md` to `docs/20_architecture/output-contracts.md`.
- Move `docs/pipeline.md` to `docs/30_pipeline/overview.md`.
- Move `docs/sync-protocol.md` to `docs/40_development/sync-protocol.md`.
- Move `docs/roadmap.md` to `docs/00_project/legacy-roadmap.md`.
- Move `docs/vBook需求意向.md` to `docs/90_reference/original-requirements.md`.

### Move progress docs

- Move `docs/progress/2026-06-25.md` to `docs/70_progress/2026-06-25.md`.
- Remove the empty `docs/progress/` directory after the move.

### Move agent planning docs

- Move `docs/superpowers/specs/` to `docs/80_superpowers/specs/`.
- Move `docs/superpowers/plans/` to `docs/80_superpowers/plans/`.
- Remove the empty `docs/superpowers/` directory after the move.

### Update live navigation and current docs

- Modify `docs/README.md`.
- Modify `docs/00_project/README.md`.
- Modify `docs/00_project/roadmap.md`.
- Modify `docs/00_project/status.md`.
- Modify `docs/10_product/README.md`.
- Modify `docs/20_architecture/README.md`.
- Modify `docs/30_pipeline/README.md`.
- Modify `docs/40_development/README.md`.
- Modify `docs/50_modules/README.md`.
- Modify `docs/60_operations/README.md`.
- Modify `docs/70_progress/README.md`.
- Modify `docs/80_superpowers/README.md`.
- Modify `docs/90_reference/README.md`.
- Modify `README.md` only if moved reference links require it.

Historical plans and specs under `docs/80_superpowers/` should remain historically accurate. Do not rewrite old plan bodies just to update paths that were true at the time they were written.

---

### Task 1: Move Durable Root Documents

**Files:**
- Move: `docs/business-plan.md` -> `docs/10_product/business-plan.md`
- Move: `docs/design.md` -> `docs/20_architecture/design.md`
- Move: `docs/architecture.md` -> `docs/20_architecture/architecture.md`
- Move: `docs/data-model.md` -> `docs/20_architecture/data-model.md`
- Move: `docs/modules.md` -> `docs/20_architecture/module-boundaries.md`
- Move: `docs/output-behavior.md` -> `docs/20_architecture/output-contracts.md`
- Move: `docs/pipeline.md` -> `docs/30_pipeline/overview.md`
- Move: `docs/sync-protocol.md` -> `docs/40_development/sync-protocol.md`
- Move: `docs/roadmap.md` -> `docs/00_project/legacy-roadmap.md`
- Move: `docs/vBook需求意向.md` -> `docs/90_reference/original-requirements.md`

- [ ] **Step 1: Move product and reference documents**

Run:

```powershell
git mv docs/business-plan.md docs/10_product/business-plan.md
git mv docs/vBook需求意向.md docs/90_reference/original-requirements.md
```

Expected: both files move with no output.

- [ ] **Step 2: Move architecture documents**

Run:

```powershell
git mv docs/design.md docs/20_architecture/design.md
git mv docs/architecture.md docs/20_architecture/architecture.md
git mv docs/data-model.md docs/20_architecture/data-model.md
git mv docs/modules.md docs/20_architecture/module-boundaries.md
git mv docs/output-behavior.md docs/20_architecture/output-contracts.md
```

Expected: files move with no output.

- [ ] **Step 3: Move pipeline, development, and legacy roadmap documents**

Run:

```powershell
git mv docs/pipeline.md docs/30_pipeline/overview.md
git mv docs/sync-protocol.md docs/40_development/sync-protocol.md
git mv docs/roadmap.md docs/00_project/legacy-roadmap.md
```

Expected: files move with no output.

- [ ] **Step 4: Verify root docs no longer contain loose legacy markdown files**

Run:

```powershell
Get-ChildItem docs -File | Sort-Object Name
```

Expected: output contains only `README.md`.

- [ ] **Step 5: Commit durable doc moves**

Run:

```powershell
git add docs
git commit -m "docs: move durable docs into layers"
```

---

### Task 2: Update Navigation for Durable Document Moves

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/00_project/README.md`
- Modify: `docs/00_project/roadmap.md`
- Modify: `docs/10_product/README.md`
- Modify: `docs/20_architecture/README.md`
- Modify: `docs/30_pipeline/README.md`
- Modify: `docs/40_development/README.md`
- Modify: `docs/50_modules/README.md`
- Modify: `docs/60_operations/README.md`
- Modify: `docs/90_reference/README.md`

- [ ] **Step 1: Update root `README.md` original intent link**

Replace:

```markdown
[`docs/vBook需求意向.md`](docs/vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md)
```

with:

```markdown
[`docs/90_reference/original-requirements.md`](docs/90_reference/original-requirements.md)
```

- [ ] **Step 2: Replace `docs/README.md` legacy section**

Replace the `## Legacy Documents During Migration` section with:

```markdown
## Migrated Source Documents

The original documents now live in the numbered layers:

- [10_product/business-plan.md](./10_product/business-plan.md)
- [20_architecture/design.md](./20_architecture/design.md)
- [20_architecture/architecture.md](./20_architecture/architecture.md)
- [20_architecture/data-model.md](./20_architecture/data-model.md)
- [20_architecture/module-boundaries.md](./20_architecture/module-boundaries.md)
- [20_architecture/output-contracts.md](./20_architecture/output-contracts.md)
- [30_pipeline/overview.md](./30_pipeline/overview.md)
- [40_development/sync-protocol.md](./40_development/sync-protocol.md)
- [00_project/legacy-roadmap.md](./00_project/legacy-roadmap.md)
- [90_reference/original-requirements.md](./90_reference/original-requirements.md)
```

Keep the final vtext independence paragraph unchanged.

- [ ] **Step 3: Update project layer roadmap links**

In `docs/00_project/README.md`, ensure the read-first list still points to `roadmap.md` for the active roadmap.

In `docs/00_project/roadmap.md`, replace:

```markdown
This page summarizes the active roadmap. The legacy roadmap remains available
at [../roadmap.md](../roadmap.md) until the documentation migration is complete.
```

with:

```markdown
This page summarizes the active roadmap. The pre-layering roadmap remains
available at [legacy-roadmap.md](./legacy-roadmap.md).
```

- [ ] **Step 4: Update product layer README**

Replace `docs/10_product/README.md` with:

```markdown
# 10 Product

Product-level documents describe user scenarios, expected workflows, feature
requirements, and acceptance criteria.

## Current Documents

- [business-plan.md](./business-plan.md)

## Reference Source

- [../90_reference/original-requirements.md](../90_reference/original-requirements.md)

## Planned Documents

- `user-scenarios.md`
- `mvp-requirements.md`
- `output-experience.md`
- `workflow.md`
```

- [ ] **Step 5: Update architecture layer README**

Replace `docs/20_architecture/README.md` with:

```markdown
# 20 Architecture

Architecture-level documents describe system design, data contracts, module
boundaries, output contracts, and durable technical decisions.

## Current Documents

- [architecture.md](./architecture.md)
- [design.md](./design.md)
- [data-model.md](./data-model.md)
- [module-boundaries.md](./module-boundaries.md)
- [output-contracts.md](./output-contracts.md)

## Planned Documents

- `decisions.md`
```

- [ ] **Step 6: Update pipeline layer README**

Replace each `../pipeline.md` link in `docs/30_pipeline/README.md` with `./overview.md`.

Replace each `../output-behavior.md` link in `docs/30_pipeline/README.md` with `../20_architecture/output-contracts.md`.

- [ ] **Step 7: Update development, module, operations, and reference READMEs**

In `docs/40_development/README.md`, replace:

```markdown
- [../sync-protocol.md](../sync-protocol.md)
```

with:

```markdown
- [sync-protocol.md](./sync-protocol.md)
```

In `docs/50_modules/README.md`, replace:

```markdown
- [../modules.md](../modules.md)
- [../data-model.md](../data-model.md)
```

with:

```markdown
- [../20_architecture/module-boundaries.md](../20_architecture/module-boundaries.md)
- [../20_architecture/data-model.md](../20_architecture/data-model.md)
```

In `docs/60_operations/README.md`, replace:

```markdown
- [../output-behavior.md](../output-behavior.md)
```

with:

```markdown
- [../20_architecture/output-contracts.md](../20_architecture/output-contracts.md)
```

In `docs/90_reference/README.md`, replace:

```markdown
- [../vBook需求意向.md](../vBook%E9%9C%80%E6%B1%82%E6%84%8F%E5%90%91.md)
- [../sync-protocol.md](../sync-protocol.md)
```

with:

```markdown
- [original-requirements.md](./original-requirements.md)
- [../40_development/sync-protocol.md](../40_development/sync-protocol.md)
```

- [ ] **Step 8: Verify no live docs link to moved root files**

Run:

```powershell
rg -n "\]\([^)]*(business-plan\.md|design\.md|pipeline\.md|modules\.md|data-model\.md|output-behavior\.md|architecture\.md|sync-protocol\.md|vBook需求意向\.md|roadmap\.md)" README.md docs/*.md docs/00_project docs/10_product docs/20_architecture docs/30_pipeline docs/40_development docs/50_modules docs/60_operations docs/70_progress docs/80_superpowers docs/90_reference
```

Expected: matches only point to valid new layered paths, or to `docs/00_project/roadmap.md` and `docs/00_project/legacy-roadmap.md`.

- [ ] **Step 9: Commit durable navigation updates**

Run:

```powershell
git add README.md docs
git commit -m "docs: update links for layered durable docs"
```

---

### Task 3: Move Progress Logs

**Files:**
- Move: `docs/progress/2026-06-25.md` -> `docs/70_progress/2026-06-25.md`
- Modify: `docs/70_progress/README.md`
- Modify: `docs/00_project/status.md`

- [ ] **Step 1: Move dated progress log**

Run:

```powershell
git mv docs/progress/2026-06-25.md docs/70_progress/2026-06-25.md
```

Expected: file moves with no output.

- [ ] **Step 2: Remove empty progress directory if it remains**

Run:

```powershell
if ((Test-Path docs/progress) -and -not (Get-ChildItem docs/progress -Force)) { Remove-Item -LiteralPath docs/progress }
```

Expected: no output.

- [ ] **Step 3: Update progress layer README**

In `docs/70_progress/README.md`, replace:

```markdown
- [../progress/2026-06-25.md](../progress/2026-06-25.md)
```

with:

```markdown
- [2026-06-25.md](./2026-06-25.md)
```

- [ ] **Step 4: Add progress log pointer to status**

In `docs/00_project/status.md`, after the `## Current Phase` section, add:

```markdown
## Progress Log

Detailed dated progress is tracked in [../70_progress/](../70_progress/).
The latest migrated log is [2026-06-25.md](../70_progress/2026-06-25.md).
```

- [ ] **Step 5: Verify progress links**

Run:

```powershell
rg -n "progress/|70_progress" docs/00_project docs/70_progress docs/README.md
```

Expected: no links to `docs/progress/`; links should use `70_progress` or local `./2026-06-25.md`.

- [ ] **Step 6: Commit progress migration**

Run:

```powershell
git add docs
git commit -m "docs: move progress logs into progress layer"
```

---

### Task 4: Move Agent Planning Docs

**Files:**
- Move: `docs/superpowers/specs/*` -> `docs/80_superpowers/specs/*`
- Move: `docs/superpowers/plans/*` -> `docs/80_superpowers/plans/*`
- Modify: `docs/80_superpowers/README.md`

- [ ] **Step 1: Create target directories**

Run:

```powershell
New-Item -ItemType Directory -Force docs/80_superpowers/specs docs/80_superpowers/plans | Out-Null
```

Expected: no output.

- [ ] **Step 2: Move spec files**

Run:

```powershell
Get-ChildItem docs/superpowers/specs -File | ForEach-Object { git mv $_.FullName docs/80_superpowers/specs/ }
```

Expected: no output.

- [ ] **Step 3: Move plan files**

Run:

```powershell
Get-ChildItem docs/superpowers/plans -File | ForEach-Object { git mv $_.FullName docs/80_superpowers/plans/ }
```

Expected: no output.

- [ ] **Step 4: Remove empty legacy superpowers directories**

Run:

```powershell
if ((Test-Path docs/superpowers/specs) -and -not (Get-ChildItem docs/superpowers/specs -Force)) { Remove-Item -LiteralPath docs/superpowers/specs }
if ((Test-Path docs/superpowers/plans) -and -not (Get-ChildItem docs/superpowers/plans -Force)) { Remove-Item -LiteralPath docs/superpowers/plans }
if ((Test-Path docs/superpowers) -and -not (Get-ChildItem docs/superpowers -Force)) { Remove-Item -LiteralPath docs/superpowers }
```

Expected: no output.

- [ ] **Step 5: Update `docs/80_superpowers/README.md`**

Replace:

```markdown
## Current Planning Documents

- [../superpowers/specs/](../superpowers/specs/)
- [../superpowers/plans/](../superpowers/plans/)

## Planned Directories

- `specs/`
- `plans/`
- `reviews/`
- `handoffs/`
```

with:

```markdown
## Current Planning Documents

- [specs/](./specs/)
- [plans/](./plans/)

## Planned Directories

- `reviews/`
- `handoffs/`
```

- [ ] **Step 6: Update docs index if needed**

Check:

```powershell
rg -n "superpowers/" docs/README.md docs/80_superpowers/README.md README.md
```

Expected: no links to `docs/superpowers/`; `docs/80_superpowers/README.md` links to local `specs/` and `plans/`.

- [ ] **Step 7: Commit agent planning migration**

Run:

```powershell
git add docs
git commit -m "docs: move agent planning docs into superpowers layer"
```

---

### Task 5: Final Link and Test Verification

**Files:**
- No planned edits unless verification exposes broken links or stale navigation.

- [ ] **Step 1: Confirm root docs directory is cleanly layered**

Run:

```powershell
Get-ChildItem docs -File | Sort-Object Name
Get-ChildItem docs -Directory | Sort-Object Name
```

Expected: root files show only `README.md`; root directories show numbered layers and no `progress` or `superpowers` directory.

- [ ] **Step 2: Check for stale live navigation links**

Run:

```powershell
rg -n "\]\((\./)?(business-plan|design|pipeline|modules|data-model|output-behavior|architecture|sync-protocol|roadmap|vBook需求意向)\.md|\]\(\.\./(business-plan|design|pipeline|modules|data-model|output-behavior|architecture|sync-protocol|roadmap|vBook需求意向)\.md|\]\([^)]*docs/superpowers|\]\([^)]*docs/progress" README.md docs/README.md docs/00_project docs/10_product docs/20_architecture docs/30_pipeline docs/40_development docs/50_modules docs/60_operations docs/70_progress docs/80_superpowers docs/90_reference
```

Expected: no output.

- [ ] **Step 3: Run full unit suite**

Run:

```powershell
python -m unittest discover
```

Expected: PASS, currently `Ran 60 tests` and `OK`.

- [ ] **Step 4: Check git status**

Run:

```powershell
git status --short --branch
```

Expected: clean worktree on the document reclassification branch.

- [ ] **Step 5: Commit fixes only if needed**

If verification exposes a stale link or doc issue, edit the affected docs and commit with:

```powershell
git add docs README.md
git commit -m "docs: fix layered documentation links"
```

If no fixes are needed, skip this step.

---

## Self-Review

- Spec coverage: The plan implements the approved staged migration strategy: durable docs first, progress logs second, agent planning artifacts last.
- User requirement: It directly answers the request to correctly classify existing `docs/` documents into the numbered structure.
- Root entry safety: `README.md` is updated for the moved original requirements link.
- Navigation safety: Each task includes targeted `rg` checks for stale links.
- Historical artifact policy: Old plans/specs are moved but their internal historical content is not rewritten solely for path churn.
- Placeholder scan: This plan contains no unresolved placeholder markers.
- Type/path consistency: All source and target paths match the current docs tree and approved numbered layers.
