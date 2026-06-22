# Closed-Loop Curriculum Engine

Curriculum Engine은 검토된 실패를 재교육 과정으로 전환합니다.

```text
FailureMemory -> WeaknessRecord -> CurriculumPlan -> AdaptiveExam -> remediation evidence
```

모든 처리는 결정적이고 로컬 우선이며 JSON/JSONL 파일로 검토 가능합니다. 비공개 메모리나 hidden chain-of-thought를 입력으로 사용하지 않습니다. 런타임과 승격 게이트에는 검토 가능한 failure, weakness, curriculum, exam 산출물만 전달해야 합니다.

공개 API:

- `detect_weaknesses`
- `generate_curriculum_plan`
- `generate_adaptive_exam`
- `apply_curriculum_completion`

Governance와 Kibo reinforcement는 활성 `WeaknessRecord`를 받아 고심각도 또는 반복 약점이 있을 때 direct reuse와 강한 pattern reinforcement를 차단합니다.
