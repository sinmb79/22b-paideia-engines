# 진짜 엔진 개발 로드맵

[English](real_engine_development.md)

## 현재 단계

`v0.2`의 첫 실제 개발 단위는 데이터 확보 엔진과 교육과정 매핑 엔진입니다. 이유는 간단합니다. 육성, 평가, 스트레스, 승급 엔진은 모두 좋은 교육 데이터와 학년/과목/성취기준 매핑 위에서만 진짜 엔진이 될 수 있습니다.

## 1순위: 데이터 확보 엔진

추가된 패키지:

```text
src/paideia_engines/data_acquisition/
```

역할:

- 데이터 출처별 라이선스 판단
- 엔진별 확보 계획 생성
- 제한 자료 자동 수집 차단
- 확보된 자료의 해시 기록
- `acquired_sources.jsonl` 매니페스트 작성

핵심 원칙:

- 교과서/디지털교과서/출판사 자료는 라이선스 없이는 차단합니다.
- AI-Hub 자료는 계정과 이용약관 확인 후 등록합니다.
- 공개 교육과정 자료는 출처 표시와 매니페스트를 남깁니다.

## 2순위: 교육과정 매핑 엔진

추가된 패키지:

```text
src/paideia_engines/curriculum_mapping/
```

역할:

- 학년, 과목, 영역, 성취기준 구조화
- 학습 단위 생성
- 데이터 출처가 어떤 성취기준을 커버하는지 보고
- 육성/평가/스트레스/승급 엔진으로 handoff

## Phase 2 진행 내용

추가된 패키지:

```text
src/paideia_engines/assessment/item_bank.py
```

강화된 기능:

- 문항 bank
- 평가 gate 생성
- 객관식/단답형/풀이과정 문항 모델
- item별 rubric scoring
- 평가 결과에서 promotion 후보로 넘길 수 있는 review label 생성
- 교육과정 learning unit 기반 육성 roadmap 생성
- roadmap 안에 assessment gate 배치

예제:

```powershell
python examples\assessment_and_cultivation_pipeline.py
```

## 다음 순서

1. **Stress Engine v0.2**
   - 오개념, 시간 압박, 모순 자료, 함정 문제 시나리오

2. **Promotion Engine v0.2**
   - 경험 승급 버전관리
   - 격리 사유와 재검토 흐름

3. **Governance Engine v0.2**
   - 저작권/데이터 사용 정책 enforcement
   - 보스 승인 기록

## 검증

현재 기준:

```powershell
python -m pytest tests -q
```

`v0.2` 첫 개발 후 기준:

- 데이터 확보 엔진 테스트
- 교육과정 매핑 엔진 테스트
- 기존 7개 엔진 회귀 테스트
- 예제 실행
