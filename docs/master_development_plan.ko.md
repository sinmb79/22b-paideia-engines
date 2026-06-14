# 22B 파이데이아 엔진 총괄 개발 마스터플랜

[English](master_development_plan.md)

## 목표

`22b-paideia-engines`는 샘플 패키지가 아닙니다. 보스의 여러 AI 시스템에서 재사용할 수 있는 엔진 제품군입니다. 최종 상태에서는 데이터 확보, 교육과정 매핑, 육성, 평가, 스트레스 리허설, 승급, 거버넌스, 런타임 추적, 설정 기반 오케스트레이션, 릴리스 가능한 문서를 모두 로컬 우선 방식으로 지원해야 합니다.

## 최종 완료 정의

다음 조건이 모두 충족되어야 최종 개발 완료로 봅니다.

- 모든 엔진이 독립 API, 계약, 테스트, 예제, 문서를 가진다.
- 데이터 확보는 출처, 라이선스, 해시, 승인자, 로컬 경로를 기록한다.
- Acquired-source manifest diagnostics는 malformed, duplicate, unsafe, public-release-ineligible record를 잡아낸다.
- 확보 자료 검증은 hash 불일치, 승인자 누락, license note 누락, 안전하지 않은 제한 원문 자료를 차단한다.
- 교육과정 매핑은 학년, 과목, 영역, 성취기준으로 학습 단위를 만든다.
- 육성은 교육과정 단위와 허가된 데이터 출처로 학습 로드맵을 만든다.
- 평가는 문항 bank, 정답, 오답, 해설, 서술형 채점, 풀이과정 rubric을 처리한다.
- 스트레스는 오개념, 시간 압박, 모순 자료, 함정 문항, 검토 누락을 시뮬레이션한다.
- Stress pack은 promotion boundary를 지키면서 curriculum-linked 과목별 scenario를 제공한다.
- 승급은 검토된 고품질 경험만 승급하고, 격리 재심사, 버전 관리, 대체 이력을 지원한다.
- 거버넌스는 보스 승인, 저작권/라이선스 규칙, 외부 업로드 금지, 위험 권한, 위원회 판단 이력을 강제한다.
- 런타임은 trace, checklist, artifact manifest, 재실행 가능한 실행 증거를 기록한다.
- 오케스트레이션은 각 엔진의 독립 계약을 숨기지 않고 설정으로 조합한다.
- CLI 명령은 JSON 입력/출력, configured-suite output validation, 엔진별 smoke check를 제공한다.
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
| 7 | 데이터셋 어댑터와 검증 리포트 | v0.2 core 구현 |
| 8 | 출처별 파서 | v0.2 core 구현 |
| 9 | 출처 parser diagnostics와 fixture pack | v0.2 core 구현 |
| 10 | configured-suite output validator | v0.2 core 구현 |
| 11 | acquired-source manifest diagnostics | v0.2 core 구현 |
| 12 | subject-specific stress scenario packs | v0.2 core 구현 |
| 13 | engine contract registry and compatibility gate | v0.2 core 구현 |
| 14 | official adapter certification matrix | v0.2 core 구현 |
| 15 | evaluation and benchmark pack | v0.2 core 구현 |
| 16 | persistent runtime and evidence store | v0.2 core 구현 |
| 17 | release candidate pipeline | v0.2 core 구현 |
| 18 | downstream reuse recipes | v0.2 core 구현 |

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

## Phase 7. 데이터셋 어댑터와 검증 리포트

산출물:

- 확보 자료 manifest loader
- 확보 자료 validation report
- hash, 로컬 경로, 승인자, license note 검사
- 제한 교과서 metadata를 위한 `metadata_only` 안전 경로
- 공개 교육과정 standards JSON 어댑터
- 공개 또는 라이선스 문항 bank JSON 어댑터
- 설정 기반 suite `acquisition_validation` 출력

완료 기준:

