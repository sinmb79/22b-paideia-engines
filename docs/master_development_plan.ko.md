# 22B Paideia Engines 총괄 개발 마스터플랜

[English](master_development_plan.md)

## 목표

`22b-paideia-engines`의 목표는 단순한 샘플 패키지가 아니라, 보스의 여러 AI 프로그램에 재사용할 수 있는 핵심 엔진 제품군을 완성하는 것이다. 최종 상태에서는 각 엔진이 독립 사용 가능하고, 함께 조합하면 교육 데이터 확보부터 성장 사이클, 평가, 스트레스, 승급, 거버넌스, 실행 추적까지 이어지는 완전한 로컬 우선 AI 성장 시스템이 되어야 한다.

## 최종 완료 정의

다음 조건을 모두 만족해야 최종 개발 완료로 본다.

- 각 엔진은 독립 API, 계약, 테스트, 예제, 문서를 가진다.
- 데이터 확보는 출처, 라이선스, 해시, 승인자, 로컬 경로를 매니페스트로 남긴다.
- 교육과정 매핑은 학년, 과목, 영역, 성취기준을 기준으로 학습 단위를 만든다.
- 육성 엔진은 교육과정 단위와 데이터 출처를 연결해 학습 로드맵을 만든다.
- 평가 엔진은 문항 bank, 정답/오답/해설, 서술형/풀이과정 rubric을 처리한다.
- 스트레스 엔진은 오개념, 시간 압박, 모순 자료, 함정 문제, 검토 누락을 시뮬레이션한다.
- 승급 엔진은 검토된 고품질 경험만 승급하고, 격리 기록과 재검토 흐름을 가진다.
- 거버넌스 엔진은 보스 승인, 저작권/라이선스, 외부 업로드 금지, 위험 권한을 강제한다.
- 런타임 엔진은 trace, checklist, artifact manifest, replay 가능한 실행 기록을 남긴다.
- 오케스트레이션 엔진은 각 엔진을 설정 파일 기반으로 조합한다.
- 전체 테스트, 예제, 컴파일, README 링크 검증이 통과한다.
- GitHub 공개 레포와 Draft/Ready PR 이력이 검증 가능해야 한다.

## 개발 단계

### Phase 0. Foundation

상태: 완료

산출물:

- Python 패키지 골격
- 7개 기본 엔진
- contracts
- 한/영 README
- 기본 테스트
- GitHub 공개 레포

검증:

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
```

### Phase 1. Data And Curriculum Core

상태: 진행 중

산출물:

- `DataAcquisitionEngine`
- `CurriculumMappingEngine`
- 교육 데이터 seed catalog
- 라이선스 게이트
- sample standards
- 데이터+교육과정 pipeline 예제

남은 작업:

- source manifest load/save API
- acquired source validation report
- curriculum standard importer
- coverage gap recommendations

### Phase 2. Assessment And Cultivation Core

상태: 다음 구현 묶음

산출물:

- `AssessmentEngine` v0.2 문항 bank
- 객관식/단답형/서술형/풀이과정 문항 모델
- 정답, 오답, 해설, scoring rubric
- `CultivationEngine` v0.2 학습 로드맵
- 교육과정 단위와 데이터 출처 연결
- 학습 단계별 평가 gate 생성

완료 기준:

- 학습 단위에서 평가 gate와 문항 bank를 만들 수 있다.
- 평가 결과가 승급 엔진으로 넘길 수 있는 review label 후보를 만든다.
- 학습 로드맵이 데이터 출처의 라이선스 상태를 보존한다.

### Phase 3. Stress And Promotion Core

상태: 예정

산출물:

- stress scenario bank
- misconception, contradiction, time pressure, trap item simulation
- promotion ledger versioning
- quarantine review workflow
- rollback or supersede decision

완료 기준:

- 스트레스 엔진은 승급 후보 신호만 만들고 승급 결정은 만들지 않는다.
- 승급 엔진은 review label 없이는 기억을 승급하지 않는다.
- 격리 경험은 active memory route에서 제외된다.

### Phase 4. Governance And Runtime Core

상태: 예정

산출물:

- policy rule evaluator
- boss approval records
- license approval records
- runtime artifact manifest
- replayable trace
- run acceptance checklist

완료 기준:

- 제한 자료 사용은 승인 기록 없이는 차단된다.
- 외부 업로드, credential, private asset 접근은 기본 차단된다.
- runtime 결과는 promotion 전 검토 상태로 남는다.

### Phase 5. Orchestration And CLI

상태: 예정

산출물:

- config-driven suite runner
- CLI commands
- JSON input/output
- end-to-end local growth pipeline
- engine-by-engine smoke commands

완료 기준:

- 로컬 명령 하나로 데이터 계획, 커리큘럼 매핑, 육성, 평가, 스트레스, 승급, 거버넌스, 런타임 검증을 실행한다.
- 각 단계는 산출물 경로와 trace를 남긴다.

### Phase 6. Documentation, Release, And Examples

상태: 예정

산출물:

- 한/영 사용 설명서
- 엔진별 README
- 예제 데이터
- architecture diagrams
- release checklist
- GitHub PR/Release

완료 기준:

- 처음 보는 사용자가 README만 보고 설치, 테스트, 예제 실행을 할 수 있다.
- 한국어 설명서는 README에서 선택 가능하다.
- 공개 레포에는 저작권 제한 자료가 포함되지 않는다.

## 작업 운영 방식

- 모든 엔진 개발은 TDD로 진행한다.
- 한 번에 하나의 함수가 아니라, Phase 단위로 묶어서 진행한다.
- 각 Phase는 테스트, 예제, 문서, 커밋, PR 업데이트까지 포함한다.
- 공개 레포에는 원천 교과서 파일을 넣지 않는다.
- 제한 자료는 `manual_license_required`와 승인 매니페스트로만 연결한다.

## 현재 활성 브랜치

```text
codex/real-engine-v02
```

현재 Draft PR:

```text
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## 바로 다음 작업

Phase 2를 시작한다.

1. assessment item bank 테스트 추가
2. assessment rubric/result 구조 강화
3. cultivation roadmap 테스트 추가
4. cultivation roadmap 구현
5. data/curriculum/assessment 연결 예제 추가
6. 전체 테스트와 예제 검증
7. 커밋/푸시/PR 업데이트
