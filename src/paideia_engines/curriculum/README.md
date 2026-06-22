# Closed-Loop Curriculum Engine

The Curriculum Engine turns reviewed failures into training work:

```text
FailureMemory -> WeaknessRecord -> CurriculumPlan -> AdaptiveExam -> remediation evidence
```

It is deterministic, local-first, and JSON/JSONL friendly. It does not read private memory or hidden chain-of-thought. Only reviewable failure, weakness, curriculum, and exam artifacts should be passed into runtime or promotion gates.

Public APIs:

- `detect_weaknesses`
- `generate_curriculum_plan`
- `generate_adaptive_exam`
- `apply_curriculum_completion`

Governance and Kibo reinforcement can consume active `WeaknessRecord` objects. High-severity or repeated weaknesses block direct reuse and prevent strong pattern reinforcement until remediation succeeds.
