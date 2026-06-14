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
```

## Run CLI

```powershell
python -m paideia_engines.cli run-config `
  --config examples\configured_suite.json `
  --output .paideia-runs\result.json `
  --output-dir .paideia-runs\engines

python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
```

## Output Meaning

- `result.json`: full configured-suite result.
- `.paideia-runs/engines/*.json`: per-engine outputs.
- `02_acquisition_validation.json`: acquired-source validation report.
- `10_verification.json`: final verification summary for the configured run.
- `smoke.json`: engine-by-engine smoke result.

## Public Release Boundary

Before release, run the checklist in [Release Checklist](release_checklist.md). Do not publish private voice assets, credentials, restricted textbook contents, personal images, or generated local run outputs.
