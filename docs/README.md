# vBook Documentation

This directory uses numbered documentation layers. Start here before reading
implementation code or dated progress logs.

## Fast Reading Path

For project orientation:

1. [00_project/overview.md](./00_project/overview.md)
2. [00_project/glossary.md](./00_project/glossary.md)
3. [00_project/status.md](./00_project/status.md)
4. [00_project/roadmap.md](./00_project/roadmap.md)

For development work:

1. [00_project/glossary.md](./00_project/glossary.md)
2. [00_project/status.md](./00_project/status.md)
3. [30_pipeline/README.md](./30_pipeline/README.md)
4. [20_architecture/README.md](./20_architecture/README.md)
5. [40_development/README.md](./40_development/README.md)

## Documentation Layers

| Layer | Purpose |
| --- | --- |
| [00_project/](./00_project/) | Project positioning, glossary, scope, roadmap, and status |
| [10_product/](./10_product/) | User scenarios, product workflow, requirements, and acceptance criteria |
| [20_architecture/](./20_architecture/) | System architecture, module boundaries, data contracts, and decisions |
| [30_pipeline/](./30_pipeline/) | Stage-by-stage media-to-knowledge pipeline documentation |
| [40_development/](./40_development/) | Setup, commands, testing, Git workflow, and agent collaboration |
| [50_modules/](./50_modules/) | Package-level documentation for `vbook_*` modules |
| [60_operations/](./60_operations/) | Local runs, smoke tests, troubleshooting, and artifact cleanup |
| [70_progress/](./70_progress/) | Status snapshots, backlog, milestones, and dated progress logs |
| [80_superpowers/](./80_superpowers/) | Agent specs, implementation plans, reviews, and handoffs |
| [90_reference/](./90_reference/) | Original requirements, external references, and vtext boundary material |

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

vBook can learn from vtext's project structure and workflow ideas, but it must
remain an independent project with independent modules, interfaces, and
evolution.
