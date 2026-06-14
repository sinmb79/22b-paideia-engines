# 진짜 엔진 개발 로드맵

[English](real_engine_development.md)

이 문서는 파이데이아 엔진 모음을 단순한 예제 패키지가 아니라, 보스의 여러 AI 시스템에서 재사용할 수 있는 독립 엔진 자산으로 발전시키기 위한 실제 개발 로드맵입니다.

## 현재 위치

현재 엔진 모음은 데이터 확보, 교육과정 매핑, 육성, 평가, 스트레스, 승급, 거버넌스, 런타임, 설정 기반 오케스트레이션까지 v0.2 core를 갖추었습니다. Phase 6에서는 릴리스 하드닝을 추가했고, Phase 7에서는 확보 자료 validation report와 JSON 어댑터를 추가했습니다. Phase 8에서는 NCIC/data.go.kr 형식 CSV parsing, AI-Hub식 수학 JSON parsing, 공개 평가 CSV parsing, 공개 시험 metadata manifest를 추가했습니다. Phase 9에서는 parser diagnostics와 공개 안전 fixture pack을 추가했습니다. Phase 10에서는 configured-suite output validation을 추가했습니다. Phase 11에서는 acquired-source manifest diagnostics를 추가했습니다. 다음 심화 작업은 과목별 stress pack입니다.

## Phase 1: 데이터와 교육과정

추가된 파일:

```text
src/paideia_engines/data_acquisition/
src/paideia_engines/curriculum_mapping/
examples/data_and_curriculum_pipeline.py
data/curriculum/sample_standards.json
```

기능:

- 라이선스 gate 기반 출처 판단
- 엔진별 데이터 확보 계획
- 제한 교과서 차단
- 확보 자료 해시 기록
- JSONL manifest 작성
- 성취기준 기반 학습 단위 생성

## Phase 2: 평가와 육성

추가된 파일:

```text
src/paideia_engines/assessment/item_bank.py
examples/assessment_and_cultivation_pipeline.py
```

기능:

- 문항 bank
- 평가 gate 생성
- 객관식, 단답, 풀이과정 문항 모델
- 문항별 rubric scoring
- 승급 후보로 넘길 수 있는 review label 생성
- 학습 단위 기반 육성 roadmap 생성

## Phase 3: 스트레스와 승급

추가된 파일:

```text
src/paideia_engines/stress/scenario_bank.py
examples/stress_and_promotion_pipeline.py
```

기능:

- 교육과정 성취기준에 매핑되는 스트레스 시나리오 bank
- 성취기준과 stressor type 기준 시나리오 선택
- 승급 후보 신호만 생성
- 함정 위험 감지
- 버전 승급 원장
- 격리 경험 재심사
- 기록 삭제 없는 promoted 경험 대체

## Phase 4: 거버넌스와 런타임

추가된 파일:

```text
examples/governance_and_runtime_pipeline.py
```

기능:

- 정책 rule evaluation
- 보스 승인 및 라이선스 승인 기록
- 위원회 판단 원장
- 외부 업로드 hard blocking
- Runtime run ID
- Runtime artifact manifest
- 재실행 가능한 runtime trace
- 승급 검토용 acceptance checklist evidence

## Phase 5: 오케스트레이션과 CLI

추가된 파일:

```text
src/paideia_engines/orchestration/config_runner.py
src/paideia_engines/cli.py
examples/configured_suite.json
```

기능:

- 설정 기반 suite runner
- JSON config 입력과 JSON result 출력
- 엔진별 JSON output file
- End-to-end local growth pipeline
- 엔진별 smoke command
- 설정 기반 suite verification output
- 콘솔 진입점: `paideia-engines`

예제:

```powershell
python -m paideia_engines.cli run-config `
  --config examples/configured_suite.json `
  --output .paideia-runs/result.json `
  --output-dir .paideia-runs/engines

python -m paideia_engines.cli smoke --engine all --output .paideia-runs/smoke.json
```

## Phase 7: 데이터셋 어댑터와 검증

추가 파일:

```text
tests/test_dataset_adapters_and_validation.py
```

기능:

- 확보 자료 manifest loading
- hash, 로컬 경로, 승인자, license note 검증
- 제한 원문 자료 차단
- 제한 자료 metadata-only manifest 경로
- 공개 교육과정 standards JSON import
- 공개 또는 라이선스 평가 문항 JSON import
- 설정 기반 suite `acquisition_validation` 출력

## Phase 8: 출처별 파서

추가 파일:

```text
src/paideia_engines/data_acquisition/source_parsers.py
examples/source_specific_parsers.py
examples/source_samples/
tests/test_source_specific_parsers.py
```

기능:

- NCIC/data.go.kr 형식 교육과정 CSV parsing
- 공개 평가 CSV parsing
- AI-Hub식 수학 문제 JSON parsing
- EBSi/공개 시험 metadata-only manifest 생성
- Config runner parser/source 조합 검사

## Phase 9: 출처 parser diagnostics

추가 파일:

```text
src/paideia_engines/data_acquisition/source_diagnostics.py
examples/source_fixture_pack.json
tests/test_source_diagnostics.py
```

기능:

- Fixture-pack diagnostics report
- 파일 존재, hash, parser 지원, 확장자, 필수 field 검사
- Parser 실행 완료와 출력 record 수 검사
- CLI 명령: `diagnose-source`

## Phase 10: Configured-suite output validation

추가 파일:

```text
src/paideia_engines/orchestration/output_validator.py
tests/test_configured_suite_output_validator.py
```

기능:

- 엔진을 다시 실행하지 않는 엔진별 JSON output validation
- full suite result와 엔진별 파일 교차 검증
- `01_data_acquisition.json`부터 `10_verification.json`까지 번호가 붙은 output file 검증
- 엔진별 schema 계약 검증
- 확보 자료 검증, 평가, verification, stress candidate-only 경계, governance, runtime replayability release guardrail
- CLI 명령: `validate-suite-output`

## Phase 11: Acquired-source manifest diagnostics

추가 파일:

```text
src/paideia_engines/data_acquisition/manifest_diagnostics.py
examples/acquired_sources_manifest.jsonl
tests/test_acquired_source_manifest_diagnostics.py
```

기능:

- release check를 crash시키지 않고 issue로 보고하는 JSONL manifest diagnostics
- duplicate source/path record 탐지
- acquired-source schema와 content-scope 검사
- hash, path, approver, license-note 검증을 위해 기존 acquired-source validation 재사용
- non-open full-content record에 대한 public-release guardrail
- CLI 명령: `diagnose-manifest`

## 다음 개발 순서

1. 과목별 평가를 위한 stress scenario pack 확대.
2. 유효한 manifest 아래 실제 공개 출처 export를 이용한 official format-specific parser hardening.
3. 최종 검증이 계속 통과할 때 Ready PR/release 준비.

## 검증

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli run-config --config examples\configured_suite.json --output .paideia-runs\result.json --output-dir .paideia-runs\engines
python -m paideia_engines.cli validate-suite-output --output-dir .paideia-runs\engines --result .paideia-runs\result.json --output .paideia-runs\suite-output-validation.json
python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
```
