# 진짜 엔진 개발 로드맵

[English](real_engine_development.md)

이 문서는 파이데이아 엔진 모음을 단순한 예제 패키지가 아니라, 보스의 여러 AI 시스템에서 재사용할 수 있는 독립 엔진 자산으로 발전시키기 위한 실제 개발 로드맵입니다.

## 현재 위치

첫 개발 단계는 데이터 확보 엔진과 교육과정 매핑 엔진이었습니다. 육성, 평가, 스트레스, 승급 엔진은 모두 좋은 교육 데이터와 학년/과목/성취기준 매핑 위에서만 진짜 엔진이 될 수 있습니다.

Phase 2에서는 평가와 육성을 강화했습니다. Phase 3에서는 스트레스 리허설과 승급 엔진을 강화해서, 오케스트레이션 안에 묻힌 기능이 아니라 각각 따로 사용할 수 있는 자산으로 만들었습니다.

## Phase 1: 데이터와 교육과정

추가된 패키지:

```text
src/paideia_engines/data_acquisition/
src/paideia_engines/curriculum_mapping/
examples/data_and_curriculum_pipeline.py
data/curriculum/sample_standards.json
```

역할:

- 데이터 출처별 라이선스 판단
- 엔진별 데이터 확보 계획 생성
- 제한 자료 자동 수집 차단
- 확보 자료 해시 기록
- `acquired_sources.jsonl` 매니페스트 작성
- 성취기준 기반 학습 단위 생성
- 육성, 평가, 스트레스, 승급 엔진으로 handoff

예제:

```powershell
python examples\data_and_curriculum_pipeline.py
```

## Phase 2: 평가와 육성

추가된 파일:

```text
src/paideia_engines/assessment/item_bank.py
examples/assessment_and_cultivation_pipeline.py
```

강화된 기능:

- 문항 bank
- 평가 gate 생성
- 객관식, 단답, 풀이과정 문항 모델
- 문항별 rubric scoring
- 승급 후보로 넘길 수 있는 review label 생성
- 교육과정 learning unit 기반 육성 roadmap 생성
- roadmap 안에 assessment gate 배치

예제:

```powershell
python examples\assessment_and_cultivation_pipeline.py
```

## Phase 3: 스트레스와 승급

추가된 파일:

```text
src/paideia_engines/stress/scenario_bank.py
examples/stress_and_promotion_pipeline.py
```

강화된 기능:

- 교육과정 성취기준에 매핑되는 스트레스 시나리오 bank
- 성취기준과 stressor type 기준 시나리오 선택
- 성취기준별 스트레스 계획 생성
- 승급 결정이 아닌 승급 후보 신호만 내보내는 시나리오 실행
- 함정 문항 위험 감지와 검토 대기 차단
- 버전이 증가하는 승급 원장
- 격리 경험의 검증 후 재심사
- promoted 경험의 삭제 없는 대체
- 격리 및 superseded 경험을 제외하는 활성 기억 라우팅

예제:

```powershell
python examples\stress_and_promotion_pipeline.py
```

## 다음 개발 순서

1. Governance Engine v0.2: 정책 enforcement, 승인 기록, 위원회 판단 trail.
2. Runtime Engine v0.2: 더 강한 trace, acceptance evidence, 재현 가능한 task record.
3. Orchestration v0.2: 업그레이드된 엔진들을 독립 계약을 숨기지 않는 방식으로 조합.
4. Dataset adapters: 공개 교육과정/평가 데이터를 합법적으로 다루는 manifest 기반 adapter.

## 검증

```powershell
python -m pytest tests -q
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
```
