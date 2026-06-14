# Release Guide

[한국어](release_guide.ko.md)

This guide is for a new user who wants to install, test, and run Paideia Engines locally.

## Install

```powershell
git clone https://github.com/sinmb79/22b-paideia-engines.git
cd 22b-paideia-engines
python -m pip install -e .[dev]
```

## Verify

```powershell
python -m pytest tests -q
python -m compileall src
```

## Run Examples

```powershell
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python examples\source_specific_parsers.py
python examples\downstream_single_engine_recipe.py
python examples\downstream_suite_recipe.py
python -m paideia_engines.cli validate-contracts --repo-root . --output .paideia-runs\contract-validation.json
python -m paideia_engines.cli certify-adapters --fixtures examples\source_fixture_pack.json --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\adapter-certification.json
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli diagnose-stress-pack --pack examples\stress_packs\core_subject_stress_pack.json --output .paideia-runs\stress-pack-diagnostics.json
```

## Run CLI

```powershell
python -m paideia_engines.cli run-config `
  --config examples\configured_suite.json `
  --output .paideia-runs\result.json `
  --output-dir .paideia-runs\engines

python -m paideia_engines.cli validate-suite-output `
  --output-dir .paideia-runs\engines `
  --result .paideia-runs\result.json `
  --output .paideia-runs\suite-output-validation.json

python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json

python -m paideia_engines.cli persist-runtime-evidence `
  --runtime-output .paideia-runs\engines\08_runtime.json `
  --store-dir .paideia-runs\runtime `
  --artifact-base-dir examples `
  --output .paideia-runs\runtime-evidence-bundle.json

python -m paideia_engines.cli validate-runtime-evidence `
  --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json `
  --output .paideia-runs\runtime-evidence-validation.json

python -m paideia_engines.cli replay-runtime-evidence `
  --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json `
  --output .paideia-runs\runtime-evidence-replay.json

python -m paideia_engines.cli validate-benchmarks `
  --pack examples\benchmark_packs\core_engine_benchmark_pack.json `
  --result .paideia-runs\result.json `
  --output-dir .paideia-runs\engines `
  --reports-dir .paideia-runs `
  --output .paideia-runs\benchmark-validation.json

python -m paideia_engines.cli validate-release-candidate `
  --repo-root . `
  --output .paideia-runs\release-candidate-validation.json
```

## Output Meaning

- `result.json`: full configured-suite result.
- `.paideia-runs/engines/*.json`: per-engine outputs.
- `contract-validation.json`: public engine API, schema, doc, example, and safety-boundary registry validation.
- `adapter-certification.json`: adapter certification matrix proving parser fixtures link to valid acquired-source manifest records.
- `manifest-diagnostics.json`: acquired-source manifest diagnostics for JSONL parsing, hashes, duplicate records, license notes, and public-release safety.
- `stress-pack-diagnostics.json`: stress scenario pack diagnostics for curriculum links, subject coverage, and promotion-boundary cleanliness.
- `02_acquisition_validation.json`: acquired-source validation report.
- `10_verification.json`: final verification summary for the configured run.
- `suite-output-validation.json`: release-quality validation report that cross-checks result JSON, per-engine files, schemas, and stress-to-promotion boundaries.
- `smoke.json`: engine-by-engine smoke result.
- `runtime-evidence-bundle.json`: persisted runtime evidence bundle index.
- `runtime-evidence-validation.json`: artifact file existence, size, byte hash, manifest hash, and trace replay validation.
- `runtime-evidence-replay.json`: replayable trace loaded from the persisted bundle.
- `benchmark-validation.json`: release benchmark report that checks golden schemas, mutation expectations, and evidence thresholds.
- `release-candidate-validation.json`: packaging metadata, links, UTF-8, replacement-character, sensitive-pattern, personal-path, acquired-source manifest, and public-asset validation.
- `downstream_single_engine_recipe.py`: verifies that one engine can be imported as a focused downstream asset.
- `downstream_suite_recipe.py`: verifies that another local project can compose the configured suite without copying agent internals.

## Public Release Boundary

Before release, run the checklist in [Release Checklist](release_checklist.md). Do not publish private voice assets, credentials, restricted textbook contents, personal images, personal local paths, or generated local run outputs.
