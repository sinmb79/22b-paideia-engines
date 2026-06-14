# Real Engine Development Roadmap

[한국어](real_engine_development.ko.md)

This roadmap tracks the work needed to turn the Paideia engine suite from a scaffold into reusable engine assets.

## Current Position

The suite now has v0.2 cores for data acquisition, curriculum mapping, cultivation, assessment, stress, promotion, governance, runtime, and config-driven orchestration. Phase 6 adds release hardening: per-engine READMEs, beginner-facing guides, public asset checks, and release checklists. The next depth work is stronger dataset adapters and validation reports for real public curriculum and assessment sources.

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

## Next Development Order

1. Dataset adapters: legal, manifest-driven adapters for public curriculum and assessment data.
2. Stronger validation reports for acquired source manifests and configured suite outputs.
3. Broader stress scenario packs for subject-specific evaluation.
4. Ready PR/release preparation after final validation remains green.

## Verification

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
```
