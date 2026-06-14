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
- Promotion promotes only reviewed high-quality experiences and supports quarantine review.
- Governance enforces boss approval, copyright/license rules, external upload bans, and risky permissions.
- Runtime records traces, checklists, artifact manifests, and replayable execution evidence.
- Orchestration composes engines from configuration.
- Tests, examples, compile checks, and README link checks pass.
- GitHub PR/release history is verifiable.

## Phases

### Phase 0. Foundation

Status: complete.

Includes package skeleton, basic engines, contracts, bilingual README, tests, examples, and public GitHub repo.

### Phase 1. Data And Curriculum Core

Status: in progress.

Includes `DataAcquisitionEngine`, `CurriculumMappingEngine`, seed catalog, license gates, sample standards, and a data/curriculum pipeline example.

Remaining:

- manifest load/save API
- acquired source validation report
- curriculum importer
- coverage gap recommendations

### Phase 2. Assessment And Cultivation Core

Status: next implementation batch.

Deliverables:

- assessment item bank
- objective, short-answer, written-response, and solution-process item models
- answers, distractors, explanations, scoring rubric
- cultivation learning roadmap
- learning roadmap to data source linkage
- assessment gate generation

### Phase 3. Stress And Promotion Core

Deliverables:

- scenario bank
- misconception, contradiction, time pressure, and trap-item simulation
- promotion ledger versioning
- quarantine review workflow
- rollback or supersede decisions

### Phase 4. Governance And Runtime Core

Deliverables:

- policy rule evaluator
- boss approval records
- license approval records
- runtime artifact manifest
- replayable trace

### Phase 5. Orchestration And CLI

Deliverables:

- config-driven suite runner
- CLI commands
- JSON input/output
- end-to-end local growth pipeline
- engine smoke commands

### Phase 6. Documentation, Release, And Examples

Deliverables:

- bilingual docs
- per-engine README files
- example data
- architecture diagrams
- release checklist
- GitHub PR/release

## Active Branch

```text
codex/real-engine-v02
```

Draft PR:

```text
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## Next Work

Start Phase 2 as a batch:

1. Add assessment item bank tests.
2. Strengthen assessment rubric/results.
3. Add cultivation roadmap tests.
4. Implement cultivation roadmap.
5. Add data/curriculum/assessment example.
6. Run full validation.
7. Commit, push, and update PR.
