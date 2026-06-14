# 22B Paideia Engines Master Development Plan

[한국어](master_development_plan.ko.md)

## Goal

`22b-paideia-engines` is not a sample package. It is intended to become a reusable engine suite for the Boss's future AI systems. The final product must support local-first data acquisition, curriculum mapping, cultivation, assessment, stress rehearsal, promotion, governance, runtime tracing, configuration-driven orchestration, and release-ready documentation.

## Final Definition Of Done

The project is complete only when:

- Every engine has an independent API, contract, tests, examples, and documentation.
- Data acquisition records source, license, hash, approver, and local path.
- Curriculum mapping builds learning units from grade, subject, domain, and achievement standards.
- Cultivation creates learning roadmaps from curriculum units and licensed data sources.
- Assessment supports item banks, answers, distractors, explanations, written-response scoring, and solution-process rubrics.
- Stress simulates misconceptions, time pressure, contradictory evidence, trap items, and missing review.
- Promotion promotes only reviewed high-quality experiences and supports quarantine review, versioning, and supersession.
- Governance enforces boss approval, copyright/license rules, external upload bans, risky permissions, and committee decision trails.
- Runtime records traces, acceptance checklists, artifact manifests, and replayable execution evidence.
- Orchestration composes engines from configuration without hiding individual engine contracts.
- CLI commands provide JSON input/output and engine-by-engine smoke checks.
- Tests, examples, compile checks, CLI checks, and README link checks pass.
- GitHub PR/release history is verifiable.

## Phase Status

| Phase | Area | Status |
| --- | --- | --- |
| 0 | Foundation package and initial engines | Complete |
| 1 | Data acquisition and curriculum mapping | Implemented v0.2 core |
| 2 | Assessment and cultivation | Implemented v0.2 core |
| 3 | Stress and promotion | Implemented v0.2 core |
| 4 | Governance and runtime | Implemented v0.2 core |
| 5 | Orchestration and CLI | Implemented v0.2 core |
| 6 | Documentation, release, examples | In progress |

## Phase 0. Foundation

Delivered:

- Python package skeleton
- Basic engines
- Shared contracts
- Bilingual README
- Basic tests and examples
- Public GitHub repository

## Phase 1. Data And Curriculum Core

Delivered:

- `DataAcquisitionEngine`
- `CurriculumMappingEngine`
- Education data seed catalog
- License gates
- Sample standards
- Data/curriculum pipeline example

Remaining depth:

- Stronger manifest load/save API
- Acquired source validation report
- Curriculum standard importer
- Coverage gap recommendations

## Phase 2. Assessment And Cultivation Core

Delivered:

- Assessment item bank
- Objective, short-answer, written-response, and solution-process item models
- Answers, distractors, explanations, and scoring rubric
- Cultivation learning roadmap
- Learning roadmap to data source linkage
- Assessment gate generation

## Phase 3. Stress And Promotion Core

Delivered:

- Stress scenario bank
- Misconception, contradiction, time-pressure, and trap-item scenarios
- Candidate-only stress signals
- Promotion ledger versioning
- Quarantine review workflow
- Supersede decisions without deleting history

## Phase 4. Governance And Runtime Core

Delivered:

- Policy rule evaluator
- Boss approval records
- License approval records
- Committee decision ledger
- Runtime artifact manifest
- Replayable trace
- Run acceptance checklist

## Phase 5. Orchestration And CLI

Delivered:

- Config-driven suite runner
- CLI commands
- JSON config input and JSON result output
- Per-engine JSON output files
- End-to-end local growth pipeline
- Engine-by-engine smoke commands
- Configured-suite verification output

Completion criteria reached:

- One local command runs data acquisition, curriculum mapping, cultivation, assessment, stress, promotion, governance, runtime, and verification.
- Each step records output paths and trace metadata.
- Smoke command checks individual engine contracts without changing existing `PaideiaEngineSuite.run_growth_cycle`.

Commands:

```powershell
python -m paideia_engines.cli run-config `
  --config examples/configured_suite.json `
  --output .paideia-runs/result.json `
  --output-dir .paideia-runs/engines

python -m paideia_engines.cli smoke --engine all --output .paideia-runs/smoke.json
```

## Phase 6. Documentation, Release, And Examples

Planned deliverables:

- Beginner-facing bilingual guide
- Per-engine README files
- Example data index
- Architecture diagrams
- Release checklist
- GitHub release or ready PR

Completion criteria:

- New users can install, test, run examples, run CLI, and understand outputs from the README.
- Korean documentation can be selected from README.
- Public release excludes restricted textbooks, private voice data, credentials, and personal assets.
- Release checklist proves tests, examples, compile checks, CLI checks, and sensitive-string scans.

## Active Branch And PR

```text
codex/real-engine-v02
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## Next Work

Move to Phase 6 as a batch:

1. Add per-engine README files.
2. Add beginner-facing Korean and English release guide.
3. Add release checklist and public asset audit.
4. Add dataset adapter backlog and validation report docs.
5. Run full validation.
6. Commit, push, and update the draft PR.
