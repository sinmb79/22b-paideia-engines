# 22B Paideia Engines Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, reusable Paideia engine suite with independent cultivation, assessment, stress, promotion, governance, runtime, and orchestration engines, then publish it as a new GitHub repository with English and Korean documentation.

**Architecture:** The package is a local-first Python library. `contracts` defines shared schemas, events, decisions, and policy objects. Each engine lives in its own package, exposes a small public API, and can be used alone or through the `PaideiaEngineSuite` orchestrator.

**Tech Stack:** Python 3.11+, standard library only at runtime, `pytest` for tests, Markdown documentation, GitHub CLI for repository publication.

---

## File Structure

- Create: `pyproject.toml`
- Create: `README.md`
- Create: `README.ko.md`
- Create: `LICENSE`
- Create: `src/paideia_engines/__init__.py`
- Create: `src/paideia_engines/contracts/`
- Create: `src/paideia_engines/cultivation/`
- Create: `src/paideia_engines/assessment/`
- Create: `src/paideia_engines/stress/`
- Create: `src/paideia_engines/promotion/`
- Create: `src/paideia_engines/governance/`
- Create: `src/paideia_engines/runtime/`
- Create: `src/paideia_engines/orchestration/`
- Create: `examples/basic_growth_cycle.py`
- Create: `tests/`

## Task 1: Project and Contract Skeleton

**Files:**

- Create: `tests/test_contracts.py`
- Create: `src/paideia_engines/contracts/__init__.py`
- Create: `src/paideia_engines/contracts/models.py`
- Create: `src/paideia_engines/contracts/policies.py`
- Create: `pyproject.toml`

- [ ] **Step 1: Write failing contract tests**

Test that engine events, review labels, and promotion decisions can be created and serialized.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_contracts.py -q`

- [ ] **Step 3: Implement contract models**

Add dataclasses for `EngineEvent`, `ReviewLabel`, `PromotionDecision`, `QuarantineDecision`, and local-only policy constants.

- [ ] **Step 4: Verify tests pass**

Run: `python -m pytest tests/test_contracts.py -q`

## Task 2: Independent Engines

**Files:**

- Create: one test file per engine under `tests/`
- Create: one engine module per engine under `src/paideia_engines/<engine>/`

- [ ] **Step 1: Write failing tests for each engine**

Cover cultivation blueprint creation, assessment rubric scoring, stress rollout generation, promotion/quarantine, governance review gates, runtime trace creation, and orchestration.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests -q`

- [ ] **Step 3: Implement each engine minimally**

Each engine must have a class API and deterministic data outputs.

- [ ] **Step 4: Verify tests pass**

Run: `python -m pytest tests -q`

## Task 3: Documentation and Examples

**Files:**

- Create: `README.md`
- Create: `README.ko.md`
- Create: `docs/architecture.md`
- Create: `docs/architecture.ko.md`
- Create: `examples/basic_growth_cycle.py`

- [ ] **Step 1: Write documentation checks**

Test that README language links and example file exist.

- [ ] **Step 2: Write docs and example**

README.md is English default and links to Korean. README.ko.md links back to English.

- [ ] **Step 3: Run example**

Run: `python examples/basic_growth_cycle.py`

## Task 4: Packaging, Validation, and GitHub Publish

**Files:**

- Modify: all package files

- [ ] **Step 1: Run validation**

Run:

```powershell
python -m pytest tests -q
python examples/basic_growth_cycle.py
python -m compileall src
```

- [ ] **Step 2: Initialize git**

Run: `git init -b main`

- [ ] **Step 3: Commit**

Stage only this new repo's files and commit.

- [ ] **Step 4: Create GitHub repo and push**

Run: `gh repo create sinmb79/22b-paideia-engines --public --source . --remote origin --push`

- [ ] **Step 5: Verify**

Run:

```powershell
git status --short --branch
git remote -v
gh repo view sinmb79/22b-paideia-engines --json name,url,visibility,defaultBranchRef
```
