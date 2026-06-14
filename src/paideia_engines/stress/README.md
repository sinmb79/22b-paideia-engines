# Stress Engine

[한국어](README.ko.md)

The Stress Engine runs resilience scenarios while preserving the promotion boundary.

## Owns

- Stress rollouts
- Curriculum-linked scenario banks
- Subject-specific scenario packs
- Trap-risk flags
- Candidate-only promotion signals

## Public API

- `StressEngine(scenario_bank=None)`
- `run_rollout(...)`
- `run_scenario(...)`
- `StressScenario`
- `StressScenarioBank`
- `StressScenarioBank.from_file(path)`
- `diagnose_stress_scenario_pack(path)`

## Safety Boundary

Stress can emit a candidate signal. It never writes a promotion decision. `StressScenarioBank.from_file(...)` uses strict diagnostics by default and rejects unknown fields, invalid types, missing subject/grade metadata, and `promotion_decision`, `ledger_version`, or `experience_id` records.
