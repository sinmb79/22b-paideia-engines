# 거버넌스 엔진

[English](README.md)

거버넌스 엔진은 로컬 우선 정책을 평가하고 승인 기록을 남깁니다.

## 책임

- 정책 rule evaluation
- 보스 승인 기록
- 라이선스 승인 기록
- 위원회 판단 trail
- 외부 업로드 차단

## 공개 API

- `GovernanceEngine(policy=None)`
- `create_board(program_id)`
- `evaluate_policy(action, context=None)`
- `record_approval(...)`
- `record_committee_decision(...)`
- `review_action(action, context=None)`

## 안전 경계

외부 업로드는 기본 차단됩니다. 승인 기록은 hard upload ban을 우회하지 않습니다.
