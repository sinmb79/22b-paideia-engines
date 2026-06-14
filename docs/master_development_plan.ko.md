# 22B 파이데이아 엔진 총괄 개발 마스터플랜

[English](master_development_plan.md)

## 목표

`22b-paideia-engines`는 샘플 패키지가 아닙니다. 보스의 여러 AI 시스템에서 재사용할 수 있는 엔진 제품군입니다. 최종 상태에서는 데이터 확보, 교육과정 매핑, 육성, 평가, 스트레스 리허설, 승급, 거버넌스, 런타임 추적, 설정 기반 오케스트레이션, 릴리스 가능한 문서를 모두 로컬 우선 방식으로 지원해야 합니다.

## 최종 완료 정의

다음 조건이 모두 충족되어야 최종 개발 완료로 봅니다.

- 모든 엔진이 독립 API, 계약, 테스트, 예제, 문서를 가진다.
- 데이터 확보는 출처, 라이선스, 해시, 승인자, 로컬 경로를 기록한다.
- 교육과정 매핑은 학년, 과목, 영역, 성취기준으로 학습 단위를 만든다.
- 육성은 교육과정 단위와 허가된 데이터 출처로 학습 로드맵을 만든다.
- 평가는 문항 bank, 정답, 오답, 해설, 서술형 채점, 풀이과정 rubric을 처리한다.
- 스트레스는 오개념, 시간 압박, 모순 자료, 함정 문항, 검토 누락을 시뮬레이션한다.
- 승급은 검토된 고품질 경험만 승급하고, 격리 재심사, 버전 관리, 대체 이력을 지원한다.
- 거버넌스는 보스 승인, 저작권/라이선스 규칙, 외부 업로드 금지, 위험 권한, 위원회 판단 이력을 강제한다.
- 런타임은 trace, checklist, artifact manifest, 재실행 가능한 실행 증거를 기록한다.
- 오케스트레이션은 각 엔진의 독립 계약을 숨기지 않고 설정으로 조합한다.
- CLI 명령은 JSON 입력/출력과 엔진별 smoke check를 제공한다.
- 테스트, 예제, 컴파일, CLI, README 링크 검증이 통과한다.
- GitHub PR/release 이력이 검증 가능해야 한다.

## Phase 상태

| Phase | 영역 | 상태 |
| --- | --- | --- |
| 0 | 기본 패키지와 초기 엔진 | 완료 |
| 1 | 데이터 확보와 교육과정 매핑 | v0.2 core 구현 |
| 2 | 평가와 육성 | v0.2 core 구현 |
| 3 | 스트레스와 승급 | v0.2 core 구현 |
| 4 | 거버넌스와 런타임 | v0.2 core 구현 |
| 5 | 오케스트레이션과 CLI | v0.2 core 구현 |
| 6 | 문서, 릴리스, 예제 | v0.2 릴리스 하드닝 구현 |

## Phase 0. Foundation

산출물:

- Python 패키지 골격
- 기본 엔진
- shared contracts
- 영문/한국어 README
- 기본 테스트와 예제
- 공개 GitHub 저장소

## Phase 1. 데이터와 교육과정

산출물:

- `DataAcquisitionEngine`
- `CurriculumMappingEngine`
- 교육 데이터 seed catalog
- 라이선스 gate
- sample standards
- 데이터/교육과정 pipeline 예제

남은 심화:

- 더 강한 manifest load/save API
- acquired source validation report
- curriculum standard importer
- coverage gap recommendations

## Phase 2. 평가와 육성

산출물:

- Assessment item bank
- 객관식, 단답, 서술형, 풀이과정 문항 모델
- 정답, 오답, 해설, scoring rubric
- 육성 learning roadmap
- 학습 로드맵과 데이터 출처 연결
- assessment gate 생성

## Phase 3. 스트레스와 승급

산출물:

- Stress scenario bank
- 오개념, 모순, 시간 압박, 함정 문항 시나리오
- 승급 후보 신호만 만드는 stress 실행
- Promotion ledger versioning
- 격리 경험 재심사 workflow
- 기록 삭제 없는 supersede decision

## Phase 4. 거버넌스와 런타임

산출물:

- Policy rule evaluator
- Boss approval records
- License approval records
- Committee decision ledger
- Runtime artifact manifest
- Replayable trace
- Run acceptance checklist

## Phase 5. 오케스트레이션과 CLI

산출물:

- Config-driven suite runner
- CLI commands
- JSON config 입력과 JSON result 출력
- 엔진별 JSON output file
- End-to-end local growth pipeline
- Engine-by-engine smoke commands
- 설정 기반 suite verification output

완료 기준:

- 로컬 명령 하나로 데이터 확보, 교육과정 매핑, 육성, 평가, 스트레스, 승급, 거버넌스, 런타임, 검증을 실행한다.
- 각 단계의 출력 경로와 trace metadata를 기록한다.
- Smoke command가 기존 `PaideiaEngineSuite.run_growth_cycle` 동작을 바꾸지 않고 개별 엔진 계약을 확인한다.

명령:

```powershell
python -m paideia_engines.cli run-config `
  --config examples/configured_suite.json `
  --output .paideia-runs/result.json `
  --output-dir .paideia-runs/engines

python -m paideia_engines.cli smoke --engine all --output .paideia-runs/smoke.json
```

## Phase 6. 문서, 릴리스, 예제

산출물:

- 초보자용 영문/한국어 guide
- 엔진별 README
- 예제 데이터 index
- Architecture diagrams
- Release checklist
- Public asset audit
- Dataset adapter backlog
- GitHub PR 갱신 경로

완료 기준:

- 처음 보는 사용자가 README만 보고 설치, 테스트, 예제 실행, CLI 실행, 출력 이해를 할 수 있다.
- README에서 한국어 설명서를 선택할 수 있다.
- 공개 릴리스에는 제한 교과서, 개인 음성, credential, 개인 자산이 포함되지 않는다.
- Release checklist가 테스트, 예제, 컴파일, CLI, 민감 문자열 검사를 증명한다.

## 현재 브랜치와 PR

```text
codex/real-engine-v02
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## 바로 다음 작업

이 브랜치의 최종 릴리스 루프를 진행합니다.

1. 전체 검증 실행
2. Phase 6 릴리스 하드닝 변경 커밋 및 푸시
3. 검증 증거를 Draft PR에 반영
4. 체크리스트가 계속 통과할 때만 PR ready 전환 또는 release 생성
