# 22B Paideia Engines Master Development Plan

[한국어](master_development_plan.ko.md)

## Goal

`22b-paideia-engines` is not a sample package. It is intended to become a reusable engine suite for the Boss's future AI systems. The final product must support local-first data acquisition, curriculum mapping, cultivation, assessment, stress rehearsal, promotion, governance, runtime tracing, configuration-driven orchestration, and release-ready documentation.

## Final Definition Of Done

The project is complete only when:

- Every engine has an independent API, contract, tests, examples, and documentation.
- Data acquisition records source, license, hash, approver, and local path.
- Acquired-source manifest diagnostics catch malformed, duplicate, unsafe, and public-release-ineligible records.
- Acquired-source validation blocks invalid hashes, missing approvers, missing license notes, and unsafe full-content restricted sources.
- Curriculum mapping builds learning units from grade, subject, domain, and achievement standards.
- Cultivation creates learning roadmaps from curriculum units and licensed data sources.
- Assessment supports item banks, answers, distractors, explanations, written-response scoring, and solution-process rubrics.
- Stress simulates misconceptions, time pressure, contradictory evidence, trap items, and missing review.
- Promotion promotes only reviewed high-quality experiences and supports quarantine review, versioning, and supersession.
- Governance enforces boss approval, copyright/license rules, external upload bans, risky permissions, and committee decision trails.
- Runtime records traces, acceptance checklists, artifact manifests, and replayable execution evidence.
- Orchestration composes engines from configuration without hiding individual engine contracts.
- CLI commands provide JSON input/output, configured-suite output validation, and engine-by-engine smoke checks.
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
| 6 | Documentation, release, examples | Implemented v0.2 release hardening |
| 7 | Dataset adapters and validation reports | Implemented v0.2 core |
| 8 | Source-specific parsers | Implemented v0.2 core |
| 9 | Source parser diagnostics and fixture packs | Implemented v0.2 core |
| 10 | Configured-suite output validator | Implemented v0.2 core |
| 11 | Acquired-source manifest diagnostics | Implemented v0.2 core |

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

Delivered:

- Beginner-facing bilingual guide
- Per-engine README files
- Example data index
- Architecture diagrams
- Release checklist
- Public asset audit
- Dataset adapter backlog
- GitHub PR update path

Completion criteria:

- New users can install, test, run examples, run CLI, and understand outputs from the README.
- Korean documentation can be selected from README.
- Public release excludes restricted textbooks, private voice data, credentials, and personal assets.
- Release checklist proves tests, examples, compile checks, CLI checks, and sensitive-string scans.

## Phase 7. Dataset Adapters And Validation Reports

Delivered:

- Acquired-source manifest loader
- Acquired-source validation report
- Hash, local path, approver, and license-note checks
- `metadata_only` safe path for restricted textbook metadata
- Public curriculum standards JSON adapter
- Public or licensed assessment item-bank JSON adapter
- Configured-suite `acquisition_validation` output

Completion criteria:

- Restricted full-content textbook sources are blocked without a valid license or terms-review note.
- Restricted metadata-only records can be tracked without copying protected source content.
- Public curriculum JSON can become `CurriculumStandard` records.
- Public or licensed assessment JSON can become `AssessmentItem` records.
- Configured-suite verification includes acquisition validation.

## Phase 8. Source-Specific Parsers

Delivered:

- NCIC/data.go.kr-style curriculum CSV parser
- Public assessment CSV parser
- AI-Hub-like math problem JSON parser
- Public exam metadata CSV manifest builder
- Config runner parser/source pairing checks
- Source parser samples and example script

Completion criteria:

- Source-specific parsers run only on files that passed acquisition validation.
- Parser/source mismatches are rejected.
- AI-Hub-like data requires terms/license note validation before parser use.
- EBSi/public exam data stays metadata-only and does not create assessment items from protected documents.

## Phase 9. Source Parser Diagnostics And Fixture Packs

Delivered:

- Source parser diagnostics report
- Public-safe source fixture pack manifest
- Required CSV header and JSON field checks
- Parser completion and record-count checks
- CLI command for fixture diagnostics

Completion criteria:

- Fixture packs use relative paths and public-safe sample or metadata-only content.
- Diagnostics report file existence, hash, parser support, required fields, parser completion, and output record count.
- Failed parser runs are reported as diagnostics issues instead of being hidden.
- Release checklist includes the diagnostics CLI command.

## Phase 10. Configured-Suite Output Validator

Delivered:

- Per-engine output validator for configured-suite runs
- Result JSON to engine-file cross-checks
- Expected numbered file checks from `01_data_acquisition.json` through `10_verification.json`
- Engine schema contract checks
- Release guardrails for acquisition validation, final verification, stress-to-promotion boundaries, governance, and runtime replayability
- CLI command: `validate-suite-output`

Completion criteria:

- A configured-suite run can be validated without rerunning any engine.
- Missing or tampered per-engine output files block release validation.
- Stress output remains candidate-only and cannot directly include promotion decision records.
- Release checklist includes the output validator CLI command.

## Phase 11. Acquired-Source Manifest Diagnostics

Delivered:

- Acquired-source JSONL manifest diagnostics
- Public-safe manifest example
- JSONL parsing, acquired-source schema, duplicate record, content-scope, hash/license-note, auto-download, and public-release safety checks
- CLI command: `diagnose-manifest`

Completion criteria:

- Manifest diagnostics catch malformed JSONL without crashing release checks.
- Duplicate source/path records block release validation.
- Non-open full-content records are blocked for public release unless explicitly running in local-only mode.
- Release checklist includes the manifest diagnostics CLI command.

## Active Branch And PR

```text
codex/real-engine-v02
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## Next Work

Final release loop for this branch:

1. Run full validation.
2. Commit and push the latest output-validation and release-readiness changes.
3. Update the draft PR with the new validation evidence.
4. Convert the PR to ready or cut a release only after the checklist remains green.
