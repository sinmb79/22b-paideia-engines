# Kibo Engine

The Kibo Engine provides deterministic contracts and governance helpers for reusing reviewed Kibo records and reinforced Pattern Candidates.

## Public APIs

- `TaskFingerprint`
- `KiboRecord`
- `ReuseDecision`
- `PatternCandidate`
- `PatternExamResult`
- `RealWorldOutcome`
- `FailureMemory`
- `CriticReport`
- `decide_reuse`
- `evaluate_kibo_governance`
- `evaluate_kibo_outcome`
- `reinforce_pattern`

## Safety Boundaries

- Use only reviewable Kibo records and pattern artifacts.
- Do not store or reuse hidden chain-of-thought.
- Quarantined records and patterns are blockers, not runtime inputs.
- High-risk direct reuse is forbidden.
- Reinforcement remains local-first and deterministic.

## Compatibility

Before `1.0`, additive fields are allowed. Any change that weakens quarantine, direct reuse gates, or schema meaning requires a new versioned schema and migration note.
