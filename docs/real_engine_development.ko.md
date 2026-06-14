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

## 다음 순서

1. **Assessment Engine v0.2**
   - 문항 bank
   - 정답/오답/해설 구조
   - 서술형/풀이과정 rubric

2. **Cultivation Engine v0.2**
   - 학년/과목별 커리큘럼 그래프
   - 학습 로드맵과 자료 연결

3. **Stress Engine v0.2**
   - 오개념, 시간 압박, 모순 자료, 함정 문제 시나리오

4. **Promotion Engine v0.2**
   - 경험 승급 버전관리
   - 격리 사유와 재검토 흐름

5. **Governance Engine v0.2**
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
