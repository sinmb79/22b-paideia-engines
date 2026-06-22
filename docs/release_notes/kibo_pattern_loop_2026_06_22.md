# Kibo Pattern Reinforcement Governance

Release date: 2026-06-22

This release extends `22b-paideia-engines` with deterministic contracts and governance rules for Paideia's Pattern Layer. The engine now treats Kibo records as concrete cases and Pattern Candidates as abstract strategies that must be validated before strong reuse.

## Highlights

- Added Pattern Candidate, PatternExamResult, RealWorldOutcome, FailureMemory, and CriticReport contracts.
- Added a deterministic `reinforce_pattern` engine using exam score, real-world score, user feedback, reuse stability, and failure penalty.
- Added status transitions for `draft`, `exam_validated`, `field_validated`, `reinforced`, `weakened`, and `quarantined`.
- Extended Kibo governance so high-risk direct reuse requires field validation and self-critic clearance when a pattern is involved.
- Added blockers for quarantined patterns and failure-memory warnings during direct reuse.
- Preserved existing Kibo reuse contracts and tests.

## Validation

- `22b-paideia-engines`: 263 tests passed.
- Kibo targeted tests: 13 tests passed.

## Post-Review Hardening

- High-risk direct reuse is now consistently forbidden in governance.
- Namespaced validation failures such as `validation_failure:self_critic_gate` and `validation_failure:failure_memory` block direct reuse.
- Quarantined patterns remain quarantined unless a separate governance process changes status.
- Failed exams are treated as failed evidence even with high numeric scores.
- Kibo is now listed in the engine contract registry and engine documentation index.

<details>
<summary>한국어 설명 보기</summary>

# Kibo Pattern Reinforcement Governance

릴리즈 일자: 2026-06-22

이번 릴리즈는 `22b-paideia-engines`에 Paideia Pattern Layer를 위한 deterministic 계약과 governance 규칙을 추가합니다. Kibo record는 구체 사례로, Pattern Candidate는 검증을 거쳐야 하는 추상 전략으로 다룹니다.

## 주요 변경

- Pattern Candidate, PatternExamResult, RealWorldOutcome, FailureMemory, CriticReport 계약 추가
- exam score, real-world score, user feedback, reuse stability, failure penalty 기반 `reinforce_pattern` 엔진 추가
- `draft`, `exam_validated`, `field_validated`, `reinforced`, `weakened`, `quarantined` 상태 전환 추가
- high-risk direct reuse에 field validation과 self-critic clearance 요구
- quarantined pattern과 failure warning이 direct reuse를 차단하도록 governance 확장
- 기존 Kibo reuse 계약과 테스트 호환성 유지

## 검증

- `22b-paideia-engines`: 전체 263개 테스트 통과
- Kibo targeted test: 13개 통과

## 리뷰 후 보강

- high-risk direct reuse를 governance에서 일관되게 금지했습니다.
- `validation_failure:self_critic_gate`, `validation_failure:failure_memory` 같은 namespaced validation failure도 direct reuse를 차단합니다.
- quarantined pattern은 별도 governance 절차 없이는 자동 복구되지 않습니다.
- failed exam은 숫자 점수가 높아도 실패 evidence로 처리합니다.
- Kibo를 engine contract registry와 engine documentation index에 등록했습니다.

</details>
