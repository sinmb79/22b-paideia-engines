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
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
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
```

## 출력 의미

- `result.json`: 전체 설정 기반 실행 결과입니다.
- `.paideia-runs/engines/*.json`: 엔진별 출력입니다.
- `02_acquisition_validation.json`: 확보 자료 검증 리포트입니다.
- `10_verification.json`: 설정 기반 실행의 최종 검증 요약입니다.
- `suite-output-validation.json`: result JSON, 엔진별 파일, 스키마, stress-to-promotion 경계를 교차 검증하는 release-quality 리포트입니다.
- `smoke.json`: 엔진별 smoke 결과입니다.

## 공개 릴리스 경계

릴리스 전 [릴리스 체크리스트](release_checklist.ko.md)를 실행합니다. 개인 음성, credential, 제한 교과서 본문, 개인 이미지, 생성된 로컬 실행 산출물은 공개하지 않습니다.
