# Experiment Review Round Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable review round package generator for formal vBook experiments.

**Architecture:** Implement a focused `tools/experiment_review_round.py` helper that scans `renders/<route>/<variant>/<lesson>/` directories and writes four review files under `reviews/<round-id>/`. Keep scoring human-owned while importing automatic preflight status as objective evidence.

**Tech Stack:** Python standard library, `unittest`, CSV, JSON, Markdown.

---

### Task 1: Add Failing Tool Tests

**Files:**

- Create: `tests/test_tools/test_experiment_review_round.py`

- [ ] **Step 1: Write fixture-based tests**

Create tests that build a temporary experiment root with two routes, two lesson
previews, and one preflight JSON under `comparisons/`.

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_experiment_review_round
```

Expected: import fails because `tools.experiment_review_round` does not exist.

### Task 2: Implement Review Round Generator

**Files:**

- Create: `tools/experiment_review_round.py`

- [ ] **Step 1: Implement data discovery**

Discover note candidates from:

```text
renders/<route>/<variant>/<lesson>/
```

Prefer `note.md`, `visual-evidence.md`, then `enhancement.md`.

- [ ] **Step 2: Implement preflight status loading**

Read `comparisons/*preflight*.json`; set route status to `pass`, `fail`, or
`not_applicable`.

- [ ] **Step 3: Write output files**

Write:

```text
review-manifest.json
review-sheet.csv
user-review.md
decision-template.md
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_experiment_review_round
```

Expected: all tests pass.

### Task 3: Document Workflow

**Files:**

- Modify: `docs/60_operations/experiment-workflow.md`
- Modify: `docs/60_operations/experiment-artifacts.md`
- Modify: `docs/70_progress/2026-07-11-existing-model-baseline-plan.md`

- [ ] **Step 1: Update Phase 6 review workflow**

Document that each user comparison creates `reviews/<round-id>/`.

- [ ] **Step 2: Update artifact layout**

Document the four review round files and their purpose.

- [ ] **Step 3: Update progress note**

Record the creation of the standard review round generator.

### Task 4: Generate Current Round And Verify

**Files:**

- Write outside repo: `F:/vbook/experiments/E20260711-existing-model-baselines/reviews/round-002/`

- [ ] **Step 1: Run generator**

Run:

```powershell
D:\anaconda3\envs\App\python.exe tools\experiment_review_round.py `
  --experiment-root "F:\vbook\experiments\E20260711-existing-model-baselines" `
  --round-id round-002 `
  --dataset-id investment-camp-hanke-basic-v1
```

- [ ] **Step 2: Run verification**

Run:

```powershell
D:\anaconda3\envs\App\python.exe -m unittest tests.test_tools.test_experiment_review_round
D:\anaconda3\envs\App\python.exe -m unittest discover
D:\anaconda3\envs\App\python.exe -m vbook_client check
```

- [ ] **Step 3: Commit**

Commit with:

```powershell
git add docs tools tests
git commit -m "Add experiment review round generator"
```
