# 릴리스 가이드

[English](release_guide.md)

이 문서는 처음 보는 사용자가 파이데이아 엔진을 로컬에서 설치, 테스트, 실행할 수 있도록 안내합니다.

## 설치

```powershell
git clone https://github.com/sinmb79/22b-paideia-engines.git
cd 22b-paideia-engines
python -m pip install -e .[dev]
```

## 검증

```powershell
python -m pytest tests -q
python -m compileall src
```

## 예제 실행

```powershell
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python examples\source_specific_parsers.py
python examples\downstream_single_engine_recipe.py
python examples\downstream_suite_recipe.py
python -m paideia_engines.cli validate-contracts --repo-root . --output .paideia-runs\contract-validation.json
python -m paideia_engines.cli certify-adapters --fixtures examples\source_fixture_pack.json --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\adapter-certification.json
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli diagnose-stress-pack --pack examples\stress_packs\core_subject_stress_pack.json --output .paideia-runs\stress-pack-diagnostics.json
```

## CLI 실행

```powershell
python -m paideia_engines.cli run-config `
  --config examples\configured_suite.json `
  --output .paideia-runs\result.json `
  --output-dir .paideia-runs\engines

python -m paideia_engines.cli validate-suite-output `
  --output-dir .paideia-runs\engines `
  --result .paideia-runs\result.json `
  --output .paideia-runs\suite-output-validation.json

python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json

python -m paideia_engines.cli persist-runtime-evidence `
  --runtime-output .paideia-runs\engines\09_runtime.json `
  --store-dir .paideia-runs\runtime `
  --artifact-base-dir examples `
  --output .paideia-runs\runtime-evidence-bundle.json

python -m paideia_engines.cli validate-runtime-evidence `
  --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json `
  --output .paideia-runs\runtime-evidence-validation.json

python -m paideia_engines.cli replay-runtime-evidence `
  --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json `
  --output .paideia-runs\runtime-evidence-replay.json

python -m paideia_engines.cli validate-benchmarks `
  --pack examples\benchmark_packs\core_engine_benchmark_pack.json `
  --result .paideia-runs\result.json `
  --output-dir .paideia-runs\engines `
  --reports-dir .paideia-runs `
  --output .paideia-runs\benchmark-validation.json

python -m paideia_engines.cli validate-release-candidate `
  --repo-root . `
  --output .paideia-runs\release-candidate-validation.json
```

## 출력 의미

- `result.json`: 전체 설정 기반 실행 결과입니다.
- `.paideia-runs/engines/*.json`: 엔진별 출력입니다.
- `contract-validation.json`: 공개 엔진 API, schema, 문서, 예제, 안전 경계 레지스트리 검증 결과입니다.
- `adapter-certification.json`: parser fixture가 valid acquired-source manifest record와 연결되어 있음을 증명하는 adapter certification matrix입니다.
- `manifest-diagnostics.json`: JSONL parsing, hash, duplicate record, license note, public-release safety를 확인하는 acquired-source manifest diagnostics입니다.
- `stress-pack-diagnostics.json`: curriculum link, subject coverage, promotion-boundary cleanliness를 확인하는 stress scenario pack diagnostics입니다.
- `02_acquisition_validation.json`: 확보 자료 검증 리포트입니다.
- `10_verification.json`: 설정 기반 실행의 최종 검증 요약입니다.
- `suite-output-validation.json`: result JSON, 엔진별 파일, 스키마, stress-to-promotion 경계를 교차 검증하는 release-quality 리포트입니다.
- `smoke.json`: 엔진별 smoke 결과입니다.
- `runtime-evidence-bundle.json`: 재실행 가능한 runtime evidence bundle index입니다.
- `runtime-evidence-validation.json`: artifact file 존재, size, byte hash, manifest hash, trace replay를 검증합니다.
- `runtime-evidence-replay.json`: 저장된 bundle에서 로드한 replayable trace입니다.
- `benchmark-validation.json`: golden schema, mutation expectation, release evidence threshold를 확인하는 benchmark report입니다.
- `release-candidate-validation.json`: packaging metadata, link, UTF-8, replacement character, sensitive pattern, 개인 로컬 경로, acquired-source manifest, public asset boundary를 검증합니다.
- `downstream_single_engine_recipe.py`: 엔진 하나를 downstream asset으로 import할 수 있음을 검증합니다.
- `downstream_suite_recipe.py`: 다른 local project가 agent 내부 코드를 복사하지 않고 configured suite를 조합할 수 있음을 검증합니다.

## 공개 릴리스 경계

릴리스 전 [릴리스 체크리스트](release_checklist.ko.md)를 실행합니다. 개인 음성, credential, 제한 교과서 본문, 개인 이미지, 개인 로컬 경로, 생성된 로컬 실행 산출물은 공개하지 않습니다.
