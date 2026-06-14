# 교육과정 매핑 엔진

[English](README.md)

교육과정 매핑 엔진은 성취기준을 재사용 가능한 학습 단위로 바꿉니다.

## 책임

- `CurriculumStandard` 정규화
- 학년, 과목, 학교급 기반 학습 단위 생성
- 데이터셋 coverage report
- 엔진 handoff metadata

## 공개 API

- `CurriculumMappingEngine(standards)`
- `build_learning_unit(...)`
- `coverage_report(dataset_sources)`

## 안전 경계

이 엔진은 성취기준을 매핑합니다. 학습자 결과를 채점하거나 기억을 승급하지 않습니다.
