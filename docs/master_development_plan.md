# 22B Paideia Engines Master Development Plan

[한국어](master_development_plan.ko.md)

## Goal

`22b-paideia-engines` is not a sample package. It is intended to become a reusable engine suite for the Boss's future AI systems. The final product must support local-first data acquisition, curriculum mapping, cultivation, assessment, stress rehearsal, promotion, governance, runtime tracing, and orchestration.

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
- Tests, examples, compile checks, and README link checks pass.
- GitHub PR/release history is verifiable.

## Phase Status

| Phase | Area | Status |
| --- | --- | --- |
| 0 | Foundation package and initial engines | Complete |
| 1 | Data acquisition and curriculum mapping | Implemented, still needs deeper importers |
| 2 | Assessment and cultivation | Implemented v0.2 core |
| 3 | Stress and promotion | Implemented v0.2 core |
| 4 | Governance and runtime | Implemented v0.2 core |
| 5 | Orchestration and CLI | Planned |
| 6 | Documentation, release, examples | Ongoing |

## Phase 0. Foundation

Delivered:

- Python package skeleton
- Seven basic engines
- Shared contracts
- Bilingual README
- Basic tests and examples
- Public GitHub repository

Verification:

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
```

## Phase 1. Data And Curriculum Core

Delivered:

- `DataAcquisitionEngine`
- `CurriculumMappingEngine`
- Education data seed catalog
- License gates
- Sample standards
- Data/curriculum pipeline example

Remaining depth:

- Manifest load/save API
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

Completion criteria reached:

- Learning units can produce assessment gates and item banks.
- Assessment results can create review-label candidates for promotion.
- Learning roadmaps preserve data-source license state.

## Phase 3. Stress And Promotion Core

Delivered:

- Stress scenario bank
- Misconception, contradiction, time-pressure, and trap-item scenarios
- Candidate-only stress signals
- Promotion ledger versioning
- Quarantine review workflow
- Supersede decisions without deleting history

Completion criteria reached:

- Stress creates promotion candidate signals but not promotion decisions.
- Promotion never promotes memory without a verified review label.
- Quarantined and superseded experiences are excluded from active memory routing.

## Phase 4. Governance And Runtime Core

Delivered:

- Policy rule evaluator
- Boss approval records
- License approval records
- Committee decision ledger
- Runtime artifact manifest
- Replayable trace
- Run acceptance checklist

Completion criteria reached:

- Restricted source use is blocked without approval records.
- External uploads, credentials, and private asset access stay blocked by default.
- Runtime results remain review-required before promotion.
- Runtime traces can be replayed by `run_id`.
- Artifact manifests are retained with hashable records.

Example:

```powershell
python examples\governance_and_runtime_pipeline.py
```

## Phase 5. Orchestration And CLI

Planned deliverables:

- Config-driven suite runner
- CLI commands
- JSON input/output
- End-to-end local growth pipeline
- Engine-by-engine smoke commands

Completion criteria:

- One local command runs data planning, curriculum mapping, cultivation, assessment, stress, promotion, governance, runtime, and verification.
- Each step records output paths and trace metadata.

## Phase 6. Documentation, Release, And Examples

Planned deliverables:

- Beginner-facing bilingual guide
- Per-engine README files
- Example data
- Architecture diagrams
- Release checklist
- GitHub PR/release

Completion criteria:

- New users can install, test, and run examples from the README.
- Korean documentation can be selected from README.
- Public release excludes restricted textbooks, private voice data, credentials, and personal assets.

## Active Branch And PR

```text
codex/real-engine-v02
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## Next Work

Move to Phase 5 as a batch:

1. Add config-driven orchestration tests.
2. Add CLI command tests.
3. Implement engine-by-engine smoke commands.
4. Add JSON input/output examples.
5. Run full validation.
6. Commit, push, and update the draft PR.
