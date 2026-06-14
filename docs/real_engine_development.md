# Real Engine Development Roadmap

[한국어](real_engine_development.ko.md)

This roadmap tracks the work needed to turn the Paideia engine suite from a scaffold into reusable engine assets.

## Current Position

The suite now has v0.2 cores for data acquisition, curriculum mapping, cultivation, assessment, stress, promotion, governance, runtime, and config-driven orchestration. Phase 6 adds release hardening. Phase 7 adds acquired-source validation reports and JSON adapters. Phase 8 adds NCIC/data.go.kr-style CSV parsing, AI-Hub-like math JSON parsing, public assessment CSV parsing, and public exam metadata manifests. Phase 9 adds parser diagnostics and public-safe fixture packs. Phase 10 adds configured-suite output validation. Phase 11 adds acquired-source manifest diagnostics. Phase 12 adds subject-specific stress packs. Phase 13 adds the public engine contract registry. Phase 14 adds adapter certification that links parser fixtures to valid acquired-source manifest records. The next depth work is evaluation and benchmark fixtures.

## Phase 1: Data And Curriculum

Added:

```text
src/paideia_engines/data_acquisition/
src/paideia_engines/curriculum_mapping/
examples/data_and_curriculum_pipeline.py
data/curriculum/sample_standards.json
```

Capabilities:

- License-gated source decisions
- Engine-specific acquisition plans
- Restricted textbook blocking
- Acquired source hashing
- JSONL manifest writing
- Learning unit generation from achievement standards

## Phase 2: Assessment And Cultivation

Added:

```text
src/paideia_engines/assessment/item_bank.py
examples/assessment_and_cultivation_pipeline.py
```

Capabilities:

- Assessment item bank
- Gate construction
- Objective, short-answer, and solution-process item models
- Per-item rubric scoring
- Review-label candidate output
- Cultivation roadmap generation from learning units

## Phase 3: Stress And Promotion

Added:

```text
src/paideia_engines/stress/scenario_bank.py
examples/stress_and_promotion_pipeline.py
```

Capabilities:

- Stress scenario bank mapped to curriculum standards
- Scenario selection by standard and stressor type
- Candidate-only promotion signals
- Trap-risk detection
- Versioned promotion ledger
- Quarantine reconsideration
- Promoted experience supersession without deleting history

## Phase 4: Governance And Runtime

Added:

```text
examples/governance_and_runtime_pipeline.py
```

Capabilities:

- Policy rule evaluation
- Boss and license approval records
- Committee decision ledger
- Hard external-upload blocking
- Runtime run IDs
- Runtime artifact manifests
- Replayable runtime traces
- Acceptance checklist evidence for promotion review

## Phase 5: Orchestration And CLI

Added:

```text
src/paideia_engines/orchestration/config_runner.py
src/paideia_engines/cli.py
examples/configured_suite.json
```

Capabilities:

- Config-driven suite runner
- JSON config input and JSON result output
- Per-engine JSON output files
- End-to-end local growth pipeline
- Engine-by-engine smoke command
- Configured-suite verification output
- Console entry point: `paideia-engines`

Example:

```powershell
python -m paideia_engines.cli run-config `
  --config examples/configured_suite.json `
  --output .paideia-runs/result.json `
  --output-dir .paideia-runs/engines

