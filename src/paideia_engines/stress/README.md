# Stress Engine

[한국어](README.ko.md)

The Stress Engine runs resilience scenarios while preserving the promotion boundary.

## Owns

- Stress rollouts
- Curriculum-linked scenario banks
- Trap-risk flags
- Candidate-only promotion signals

## Public API

- `StressEngine(scenario_bank=None)`
- `run_rollout(...)`
- `run_scenario(...)`
- `StressScenario`
- `StressScenarioBank`

## Safety Boundary

Stress can emit a candidate signal. It never writes a promotion decision.
