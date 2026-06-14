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

## 안전 경계

이 엔진은 검증된 고품질 경험만 승급하고, 격리되었거나 대체된 항목은 활성 기억에서 제외합니다.