python -m paideia_engines.cli smoke --engine all --output .paideia-runs/smoke.json
```

## Phase 7: Dataset Adapters And Validation

Added:

```text
tests/test_dataset_adapters_and_validation.py
```

Capabilities:

- Acquired-source manifest loading
- Hash, local path, approver, and license-note validation
- Restricted full-content source blocking
- Restricted metadata-only manifest path
- Public curriculum standards JSON import
- Public or licensed assessment item JSON import
- Configured-suite `acquisition_validation` output

## Phase 8: Source-Specific Parsers

Added:

```text
src/paideia_engines/data_acquisition/source_parsers.py
examples/source_specific_parsers.py
examples/source_samples/
tests/test_source_specific_parsers.py
```

Capabilities:

- NCIC/data.go.kr-style curriculum CSV parsing
- Public assessment CSV parsing
- AI-Hub-like math problem JSON parsing
- EBSi/public exam metadata-only manifest building
- Config runner parser/source pairing checks

## Phase 9: Source Parser Diagnostics

Added:

```text
src/paideia_engines/data_acquisition/source_diagnostics.py
examples/source_fixture_pack.json
tests/test_source_diagnostics.py
```

Capabilities:

- Fixture-pack diagnostics report
- File existence, hash, parser support, extension, and required-field checks
- Parser completion and output record-count checks
- CLI command: `diagnose-source`

## Phase 10: Configured-Suite Output Validation

Added:

```text
src/paideia_engines/orchestration/output_validator.py
tests/test_configured_suite_output_validator.py
```

Capabilities:

- Per-engine JSON output validation without rerunning engines
- Full suite result to engine-file cross-checks
- Numbered output file validation from `01_data_acquisition.json` to `10_verification.json`
- Engine schema contract checks
- Release guardrails for acquisition validation, assessment, verification, stress candidate-only boundaries, governance, and runtime replayability
- CLI command: `validate-suite-output`

## Phase 11: Acquired-Source Manifest Diagnostics

Added:

```text
src/paideia_engines/data_acquisition/manifest_diagnostics.py
examples/acquired_sources_manifest.jsonl
tests/test_acquired_source_manifest_diagnostics.py
```

Capabilities:

- JSONL manifest diagnostics that report issues instead of crashing release checks
- Duplicate source/path record detection
- Acquired-source schema and content-scope checks
- Reuse of acquired-source validation for hash, path, approver, and license-note checks
- Public-release guardrail for non-open full-content records
- CLI command: `diagnose-manifest`

## Phase 12: Subject-Specific Stress Packs

Added:

```text
examples/stress_packs/core_subject_stress_pack.json
tests/test_stress_scenario_packs.py
```

Capabilities:

- Public-safe reusable stress pack for math, language, science, and evidence review
- Stress pack JSON loader through `StressScenarioBank.from_file(...)`
- Stress pack diagnostics for schema, unique ids, valid scenarios, curriculum links, subject coverage, and promotion-boundary cleanliness
- CLI command: `diagnose-stress-pack`

## Phase 13: Engine Contract Registry

Added:

```text
src/paideia_engines/contracts/registry.py
docs/engine_contracts.md
docs/engine_contracts.ko.md
```

Capabilities:

- Public contract registry for every reusable engine
- API, input schema, output schema, CLI, example, doc, safety-boundary, and compatibility declarations
- Contract validation report
- CLI command: `validate-contracts`
- Pre-1.0 compatibility policy for additive changes, schema bumps, and deprecations

## Phase 14: Official Adapter Certification Matrix

Added:

```text
src/paideia_engines/data_acquisition/adapter_certification.py
examples/source_samples/public_assessment_sample.csv
tests/test_adapter_certification.py
```

Capabilities:

- Adapter certification report that links source fixture diagnostics to acquired-source manifest diagnostics
- CLI command: `certify-adapters`
- Parser/source allowlist checks
- Fixture path/hash/source_id linkage to acquired-source manifest records
- Public-safe sample policy for synthetic, metadata-only, and open-public fixture exports
- Public assessment CSV fixture coverage alongside NCIC/data.go.kr, AI-Hub-like, and EBSi metadata fixtures

## Next Development Order

1. Evaluation and benchmark pack for engine-by-engine regression testing.
2. Persistent runtime and evidence store for replayable run bundles.
3. Release candidate pipeline with wheel install smoke, CLI matrix, link/encoding checks, and concrete sensitive scans.
4. Downstream reuse recipes for other 22B AI projects.

## Verification

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python -m paideia_engines.cli validate-contracts --repo-root . --output .paideia-runs\contract-validation.json
python -m paideia_engines.cli certify-adapters --fixtures examples\source_fixture_pack.json --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\adapter-certification.json
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli diagnose-stress-pack --pack examples\stress_packs\core_subject_stress_pack.json --output .paideia-runs\stress-pack-diagnostics.json
python -m paideia_engines.cli run-config --config examples\configured_suite.json --output .paideia-runs\result.json --output-dir .paideia-runs\engines
python -m paideia_engines.cli validate-suite-output --output-dir .paideia-runs\engines --result .paideia-runs\result.json --output .paideia-runs\suite-output-validation.json
python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
```
