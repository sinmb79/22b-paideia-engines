# 폐쇄형 보완 교육과정 피드백 루프

릴리즈 목표: 2026-Q3  
코드명: Adaptive Curriculum Feedback Loop

이번 보완은 Paideia의 패턴 학습 루프를 다음 단계로 확장합니다.

```text
Learning -> Exam -> Outcome -> Reinforcement
```

에서:

```text
Outcome -> Weakness Detection -> Curriculum Generation -> Adaptive Exam -> Reinforcement Re-evaluation
```

으로 확장됩니다.

## 추가 내용

- `paideia_engines.curriculum`
- `WeaknessRecord`
- `CurriculumPlan`
- `AdaptiveExam`
- 실패 기록을 약점으로 변환하는 규칙
- 약점 기반 커리큘럼 생성
- 약점 심각도와 반복 횟수 기반 적응형 시험 생성
- 시험 완료 결과에 따른 약점 감소/증가
- 고심각도 또는 반복 약점에 대한 Kibo governance 차단
- 재교육 완료 전 pattern reinforcement 제한

## 안전 경계

- 로컬 JSON/JSONL 산출물만 사용합니다.
- 외부 DB 의존성을 추가하지 않습니다.
- hidden chain-of-thought를 사용하지 않습니다.
- 반복 약점은 direct reuse를 차단합니다.
- 고심각도 약점은 재시험 증거 전까지 강한 재사용을 막습니다.

## 검증

- 전체 테스트: `271 passed`
