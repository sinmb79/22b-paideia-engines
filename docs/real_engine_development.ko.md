# 진짜 엔진 개발 로드맵

[English](real_engine_development.md)

이 문서는 파이데이아 엔진 모음을 단순한 예제 패키지가 아니라, 보스의 여러 AI 시스템에서 재사용할 수 있는 독립 엔진 자산으로 발전시키기 위한 실제 개발 로드맵입니다.

## 현재 위치

현재 엔진 모음은 데이터 확보, 교육과정 매핑, 육성, 평가, 스트레스, 승급, 거버넌스, 런타임, 설정 기반 오케스트레이션까지 v0.2 core를 갖추었습니다. Phase 6에서는 릴리스 하드닝을 추가했고, Phase 7에서는 확보 자료 validation report와 JSON 어댑터를 추가했습니다. Phase 8에서는 NCIC/data.go.kr 형식 CSV parsing, AI-Hub식 수학 JSON parsing, 공개 평가 CSV parsing, 공개 시험 metadata manifest를 추가했습니다. Phase 9에서는 parser diagnostics와 공개 안전 fixture pack을 추가했습니다. Phase 10에서는 configured-suite output validation을 추가했습니다. Phase 11에서는 acquired-source manifest diagnostics를 추가했습니다. Phase 12에서는 subject-specific stress pack을 추가했습니다. Phase 13에서는 공개 엔진 계약 레지스트리를 추가했습니다. Phase 14에서는 parser fixture를 valid acquired-source manifest record와 연결하는 adapter certification을 추가했습니다. Phase 15에서는 release evidence와 regression threshold를 확인하는 benchmark-pack validation을 추가했습니다. Phase 16에서는 persistent runtime evidence bundle과 artifact validation을 추가했습니다. Phase 17에서는 release-candidate packaging, link, encoding, sensitive pattern, 개인 로컬 경로, manifest boundary, public asset validation을 추가했습니다. 다음 심화 작업은 downstream reuse recipe입니다.

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

## Phase 12: Subject-specific stress packs

추가 파일:

```text
examples/stress_packs/core_subject_stress_pack.json
tests/test_stress_scenario_packs.py
```

기능:

- 수학, 국어/언어, 과학, evidence review용 공개 안전 reusable stress pack
- `StressScenarioBank.from_file(...)` 기반 stress pack JSON loader
- schema, unique id, valid scenario, curriculum link, subject coverage, promotion-boundary cleanliness용 stress pack diagnostics
- CLI 명령: `diagnose-stress-pack`

## Phase 13: 엔진 계약 레지스트리

추가 파일:

```text
src/paideia_engines/contracts/registry.py
docs/engine_contracts.md
docs/engine_contracts.ko.md
```

기능:

- 모든 재사용 엔진의 public contract registry
- API, input schema, output schema, CLI, example, doc, safety boundary, compatibility 선언
- Contract validation report
- CLI 명령: `validate-contracts`
- Pre-1.0 compatibility policy

## Phase 14: 공식 Adapter Certification Matrix

추가 파일:

```text
src/paideia_engines/data_acquisition/adapter_certification.py
examples/source_samples/public_assessment_sample.csv
tests/test_adapter_certification.py
```

기능:

- Source fixture diagnostics와 acquired-source manifest diagnostics를 연결하는 certification report
- CLI 명령: `certify-adapters`
- Parser/source allowlist 검사
- Fixture path/hash/source_id와 acquired-source manifest record linkage 검사
- Synthetic, metadata-only, open-public fixture export 정책

## Phase 15: Evaluation And Benchmark Pack

추가 파일:

```text
src/paideia_engines/evaluation/benchmark_pack.py
examples/benchmark_packs/core_engine_benchmark_pack.json
tests/test_benchmark_pack.py
```

기능:

- Benchmark pack schema와 report validation
- Golden configured-suite engine schema 검사
- Mutation/tamper expectation 선언
- Contract, adapter, source fixture, manifest, stress pack, smoke, suite-output, runtime evidence report 검증
- Minimum release-readiness threshold
- CLI 명령: `validate-benchmarks`

## Phase 16: Persistent Runtime Evidence Store

추가 파일:

```text
src/paideia_engines/runtime/evidence_store.py
examples/runtime_artifacts/math-evidence.json
tests/test_runtime_evidence_store.py
```

기능:

- Run ID 기준 runtime evidence bundle 저장
- Runtime run, trace, artifact manifest, acceptance checklist 파일화
- Bundle 내부 artifact copy 저장
- 실제 artifact file existence, size, SHA-256 validation
- In-memory runtime index 없이 disk-based replay
- CLI 명령: `persist-runtime-evidence`, `validate-runtime-evidence`, `replay-runtime-evidence`

## Phase 17: Release Candidate Pipeline

추가 파일:

```text
src/paideia_engines/release_candidate.py
tests/test_release_candidate.py
```

기능:

- Packaging metadata와 console script validation
- Markdown local link validation
- Public text file UTF-8 readability check
- Unicode replacement character detection
- Concrete sensitive-pattern scanning
- 개인 로컬 경로 scanning
- Acquired-source manifest public path와 content-scope check
- Public forbidden asset extension check
- Installed package target에서 console script와 module entrypoint wheel smoke
- CLI 명령: `validate-release-candidate`

## 다음 개발 순서

1. 다른 22B AI 프로젝트에서 바로 가져다 쓸 수 있는 downstream reuse recipe.

## 검증

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python examples\source_specific_parsers.py
python -m paideia_engines.cli validate-contracts --repo-root . --output .paideia-runs\contract-validation.json
python -m paideia_engines.cli certify-adapters --fixtures examples\source_fixture_pack.json --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\adapter-certification.json
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli diagnose-stress-pack --pack examples\stress_packs\core_subject_stress_pack.json --output .paideia-runs\stress-pack-diagnostics.json
python -m paideia_engines.cli run-config --config examples\configured_suite.json --output .paideia-runs\result.json --output-dir .paideia-runs\engines
python -m paideia_engines.cli validate-suite-output --output-dir .paideia-runs\engines --result .paideia-runs\result.json --output .paideia-runs\suite-output-validation.json
python -m paideia_engines.cli persist-runtime-evidence --runtime-output .paideia-runs\engines\09_runtime.json --store-dir .paideia-runs\runtime --artifact-base-dir examples --output .paideia-runs\runtime-evidence-bundle.json
python -m paideia_engines.cli validate-runtime-evidence --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json --output .paideia-runs\runtime-evidence-validation.json
python -m paideia_engines.cli replay-runtime-evidence --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json --output .paideia-runs\runtime-evidence-replay.json
python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
python -m paideia_engines.cli validate-benchmarks --pack examples\benchmark_packs\core_engine_benchmark_pack.json --result .paideia-runs\result.json --output-dir .paideia-runs\engines --reports-dir .paideia-runs --output .paideia-runs\benchmark-validation.json
python -m paideia_engines.cli validate-release-candidate --repo-root . --output .paideia-runs\release-candidate-validation.json
```
