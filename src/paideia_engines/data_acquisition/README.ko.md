# 데이터 확보 엔진

[English](README.md)

데이터 확보 엔진은 출처 라이선스를 우회하지 않고 교육 데이터 사용 계획을 만듭니다.

## 책임

- 출처별 라이선스 판단
- 엔진별 데이터 확보 계획
- 제한 교과서 차단
- 확보 자료 hash와 JSONL manifest 기록

## 공개 API

- `DataAcquisitionEngine(records, storage_root)`
- `evaluate_source(source_id)`
- `build_engine_plan(engine_name)`
- `register_acquired_source(...)`

## 안전 경계

이 엔진은 metadata와 로컬 확보 증거를 기록합니다. 제한 교과서를 자동 다운로드하지 않습니다.
