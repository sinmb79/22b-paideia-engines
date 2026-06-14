# 아키텍처

[English](architecture.md)

## 신뢰 경계

설정 기반 suite 출력은 trace schema v2를 사용합니다. 검토 도구는 평가와 스트레스 이후에 거버넌스와 런타임이 실행되고, 그 다음에 승급과 검증이 온다는 순서에 의존할 수 있습니다. 거버넌스가 `blocked`를 반환하면 governance-blocked promotion quarantine 규칙에 따라 평가 점수가 높아도 승급 기록은 반드시 격리되고 보스 검토가 필요합니다. 이 격리 기록을 재심사하려면 quarantined `experience_id`, promotion이 발급한 `quarantine_ref`, `active_memory` 사용 범위에 묶이고 governance approval ledger 안의 같은 `experience_id` 및 `quarantine_ref` active `boss_approval`을 포함한 `memory_promotion`용 fresh allowed `paideia-governance-review/v1` payload가 필요하며, 단순 decision 문자열은 충분하지 않습니다. verified artifact는 런타임 evidence bundle 검증이 복사된 파일, 바이트 해시, manifest 해시, replay trace를 증명하기 전까지는 릴리스 검토 가능한 증거 주장으로만 취급하며, bundle-backed promotion은 v0.3 증거 파이프라인에서 더 깊게 연결합니다.

파이데이아 엔진은 하나의 에이전트 루프가 아니라, 명확한 엔진 경계를 중심으로 구성됩니다. 각 엔진은 한 종류의 판단을 책임지고, 다른 엔진이 소비할 수 있는 결정적 기록을 남깁니다.

```mermaid
flowchart TD
  Config["Config JSON"] --> Runner["설정 기반 실행기"]
  CLI["CLI"] --> Runner
  Runner --> DA["데이터 확보"]
  DA --> SP["출처별 파서"]
  SP --> CM["교육과정 매핑"]
  SP --> AS["평가"]
  CM --> C["육성"]
  C --> AS["평가"]
  AS --> S["스트레스"]
  S --> PS["승급 후보 신호"]
  PS --> P["승급"]
  Runner --> G["거버넌스"]
  G --> R["런타임"]
  R --> AM["Artifact Manifest"]
  R --> RT["Replayable Trace"]
  R --> P
  R --> V["검증"]
  P --> M["원장 / 활성 기억"]
  G --> B["보스 승인 기록"]
  G --> L["라이선스 승인 기록"]
  G --> CD["위원회 판단 원장"]
  V --> OUT["엔진별 JSON 출력"]
```

## 공통 계약

`paideia_engines.contracts`는 엔진들이 공유하는 작은 계약을 정의합니다.

- `EngineEvent`
- `ReviewLabel`
- `PromotionDecision`
- `QuarantineDecision`
- `default_local_policy()`

계약은 의도적으로 작게 유지합니다. 그래야 각 엔진이 독립적으로 개발되고 재사용될 수 있습니다.

## 엔진 경계

| 엔진 | 책임 | 책임이 아닌 것 |
| --- | --- | --- |
| 데이터 확보 | 출처 판단, 라이선스 gate, 확보 manifest | 교육과정 설계 |
| 출처별 파서 | 검증 이후 로컬 CSV/JSON 정규화 | 다운로드, 스크래핑, 라이선스 판단 |
| 교육과정 매핑 | 학습 단위와 성취기준 coverage | 채점 또는 승급 |
| 육성 | 청사진, 로드맵, handoff | 채점, 승급 |
| 평가 | 문항 bank, rubric 결과, transcript | 기억 승급 |
| 스트레스 | 시나리오 bank, 회복력 신호 | 승급 결정 |
| 승급 | 버전 원장, 격리, 활성 기억 라우팅 | 작업 실행 |
| 거버넌스 | 정책 평가, 승인 기록, 위원회 판단 | 모델 출력 생성 |
| 런타임 | 실행 trace, artifact manifest, replay evidence, checklist | 학습 업데이트 |
| 오케스트레이션 | 설정 기반 실행기, CLI 조합, 출력 경로, 검증 요약 | 각 엔진 내부 정책 |

## 설계 규칙

어떤 엔진도 다른 엔진의 결정을 조용히 대신하면 안 됩니다. 출처별 파서는 검증된 로컬 파일을 정규화할 수 있지만, 그 파일을 법적으로 사용할 수 있는지는 결정하지 않습니다. 스트레스 엔진은 승급 후보 신호를 만들 수 있지만, 실제 승급 결정은 승급 엔진만 만들 수 있습니다. 런타임은 증거를 기록할 수 있지만 기억을 활성화하지 않습니다. 거버넌스는 실행을 허용하거나 차단할 수 있지만 모델 출력을 생성하지 않습니다. 설정 기반 실행기는 엔진을 조합하고 산출물과 검증 요약을 저장하지만, 각 엔진 결과의 의미를 바꾸지 않습니다.
