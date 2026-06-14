# 승급 엔진

[English](README.md)

승급 엔진은 검토된 경험이 활성 기억이 될 수 있는지 결정합니다.

## 책임

- 버전 승급 원장
- 격리 경험
- 격리 경험 재심사
- promoted 경험 대체
- 활성 기억 라우팅

## 공개 API

- `PromotionEngine(owner, minimum_score=80)`
- `record_experience(...)`
- `reconsider_quarantined(...)`
- `supersede_promoted(...)`
- `route_active_memory(...)`
- `owner`, `minimum_score`, `ledger`, `events`는 read-only accessor입니다.

`PromotionEngine(owner, minimum_score=80)`는 초기화 시 trust config를 검증합니다. `owner`는 앞뒤 공백이 없는 비어 있지 않은 문자열이어야 하며, `minimum_score`는 0과 100 사이의 정수여야 합니다.

Promotion gate는 generic review helper보다 엄격합니다. memory promotion 또는 `PromotionDecision.from_review(...)` 결과 생성에는 `review.status == "verified"`만 충분합니다. Generic `ReviewLabel.is_verified()`는 `approved` 또는 `passed`를 허용할 수 있지만, Promotion은 이 상태만으로 active memory를 만들지 않습니다.

`ledger`, `events`, 반환된 promotion decision, active-memory route는 detached mutable snapshots입니다. Python 객체 의미상 반환 snapshot 수정은 가능하지만 엔진 내부 상태는 바뀌지 않습니다. 큰 ledger에서는 snapshot copy 비용이 생길 수 있으므로, 대용량 사용은 향후 persistence/replay backend를 우선 고려합니다.

## 안전 경계

이 엔진은 검증된 고품질 경험만 승급하고, 격리되었거나 대체된 항목은 활성 기억에서 제외합니다.
