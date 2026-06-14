# 평가 엔진

[English](README.md)

평가 엔진은 파이데이아 엔진 묶음의 릴리스 증거를 벤치마크 팩 기준으로 검증합니다.

## 책임

- 벤치마크 팩 스키마 검증
- 엔진별 golden 출력 스키마 검증
- 변조/회귀 기대 항목 선언 검증
- 계약, 어댑터, 소스 fixture, manifest, stress pack, smoke, configured-suite 출력 증거 리포트 검증
- 릴리스 준비 임계값 검증

## 공개 API

- `validate_benchmark_pack(pack_path, result, output_dir, reports_dir=None)`

## CLI

```powershell
python -m paideia_engines.cli validate-benchmarks `
  --pack examples\benchmark_packs\core_engine_benchmark_pack.json `
  --result .paideia-runs\result.json `
  --output-dir .paideia-runs\engines `
  --reports-dir .paideia-runs `
  --output .paideia-runs\benchmark-validation.json
```

## 안전 경계

평가 엔진은 로컬 JSON 증거만 읽습니다. 엔진을 다시 실행하거나, 데이터셋을 다운로드하거나, 산출물을 업로드하거나, 기억을 승격하지 않습니다.