- 제한 교과서 본문 전체 자료는 유효한 license 또는 terms-review note 없이는 차단된다.
- 제한 자료도 metadata-only 기록은 보호 원본을 복사하지 않고 추적할 수 있다.
- 공개 교육과정 JSON은 `CurriculumStandard` record로 변환된다.
- 공개 또는 라이선스 평가 JSON은 `AssessmentItem` record로 변환된다.
- 설정 기반 suite 검증에 확보 자료 검증이 포함된다.

## Phase 8. 출처별 파서

산출물:

- NCIC/data.go.kr 형식 교육과정 CSV parser
- 공개 평가 CSV parser
- AI-Hub식 수학 문제 JSON parser
- 공개 시험 metadata CSV manifest builder
- Config runner parser/source 조합 검사
- Source parser 샘플과 예제 script

완료 기준:

- 출처별 parser는 확보 자료 검증을 통과한 파일에만 실행된다.
- parser/source 조합이 맞지 않으면 거부된다.
- AI-Hub식 데이터는 terms/license note 검증 이후에만 parser를 사용할 수 있다.
- EBSi/공개 시험 자료는 metadata-only로 유지하며 보호 문서에서 평가 문항을 생성하지 않는다.

## Phase 9. 출처 parser diagnostics와 fixture pack

산출물:

- Source parser diagnostics report
- 공개 안전 source fixture pack manifest
- 필수 CSV header와 JSON field 검사
- Parser 실행 완료와 record 수 검사
- Fixture diagnostics용 CLI 명령

완료 기준:

- Fixture pack은 상대 경로와 공개 안전 sample 또는 metadata-only content만 사용한다.
- Diagnostics report가 파일 존재, hash, parser 지원 여부, 필수 field, parser 실행 완료, 출력 record 수를 보고한다.
- Parser 실행 실패가 숨겨지지 않고 diagnostics issue로 기록된다.
- Release checklist에 diagnostics CLI 명령이 포함된다.

## Phase 10. Configured-suite output validator

산출물:

- 설정 기반 suite 실행 결과의 엔진별 output validator
- result JSON과 엔진별 파일의 교차 검증
- `01_data_acquisition.json`부터 `10_verification.json`까지 번호가 붙은 파일 검증
- 엔진별 schema 계약 검증
- 확보 자료 검증, 최종 verification, stress-to-promotion 경계, governance, runtime replayability release guardrail
- CLI 명령: `validate-suite-output`

완료 기준:

- 엔진을 다시 실행하지 않고도 configured-suite 산출물을 검증할 수 있다.
- 엔진별 파일이 누락되거나 변조되면 release validation이 blocked가 된다.
- Stress output은 candidate-only이며 promotion decision record를 직접 포함할 수 없다.
- Release checklist에 output validator CLI 명령이 포함된다.

## Phase 11. Acquired-source manifest diagnostics

산출물:

- Acquired-source JSONL manifest diagnostics
- 공개 안전 manifest 예제
- JSONL parsing, acquired-source schema, duplicate record, content-scope, hash/license-note, auto-download, public-release safety check
- CLI 명령: `diagnose-manifest`

완료 기준:

- Manifest diagnostics가 malformed JSONL을 release check crash 없이 잡아낸다.
- Duplicate source/path record는 release validation을 blocked로 만든다.
- Non-open full-content record는 local-only mode를 명시하지 않는 한 public release에서 blocked가 된다.
- Release checklist에 manifest diagnostics CLI 명령이 포함된다.

## Phase 12. Subject-specific stress scenario packs

산출물:

- 공개 안전 과목별 stress scenario pack
- Stress scenario pack loader
- Stress scenario pack diagnostics
- `promotion_decision`, `ledger_version`, `experience_id` promotion-boundary leak check
- CLI 명령: `diagnose-stress-pack`

완료 기준:

- Stress pack은 수학, 국어/언어, 과학 scenario를 포함한다.
- 모든 scenario는 적어도 하나의 curriculum standard id에 연결된다.
- Stress pack diagnostics는 promotion-decision 또는 ledger record를 거부한다.
- Release checklist에 stress pack diagnostics CLI 명령이 포함된다.

## Phase 13. Engine contract registry

