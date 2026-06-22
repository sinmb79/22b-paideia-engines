# Kibo Engine

Kibo Engine은 검토된 Kibo record와 강화된 Pattern Candidate를 재사용하기 위한 deterministic 계약과 governance helper를 제공합니다.

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

## 안전 경계

- 검토 가능한 Kibo record와 pattern artifact만 사용합니다.
- hidden chain-of-thought는 저장하거나 재사용하지 않습니다.
- quarantined record/pattern은 runtime 입력이 아니라 차단 신호입니다.
- high-risk direct reuse는 금지합니다.
- reinforcement는 local-first deterministic 방식으로 유지합니다.

## 호환성

`1.0` 이전에는 additive field 추가를 허용합니다. quarantine, direct reuse gate, schema 의미를 약화하는 변경은 새 versioned schema와 migration note가 필요합니다.