산출물:

- 공개 엔진 계약 레지스트리
- 계약 검증 리포트
- CLI 명령: `validate-contracts`
- 1.0 이전 additive change, schema version bump, deprecation 정책
- 영문/한국어 엔진 계약 문서

완료 기준:

- 모든 재사용 엔진이 계약 레지스트리에 등록된다.
- 모든 계약은 공개 API 이름, 입력/출력 schema, 문서, 예제, 안전 경계를 선언한다.
- Release checklist가 parser, manifest, stress pack, suite output, smoke check 전에 계약 검증을 포함한다.
- Orchestration은 조합 계층으로 남고 개별 엔진 계약을 숨기지 않는다.

## Phase 14. Official adapter certification matrix

산출물:

- Adapter certification report
- CLI 명령: `certify-adapters`
- Public assessment CSV fixture
- Acquired-source manifest record와 연결된 source fixture pack
- Parser/source allowlist checks
- Manifest hash/source/path linkage checks
- Non-open source를 위한 public-safe sample policy checks

완료 기준:

- 모든 public parser fixture는 source id, local path, hash 기준으로 valid acquired-source manifest record와 연결된다.
- Source fixture diagnostics와 acquired-source manifest diagnostics가 certification 전에 통과한다.
- 허용되지 않은 parser/source pair는 차단된다.
- Non-open source fixture는 synthetic, user-created, metadata-only public-safe sample이어야 한다.
- EBSi/public exam data는 metadata-only로 남고 assessment item content로 인증되지 않는다.
- Release checklist에 adapter certification CLI 명령이 포함된다.

## 최종 개발 총괄 프로그램

남은 작업은 개별 패치가 아니라 연결된 프로그램으로 진행합니다.

1. **Phase 15: Evaluation and benchmark pack**
   - 구현 완료: golden schema, benchmark evidence report, mutation expectation, release readiness threshold, `validate-benchmarks` CLI.
   - 모든 엔진별 golden fixture를 추가합니다.
   - schema, boundary, stress coverage, assessment quality, governance evidence에 대한 mutation/tamper test를 추가합니다.
   - release readiness를 위한 최소 coverage threshold를 정의합니다.

2. **Phase 16: Persistent runtime and evidence store**
   - 구현 완료: runtime evidence bundle 저장, artifact 복사, 실제 파일 size/hash 검증, 디스크 기반 replay, `persist-runtime-evidence`/`validate-runtime-evidence`/`replay-runtime-evidence` CLI.
   - Python process가 종료된 뒤에도 재생 가능한 run bundle을 저장합니다.
   - 실제 artifact file 존재, 크기, content hash를 검증합니다.
   - artifact manifest validation을 release path에 추가합니다.

3. **Phase 17: Release candidate pipeline**
   - 구현 완료: packaging metadata, link, UTF-8, replacement character, sensitive pattern, 개인 로컬 경로, acquired-source manifest, public asset boundary 검증과 `validate-release-candidate` CLI.
   - 설치된 패키지 기준 console script와 module entrypoint wheel smoke를 실행합니다.
   - link, encoding, concrete sensitive-pattern, personal-path check를 추가합니다.
   - GitHub release evidence를 준비합니다.

4. **Phase 18: Downstream reuse recipes**
   - 구현 완료: 다른 22B AI project가 가져다 쓸 수 있는 integration recipe.
   - 엔진 하나만 import하는 예제와 full configured-suite 조합 예제를 함께 추가했습니다.
   - local agent 내부 구현에서 reusable package contract로 이동하는 migration note를 추가했습니다.
   - 영문/한국어 downstream reuse 문서를 추가했습니다.

## 현재 브랜치와 PR

```text
codex/real-engine-v02
https://github.com/sinmb79/22b-paideia-engines/pull/1
```

## 바로 다음 작업

다음 단계는 총괄 프로그램 순서대로 진행합니다.

1. Phase 18 이후 최종 release check 실행
2. 모든 checklist와 gate가 계속 green일 때만 PR ready 전환 또는 release 생성
